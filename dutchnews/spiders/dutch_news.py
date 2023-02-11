import scrapy
from enum import Enum


class Xpath(Enum):
    news_categories = r'//*[@id="body"]/section/div/div[1]/div/h3/a/@href'
    news_article = r'//*[@id="body"]/section/div/div[1]/div[3]/ul/li/a/@href'
    text_header = r'//header/h1/text()'
    element_p = r'//div[contains(@class, "entry-content ")]/p'
    elements_containing_text = r'./text() | a/text() | ./strong/text()'
    text_inside_paragraphs = r'./text() | a/text()'
    news_release_date = r'//header/div/span/text()'


class DutchNewsSpider(scrapy.Spider):
    name = "dutchnews"
    start_urls = [
        'https://www.dutchnews.nl/'
    ]
    custom_settings = {'FEED_URI': 'dutchnews_%(time)s.xlsx',
                       'FEED_FORMAT': 'xlsx'}

    def parse(self, response):
        # follow the list of links to news categories
        links = response.xpath(Xpath.news_categories.value).getall()
        for link in links:
            yield response.follow(link, self.parse_news)

    def parse_news(self, response):
        # extract the text from the header of each news article
        links = response.xpath(
            Xpath.news_article.value).getall()
        for link in links:
            yield response.follow(link, self.parse_item)

    def parse_item(self, response):
        def filling_dictionary_by_rows(item, type_cell, options_cell, english_cell):
            item['Type'].append(type_cell)
            item['Options'].append(options_cell)
            item['English'].append(english_cell)

        item = {'Type': [], 'Options': [], 'English': []}

        # extract the text and tag from the header
        header_text = response.xpath(Xpath.text_header.value).get()
        filling_dictionary_by_rows(item, 'H', '', header_text)

        # extract the text and tag from the content
        data = response.xpath(Xpath.news_release_date.value).get()
        filling_dictionary_by_rows(item, 'DATE', '', data)

        filling_dictionary_by_rows(item, 'T', 'H1', header_text)

        content_text = response.xpath(Xpath.element_p.value)

        for el in content_text:
            text = el.xpath(Xpath.elements_containing_text.value).getall()
            full_text = ''.join(text)
            if el.xpath(Xpath.text_inside_paragraphs.value).getall():
                filling_dictionary_by_rows(item, 'T', '', full_text)
            else:
                filling_dictionary_by_rows(item, 'T', 'H2', full_text)
        print(item)
        yield item
