# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

import pandas as pd
import openai

# Set up the OpenAI API key
openai.api_key = "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"
tags_ignored_rewrite = ['H2']


class DutchnewsPipeline:

    def __init__(self):
        self.df = pd.DataFrame(columns=['tag', 'text'])

    def process_item(self, item, spider):
        def clean_text(text):
            text = text.strip()  # remove spaces from the beginning and end of the text
            text = text.rstrip('\n')  # remove line breaks
            return text

        for count, text in enumerate(item['text']):
            if item['tag'][count] not in tags_ignored_rewrite:
                # The prompt to be passed to the API
                prompt = "Rewrite the following sentence, except quotes, don't put quotes where there are no quotes,  don't create new quotes, use only existing ones: \n" + text

                # Call the API and get the response
                completions = openai.Completion.create(
                    engine="text-davinci-002",
                    prompt=prompt,
                    max_tokens=1024,
                    n=1,
                    stop=None,
                    temperature=0.5,
                )
                item['text'][count] = clean_text(completions.choices[0].text)

        self.df = self.df.append(pd.DataFrame(item), ignore_index=True)
        return item

    def close_spider(self, spider):
        self.df.to_excel(f"{spider.name}_rec.xlsx", index=False)
