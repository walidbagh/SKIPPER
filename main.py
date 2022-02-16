import os
import rsa
import json
import requests
from time import time, sleep
from datetime import timedelta
from base64 import b64decode
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

import Proxies.proxiesGetter as proxiesGetter
from Bots.webnovelBot import webnovelBot
from Bots.wattpadBot import wattpadBot
from loader import get_parameters
from utils import banner, std_out_err_redirect_tqdm
from playwright.sync_api import sync_playwright


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='app.log')
logger = logging.getLogger(__name__)

threads_number = 1
requests_per_cycle = 50
time_per_cycle = 60  # 1 minute
skipper_start_time = int(time())
start_time = 0
cycle_count = 1
views_boosted = 0


def getHttpbin():
    proxy =  next(proxiesGetter.proxies, None)
    print(proxy)
    proxies = {'http': f'http://{proxy}'} 
    response = requests.get('http://httpbin.org/ip', proxies=proxies)
    print(response.json())
    response = requests.get('http://httpbin.org/headers') 
    print(response.json())
    print("===================")
    return getHttpbin()

def getPixiscan():
    with sync_playwright() as p:
        for browser_type in [p.chromium, p.firefox, p.webkit]:
            browser = browser_type.launch(proxy={
                "server": "http://85.8.167.242:7792",
                "username": "wkg8f3iwCr",
                "password": "XKA0W1Zd3A"
            })
            page = browser.new_page()
            page.goto('https://pixelscan.net/', timeout=0)
            page.wait_for_timeout(40000)
            page.screenshot(path=f"./screenshots/{browser_type.name}.png", full_page=True)
            browser.close()


def skipperStart(answers, chapters):
    global start_time
    global cycle_count
    global views_boosted

    service = answers['service']
    actions = [a.lower() for a in answers['actions']]
    use_user_accounts = answers['use_user_accounts']
    user_combos_file_path = answers.get('user_combos_file_path', '')
    novel_id = answers['novel_id']
    boost_first_chapter_only = answers['boost_first_chapter_only']
    use_proxies = answers['use_proxies']
    use_local_proxies_only = answers['use_local_proxies_only']
    filter_bad_proxies = answers.get('filter_bad_proxies', False)

    proxiesGetter.get(use_proxies, use_local_proxies_only, filter_bad_proxies)
    last_cycle_duration = int(time()) - start_time

    if last_cycle_duration >= time_per_cycle:
        start_time = int(time())
    else:
        for secs in range(abs(last_cycle_duration - time_per_cycle), 0, -1):
            print(f'Waiting {secs} seconds to start new cycle...', end='\r')
            sleep(1)
    ###
    #getPixiscan()
    #getHttpbin()
    #return True
    ###
    print(
        f'Cycle #{cycle_count}: Seeding novel \033[92m{novel_id}\033[0m with {threads_number} threads and {len(proxiesGetter.proxies)} proxies.\n')

    with ThreadPoolExecutor(threads_number) as executor:
        if service == 'webnovel':
            futures = [executor.submit(
                webnovelBot, novel_id, chapters, boost_first_chapter_only) for i in range(requests_per_cycle)]
        elif service == 'wattpad':
            if use_user_accounts:
                combos = loadCombos(user_combos_file_path)
                futures = [executor.submit(wattpadBot, novel_id, chapters, boost_first_chapter_only,
                                           use_proxies, use_local_proxies_only, actions, use_user_accounts, combo, i) for i, combo in enumerate(combos)]
            else:
                futures = [executor.submit(
                    wattpadBot, novel_id, chapters, boost_first_chapter_only, use_proxies, use_local_proxies_only, actions, False, None, None) for i in range(requests_per_cycle)]

        with std_out_err_redirect_tqdm() as orig_stdout:
            with tqdm(total=len(futures), unit='req', file=orig_stdout, dynamic_ncols=True,
                      postfix=f'{len(proxiesGetter.proxies)} proxies © SKIPPER 2021 by \033[92m@NetD0G\033[0m\033[0m.', unit_scale=True) as pbar:
                for future in as_completed(futures):
                    pbar.set_postfix_str(
                        f'{len(proxiesGetter.proxies)} proxies © SKIPPER 2021 by \033[92m@NetD0G\033[0m\033[0m.', refresh=True)
                    try:
                        result = future.result()
                        if result:
                            pbar.update(1)
                            views_boosted += 1
                        else:
                            # Clear proxies cache to force get new ones
                            proxiesGetter.cache.clear()
                            break
                    except Exception as exc:
                        print(f'generated an exception: {exc}')
                pbar.close()
    if service != 'wattpad':
        skipperStart(answers, chapters)


def loadCombos(user_combos_file_path):
    lines = open(user_combos_file_path, "r").readlines()
    combos = [line.replace("\n", "") + ':local' for line in lines]
    print(len(combos), ' combos loaded.')
    return combos


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
        l = open('licence', 'r').read().splitlines()
        try:
            rsa.verify(l[0].encode('utf-8'), b64decode(l[1]),
                       rsa.PublicKey.load_pkcs1(pk))
            print(
                f'\033[92mLICENSE OK\033[0m, registred to: \033[1m{l[0]}\033[0m.\n')
        except rsa.VerificationError:
            raise Exception('Invalid licence file.')
        else:
            return
    except IndexError:
        Exception('Invalid licence file.')
    except IOError:
        Exception('No licence file found!')


def loadChapters(service, novel_id, chapters_file_path):
    if service == 'wattpad':
        return wattpadBot.getChapters(novel_id)
    elif service == 'webnovel':
        return json.load(open(chapters_file_path))
    else:
        return []


def main():
    banner()
    check_licence()
    answers = get_parameters()
    print(f'CPU count: {os.cpu_count()}\n')
    chapters = loadChapters(
        answers['service'], answers['novel_id'], answers['chapters_file_path'])
    if(len(chapters) != 0):
        try:
            skipperStart(answers, chapters)
        except KeyboardInterrupt:
            print('Stop requested by user...\n')
            print(
                f'Boosted novel {answers["novel_id"]} with {views_boosted} views during {str(timedelta(seconds=int(time())-skipper_start_time))}.\n')
    else:
        print('Nothing to do! Exiting...')


if __name__ == '__main__':
    main()
