## Инструкция по использованию 
**Настройка проекта:**
1. Нужно получить API от google cloude (весьма понятное объяснение https://codesolid.com/google-sheets-in-python-and-pandas/)в виде json файла.
2. Поместить json файл в проект, желательно в отдельную папку data (...\news-parser\dutchnews\data)
3. Внутри ...\news-parsernews-parser\dutchnews\pipelines.py нужно найти константу CREDENTIALS_FILE и указать в кавычках полный путь (можно и относительный, но иногда он не находит файл по нему).
4. Открыть json файл и скопировать из него client_email.
5. Взять  таблицу, которую вы используете для выгрузки данных(в https://docs.google.com/) и нажать на кнопку "настройки доступа" добавить client_email и нажать отправить.
6. Внутри news-parser\dutchnews\pipelines.py нужно найти константу SPREADSHEET_ID и указать в кавычках ID таблицы его можно найти в URL (Выглядит примерно так: 3ln1rhANfDqyyaEtIZokFfuVivgrW4L3io20)


**Запуск проекта:**
1. Открыть cmd.
2. Перейти в дирректорию, где храниться проект (...\news-parser\dutchnews\spiders)
3. Указать команду: scrapy crawl dutchnews


**Как уменьшить число новостей для  парсинга:**
1. При уменьшении числа категорий:
	В news-parser\dutchnews\spiders\dutch_news.py методе parse найти строку с данным кодом:
	links = response.xpath(Xpath.news_categories.value).getall()  и добавить [:n] - где n это число категорий, получиться:
	links = response.xpath(Xpath.news_categories.value).getall()[:n]
	
2. Числа новостей с каждой категории: 	
	В news-parser\dutchnews\spiders\dutch_news.py методе parse_news найти строку с данным кодом:
	links = response.xpath(Xpath.news_article.value).getall()  и добавить [:n] - где n это число новостей, получиться:
	links = response.xpath(Xpath.news_article.value).getall()[:n]