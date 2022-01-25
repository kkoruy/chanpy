from flask import Flask
from flask_pymongo import PyMongo


class FlaskDBWriter:
    def __init__(self, app: Flask):
        self.__client = PyMongo(app, uri='mongodb://chanbot:poolsclosed@localhost:49153/chanbot_db')
        self.__db = self.__client.db
        self.__threads = self.__db.threads
        self.__posts = self.__db.posts

    # for the POST method
    def create_thread(self, thread):
        self.__threads.insert_one(thread)
        return self.__threads.find_one({'_id': thread['_id']})

    # for DELETE method
    def delete_thread(self, thrd_no):
        target = self.__threads.find_one({'_id': int(thrd_no)})

        if target is None:
            return 'False'
        else:
            self.__threads.delete_one(target)

        check = self.__threads.find_one({'_id': int(thrd_no)})
        if check is None:
            return 'True'
        else:
            return 'False'

    def post_on_thread(self, post):
        self.__threads.update_one({'_id': int(post['thread_id'])}, {'$push': {'posts': {'$each': [post]}}})
        return self.__threads.find_one({'_id': int(post['thread_id'])})
    #
    # def delete_post(self, thrd_no, post_no):  # not working
    #     target = self.__threads.posts.find_one({'_id': int(post_no)})
    #     self.__threads.delete_one(target)
    #     check = self.__threads.find_one({'_id': int(thrd_no), 'posts._id': int(post_no)})
    #     if check is None:
    #         return 'post deleted'
    #     else:
    #         return 'error, post not deleted\n\n'
