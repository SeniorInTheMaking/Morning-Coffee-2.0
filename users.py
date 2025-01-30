from mysql.connector import connect
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


class Good_Articles:
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

        if all_key_words_count >= 3:
            return main_key_word, all_key_words_count
        return False




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

    def detect_interesting_articles(self, database):
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
                article = Good_Articles(article[0], article[1], article[2], article[3], article[4], article[5], article[6])
                check = article.check_article(self.user_stop_words, self.user_key_words)
                if check:
                    key_word = check[0]
                    key_word_count = check[1]
                    if key_word in used_key_words:
                        good_articles.append([article, key_word_count])
                    else:
                        sent_news_count += 1
                        used_key_words.append(key_word)
                        self.user_sent_urls.append(str(article.id))

        if sent_news_count < self.user_news_limit:
            good_articles = sorted(good_articles, key=lambda article: article[1], reverse=True)
            for article in good_articles:
                article = article[0]
                article = Good_Articles(article.id, article.web, article.url, article.title, article.content, article.summary, article.status)