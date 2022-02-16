import Proxies.proxy_sources as proxy_sources
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from tqdm import tqdm
from collections import deque
from cachetools import cached, TTLCache

cache = TTLCache(maxsize=100, ttl=600) # 600 second = 10 minutes

class ModifiableCycle(object):
    def __init__(self, items=()):
        self.deque = deque(items)
    def __iter__(self):
        return self
    def __next__(self):
        if not self.deque:
            raise StopIteration
        item = self.deque.popleft()
        self.deque.append(item)
        return item
    next = __next__
    def __len__(self):
      return len(self.deque)
    len = __len__
    def delete_next(self):
        self.deque.popleft()
    def delete_prev(self):
        # Deletes the item just returned.
        # I suspect this will be more useful than the other method.
        self.deque.pop()
    def __remove__(self, item):
        self.deque.remove(item)
    remove = __remove__

def format_proxy(proxy):
  p = proxy.split(':')
  if len(p) == 2:
    return proxy
  else:
    # Proxies that have authentication user:pass
    return f'{p[2]}:{p[3]}@{p[0]}:{p[1]}'

def check_proxy(session, proxy):
    try:
        response = session.get(
            'https://httpbin.org/get?show_env',
            proxies={
              "http": f'http://{proxy}',
              "https": f'http://{proxy}'
            },timeout=8
        )
        if response.status_code == 200:
          return proxy
        return False
    except Exception:
        return False

@cached(cache)
def get(use_proxies, use_local_proxies_only, filter_bad_proxies):
  global proxies
  proxies = set()
  if(use_proxies):
    # Local proxies
    lines = open('proxies.txt', "r").readlines()
    #local_proxies = [":".join(line.replace("\n", "").split(":", 2)[:2]) for line in lines]
    local_proxies = [format_proxy(line.replace("\n", "")) for line in lines]
    proxies.update(local_proxies)
    print(f'Found \033[92m{len(local_proxies)}\033[0m Proxies from source #Local.\n')
    # Remote FREE proxies
    if not use_local_proxies_only:
      for i in (1,2,3,4):
        proxies.update(getattr(proxy_sources, 'source_%d' % i)())
    print(f'Found \033[92m{len(proxies)}\033[0m Unique Proxies.\n')
    if filter_bad_proxies:
      with ThreadPoolExecutor(15) as executor:
        session = requests.session()
        futures = [executor.submit(check_proxy, session, proxy) for proxy in proxies]
        with tqdm(total=len(futures), desc='Checking proxies', leave=False, unit='proxy') as pbar:
          results = []
          for future in as_completed(futures):
            results.append(future.result())
            pbar.update(1)
        good_proxies = list(filter(bool,results))
        print(f'Found \033[92m{len(good_proxies)}\033[0m good proxies out of {len(proxies)}... \n')
        proxies = good_proxies
  proxies = ModifiableCycle(proxies)
  return proxies