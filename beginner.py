import time
import yaml

with open('/app/config_files/keys.yml', 'r', encoding='utf-8') as file:
    keys_data = yaml.safe_load(file)
    frequency = keys_data['frequency']

# with open('keys.yml', 'r', encoding='utf-8') as file:
#     keys_data = yaml.safe_load(file)
#     frequency = keys_data['frequency']

while True:
    start_time = time.time()

    with open('main.py') as f:
        code = f.read()
        exec(code)

    end_time = time.time()
    print('time used: ', end_time - start_time)

    time.sleep(int(frequency))