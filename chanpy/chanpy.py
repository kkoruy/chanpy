# the main chanpy of the project
import getmac
import time
from datetime import datetime
from random import randint
import json
import requests as req
from webapp.user_login_app import mongo
from db.flaskdbreader import int2dt
import numpy as np


class Client:

    def __init__(self):
        self._t = None
        self._u_id = None
        self._u_name = None
        # checking if user has account
        self._mac = getmac.getmac.get_mac_address()
        _u_mac = mongo.db.users.find_one({'mac': self._mac})
        if _u_mac is None:
            print('Register first:')
            self.register()
        else:
            self._u_id = mongo.db.users.find_one({'mac': self._mac})['_id']
            self._t = mongo.db.api_tokens.find_one({'user_id': self._u_id})['token']
            self._u_name = mongo.db.users.find_one({'_id': self._u_id})['name']

    # Provides sign-up link if user is not registered
    def register(self):
        print('Sign up here: http://127.0.0.1:5001/registration')
        api_token = input('Token: ')
        try:
            self._t = mongo.db.api_tokens.find_one({'token': api_token})['token']
            self._u_id = mongo.db.api_tokens.find_one({'token': api_token})['user_id']
            self._u_name = mongo.db.users.find_one({'_id': self._u_id})['name']

            req.put(url=f'http://127.0.0.1:5001/user/{self._u_id}')  # setting user as admin
            print('Logged in as {0}'.format(self._u_name))

        # giving possibility to copy and pasting again the token
        except TypeError:
            api_token = input('Invalid or missing token, make sure you copied it right: ')
            t = mongo.db.api_tokens.find_one({'token': api_token})
            u = mongo.db.api_tokens.find_one({'token': api_token})

            while t is None or u is None:
                api_token = input('Invalid or missing token, make sure you copied it right (type exit to abort): ')
                if api_token.lower() == 'exit':
                    print('Please register correctly or you will not be able to use any command')
                    break

                t = mongo.db.api_tokens.find_one({'token': api_token})
                u = mongo.db.api_tokens.find_one({'token': api_token})

            else:
                self._t = t['token']
                self._u_id = t['user_id']
                self._u_name = mongo.db.users.find_one({'_id': self._u_id})['name']

                req.put(url=f'http://127.0.0.1:5001/user/{self._u_id}')  # setting user as admin
                print('Logged in as {0}'.format(self._u_name))

    # provides all users signed up
    def users(self):
        r = req.get(url='http://127.0.0.1:5001/user', headers={'x-access-token': self._t})
        data = r.json()['Users']
        res = []
        for user in data:
            res.append(user["name"])
        return np.array(res, dtype=object)

    # Returns number of images in active threads
    def n_images(self) -> int:
        r = req.get(url='http://127.0.0.1:5000/active-images', headers={'x-access-token': self._t})
        data = r.json()['active-images']
        return data

    # Returns number of replies in active threads
    def n_replies(self) -> int:
        r = req.get(url='http://127.0.0.1:5000/active-replies', headers={'x-access-token': self._t})
        data = r.json()['active-replies']
        return data

    # Return all posts in a given timespan
    def posts_ts(self, start_ddmmyyyy: str):
        start_ts = int(datetime.strptime(start_ddmmyyyy, "%d/%m/%Y").timestamp() * 1000)

        r = req.get(url='http://127.0.0.1:5000/posts/from', params={'start': start_ts},
                    headers={'x-access-token': self._t})
        data = r.json()['posts']
        return np.array(data, dtype=object)

    # Returns last "n" posts
    def latest_np(self, n: str) -> [[int, str, str, str]]:
        n = str(n)
        r = req.get(url='http://127.0.0.1:5000/posts/last', params={'n': n}, headers={'x-access-token': self._t})
        data = r.json()['posts']
        return np.array(data, dtype=object)

    # Returns statistics on users countries
    def c_stats(self, start_ddmmyyyy: str, end_ddmmyyyy: str):
        start_ts = int(datetime.strptime(start_ddmmyyyy, "%d/%m/%Y").timestamp() * 1000)
        end_ts = int(datetime.strptime(end_ddmmyyyy, "%d/%m/%Y").timestamp() * 1000)

        r = req.get(url='http://127.0.0.1:5000/stats/country/from', params={'start': start_ts, 'end': end_ts},
                    headers={'x-access-token': self._t})
        return r.json()

    # Returns statistics on board
    def b_stats(self, start_ddmmyyyy: str, end_ddmmyyyy: str):
        start_ts = int(datetime.strptime(start_ddmmyyyy, "%d/%m/%Y").timestamp() * 1000)
        end_ts = int(datetime.strptime(end_ddmmyyyy, "%d/%m/%Y").timestamp() * 1000)

        r = req.get(url='http://127.0.0.1:5000/stats/fetch', params={'start': start_ts, 'end': end_ts},
                    headers={'x-access-token': self._t})
        data = r.json()['bstats']
        return np.array(data, dtype=object)

    # Search for thread with given number
    def thread(self, thread_number=0):
        thrd_no = thread_number

        r = req.get(url='http://127.0.0.1:5000/threads', params={'thrd_no': thrd_no},
                    headers={'x-access-token': self._t})
        thrd = r.json()['threads']
        if type(thrd) == list:
            res = [(thrd[idx][0], thrd[idx][1], thrd[idx][2], int2dt(thrd[idx][3]).strftime('%d/%m/%Y %H:%M:%S'),
                    round(thrd[idx][4], 2), round(thrd[idx][5], 2)) for idx, k in enumerate(thrd)]
            return np.array(res)

        elif type(thrd) == dict:
            res = thrd['_id'], thrd['#images'], thrd['#replies'], int2dt(thrd['ts']).strftime('%d/%m/%Y %H:%M:%S'), \
                  round(thrd['subjectivity'], 2), round(thrd['polarity'], 2)
            return np.array(res)

        elif type(thrd) is None:
            return 'Thread not found'

    def add_t(self, title: str, username: str, text: str):  # Creates a new thread
        thread = {
            '_id': randint(1000000, 9999999),
            'title': title,
            'users': username,
            'text': text,
            'ts': int(round(time.time() * 1000)),
            'posts': []
        }
        r = req.post(url='http://127.0.0.1:5000/threads',
                     data=json.dumps(thread, indent=4, sort_keys=True, default=str), headers={'x-access-token': self._t})

        thrd = r.json()
        res = thrd['_id'], thrd['title'], thrd['text'], thrd['users'], int2dt(thrd['ts']).strftime('%d/%m/%Y %H:%M:%S')
        return np.array(res)

    def del_t(self, thread_number: int):  # Deletes a thread
        thrd_no = thread_number

        r = req.delete(url='http://127.0.0.1:5000/threads', params={'thrd_no': str(thrd_no)},
                       headers={'x-access-token': self._t})
        return r.text

    def add_p(self, thread_number: int, title: str, username: str, text: str):  # Creates a new post on a selected thread
        thrd_no = thread_number

        post = {
            '_id': randint(1000000, 9999999),
            'thread_id': int(thrd_no),
            'title': title,
            'users': username,
            'text': text,
            'ts': int(round(time.time() * 1000))
        }
        r = req.post(url='http://127.0.0.1:5000/threads/posts',
                     data=json.dumps(post, indent=4, sort_keys=True, default=str), headers={'x-access-token': self._t})

        thrd = r.json()
        pst = [i for i in thrd['posts'] if i['_id'] == post['_id']]
        res = thrd['_id'], pst[0]['title'], pst[0]['text'], pst[0]['users'], int2dt(pst[0]['ts']).strftime(
            '%d/%m/%Y %H:%M:%S')
        return np.array(res)

    # Search for post with given thread number
    def posts(self, thread_number: int, n=-1, msg=False):
        thrd_no = thread_number
        lastn = n
        if lastn == 0:
            lastn = 1
        r = req.get(url='http://127.0.0.1:5000/threads/posts', params={'thrd_no': thrd_no},
                    headers={'x-access-token': self._t})
        pst = r.json()['posts']
        if msg:
            res = [(pst[k][0], pst[k][1][0], pst[k][1][1], pst[k][1][2],
                    int2dt(pst[k][1][3]).strftime('%d/%m/%Y %H:%M:%S'),
                    pst[k][1][4], pst[k][1][5]) for k in range(len(pst))]
        else:
            res = [(pst[k][0], int2dt(pst[k][1][3]).strftime('%d/%m/%Y %H:%M:%S'),
                    pst[k][1][4], pst[k][1][5]) for k in range(len(pst))]
        if pst is not None:
            if lastn == 1:
                return res[-1]
            elif lastn == -1:
                return np.array(res[:-lastn:-1], dtype=object)
            else:
                return np.array(res[:-(lastn + 1):-1], dtype=object)  # returns every post or last n posts
        else:
            return 'Thread not found'

    def max_att(self):
        r = req.get(url='http://127.0.0.1:5000/threads/attachment/max', headers={'x-access-token': self._t})
        data = r.json()['biggest-att']
        res = data['filename'], data['size']/1000000, data['ext']
        return np.array(res, dtype=object)

    def att(self):
        r = req.get(url='http://127.0.0.1:5000/threads/attachment', headers={'x-access-token': self._t})
        data = r.json()['att']
        return np.array(data)

