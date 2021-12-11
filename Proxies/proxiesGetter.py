import Proxies.proxy_sources as proxy_sources
from collections import deque

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

def get(use_proxies):
  global proxies
  proxies = set()
  if(use_proxies):
    for i in (1,2):
      proxies.update(getattr(proxy_sources, 'source_%d' % i)())
  proxies = ModifiableCycle(proxies)
  return proxies