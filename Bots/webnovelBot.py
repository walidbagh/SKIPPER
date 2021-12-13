import requests
import logging
import threading
import random
import Proxies.proxiesGetter as proxiesGetter
from utils import wait

class webnovelBot():

  def __init__(self, novel_id, chapters, boost_first_chapter_only):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename = 'app.log')
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    self.first_check = True
    self.threadName = threading.currentThread().name
    self.novel_id = novel_id

    if boost_first_chapter_only:
      number_of_chapters = 1
    else:
      # at least 3 chapters, if chapters list has less then 3, it will eventually get the max
      number_of_chapters = random.randrange(3, len(chapters)-1)
      if number_of_chapters > 10:
        # 98% of the time, we limit the chapters number to less than 10
        # random.choices() returns list, so access the result in index 0
        if random.choices([True, False], weights=[0.98, 0.02])[0]:
          number_of_chapters = random.randrange(3, 7)

    self.chapters = chapters[:number_of_chapters]
    self.chapter_index = 0
    self.check()

  def check(self, next_proxy:bool = False):
    if (self.first_check):
      self.first_check = False
      self.proxy = next(proxiesGetter.proxies,None)
    if (next_proxy):
      self.proxy = next(proxiesGetter.proxies,None)
    proxy = self.proxy
    if not proxy:
      return False
    print(f'\n[#{self.threadName}] Trying chapter {self.chapter_index + 1}/{len(self.chapters)} ' + (f'with proxy {proxy}.' if proxiesGetter.proxies else 'without proxy.'))
    try:
        api = requests.session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36",
        }
        response = api.get(
            f'https://www.webnovel.com/book/{self.novel_id}/{self.chapters[self.chapter_index]["id"]}',
            headers=headers,
            proxies={
              "http": f'http://{proxy}',
              "https": f'http://{proxy}'
            },
            timeout=(5, 10),
            verify=False
        )
        if response.status_code == 200:
          print(f'[#{self.threadName}] \033[94m #{response.status_code}: Request Success!\033[0m\n')
          if self.chapter_index < (len(self.chapters) - 1):
            self.chapter_index += 1
            self.check()
          else:
            return True
        elif response.status_code == 429:  # Too many requests error.
          print(f'[#{self.threadName}] \033[41m #{response.status_code}: Too many requests error!\033[0m\n')
          retryAfter = int(response.headers['Retry-After']) + 3
          wait(retryAfter)
          self.check(True)
        elif response.status_code == 403:  # Cloudflare captcha.
          print(f'[#{self.threadName}] \033[41m #{response.status_code}: Bad proxy, Cloudflare captcha!\033[0m\n')
          self.check(True)
        else:
          print(f'[#{self.threadName}] \033[41m #{response.status_code}: An error has occurred!\033[0m\n')
          print(f"[#{self.threadName}] Failed Request:\n{response.status_code}\n{response.headers}\n{response.text}\n",file=open("debug.txt", "a+"))
          self.check(True)
    except Exception as e:
        logging.exception(str(e))
        print(f"[#{self.threadName}] \033[93mConnnection error! Skipping proxy and retrying...\033[0m\n")
        try:
          proxiesGetter.proxies.remove(proxy)
        except ValueError as e:
          logging.exception(str(e))
          print(f"[#{self.threadName}] \033[93m Couldn't remove proxy, not found...\033[0m\n")
        self.check(True)