import loader
import news
import users

data = loader.Load()
data.get_users_requests('config_files')
data.get_keys('keys.yml')

for web in data.all_webs:
    web = news.Webs(web)
    web.get_all_urls()
    web.check_duplicates(data.database)

    for url in web.urls[:2]:
        url = news.News(url, web.web)
        url.download_content()
        print(url.__dict__)

