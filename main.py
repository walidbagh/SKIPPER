import os
import rsa
import json
from base64 import b64decode
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

import Proxies.proxiesGetter as proxiesGetter
from Bots.webnovelBot import webnovelBot
from loader import get_parameters
from utils import banner, std_out_err_redirect_tqdm



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename = 'app.log')
logger = logging.getLogger(__name__)


def skipperStart(novel_id, chapters, use_proxies):
    print(f'CPU count: {os.cpu_count()}\n')
    threads_number = 10
    proxiesGetter.get(use_proxies)
    print(f'Seeding \033[92m{novel_id}\033[0m combos with {threads_number} threads and {len(proxiesGetter.proxies)} proxies.\n')
    with ThreadPoolExecutor(threads_number) as executor:
      futures = [executor.submit(webnovelBot, novel_id, chapters) for i in range(100)]
      with std_out_err_redirect_tqdm() as orig_stdout:
        with tqdm(total=len(futures), unit='req', file=orig_stdout, dynamic_ncols=True, postfix=f'{len(proxiesGetter.proxies)} proxies © SKIPPER 2021 by \033[92m@NetD0G\033[0m\033[0m.', unit_scale=True) as pbar:
          pbar.set_postfix({'proxies': len(proxiesGetter.proxies)})
          for future in as_completed(futures):
            try:
              result = future.result()
              if result:
                pbar.update(1)
            except Exception as exc:
              print(f'generated an exception: {exc}')
      

def check_licence():
  pk = """-----BEGIN RSA PUBLIC KEY-----
      MIICCgKCAgEAuSnOkoTuYNt6+NBVYZxCPjPw1PoQM4tavYOmZ0KFpzTKOLsH5QH9
      Yd6ec4H+JC0dwxXTbVeNoxwsB3tcFa1U+9WFvXN9WMoi6zmK/kgOoV5tQitc6lCW
      El83OaOzOO2v8MHFmtGGohH8QpH++lk68UheKqPujZKnmS8+XuqhXRfJwXHMg18Y
      Q+SQKRP1uzN7TCJ7JbabrO2SChr9Jc0i0GxJV0/zfRREJ29Y8nXXe2gFp/e5ZRuO
      dpq1novWKzxQyOmJg3gPjeywAGf1JEXeQzyFI4qwDQ1L8qWGqWhPgipq+VGhUz52
      yujS7/81NHaZo9MSjifcB6D5DX9OC9MCJpXQHwJetETV3Vb4AE94BLdmLMsnIRKs
      WDLBJYqQ75W9sR5NlbDi42HgbvMv+1FnoR796FohTt8YI9Yt6TwXGnXCQhRPKDcQ
      fbYCTvUQYguMERMK+rgTpxcTX3Kob6q3PFxwsO2+Ipsw94uGCVTTovpy1XqjhmfD
      T+2yW8fkI+anX4vou7erfKugbBBGZTSmk0mYRCkFeXqeSJJtv0ybT6zCiMqj+YJt
      XarIMsyT10Ca4ajCFrNJhnaPHfBnDk76k2lgkjCP68roaJ2ZH/OAviD9YojvgHTP
      lqbQQXzeZMvX7gmx7AW+3p7FXL50tF2Y203Ga6ZbnZSXBwgcPErz0hECAwEAAQ==
      -----END RSA PUBLIC KEY-----
      """
  try:
      l = open('licence','r').read().splitlines()
      try:
        rsa.verify(l[0].encode('utf-8'),b64decode(l[1]),rsa.PublicKey.load_pkcs1(pk))
        print(f'\033[92mLICENSE OK\033[0m, registred to: \033[1m{l[0]}\033[0m.\n')
      except rsa.VerificationError:
        raise Exception('Invalid licence file.')
      else:
        return
  except IndexError:
    Exception('Invalid licence file.')
  except IOError:
    Exception('No licence file found!')

def main():
    banner()
    check_licence()
    answers = get_parameters()
    print()
    chapters = json.load(open(answers['chapters_file_path']))
    if(len(chapters) != 0):
      skipperStart(answers['novel_id'], chapters, answers['use_proxies'])
    else:
      print('Nothing to do! Exiting...')


if __name__ == '__main__':
    main()