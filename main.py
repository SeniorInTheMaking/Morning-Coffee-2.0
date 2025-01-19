import loader
import users

data = loader.Load()
data.get_users_requests('config_files')
data.get_keys('keys.yml')

print(data.__dict__)