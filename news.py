from mysql.connector import connect
from bs4 import BeautifulSoup
import requests
import re
import logs
import datetime


def access_database(database, request):
    try:
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
    except:
        logs.write_log('database error', "Can't connect to database")


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
            key_tags = [r'/news/.*\d{2}.*', r'/\d{5,}/', r'/\d{5,}$', r'\d{4}/\d{2}/\d{2}|\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}']
            return any(re.search(tag, url) for tag in key_tags)

        def stop_tags_checker(url):
            stop_tags = ['/app/', 'org$', '.com$', '.rss$', '/group/', '/story/', '/channel/', '/rutube/', '/ticker/',
                         '/theme/', '/serve/', '/themes']
            return any(re.search(tag, url) for tag in stop_tags)

        def title_checker(url):
            return url.count('-') >= 5

        try:
            response = requests.get(self.web, timeout=10)
            if response != '<Response [200]>':
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
                response = requests.get(self.web, headers=headers)

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
            logs.write_log(self.web, "Can't download urls from website")


    def check_duplicates(self, database):
        try:
            request = f"select URL from NS_table where Web = '{self.domain}'"
            urls_from_db = access_database(database, request)
            urls_from_db = [i[0] for i in urls_from_db]
            self.urls = [url for url in self.urls if url not in urls_from_db]
        except:
            logs.write_log(self.web, "Can't connect to db to check duplicates")


class News():
    def __init__(self, url, web):
        self.web = web
        self.url = url
        self.title = None
        self.content = None

    def download_content(self):
        try:
            response = requests.get(self.url, timeout=10)
            if response != '<Response [200]>':
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
                response = requests.get(self.url, headers=headers)

            response.encoding = response.apparent_encoding

            soup = BeautifulSoup(response.text, 'html.parser')
            all_strings = [str(string.get_text().strip()) for string in soup.findAll('p')]
            if not all_strings:
                all_strings = [str(string.get_text().strip()) for string in soup.findAll('div', class_='article__text')]


            title = soup.find('title').text.strip()
            self.title = title
            all_text = []

            for string in all_strings:
                string = ' '.join(string.split())
                string = string.replace('\n', '')
                if len(string) > 100:
                    all_text.append(string)

            while sum(len(text) for text in all_text) > 2500:
                all_text.remove(min(all_text, key=len))

            content = ''.join(all_text)
            if len(content) > 500:
                self.content = ''.join(all_text)

        except:
            logs.write_log(self.url, "Can't download content")


    def upload_new_url(self, database):
        if self.content and self.title:
            try:
                time = str(datetime.datetime.now().today().replace(microsecond=0))
                request = f"""insert into NS_table (Web, URL, Title, DownloadTime, Content, Status) values
                 ('{self.web}', '{self.url}', '{self.title}', '{time}', '{self.content}', 'downloaded');"""
                access_database(database, request)
            except:
                logs.write_log(self.url, "Can't upload new url")

