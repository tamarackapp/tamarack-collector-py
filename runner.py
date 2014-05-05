import random
import requests
import time

if __name__ == '__main__':
    while True:
        delay = random.uniform(0.01, 0.8)
        time.sleep(delay)

        url = random.choice(['/', '/about', '/'])

        requests.get('http://127.0.0.1:8000' + url)
