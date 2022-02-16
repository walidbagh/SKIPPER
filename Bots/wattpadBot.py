import time
import requests
from requests.adapters import HTTPAdapter
import logging
import threading
import Proxies.proxiesGetter as proxiesGetter
from utils import wait


class wattpadBot():

    def __init__(self, novel_id, chapters, boost_first_chapter_only, use_proxies, use_local_proxies_only, actions, use_user_accounts, combo, i):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename=f'./logs/{i}.log')
        requests.packages.urllib3.disable_warnings(
            requests.packages.urllib3.exceptions.InsecureRequestWarning)

        requests.packages.urllib3.util.connection.HAS_IPV6 = False

        self.first_check = True
        self.max_check_retries = 3
        self.current_check_retries = 0
        self.headers = {
            'Connection': 'close',  # Force Close TCP connection, fixes too many open files error
            'origin': 'https://www.wattpad.com',
            'referer': 'https://www.wattpad.com',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            "Authority": "www.wattpad.com",
            'authorization': 'IwKhVmNM7VXhnsVb0BabhS',
            'accept-language': 'en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7,ar;q=0.6',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15',
        }
        self.next_proxy_on_400 = True
        self.use_proxies = use_proxies
        self.use_local_proxies_only = use_local_proxies_only
        self.proxy = None
        self.proxies = {}
        self.threadName = threading.currentThread().name
        self.novel_id = novel_id

        self.chapters = chapters
        self.chapter_index = 0

        self.wattpadSession = None
        self.currentUser = None
        self.use_user_accounts = use_user_accounts
        self.combo = combo
        self.combo_index = i
        self.actions = actions
        self.user_excedded_daily_votes_limit = False
        self.check()

    # Used in main.py to load chapters data
    @staticmethod
    def getChapters(novel_id):
        response = requests.get(f'https://www.wattpad.com/api/v3/stories/{novel_id}',
                                params={
                                    'drafts': 0,
                                    'include_deleted': 0,
                                    'fields': 'parts(id,url)'
                                },
                                headers={
                                    'Connection': 'close',  # Force Close TCP connection, fixes too many open files error
                                    "X-Requested-With": "XMLHttpRequest",
                                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15',
                                })
        if response.status_code == 200:
            return response.json()['parts']
        else:
            return []

    def do(self):
        if 'read' in self.actions:
            # self.readChapter() is optional, in my tests, it doesn't register a new read...
            # self.emulateReadingTrackingEvent() is what registers a new read !
            readResult = True  # self.readChapter()
            readTrackingEventResult = self.emulateReadingTrackingEvent()
            readPositionResult = self.syncReadingPositionChapter()
        else:
            readResult = True
            readTrackingEventResult = True
            readPositionResult = True

        if self.user_excedded_daily_votes_limit:
            voteResult = True
        else:
            voteResult = self.voteChapter() if 'vote' in self.actions else True
        return [readResult, readTrackingEventResult, readPositionResult, voteResult]

    def getWattpadSession(self):
        session = requests.Session()
        session.verify = False
        session.headers.update(self.headers)
        session.proxies = self.proxies
        session.mount("https://", HTTPAdapter(max_retries=0))
        session.mount("http://", HTTPAdapter(max_retries=0))

        print(f'[#{self.threadName}] Getting wattpad Session...\n')
        '''
        https://stackoverflow.com/a/10115553/10292252
        https://docs.python-requests.org/en/latest/user/advanced/#keep-alive
        Note that connections are only released back to the pool for reuse once all body data has been read;
        be sure to either set stream to False or read the content property of the Response object.
        '''
        response = session.head("https://www.wattpad.com",
                                stream=False,
                                timeout=(6, 8)
                                )

        if response.status_code == 200:
            print(
                f'[#{self.threadName}] Got session id: {response.cookies.get_dict()["wp_id"]}\n')
            self.setTrackingSessionIdCookie(session)
        else:
            print(
                f"[#{self.threadName}] {response.status_code}: error getting session id.\n")

        return session

    def setTrackingSessionIdCookie(self, session: requests.Session):
        session.cookies.set('te_session_id', str(
            int(time.time() * 1000)), domain='.wattpad.com')

    def emulateWattpadTrackingSessionStartEvent(self):
        uuid = str(self.wattpadSession.cookies.get_dict()['wp_id'])
        te_session_id = int(
            self.wattpadSession.cookies.get_dict()["te_session_id"])
        userId = self.currentUser['id'] if self.currentUser else None
        headers = {
            "X-Requested-With": "XMLHttpRequest",
        }

        data_1 = {
            "events": [
                {
                    "name": "web:wattpad:::start",
                    "details": {
                        "referer": "direct",
                        "page": "story",
                        "storyid": self.chapters[self.chapter_index]["id"]
                    },
                    "uuid": uuid,
                    "userid": userId,
                    "timestamp": int(time.time() * 1000),
                    "session_id": te_session_id,
                }
            ],
            "timestamp": int(time.time() * 1000) + 200,
        }
        response_1 = self.wattpadSession.post('https://track.wattpad.com/api/event',
                                              json=data_1,
                                              headers=headers,
                                              )
        if response_1.status_code == 200:
            if response_1.text == 'OK':
                print(
                    f'[#{self.threadName}] \033[94m #{response_1.status_code}: Event "web:wattpad:::start": OK!\033[0m\n')
        return response_1

    def emulateReadingTrackingEvent(self):
        uuid = str(self.wattpadSession.cookies.get_dict()['wp_id'])
        te_session_id = int(
            self.wattpadSession.cookies.get_dict()["te_session_id"])
        userId = self.currentUser['id'] if self.currentUser else None
        headers = {
            "X-Requested-With": "XMLHttpRequest",
        }

        data_2 = {
            "events": [
                {
                    "name": "web:reading:::start",
                    "details": {
                        "storyid": f"{self.novel_id}",
                        "partid": self.chapters[self.chapter_index]["id"],
                        "published_parts": len(self.chapters)
                    },
                    "uuid": uuid,
                    "userid": userId,
                    "timestamp": int(time.time() * 1000),
                    "session_id": te_session_id,
                }
            ],
            "timestamp": int(time.time() * 1000) + 200,
        }
        response_2 = self.wattpadSession.post('https://track.wattpad.com/api/event',
                                              json=data_2,
                                              headers=headers,
                                              )
        if response_2.status_code == 200:
            if response_2.text == 'OK':
                print(
                    f'[#{self.threadName}] \033[94m #{response_2.status_code}: Event "web:reading:::start": OK!\033[0m\n')
        return response_2

    def tryToAuthenticate(self):
        if self.use_user_accounts:
            logging.info(f'Combo {self.combo_index} - {self.combo}')
            combo = self.combo.split(':')
            success, token = self.handleCombo(combo, self.combo_index)
            if success:
                print(
                    f'[#{self.threadName}] Logged in (combo #{self.chapter_index}): {token}\n')
                self.token = token

            return success
        else:
            return True

    def getToken(self, email, password):
        return self.wattpadSession.post(
            "https://api.wattpad.com/v4/sessions",
            params={
                "type": "wattpad",
                "username": email,
                "password": password,
                "fields": "token,user(verified_email)"
            },
            headers={
                "X-Requested-With": "XMLHttpRequest",
            },
        )

    def handleCombo(self, combo, combo_number, getNewWattpadSession=False, retries=0):
        if retries == 2:
            return False, None

        if (getNewWattpadSession):
            self.wattpadSession = self.getWattpadSession()

        response = self.getToken(combo[0], combo[1])

        if response.status_code == 200:
            jsonResponse = response.json()
            if "token" in jsonResponse:
                print(f'[#{self.threadName}] Correct combo {combo_number}.\n')
                self.currentUser = {
                    'id': int(jsonResponse["token"].split(':')[0])
                }
                if not jsonResponse['user']['verified_email']:
                    print(
                        f'[#{self.threadName}] Combo {combo_number}: Unverified email.\n')
                return True, jsonResponse["token"]
            else:
                print(f'[#{self.threadName}] Wrong Combo {combo_number}')
                return False, None
        else:
            print(response.status_code)
            print('=========\n', response.text, '\n=========')
            if response.status_code == 429:
                print(
                    f'[#{self.threadName}] handleCombo - Sleeping for 120s...\n')
                time.sleep(121)
                return self.handleCombo(combo, combo_number, True, retries + 1)
            elif response.status_code == 400:
                jsonResponse = response.json()
                if "error_code" in jsonResponse:
                    if jsonResponse["error_code"] == 1029:
                        print(
                            f'[#{self.threadName}] Wrong Combo {combo_number}\n')
                        return False, None
                    else:
                        print(
                            f'[#{self.threadName}] handleCombo - Wattpad error code {jsonResponse["error_code"]}\n')
                        return self.handleCombo(combo, combo_number, True, retries + 1)
                else:
                    return False, None
            else:
                return False, None

    def readChapter(self, retries=0):
        if retries == 2:
            return False

        response = self.wattpadSession.get(self.chapters[self.chapter_index]["url"],
                                           timeout=(5, 10),
                                           # headers=self.headers,
                                           # proxies=self.proxies,
                                           # verify=False,
                                           )

        if response.status_code == 200:
            print(
                f'[#{self.threadName}] \033[94m #{response.status_code}: READ - Request Success!\033[0m\n')
            return True
        # Too many requests error.
        elif response.status_code == 429 or response.status_code == 400:
            print(
                f'[#{self.threadName}] \033[41m #{response.status_code}: Too many requests error!\033[0m\n')
            if self.next_proxy_on_400:
                return 'TOO_MANY_REQUESTS'
            else:
                #retryAfter = int(response.headers['Retry-After']) + 3
                retryAfter = 121
                wait(retryAfter)
                return self.readChapter(retries + 1)
        elif response.status_code == 403:  # Cloudflare captcha.
            print(
                f'[#{self.threadName}] \033[41m #{response.status_code}: Bad proxy, Cloudflare captcha!\033[0m\n')
            return 'BAD_PROXY'
        else:
            print(
                f'[#{self.threadName}] \033[41m #{response.status_code}: An error has occurred!\033[0m\n')
            logging.exception(
                f"[#{self.threadName}] Failed Request:\n{response.status_code}\n{response.headers}\n{response.text}\n")
            return self.readChapter(retries + 1)

    def syncReadingPositionChapter(self, retries=0):
        if retries == 2:
            return False

        response = self.wattpadSession.post(
            "https://www.wattpad.com/apiv2/syncreadingposition",
            data={
                "story_id": self.chapters[self.chapter_index]["id"],
                "position": 1
            },
            headers={
                "X-Requested-With": "XMLHttpRequest",
            },
            # headers=self.headers,
            # proxies=self.proxies,
            timeout=(5, 10),
            # verify=False
        )

        if response.status_code == 200:
            if response.text == '""':
                print(
                    f'[#{self.threadName}] \033[94m #{response.status_code}: SYNC - Request Success!\033[0m\n')
                return True
        elif response.status_code == 429 or response.status_code == 400:
            jsonResponse = response.json()
            if "error_code" in jsonResponse:
                if jsonResponse["error_code"] == 1019:
                    print(
                        f'[#{self.threadName}] #{response.status_code}: SYNC - Already Synced!\n')
                    return True
                # Too many requests error.
                elif jsonResponse['error_code'] == 1002:
                    print(
                        f'[#{self.threadName}] \033[41m #{response.status_code}: Too many requests error!\033[0m\n')
                    if self.next_proxy_on_400:
                        return 'TOO_MANY_REQUESTS'
                    else:
                        #retryAfter = int(response.headers['Retry-After']) + 3
                        retryAfter = 121
                        wait(retryAfter)
                        return self.syncReadingPositionChapter(retries + 1)
                elif jsonResponse['error_code'] == 1073:
                    print(
                        f'[#{self.threadName}] #{response.status_code}: Wattpad - Email not verified!\n')
                    return False
                else:
                    print(
                        f'[#{self.threadName}] \033[41m #{response.status_code}: Wattpad error {jsonResponse["error_code"]}! Retrying...\n')
                    return self.syncReadingPositionChapter(retries + 1)
            else:
                print(
                    f'[#{self.threadName}] \033[41m #{response.status_code}: No Wattpad error code... Retrying...\033[0m\n')
                return self.syncReadingPositionChapter(retries + 1)
        elif response.status_code == 403:  # Cloudflare captcha.
            print(
                f'[#{self.threadName}] \033[41m #{response.status_code}: Bad proxy, Cloudflare captcha!\033[0m\n')
            return 'BAD_PROXY'
        else:
            print(
                f'[#{self.threadName}] \033[41m #{response.status_code}: An error has occurred!\033[0m\n')
            logging.exception(
                f"[#{self.threadName}] Failed Request:\n{response.status_code}\n{response.headers}\n{response.text}\n")
            return self.syncReadingPositionChapter(retries + 1)

    def voteChapter(self, retries=0):
        if retries == 2:
            return False

        response = self.wattpadSession.post(
            f'https://www.wattpad.com/api/v3/stories/{self.novel_id}/parts/{self.chapters[self.chapter_index]["id"]}/votes',
            headers={
                "X-Requested-With": "XMLHttpRequest",
            },
            # proxies=self.proxies,
            timeout=(6, 10),
            # verify=False
        )

        if response.status_code == 200:
            jsonResponse = response.json()
            if "votes" in jsonResponse:
                print(
                    f'[#{self.threadName}] \033[94m #{response.status_code}: VOTE - Request Success!\033[0m\n')
                return True
        elif response.status_code == 429 or response.status_code == 400:
            jsonResponse = response.json()
            if "error_code" in jsonResponse:
                if jsonResponse["error_code"] == 1019:
                    print(
                        f'[#{self.threadName}] #{response.status_code}: VOTE - Already Voted!\n')
                    return True
                # Exceeded the 100 votes per 24h limit.
                elif jsonResponse['error_code'] == 1088:
                    print(
                        f'[#{self.threadName}] \033[41m #{response.status_code}: VOTE - Exceeded daily vote limit!\033[0m\n')
                    self.user_excedded_daily_votes_limit = True
                    return False
                # Too many requests error.
                elif jsonResponse['error_code'] == 1002:
                    print(
                        f'[#{self.threadName}] \033[41m #{response.status_code}: Too many requests error!\033[0m\n')
                    if self.next_proxy_on_400:
                        return 'TOO_MANY_REQUESTS'
                    else:
                        #retryAfter = int(response.headers['Retry-After']) + 3
                        retryAfter = 121
                        wait(retryAfter)
                        return self.voteChapter(retries + 1)
                elif jsonResponse['error_code'] == 1073:
                    print(
                        f'[#{self.threadName}] #{response.status_code}: Wattpad - Email not verified!\n')
                    return False
                else:
                    print(
                        f'[#{self.threadName}] \033[41m #{response.status_code}: Wattpad error {jsonResponse["error_code"]}! Retrying...\n')
                    print(f'[#{self.threadName}] {response.text}')
                    return self.voteChapter(retries + 1)
            else:
                print(
                    f'[#{self.threadName}] \033[41m #{response.status_code}: No Wattpad error code... Retrying...\033[0m\n')
                return self.voteChapter(retries + 1)
        elif response.status_code == 403:  # Cloudflare captcha.
            print(
                f'[#{self.threadName}] \033[41m #{response.status_code}: Bad proxy, Cloudflare captcha!\033[0m\n')
            return 'BAD_PROXY'
        else:
            print(
                f'[#{self.threadName}] \033[41m #{response.status_code}: An error has occurred!\033[0m\n')
            logging.exception(
                f"[#{self.threadName}] Failed Request:\n{response.status_code}\n{response.headers}\n{response.text}\n")
            return self.voteChapter(retries + 1)

    def removeProxy(self):
        if not self.use_local_proxies_only:
            try:
                proxiesGetter.proxies.remove(self.proxy)
            except ValueError as e:
                logging.exception(str(e))
                print(
                    f"[#{self.threadName}] \033[93m Couldn't remove proxy, not found...\033[0m\n")

    def retry(self, next_proxy: bool = False, remove_proxy: bool = False, wait_seconds: int = 0, increment_retries: bool = False):
        if remove_proxy:
            self.removeProxy()
        if increment_retries:
            self.current_check_retries += 1
        self.wattpadSession.close()
        self.wattpadSession = None
        self.currentUser = None
        if wait_seconds:
            wait(wait_seconds)
        return self.check(next_proxy)

    def check(self, next_proxy: bool = False):
        if (self.first_check):
            self.first_check = False

        if self.current_check_retries == self.max_check_retries:
            return False

        if self.use_proxies:
            if not self.proxy:
                self.proxy = next(proxiesGetter.proxies, None)
            if (next_proxy):
                self.proxy = next(proxiesGetter.proxies, None)
            if not self.proxy:
                print(
                    f'\n[#{self.threadName}] Exit... No proxy set and proxies enabled!')
                return False
            print(f'[#{self.threadName}] Using proxy: {self.proxy}\n')
            self.proxies = {
                "http": f'http://{self.proxy}',
                "https": f'http://{self.proxy}'
            }

        try:
            if not self.wattpadSession or next_proxy:
                self.wattpadSession = self.getWattpadSession()
                loggedIn = self.tryToAuthenticate()
                if not loggedIn:
                    return False

            print(f'\n[#{self.threadName}] Trying chapter {self.chapter_index + 1}/{len(self.chapters)} ' +
                  (f'with proxy {self.proxy}.' if self.use_proxies else 'without proxy.'))

            results = self.do()

            if ('BAD_PROXY' in results):
                return self.retry(next_proxy=True, remove_proxy=True, wait_seconds=0)
            elif ('TOO_MANY_REQUESTS' in results):
                return self.retry(next_proxy=True, remove_proxy=False, wait_seconds=0)
            else:
                if self.chapter_index < (len(self.chapters) - 1):
                    self.chapter_index += 1
                    self.check()
                else:
                    return True

        except requests.exceptions.ProxyError as e:
            logging.exception(str(e))
            print(
                f"[#{self.threadName}] \033[93mProxy error!\033[0m\n")
            print(
                f"[#{self.threadName}] \033[93mSkipping proxy and retrying...\033[0m\n")
            return self.retry(next_proxy=True, remove_proxy=True, wait_seconds=120, increment_retries=True)

        except Exception as e:
            logging.exception(str(e))
            print(
                f"[#{self.threadName}] \033[93mConnnection error!\033[0m\n")
            if self.use_proxies:
                print(
                    f"[#{self.threadName}] \033[93mSkipping proxy and retrying...\033[0m\n")
            return self.retry(next_proxy=True, remove_proxy=True, wait_seconds=120, increment_retries=True)

