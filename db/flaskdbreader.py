import time

from flask import Flask
from flask_pymongo import PyMongo
from datetime import datetime
from bson.json_util import dumps
import re
import json


def int2dt(unix_int: [int, float]) -> datetime:
    if unix_int > 999999999999:
        unix_int /= 1000.0
    return datetime.fromtimestamp(unix_int)


class FlaskDBReader:
    def __init__(self, app: Flask):
        self.__client = PyMongo(app, uri='mongodb://chanbot:poolsclosed@localhost:49153/chanbot_db')
        self.__db = self.__client.db
        self.__threads = self.__db.threads
        self.__posts = self.__db.posts
        self.__attachments = self.__db.attachments
        self.__fstats = self.__db.fstats

    def get_biggest_attachment(self) -> dict:
        vals = [i['size'] for i in self.__attachments.find()]
        mx = max(vals)
        clean_json = re.compile('ISODate\(("[^"]+")\)').sub('\\1', dumps(self.__attachments.find_one({'size': mx}, {'_id': 0, 'md5': 0, 'posts': 0})))
        json_obj = json.loads(clean_json)
        return json_obj

    def get_attachment(self) -> list:
        vals = [(i['filename'], i['size']/1000000, i['ext']) for i in self.__attachments.find({}, {'_id': 0, 'md5': 0, 'posts': 0})]
        return vals

    def get_thread(self, thrd_no) -> list or dict:
        if int(thrd_no) == 0:
            vals = [(i['_id'], i['#images'], i['#replies'], i['ts'], i['subjectivity'], i['polarity']) for i in self.__threads.find()]
            return vals
        else:
            clean_json = re.compile('ISODate\(("[^"]+")\)').sub('\\1', dumps(self.__threads.find_one({'_id': int(thrd_no)})))
            json_obj = json.loads(clean_json)
            return json_obj

    def get_imageno(self) -> int:
        n = 0
        for doc in self.__threads.aggregate([{'$match': {'active': True}},
                                             {'$group': {'_id': 'null', 'imgs': {'$sum': "$#images"}}}]):
            n += doc['imgs']
        return n

    def get_replyno(self) -> int:  # gets the number of replies of all active threads
        return self.__posts.find({'active': True}).count()

    def get_posts_timespan(self, start) -> list:
        values = []
        for post in self.__posts.find({'ts': {'$gte': int(start)}}):
            values.append(post)
        now = int(round(time.time() * 1000))
        res = [(post['tn'], post['active'], round((now - post['ts']) / 3600000)) for post in values]
        # returns (thrd_id, active, rel_date_hours)
        return res

    def get_latest_n_posts(self, n) -> list:
        values = []
        for post in self.__posts.find({'$query': {}, '$orderby': {'ts': -1}}).limit(int(n)):
            values.append(post)
        now = int(round(time.time() * 1000))
        res = [(post['tn'], post['active'], round((now - post['ts'])/3600000)) for post in values]
        # returns (thrd_id, active, rel_date_hours)
        return res

    def get_posts_from_thread(self, tnum) -> list:
        vals = [(i['_id'], i['posts']) for i in self.__threads.find({'_id': int(tnum)}, {'posts': 1})]
        res = []
        for index in range(len(vals)):
            for post in vals[index][1]:
                fpost = post['title'], post['msg'], post['links'], post['ts'], post['subjectivity'], post['polarity']
                threadid = vals[index][0]
                res.append((threadid, fpost))
        return res

    def get_flag_stats(self, start: [int, float], end: [int, float]) -> tuple:
        pass

    def get_boardstats(self, start: [int, float], end: [int, float]) -> list:
        res = [(doc['new_posts'], doc['new_threads'], round(doc['ppm'], 2), doc['words'], doc['ts']) for doc in self.__fstats.find({'ts': {'$gt': int2dt(start), '$lt': int2dt(end)}})]
        # returns [#new_posts, #new_threads, #posts_pm, #words_written, date_of_analysis]
        return res
