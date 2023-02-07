# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import pandas as pd



import pandas as pd

class DutchnewsPipeline:
    def __init__(self):
        self.df = pd.DataFrame(columns=['tag', 'text'])

    def process_item(self, item, spider):
        self.df = self.df.append(pd.DataFrame(item), ignore_index=True)
        return item

    def close_spider(self, spider):
        self.df.to_excel(f"{spider.name}.xlsx", index=False)
