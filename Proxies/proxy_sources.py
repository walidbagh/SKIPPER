import requests
import inspect
import sys
from lxml.html import fromstring

def print_count(count):
  source = inspect.stack()[1].function.split("_",1)[1]
  print(f'Found \033[92m{count}\033[0m Proxy from source #{source}.\n')

def print_download():
  source = inspect.stack()[1].function.split("_",1)[1]
  print(f'Pulling Proxies from source #{source} ...\n')

def print_error():
  source = inspect.stack()[1].function.split("_",1)[1]
  print(f'Error pulling Proxies from source #{source}.\n')

def print_page_progress(page = 1, num_pages = 1):
  sys.stdout.write(f'Downloaded \033[92m{page}\033[0m/{num_pages} pages...\r'),
  sys.stdout.flush()

def source_1():
  print_download()
  proxies = set()
  url = 'https://free-proxy-list.net/'
  response = requests.get(url)
  parser = fromstring(response.text)
  for i in parser.xpath('//tbody/tr')[:250]:
      if i.xpath('.//td[7][contains(text(),"yes")]'):
          proxy = ":".join(
              [i.xpath('.//td[1]/text()')[0],
                i.xpath('.//td[2]/text()')[0]])
          proxies.add(proxy)
  print_count(len(proxies))
  return proxies

def source_2():
  print_download()
  proxies = set()
  session = requests.Session()

  def get_token():
    response = session.get('https://www.proxydocker.com/en/')
    parser = fromstring(response.text)
    return parser.xpath('//meta[@name="_token"]/@content')

  def call_api(page, token, num_pages = 1):
      url = 'https://www.proxydocker.com/en/api/proxylist/'
      response = session.post(
          url,
          data = {
              'token': token,
              'country': 'all',
              'city': 'all',
              'state': 'all',
              'port': 'all',
              'type': 'https',
              'anonymity': 'ELITE',
              'need': 'Google',
              'page': page
          }).json()
      print_page_progress(page, num_pages)
      return response

  def get_data():
      token = get_token()
      first_page = call_api(page = 1, token = token)
      yield first_page
      num_pages = 5 or int(round(first_page['rows_count'] / 20))
      for page in range(2, num_pages + 1):
        next_page = call_api(page = page, num_pages = num_pages, token =token)
        yield next_page

  try:
    for page in get_data():
      for proxy in page["proxies"]:
        if(proxy['isGoogle']):
          proxies.add(proxy['ip'] + ':' + str(proxy['port']))
    print_count(len(proxies))
  except:
    print_error()
  return proxies
    