import scrapy


class DutchNewsSpider(scrapy.Spider):
    name = "dutchnews"
    start_urls = [
        'https://www.dutchnews.nl/'
    ]
    custom_settings = {'FEED_URI': 'dutchnews_%(time)s.xlsx',
                       'FEED_FORMAT': 'xlsx'}

    def parse(self, response):
        # follow the list of links to news categories
        links = response.xpath(
            '//*[@id="body"]/section/div/div[1]/div/h3/a/@href').getall()
        for link in links:
            yield response.follow(link, self.parse_news)

    def parse_news(self, response):
        # extract the text from the header of each news article
        links = response.xpath(
            '//*[@id="body"]/section/div/div[1]/div[3]/ul/li/a/@href').getall()
        for link in links:
            yield response.follow(link, self.parse_item)

    def parse_item(self, response):
        item = {}
        tags = []
        texts = []

        # extract the text from the header
        header_text = response.xpath('//header/h1/text()').get()
        tags.append('H1')
        texts.append(header_text)

        # extract the text from the content
        content_text = response.xpath(
            '//div[contains(@class, "entry-content ")]/p')  

        for el in content_text:
            text = el.xpath('./text() | a/text() | ./strong/text()').getall()
            full_text = ''.join(text)
            tag = 'p' if el.xpath('./text() | a/text()').getall() else 'H2'
            tags.append(tag)
            texts.append(full_text)

        item['tag'] = tags
        item['text'] = texts

        yield item