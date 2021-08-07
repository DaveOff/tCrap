from requests.utils import dict_from_cookiejar
import urllib,string,random,requests, json,sys
from db import DBHepler
from time import sleep

class tCrap:
    @property
    def firstPack(self):
        return self.firstPack

    @firstPack.setter
    def firstPack(self, value):
        if type(value) is not str :
            self.db.updateSetting((json.dumps(value), 'last_tweet_id'))
        self.firstPack = value

    def __init__(self):
        self.token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))
        self.publicToken = 'AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'
        self.cursor, self.guestToekn = '', ''
        self.cookies = {}
        self.db = DBHepler('<host>', '<user>', '<pass>', '<database>', '<port>', '<charset>')
        self.query = ' OR '.join([
            't.me/BChatBot',
            't.me/BiChatBot',
            't.me/HarfBeManBot',
            'telegram.me/HarfBeManBot',
            'telegram.me/BiChatBot',
            'telegram.me/BChatBot'
        ])
        init = self.db.getSetting(('last_tweet_id'))['value']
        self.firstPack = json.loads(init) if init is not None else None

    def createParams(self,query, cursor=None):
        params = {
            'include_profile_interstitial_type': 1,
            'include_blocking': 1,
            'include_blocked_by': 1,
            'include_followed_by': 1,
            'include_want_retweets': 1,
            'include_mute_edge': 1,
            'include_can_dm': 1,
            'include_can_media_tag': 1,
            'skip_status': 1,
            'cards_platform': 'Web-12',
            'include_cards': 1,
            'include_ext_alt_text': True,
            'include_quote_count': True,
            'include_reply_count': 1,
            'tweet_mode': 'extended',
            'include_entities': True,
            'include_user_entities': True,
            'include_ext_media_color': True,
            'include_ext_media_availability': True,
            'send_error_codes': True,
            'simple_quoted_tweet': True,
            'q': query,
            'count': 20,
            'query_source': 'typed_query',
            'pc': 1,
            'spelling_corrections': 1,
            'tweet_search_mode': 'live',
            'ext': 'mediaStats,highlightedLabel,voiceInfo'
        }
        if cursor is not None: params['cursor'] = cursor
        return urllib.parse.urlencode(params)

    def getCsrf(self):
        resp = self.request("https://twitter.com/search?q=hf&src=typed_query")
        if not resp.cookies:
            raise Exception("[getCsrf] Something is Wrong!") 
        cookies_dict = dict_from_cookiejar(resp.cookies)
        cookies_dict.update({'x-csrf-token': self.token})
        self.cookies = cookies_dict 

    def getGuestToken(self):
        headers = {
            'x-csrf-token': self.token,
            'authorization': 'Bearer ' + self.publicToken,
        }
        resp = self.request('https://api.twitter.com/1.1/guest/activate.json', cookies=self.cookies, headers=headers, method='POST')
        try:
            resp_json = json.loads(resp.content)
        except ValueError as e:
            raise Exception("[getGuestToken] Json is Not Valid!")
        self.guestToekn = resp_json['guest_token']

    def getTweets(self, query):
        headers = {
            'x-csrf-token': self.token,
            'authorization': 'Bearer ' + self.publicToken,
            'x-guest-token': self.guestToekn
        }
        self.cookies.update({'gt': self.guestToekn, 'ct0': self.token})
        resp = self.request("https://twitter.com/i/api/2/search/adaptive.json?" + self.createParams(self.query, self.cursor), cookies=self.cookies, headers=headers)
        try:
            resp_json = json.loads(resp.content)
        except ValueError as e:
            raise Exception("[getTweets] Json is Not Valid!")
        if len(resp_json['timeline']['instructions']) < 2:
            cursor = resp_json['timeline']['instructions'][0]['addEntries']['entries'][len(resp_json['timeline']['instructions'][0]['addEntries']['entries'])-1]['content']['operation']['cursor']['value']
        else: cursor = resp_json['timeline']['instructions'][2]['replaceEntry']['entry']['content']['operation']['cursor']['value']
        if cursor == self.cursor or len(resp_json['globalObjects']['tweets']) == 0: return None
        if self.cursor == '': 
            if self.firstPack is not None:
                diff = len(list(set(list(resp_json['globalObjects']['tweets'].keys())) ^ set(self.firstPack)))
                if diff > 0:
                    self.firstPack = list(resp_json['globalObjects']['tweets'].keys())
            else:
                self.firstPack = list(resp_json['globalObjects']['tweets'].keys())
        
        self.cursor = cursor
        return resp_json['globalObjects']
       
    def run(self):
        self.getCsrf()
        self.getGuestToken()
        coutner,coutner2,i = 0,0,0
        while True:
            results = self.getTweets(self.query)
            if results is None: 
                    self.cursor = ''
                    sys.stdout.write('[Sleeping...]\r')
                    sleep(5)
                    continue

            if len(list(set(list(results['tweets'].keys())) ^ set(self.firstPack))) == 0 and coutner > 0: 
                self.cursor = ''
                sys.stdout.write('[Nope Sleeping...]\r')
                sleep(5)
                continue
            coutner2 += len(results['tweets'])
            for key,value in results['tweets'].items():
                if len(value['entities']['urls']) == 0: continue
                url = value['entities']['urls'][0]['expanded_url']
                userId = value['user_id_str']
                if results['users'].get(userId) is None: continue
                userName = results['users'][userId]['screen_name']
                self.db.insert('users', 
                    {
                        'user_id': userId,
                        'tweet_id': value['id'],
                        'user_name': userName,
                        'time': value['created_at'],
                        'link': url
                    }
                )
                coutner+=1
                sys.stdout.write('[%s]\r' % (coutner))
            i+=1

    def request(self, uri, headers={}, cookies=None, method='GET'):
        headers.update({
            'Referer': 'https://twitter.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:79.0) Gecko/20100101 Firefox/79.0'
        })
        response = requests.request(method, uri, cookies=cookies, headers=headers)
        if response.ok is False :
            raise Exception("[Request] Something is Wrong!")
        return response
