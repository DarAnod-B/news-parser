from enum import (
    Enum,
)
import scrapy


class Xpath(Enum):
    """
    Перечисление XPath, используемых для извлечения информации из новостных статей.
    """

    news_categories = r'//*[@id="body"]/section/div/div[1]/div/h3/a/@href'
    news_article = r'//*[@id="body"]/section/div/div[1]/div[3]/ul/li/a/@href'
    text_header = r"//header/h1/text()"
    element_p = r'//div[contains(@class, "entry-content ")]/p'
    elements_containing_text = r"./text() | a/text() | ./strong/text()"
    text_inside_paragraphs = r"./text() | a/text()"
    news_release_date = r"//header/div/span/text()"


class DutchNewsSpider(scrapy.Spider):
    """
    Scrapy паук для извлечения информации из новостных статей на dutchnews.nl .

    Этот паук переходит по ссылкам на категории новостей, по ссылкам на отдельные
    новостные статьи и извлекает такую информацию, как заголовок, дата выхода и
    содержание каждой статьи. Извлеченная информация сохраняется в словаре
    с ключами "Type", "Options" и "English".
    """

    name = "dutchnews"
    start_urls = ["https://www.dutchnews.nl/"]
    custom_settings = {
        "FEED_URI": "dutchnews_%(time)s.xlsx",
        "FEED_FORMAT": "xlsx",
    }

    def parse(
        self,
        response: scrapy.http.response.Response,
    ):
        """
        Парсинг списка ссылок на категории новостей.

        Args:
            response (scrapy.http.response.Response):

        Returns:
            None
        """
        # follow the list of links to news categories
        links = response.xpath(Xpath.news_categories.value).getall()
        for link in links:
            yield response.follow(
                link,
                self.parse_news,
            )

    def parse_news(
        self,
        response: scrapy.http.response.Response,
    ):
        """
        Парсинг списка ссылок на отдельные новостные статьи.

        Args:
            response (scrapy.http.response.Response): The response object.

        Returns:
            None
        """
        # extract the text from the header of each news article
        links = response.xpath(Xpath.news_article.value).getall()
        for link in links:
            yield response.follow(
                link,
                self.parse_item,
            )

    def parse_item(
        self,
        response: scrapy.http.response.Response,
    ):
        """
        Проанализируйте ответ на предмет информации из новостной статьи.

        Этот метод заполняет словарь такой информацией, как заголовок, выпуск
        дата и содержание статьи.

        Args:
            response (scrapy.http.response.Response): The response object.

        Returns:
            dict: словарь с ключами "Type", "Options" и "English" и
                  извлеченной информацией в виде значений.
        """

        def filling_dict_by_rows(
            item,
            type_cell,
            options_cell,
            english_cell,
        ):
            """
            Заполните словарь информацией, извлеченной из ответа.

            Args:
                item (dict): Словарь, который должен быть заполнен информацией.
                type_cell (str): список внутри словаря содержащий колонку Type нашей будущей таблицы.
                options_cell (str): список  внутри словаря содержащий колонку Options нашей будущей таблицы.
                english_cell (str): список словаря содержащий колонку English нашей будущей таблицы.

            Returns:
                None
            """
            item["Type"].append(type_cell)
            item["Options"].append(options_cell)
            item["English"].append(english_cell)

        item = {
            "Type": [],
            "Options": [],
            "English": [],
        }

        # extract the text and tag from the header
        header_text = response.xpath(Xpath.text_header.value).get()
        filling_dict_by_rows(
            item,
            "H",
            "",
            header_text,
        )

        # extract the text and tag from the data
        data = response.xpath(Xpath.news_release_date.value).get()
        filling_dict_by_rows(
            item,
            "DATE",
            "",
            data,
        )

        filling_dict_by_rows(
            item,
            "T",
            "H1",
            header_text,
        )

        content_text = response.xpath(Xpath.element_p.value)

        for el in content_text:
            text = el.xpath(Xpath.elements_containing_text.value).getall()
            full_text = "".join(text)
            if el.xpath(Xpath.text_inside_paragraphs.value).getall():
                filling_dict_by_rows(
                    item,
                    "T",
                    "",
                    full_text,
                )
            else:
                filling_dict_by_rows(
                    item,
                    "T",
                    "H2",
                    full_text,
                )
        print(item)
        yield item
