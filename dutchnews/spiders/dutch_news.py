import scrapy
from enum import Enum


class Xpath(Enum):
    news_categories = r'//*[@id="body"]/section/div/div[1]/div/h3/a/@href'
    news_article = r'//*[@id="body"]/section/div/div[1]/div[3]/ul/li/a/@href' 
    text_header = r'//header/h1/text()'
    element_p = r'//div[contains(@class, "entry-content ")]/p'
    elements_containing_text = r'./text() | a/text() | ./strong/text()'
    text_inside_paragraphs = r'./text() | a/text()'
    


class DutchNewsSpider(scrapy.Spider):
    name = "dutchnews"
    start_urls = [
        'https://www.dutchnews.nl/'
    ]
    custom_settings = {'FEED_URI': 'dutchnews_%(time)s.xlsx',
                       'FEED_FORMAT': 'xlsx'}

    def parse(self, response):
        # follow the list of links to news categories
        links = response.xpath(Xpath.news_categories.value).getall()[:1]
        for link in links:
            yield response.follow(link, self.parse_news)

    # def parse(self, response):
    #     # follow the list of links to news categories
    #     links = response.xpath(Xpath.news_categories.value).getall()
    #     for link in links:
    #         yield response.follow(link, self.parse_news)

    def parse_news(self, response):
        # extract the text from the header of each news article
        links = response.xpath(
            Xpath.news_article.value).getall()[:1]
        for link in links:
            yield response.follow(link, self.parse_item)


    # def parse_news(self, response):
    #     # extract the text from the header of each news article
    #     links = response.xpath(
    #         Xpath.news_article.value).getall()
    #     for link in links:
    #         yield response.follow(link, self.parse_item)

    def parse_item(self, response):
        item = {}
        tags = []
        texts = []

        # extract the text and tag from the header
        header_text = response.xpath(Xpath.text_header.value).get()
        tags.append('H1')
        texts.append(header_text)

        # extract the text and tag from the content
        content_text = response.xpath(Xpath.element_p.value)  

        for el in content_text:
            text = el.xpath(Xpath.elements_containing_text.value).getall()
            full_text = ''.join(text)
            tag = 'p' if el.xpath(Xpath.text_inside_paragraphs.value).getall() else 'H2'
            tags.append(tag)
            texts.append(full_text)

        item['tag'] = tags
        item['text'] = texts

        yield item