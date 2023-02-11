# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe
import gspread
from nltk.tokenize import sent_tokenize
import pandas as pd
import openai
import os
import time
import nltk
nltk.download('punkt')


openai.api_key = os.environ.get('gpt_api_key')
headline_lists = ['H1', 'H2']


# Файл, полученный в Google Developer Console
CREDENTIALS_FILE = r''
# ID Google Sheets документа (можно взять из его URL)
SPREADSHEET_ID = r''


class DutchnewsPipeline:

    def __init__(self):
        self.df = pd.DataFrame(columns=['Type', 'English', 'Options'])

    def process_item(self, item, spider):
        def clean_text(text):
            text = text.strip()
            text = text.replace("\n", "")
            if text.startswith('"') and text.endswith('"'):
                if '"' not in text[1:-1]:
                    text = text[1:-1]
            return text

        def combining_sentences_into_text(item):
            list_type = []
            list_options = []
            list_English = []

            for type_cell, options_cell, english_cell in zip(item['Type'], item['Options'], item['English']):
                if options_cell in headline_lists or type_cell in 'H':
                    list_type.append(type_cell)
                    list_options.append(options_cell)
                    list_English.append(english_cell)
                else:
                    list_type[-1].append(type_cell)
                    list_options[-1].append(options_cell)
                    list_English[-1].append(english_cell)

                if options_cell in headline_lists:
                    list_type.append([])
                    list_options.append([])
                    list_English.append([])

            item['Type'] = [tag[0] if type(
                tag) == list else tag for tag in list_type]
            item['Options'] = [options[0] if type(
                options) == list else options for options in list_options]
            item['English'] = [''.join(text) for text in list_English]

            return item

        def splitting_the_text_into_sentences(item):
            df = pd.DataFrame(item)
            # Split the text column into sentences
            df = df.assign(English=df['English'].apply(
                lambda x: sent_tokenize(x)))

            # Convert the list of sentences in each row into separate rows
            df = df.explode('English')

            return(df)

        def text_rewriting(item):
            count = 0
            for english_cell, options_cell, type_cell in zip(item['English'], item['Options'], item['Type']):
                if options_cell not in headline_lists and type_cell != 'H':
                    status = 'Not completed'
                    rate_limit_retry_count = 10
                    prompt = "Rewrite the following sentence, except quotes, add more uniqueness, the text should deceive the anti-plagiarism service: \n" + english_cell

                    while status != 'OK':
                        try:
                            completions = openai.Completion.create(
                                engine="text-davinci-003",
                                presence_penalty=0.8,
                                prompt=prompt,
                                max_tokens=1024,
                                n=1,
                                stop=None,
                                temperature=0.7,
                            )
                            status = 'OK'
                        except openai.error.RateLimitError as error:
                            status == 'ERROR'
                            print(error)
                            rate_limit_retry_count -= 1
                            if rate_limit_retry_count == 0:
                                break
                            else:
                                time.sleep(60)

                    item['English'][count] = completions.choices[0].text
                count += 1
                time.sleep(25)
            return item

        df_rewriting = splitting_the_text_into_sentences(
            text_rewriting(combining_sentences_into_text(item)))

        self.df = self.df.append(df_rewriting, ignore_index=True)

        self.df = self.df.applymap(clean_text)
        df_length = len(self.df)

        self.df = self.df.assign(Placement=[''] * df_length,
                                 Media=[''] * df_length,
                                 Voice=[''] * df_length
                                 )
        self.df = self.df[['Placement', 'Media',
                           'Type', 'Options', 'Voice', 'English']]
        return df_rewriting

    def close_spider(self, spider):
        def saving_to_google_sheets(df):
            # Авторизуемся и получаем service — экземпляр доступа к API
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                CREDENTIALS_FILE,
                ['https://www.googleapis.com/auth/spreadsheets',
                 'https://www.googleapis.com/auth/drive'])

            gc = gspread.authorize(credentials)

            # open a google sheet
            gs = gc.open_by_key(SPREADSHEET_ID)

            # select a work sheet from its name
            worksheet1 = gs.worksheet('Sheet1')

            # write to dataframe
            set_with_dataframe(worksheet=worksheet1, dataframe=df, include_index=False,
                               include_column_header=True, resize=True)
        saving_to_google_sheets(self.df)
