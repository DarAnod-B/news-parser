# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


import pandas as pd
import openai
import os
import time

openai.api_key = os.environ.get('gpt_api_key')

tags_ignored_rewrite = ['H1', 'H2']


class DutchnewsPipeline:

    def __init__(self):
        self.df = pd.DataFrame(columns=['tag', 'text'])

    def process_item(self, item, spider):
        def clean_text(text):
            text = text.strip()
            text = text.replace("\n", "")
            if text.startswith('"') and text.endswith('"'):
                if '"' not in text[1:-1]:
                    text = text[1:-1]
            return text

        def combining_text_paragraphs(item):
            list_text = []
            list_tag = []
            for text, tag in zip(item['text'], item['tag']):
                if tag in ['H1', 'H2']:
                    list_tag.append(tag)
                    list_text.append(text)
                    list_tag.append([])
                    list_text.append([])
                else:
                    list_tag[-1].append(tag)
                    list_text[-1].append(text)

            item['text'] = [''.join(text) for text in list_text]
            item['tag'] = [tag[0] if type(
                tag) == list else tag for tag in list_tag]
            return item

        def text_rewriting(item):
            count = 0
            for text, tag in zip(item['text'], item['tag']):
                if tag not in tags_ignored_rewrite:
                    status = 'Not completed'
                    rate_limit_retry_count = 10
                    prompt = "Rewrite the following sentence, except quotes, add more uniqueness, the text should deceive the anti-plagiarism service: \n" + text

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
                        except openai.error.RateLimitError:
                            status == 'ERROR'
                            rate_limit_retry_count -= 1
                            if rate_limit_retry_count == 0:
                                break
                            else:
                                time.sleep(60)

                    item['text'][count] = clean_text(
                        completions.choices[0].text)
                count += 1
                time.sleep(20)
            return item

        item_rewriting = text_rewriting(combining_text_paragraphs(item))

        self.df = self.df.append(pd.DataFrame(
            item_rewriting), ignore_index=True)
        return item_rewriting

    def close_spider(self, spider):
        self.df.to_excel(f"{spider.name}_rec.xlsx", index=False)
