import datetime
from db.database import DataBase
from bson.binary import Binary, BINARY_SUBTYPE


class AsyncDBWriter(DataBase):
    def __init__(self, loop, user, db_name, host='localhost', port=49153):
        DataBase.__init__(self, loop, user, db_name, host, port)

    async def insert_thread(self, thread: dict) -> None:
        await self.__async_insert_thread(thread)

    async def insert_threads(self, threads: list[dict, ...]) -> None:
        await self.__async_insert_threads(threads)

    async def update_thread(self, thread: dict, tnum: int, operations: dict) -> None:
        await self.__async_update_thread(thread, tnum, operations)

    async def update_analysis(self, tnum: int, keywords: list[str, ...], polarity: float, subjectivity: float,
                              sentiment_posts: list[tuple[int, tuple[float, float]], ...]) -> None:
        await self.__async_update_analysis(tnum, keywords, polarity, subjectivity, sentiment_posts)

    async def insert_posts_relational(self, posts: dict) -> None:
        await self.__async_insert_posts_relational(posts)

    async def insert_attachments(self, attachments: dict) -> None:
        await self.__async_insert_attachments(attachments)

    async def insert_boardstats(self, timestamp: datetime.datetime, stat_data: dict) -> None:
        await self.__async_insert_boardstats(timestamp, stat_data)

    async def prune_thread(self, tn: int) -> None:
        await self.__async_prune_thread(tn)

    async def test_threads_for_dupes(self, indices) -> None:
        await self.__async_test_threads_for_dupes(indices)

    async def test_posts_for_dupes(self, indices) -> None:
        await self.__async_test_posts_for_dupes(indices)

    async def __async_insert_thread(self, thread: dict) -> None:
        await self._threads.insert_one(thread)

    async def __async_insert_threads(self, threads: list[dict, ...]) -> None:
        await self._threads.insert_many(documents=threads, ordered=False)

    async def __async_update_thread(self, thread: dict, tnum: int, operations: dict) -> None:
        await self._threads.update_one({'_id': tnum}, {'$set': operations['thread']})
        offset = operations['poffset']
        if offset > 0:
            await self._threads.update_one({'_id': tnum}, {'$push': {'posts': {'$each': thread['posts'][offset:]}}})
            if 'new' in operations['update']['users'].keys():
                await self._threads.update_one({'_id': tnum},
                                               {'$set':
                                                    {f'users.{uid}':
                                                         data for uid, data in
                                                     operations['update']['users']['new'].items()}})
            if 'posts' in operations['update'].keys():
                for pnum, val in operations['update']['posts'].items():
                    await self._threads.update_one({'_id': tnum},
                                                   {'$push':
                                                        {f'posts.{pnum}.rby_posts':
                                                             {'$each': v} if len(v) > 0 else v[0]
                                                         for k, v in val.items()}})
            if 'update' in operations['update']['users'].keys():
                db_update = {'$push': {f'users.{uid}.{k}': {'$each': v} if len(v) > 0 else v[0]
                                       for uid, val in operations['update']['users']['update'].items()
                                       for k, v in val.items() if k != 'flag'}}
                if 'flag' in operations['update']['users'].keys():
                    db_update['$set'] = {f'users.{uid}.flag': val['flag']
                                         for uid, val in operations['update']['users']['update'].items()}
                await self._threads.update_one({'_id': tnum}, db_update, upsert=True)

    async def __async_update_analysis(self, tnum: int, keywords: list[str, ...],
                                      polarity: float, subjectivity: float,
                                      post_sentiments: list[tuple[int, tuple[float, float]], ...]) -> None:
        print(f'{tnum} ANALYSIS:', polarity, subjectivity, keywords)
        update_dict = {'kw': [], 'polarity': polarity, 'subjectivity': subjectivity}
        update_dict.update({k: v for pnum, (p, s) in post_sentiments
                            for k, v in {f'posts.{pnum}.polarity': p, f'posts.{pnum}.subjectivity': s}.items()})
        await self._threads.update_one({'_id': tnum}, {'$set': update_dict})
        await self._threads.update_one({'_id': tnum}, {'$push': {'kw': {'$each': keywords}}})

    async def __async_insert_posts_relational(self, posts: dict) -> None:
        await self._posts.insert_many([refs for pnum, refs in sorted(posts.items())], ordered=True)

    async def __async_insert_attachments(self, attachments: dict) -> None:
        # await self._attachments.update_many(*[({'_id': Binary(key, subtype=BINARY_SUBTYPE)},
        #                                       {'$push': {'posts': {'$each': vals['posts']}}})
        #                                      for key, vals in attachments.items()], upsert=True)
        for key, vals in attachments.items():
            bsonbinary = Binary(key, subtype=BINARY_SUBTYPE)
            if await self._attachments.count_documents({'_id': bsonbinary}, limit=1) > 0:
                await self._attachments.update_one({'_id': bsonbinary}, {'$push': {'posts': {'$each': vals['posts']}}})
            else:
                await self._attachments.insert_one(vals)

    async def __async_insert_boardstats(self, timestamp: datetime.datetime, stat_data: dict) -> None:
        bson = {'ts': timestamp}
        bson.update(stat_data)
        await self._fstats.insert_one(bson)

    async def __async_test_threads_for_dupes(self, indices) -> None:
        await self._threads.delete_many({'_id': {'$in': indices}})

    async def __async_test_posts_for_dupes(self, indices) -> None:
        await self._posts.delete_many({'_id': {'$in': indices}})

    @staticmethod
    def __k2s(d: dict) -> [list, dict]:
        return [AsyncDBWriter.__k2s(el) for el in d] if isinstance(d, list) else (
            {str(k): AsyncDBWriter.__k2s(v) if isinstance(v, dict) else v for k, v in d.items()}
            if isinstance(d, dict) else d)

    async def __async_prune_thread(self, tnum: int) -> None:
        await self._threads.update_one({'_id': tnum}, {'$set': {'active': False, 'newreps': 0}})
        cursor = self._threads.aggregate([{'$match': {'_id': tnum}},
                                          {'$project': {'_id': 0, 'p': "$posts"}}, {'$unwind': "$p"},
                                          {'$project': {'_id': "$p._id"}}])
        # {'$unwind': {'path': '$posts'}},
        # {'$project': {'_id': 0, 'pnum': '$posts._id'}}])
        for doc in await cursor.to_list(length=None):
            await self._posts.update_one({'_id': doc['_id']}, {'$set': {'active': False}})
