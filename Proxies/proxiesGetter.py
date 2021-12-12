import Proxies.proxy_sources as proxy_sources
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from tqdm import tqdm
from collections import deque
from cachetools import cached, TTLCache

cache = TTLCache(maxsize=100, ttl=86400)

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

def check_proxy(proxy):
    try:        
        response = requests.get(
            'http://azenv.net/',
            proxies={
              "http": proxy,
              "https": proxy,
            },timeout=5
        )
        if response.status_code == 200:
          return proxy
        return False
    except Exception:
        return False

@cached(cache)
def get(use_proxies):
  global proxies
  proxies = set()
  if(use_proxies):
    for i in (1,2):
      proxies.update(getattr(proxy_sources, 'source_%d' % i)())
    with ThreadPoolExecutor(10) as executor:
      futures = [executor.submit(check_proxy, proxy) for proxy in proxies]
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