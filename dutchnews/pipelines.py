# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import os
import time
from oauth2client.service_account import (
    ServiceAccountCredentials,
)
from gspread_dataframe import (
    set_with_dataframe,
)
from nltk.tokenize import (
    sent_tokenize,
)
import gspread
import pandas as pd
import openai
import nltk
from enum import Enum
import configparser
from pathlib import Path

nltk.download("punkt")


path_to_config = Path(__file__).parent.joinpath('data', 'config.ini')
config = configparser.ConfigParser()
config.read(path_to_config, encoding="utf-8")

CREDENTIALS_FILE = config["PATH"]["CREDENTIALS_FILE"]
SPREADSHEET_ID = config["PATH"]["SPREADSHEET_ID"]
openai.api_key = config["API_KEY"]["OPEN_AI"]

EXCLUDED_TYPE_CELL_FROM_REWRITE = [
    "H",
    "DATE",
]
HEADLINE_LISTS = [
    "H1",
    "H2",
]


class StopTimeBetweenRequests(Enum):
    """
    Перечисления, переменных содержащих время остановки исполнения программы  между запросами.
    """
    usual = 30
    emergency = 60


class DutchnewsPipeline:
    def __init__(
        self,
    ):
        self.df = pd.DataFrame(
            columns=[
                "Type",
                "English",
                "Options",
            ]
        )

    def process_item(self, item, spider):
        """
        Processes the item scraped by the spider.

        This method takes in the scraped item and performs the following
        operations: cleaning the text, combining sentences into text,
        splitting the text into sentences, and rewriting the text.

        Parameters:
        - item (dict): The scraped item.
        - spider (Spider): The spider that scraped the item.

        Returns:
        - item (dict): The processed item.

        """

        item = self.combining_sentences_into_text(item)
        item = self.text_rewriting(item)

        df_latest_news = pd.DataFrame(item)
        df_latest_news = self.splitting_the_text_into_sentences(df_latest_news)
        df_latest_news = df_latest_news.applymap(self.clean_text)

        self.df = self.df.append(
            df_latest_news,
            ignore_index=True,
        )

        return df_latest_news

    def clean_text(
        self,
        text: str,
    ) -> str:
        """
        Очищает вводимый текст, удаляя пробелы и кавычки.

        Parameters:
        text (str): Вводимый текст, который необходимо очистить.

        Returns:
        text (str): Очищенный текст.
        """
        text = text.strip()
        text = text.replace(
            "\n",
            "",
        )
        if text.startswith('"') and text.endswith('"'):
            if '"' not in text[1:-1]:
                text = text[1:-1]
        return text

    def combining_sentences_into_text(
        self,
        item: dict,
    ) -> dict:
        """
        Объединяет несколько предложений из словаря в единый текст.

        Parameters:
        item (dict): Входной словарь, содержащий данные, которые необходимо обработать.

        Returns:
        item (dict): Модифицированный словарь со сборными предложениями.
        """
        list_type = []
        list_options = []
        list_English = []

        for (type_cell, options_cell, english_cell,) in zip(
            item["Type"],
            item["Options"],
            item["English"],
        ):
            if (
                options_cell in HEADLINE_LISTS
                or type_cell in EXCLUDED_TYPE_CELL_FROM_REWRITE
            ):
                list_type.append(type_cell)
                list_options.append(options_cell)
                list_English.append(english_cell)
            else:
                list_type[-1].append(type_cell)
                list_options[-1].append(options_cell)
                list_English[-1].append(english_cell)

            if options_cell in HEADLINE_LISTS:
                list_type.append([])
                list_options.append([])
                list_English.append([])

        item["Type"] = [
            tag[0] if type(tag) == list else tag for tag in list_type
        ]
        item["Options"] = [
            options[0] if type(options) == list else options
            for options in list_options
        ]
        item["English"] = ["".join(text) for text in list_English]

        return item

    def splitting_the_text_into_sentences(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """ 
        Объединяет несколько предложений из словаря в единый текст.

        Parameters:
        item (dict): Входной словарь, содержащий данные, которые необходимо обработать.

        Returns:
        item (dict): Модифицированный словарь со сборными предложениями.
        """
        # Split the text column into sentences
        df = df.assign(English=df["English"].apply(lambda x: sent_tokenize(x)))
        # Convert the list of sentences in each row into separate rows
        df = df.explode("English")
        return df

    def text_rewriting(
        self,
        item: dict,
    ) -> dict:
        """ 
        Перепишите текст, используя языковую модель GPT-3 OpenAI.

        Этот метод использует языковую модель GPT-3 OpenAI для 
        рерайта текста на ангойиском языке.

        Parameters:
        - item (dict)

        Returns:
        - item (dict): Список с рерайтнутым параметром English.
        """
        row_number = 0
        for (english_cell, options_cell, type_cell,) in zip(
            item["English"],
            item["Options"],
            item["Type"],
        ):
            if (
                options_cell not in HEADLINE_LISTS
               and type_cell not in EXCLUDED_TYPE_CELL_FROM_REWRITE
               ):

                prompt = (
                    """Rewrite the following sentence, 
                    except quotes, 
                    add more uniqueness,
                    the text should deceive the anti-plagiarism service,
                    logically divided into paragraphs: \n"""
                    + english_cell
                )
                status = "Not completed"
                rate_limit_retry_count = 10

                while status != "OK":
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
                        status = "OK"
                    except openai.error.RateLimitError as error:
                        status == "ERROR"
                        print(error)
                        rate_limit_retry_count -= 1
                        if rate_limit_retry_count == 0:
                            break
                        time.sleep(StopTimeBetweenRequests.emergency.value)

                item["English"][row_number] = completions.choices[0].text
            row_number += 1
            time.sleep(StopTimeBetweenRequests.usual.value)
        return item

    def close_spider(
        self,
        spider,
    ):
        def preparing_a_dataframe(df: pd.DataFrame) -> None:
            """
            Эта функция подготавливает dataframe, добавляя новые столбцы 
            "Placement", "Media" и "Voice" и изменяя порядок столбцов.

            Parameters:
            df (pandas.DataFrame): DataFrame входных данных.

            Returns:
            pandas.DataFrame: Обновленный и переупорядоченный DataFrame.
            """
            df_length = len(df)
            df = df.assign(
                Placement=[""] * df_length,
                Media=[""] * df_length,
                Voice=[""] * df_length,
            )
            df = df[
                [
                    "Placement",
                    "Media",
                    "Type",
                    "Options",
                    "Voice",
                    "English",
                ]
            ]
            return df

        def saving_to_google_sheets(
            df: pd.DataFrame,
        ) -> None:
            """
            Сохранение df в google sheets.

            Parameters:
            df (pandas.DataFrame): DataFrame входных данных.

            Returns: None
            """

            # Авторизуемся и получаем service — экземпляр доступа к API
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                CREDENTIALS_FILE,
                [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ],
            )

            gc = gspread.authorize(credentials)

            # open a google sheet
            gs = gc.open_by_key(SPREADSHEET_ID)

            # select a work sheet from its name
            worksheet1 = gs.worksheet("Sheet1")

            # write to dataframe
            set_with_dataframe(
                worksheet=worksheet1,
                dataframe=df,
                include_index=False,
                include_column_header=True,
                resize=True,
            )

        self.df = preparing_a_dataframe(self.df)
        saving_to_google_sheets(self.df)
