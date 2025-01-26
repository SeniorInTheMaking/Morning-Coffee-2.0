from mysql.connector import connect
from bs4 import BeautifulSoup
import requests
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
            return result

class Webs:
    def __init__(self, web):
        self.web = web
        self.domain = web.split('/')[2]
        self.urls = []

    def get_all_urls(self):

        def set_web(url):
            if 'http' not in url:
                web = '/'.join(self.web.split('/')[:3])
                url = web.rstrip('/') + '/' + url.lstrip('/')
            return url

        def key_tags_checker(url):
            key_tags = [r'/news/.*d.*d', r'/\d{5,}/', r'/\d{5,}$', r'\d{4}/\d{2}/\d{2}|\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}']
            return any(re.search(tag, url) for tag in key_tags)

        def stop_tags_checker(url):
            stop_tags = ['/app/', 'org$', '.com$', '.rss$', '/group/', '/story/', '/channel/', '/rutube/', '/ticker/',
                         '/theme/', '/serve/', '/themes']
            return any(re.search(tag, url) for tag in stop_tags)

        def title_checker(url):
            return url.count('-') >= 5

        try:
            response = requests.get(self.web, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            all_urls = soup.find_all('a', href=True)
            all_urls = list(set(all_urls))

            for url in all_urls:
                url = url['href']
                url = set_web(url)
                if not stop_tags_checker(url):
                    if key_tags_checker(url) or title_checker(url):
                        self.urls.append(url)
            self.urls = list(set(self.urls))
        except:
            pass

    def check_duplicates(self, database):
        request = f"select URL from NS_table where Web = '{self.domain}'"
        urls_from_db = access_database(database, request)
        urls_from_db = [i[0] for i in urls_from_db]
        self.urls = [url for url in self.urls if url not in urls_from_db]


class News():
    def __init__(self, url, web):
        self.web = web
        self.url = url
        self.title = None
        self.content = None

    def download_content(self):
        response = requests.get(self.url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        try:
            title = soup.find('title').text.strip()
            self.title = title
        except:
            pass

