import yaml
import os


class Load:

    def __init__(self):
        self.users_requests = []
        self.all_webs = []
        self.database = None
        self.api_key = None
        self.prompt1 = None
        self.prompt2 = None
        self.bot_token = None
        self.frequency = None

    def get_users_requests(self, config_files_path):

        yml_files = [file for file in os.listdir(config_files_path) if file.endswith('.yml')]

        for yml_file in yml_files:
            path = os.path.join(config_files_path, yml_file)
            with open(path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)

            if data['user_id'] and data['user_tg_channel'] and data['user_webs'] and data['user_key_words']:
                for web in data['user_webs']:
                    if web not in self.all_webs:
                        self.all_webs.append(web)

                try:
                    self.users_requests.append(
                        {'user_id': data['user_id'],
                         'user_tg_channel': data['user_tg_channel'],
                         'user_webs': data['user_webs'],
                         'user_key_words': data['user_key_words'],
                         'user_stop_words': data['user_stop_words'],
                         'user_urls_to_send': [],
                         'user_sent_urls': []})
                except:
                    pass

    def get_keys(self, keys_path):
        with open(keys_path, 'r', encoding='utf-8') as file:
            keys_data = yaml.safe_load(file)

            self.database = keys_data['database']
            self.api_key = keys_data['api_key']
            self.prompt1 = keys_data['prompt1']
            self.prompt2 = keys_data['prompt2']
            self.bot_token = keys_data['bot_token']
            self.frequency = keys_data['frequency']

