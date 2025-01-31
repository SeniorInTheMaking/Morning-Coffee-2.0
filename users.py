from mysql.connector import connect
from openai import OpenAI
import requests
import time
import re


def access_database(database, request):
    with connect(
            host=database['host'],
            port=database['port'],
            user=database['user'],
            password=database['password'],
            database=database['database']
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(request)
            result = cursor.fetchall()
            connection.commit()
            return result


class GoodArticles:
    def __init__(self, id, web, url, title, content, summary, status):
        self.id = id
        self.web = web
        self.url = url
        self.title = title
        self.content = content
        self.summary = summary
        self.status = status


    def check_article(self, user_stop_words, user_key_words):
        for stop_word in user_stop_words:
            stop_pattern = r'\b' + re.escape(stop_word.lower()) + r'\b'
            if re.search(stop_pattern, self.title.lower()) or re.search(stop_pattern, self.content.lower()):
                return False

        all_key_words_count = 0
        main_key_word = ''
        main_key_word_count = 0

        for key_word in user_key_words:
            all_repetitions = 0
            key_pattern = r'\b' + re.escape(key_word.lower()) + r'\b'
            if re.search(key_pattern, self.title.lower()):
                all_repetitions += 3
            all_repetitions += len(re.findall(key_pattern, self.content.lower()))
            all_key_words_count += all_repetitions

            if all_repetitions > main_key_word_count:
                main_key_word = key_word

        if all_key_words_count >= 5:
            return main_key_word, all_key_words_count
        return False

    def compress_article(self, api_key, model, prompt1, prompt2, database):
        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt1},
                {"role": "user", "content": self.content}
            ]
        )
        summarized_article = completion.choices[0].message.content

        if summarized_article.count('\n') < 2 or len(summarized_article) > 800:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt2},
                    {"role": "user", "content": summarized_article}
                ]
            )
            summarized_article = completion.choices[0].message.content

        self.summary = summarized_article

        request = f"""update NS_table set Summary = '{self.summary}', Status = 'summarized' where id = '{self.id}'"""
        access_database(database, request)

    def send_message(self, tg_channel, bot_token):
        message = f"[{self.web}]({self.url}) *{self.title}*\n\n{self.summary}"
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        params = {'chat_id': tg_channel, 'text': message, 'parse_mode': 'Markdown',
                  'disable_web_page_preview': True}

        for i in range(2):
            response = requests.post(url, data=params)

            if response.status_code == 200:
                break

            elif response.status_code == 429:
                retry_after = response.json().get('parameters', {}).get('retry_after', 45)
                time.sleep(retry_after)


class Users:
    def __init__(self, user_id, user_tg_channel, user_news_limit, user_webs, user_key_words, user_stop_words, user_sent_urls, user_sent_titles):
        self.user_id = user_id
        self.user_tg_channel = user_tg_channel
        self.user_news_limit = user_news_limit
        self.user_webs = user_webs
        self.user_key_words = user_key_words
        self.user_stop_words = user_stop_words
        self.user_sent_urls = user_sent_urls
        self.user_sent_titles = user_sent_titles

    def detect_interesting_articles(self, database, api_key, model, prompt1, prompt2, bot_token):
        webs_for_request = f"({', '.join([f"'{web.split('/')[2]}'" for web in self.user_webs])})"
        request = f"select id, Web, URL, Title, Content, Summary, status from NS_table where Status in ('downloaded', 'summarized') and Web in {webs_for_request} and DownloadTime > NOW() - INTERVAL 1 DAY;"
        all_articles = access_database(database, request)

        sent_news_count = 0
        used_key_words = []
        good_articles = []

        for article in all_articles:
            if sent_news_count >= self.user_news_limit:
                break
            if str(article[0]) not in self.user_sent_urls:

                article = GoodArticles(article[0], article[1], article[2], article[3], article[4], article[5], article[6])
                check = article.check_article(self.user_stop_words, self.user_key_words)

                if check:
                    key_word = check[0]
                    key_word_count = check[1]

                    if key_word in used_key_words:
                        good_articles.append([article, key_word_count])
                    else:
                        if article.status == 'downloaded' and not article.summary:
                            article.compress_article(api_key, model, prompt1, prompt2, database)
                        article.send_message(self.user_tg_channel, bot_token)

                        sent_news_count += 1
                        used_key_words.append(key_word)
                        self.user_sent_urls.append(str(article.id))

        if sent_news_count < self.user_news_limit:
            good_articles = sorted(good_articles, key=lambda article: article[1], reverse=True)
            for article in good_articles[:self.user_news_limit - sent_news_count]:
                article = article[0]
                article = GoodArticles(article.id, article.web, article.url, article.title, article.content, article.summary, article.status)
                if article.status == 'downloaded' and not article.summary:
                    article.compress_article(api_key, model, prompt1, prompt2, database)
                article.send_message(self.user_tg_channel, bot_token)
                self.user_sent_urls.append(str(article.id))

    def update_sent_urls(self, database):
        sent_urls_for_request = f"{', '.join([f"{url}" for url in self.user_sent_urls])}"
        request = f'update Users_table set sent_urls = "{sent_urls_for_request}" where id = "{self.user_id}"'
        access_database(database, request)
