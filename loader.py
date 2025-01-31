from mysql.connector import connect
import yaml


class Load:
    def __init__(self):
        self.users_requests = []
        self.all_webs = []
        self.database = None
        self.api_key = None
        self.model = None
        self.prompt1 = None
        self.prompt2 = None
        self.bot_token = None
        self.frequency = None

    def get_keys(self, keys_path):
        with open(keys_path, 'r', encoding='utf-8') as file:
            keys_data = yaml.safe_load(file)

            self.database = keys_data['database']
            self.api_key = keys_data['api_key']
            self.model = keys_data['model']
            self.prompt1 = keys_data['prompt1']
            self.prompt2 = keys_data['prompt2']
            self.bot_token = keys_data['bot_token']
            self.frequency = keys_data['frequency']

    def get_users_requests(self, database):
        with connect(
                host=database['host'],
                port=database['port'],
                user=database['user'],
                password=database['password'],
                database=database['database']
        ) as connection:
            with connection.cursor() as cursor:
                request = "select id, tg_channel, news_limit, webs, key_words, stop_words, sent_urls, sent_titles from Users_table;"
                cursor.execute(request)
                result = cursor.fetchall()
                result = [{'user_id': id,
                           'user_tg_channel': channel,
                           'user_news_limit': limit,
                           'user_webs': webs.split(', '),
                           'user_key_words': key_words.split(', '),
                           'user_stop_words': stop_words.split(', '),
                           'user_sent_urls': sent_urls.split(', '),
                           'user_sent_titles': sent_titles.split(', ')}
                          for (id, channel, limit, webs, key_words, stop_words, sent_urls, sent_titles) in result]
                connection.commit()
                self.users_requests = result
                self.all_webs = list(set(web for user_request in result for web in user_request['user_webs']))