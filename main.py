import loader
import news
import users


data = loader.Load()
# data.get_keys('keys.yml')
data.get_keys('/app/config_files/keys.yml')
data.get_users_requests(data.database)

for web in data.all_webs:
    web = news.Webs(web)
    web.get_all_urls()
    web.check_duplicates(data.database)

    for url in web.urls:
        url = news.News(url, web.domain)
        url.download_content()
        url.upload_new_url(data.database)

for request in data.users_requests:
    request = users.Users(**request)
    request.detect_interesting_articles(data.database, data.api_key, data.model, data.prompt1, data.prompt2,
                                        data.bot_token)
    request.update_sent_urls(data.database)

news.db_maintenance(data.database)
