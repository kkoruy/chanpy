import datetime
import time
from urllib.error import HTTPError
from urllib.request import urlopen
import asyncio
import json

import pymongo.errors

from ml.analyser import Analyzer
import OpenSSL.SSL
import aiohttp
from aiohttp import ClientHttpProxyError, ServerTimeoutError, ServerDisconnectedError, ServerConnectionError, \
    ContentTypeError
import numpy as np
from db.asyncdbwriter import AsyncDBWriter
from crwlr.textmanipulator import TextManipulator
from crwlr.threadutils import new_thread, update_thread, fetch_posts


class Crawler:
    def __init__(self, eventloop: asyncio.events, board='pol'):
        self.__loop = eventloop
        self.api_prefix = 'a.4cdn.org'
        self.turl = 'boards.4chan.org'
        self.tkw = 'thread'
        self.tsuffix = ''
        self.iurl = f'is2.4chan.org/{board}'
        self.pol = '4pol'
        self.board = board
        self.__json_url = 'https://{0}/{1}/catalog.json'.format(self.api_prefix, self.board)
        self._threads = {}
        self._msgs = {}
        self._fstats = {}
        self._active_list = [0] * 216
        self._kill_list = [0] * 216
        self._database = AsyncDBWriter(self.__loop, 'chanbot', 'chanbot_db', '127.0.0.1', 49153)
        self._thread_api_base = 'https://{0}/{1}/{2}/'.format(self.api_prefix, self.board, self.tkw)
        self.__initialized = False
        self.__analyzer = Analyzer(7)
        self.__last_timestamp = time.time_ns() - 59999999999
        self._txtmp = TextManipulator()

    async def chkdb(self):
        tnums = [t['no'] for p in self.__fetch() for t in p['threads']]
        await self._database.test_threads_for_dupes(tnums)
        ts = 2 * (len(tnums) - 1) + 1
        tasks = [self.__chkpsts(tn) for tn in tnums]
        coroutine = asyncio.as_completed(tasks)
        for i, coro in enumerate(coroutine):
            print(f'\rTesting DB: {str(round(100.0 * float(i * 2) / float(ts), 2)).rjust(5)} %', end='')
            await coro
            print(f'\rTesting DB: {str(round(100.0 * float(2 * i + 1) / float(ts), 2)).rjust(5)} %', end='')

    async def __chkpsts(self, tn):
        thread_api = await self._async_chk_thread(tn)
        if thread_api != '':
            await self._database.test_posts_for_dupes([post['no'] for post in json.loads(thread_api)['posts']])

    async def _async_chk_thread(self, tn: int):
        turl = self._thread_api_base + str(tn) + '.json'
        thread_api_json = ''
        for i in range(14):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(turl) as resp:
                        thread_api_json = await resp.text()
            except (ClientHttpProxyError, ServerTimeoutError, ServerDisconnectedError, ServerConnectionError,
                    ContentTypeError, TimeoutError) as err:
                if err.code == 404:
                    print('\nthread {0} err 404'.format(turl))
                    return ''
                else:
                    print(err.code, err)
                    thread_api_json = ''
            if thread_api_json != '':
                return thread_api_json
        return thread_api_json

    def __fetch(self):
        chan_api = []
        while len(chan_api) == 0:
            try:
                chan_api = json.loads(urlopen(self.__json_url).read())
            except HTTPError as err:
                if err.code == 404:
                    print('\napi {0} err 404'.format(self.__json_url))
                print(err)
                chan_api = []
            except OpenSSL.SSL.Error as sslerr:
                print(sslerr)
                chan_api = []
        chan_api[0]['threads'] = chan_api[0]['threads'][2:]
        return chan_api

    # gets the json file and iterates through threads
    async def get_threads(self) -> None:
        txxx0 = time.time_ns()
        if self.__loop.is_closed():
            self.__loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.__loop)
        self._fstats = {'new_posts': 0, 'new_threads': 0, 'words': 0, 'ppm': -1.0, 'flags': {}}
        self._active_list = []
        self._kill_list = []
        posts, attachments, new_threads = {}, {}, []
        ts_fetch_start = time.time_ns()
        while time.time_ns() - self.__last_timestamp < 59999999999:
            ts_fetch_start = time.time_ns()
        board_api = self.__fetch()
        ts_fetch_complete = datetime.datetime.now()
        for page in reversed(board_api):
            tasks = [asyncio.create_task(self.__threadripper(thread['no'], self._threads, self._fstats, self._msgs,
                                                             self._database, self._txtmp, thread))
                     for thread in reversed(page['threads'])]
            for coroutine in asyncio.as_completed(tasks):
                result = await coroutine
                thread, new_posts, new_attachments, self._fstats, tlist, nwthrd, tn = result
                self._threads[tn] = thread
                if nwthrd:
                    new_threads.append(tn)
                posts.update(new_posts)
                for k, v in new_attachments.items():
                    if k in attachments.keys():
                        attachments[k]['posts'].extend(v['posts'])
                    else:
                        attachments[k] = v
                if tlist:
                    self._active_list.append(tn)
                else:
                    self._kill_list.append(tn)
        try:
            if len(new_threads) > 0:
                await self._database.insert_threads([self._threads[tnum] for tnum in sorted(new_threads)])
            await self._database.insert_posts_relational(posts)
            await self._database.insert_attachments(attachments)
            for k, v in self._msgs.items():
                self._threads[k], self._msgs[k] = await self.analyze_text(self._threads[k], k, v, 7)
            print(f"\n\nTotal Fetch Time: {round((time.time_ns() - txxx0) / 10.0e8, 5)} s")
            Crawler.__print_country_stats(self._fstats)
            await self.__prune_threads_from_memory()

            if self.__initialized:
                deltat = float(ts_fetch_start - self.__last_timestamp) / 10.0e8
                self._fstats['ppm'] = 60.0 * float(self._fstats['new_posts']) / deltat
                await self._database.insert_boardstats(ts_fetch_complete, self._fstats)
                self.__last_timestamp = ts_fetch_start
                self.__print_fetch_stats(self._fstats, deltat)
            else:
                self.__initialized = True
            print(
                f"Total Time: {round((time.time_ns() - txxx0) / 10.0e8, 5)} s\t\t{datetime.datetime.now().strftime('%H:%M:%S')}")
        except pymongo.errors.BulkWriteError:
            print('No new threads to add\n')  # skips the threads since they already exist

    async def __threadripper(self, tn: int, threads: dict, fstats: dict, msgs: dict, db: AsyncDBWriter,
                             txtmp: TextManipulator, fetched_thread: dict) -> tuple[
        dict, dict, dict, dict, bool, bool, int]:
        if tn not in threads.keys():
            threads[tn] = new_thread(fetched_thread)
            fstats['new_threads'] += 1
            msgs[tn] = Crawler.CleanedMessages()
            thread_ops, newthread = {}, True
        elif fetched_thread['replies'] > threads[tn]['#replies']:
            threads[tn], thread_ops = update_thread(threads[tn], fetched_thread)
            newthread = False
        else:
            threads[tn]['newreps'] = 0
            return threads[tn], {}, {}, fstats, True, False, tn
        thread_api = await self._async_chk_thread(tn)
        if thread_api == '':
            threads[tn]['newreps'] = 0
            threads[tn]['active'] = False
            # await db.prune_thread(tn)
            return threads[tn], {}, {}, fstats, False, False, tn
        posts, attchmnts, threads[tn], stats, ops, m = await fetch_posts(threads[tn], thread_api, txtmp, thread_ops)
        msgs[tn].extend(m)
        fstats = Crawler._update_stats(fstats, stats)
        if ops['poffset'] > 0:
            await db.update_thread(threads[tn], tn, ops)
        if not threads[tn]['active']:
            # await db.prune_thread(tn)
            return threads[tn], posts, attchmnts, fstats, False, False, tn
        return threads[tn], posts, attchmnts, fstats, True, newthread, tn

    async def __prune_threads_from_memory(self) -> None:
        pruned_list = [int(tn) for tn in np.setdiff1d(list(self._threads.keys()), self._active_list)]
        if len(pruned_list) > 0:
            merged_kill_list = list(set(self._kill_list) | set(pruned_list))
            tsks = [asyncio.create_task(self.__async_prune(tn)) for tn in merged_kill_list]
            coroutine = asyncio.as_completed(tsks)
            for coro in coroutine:
                await coro

    async def __async_prune(self, tn: int) -> None:
        if self._msgs[tn] > 0 and len(self._msgs[tn].msgs) > 1:
            await self.analyze_text(tn, self._msgs[tn], 0)
            # kws = keyword_extraction({tn: self._msgs[tn].msgs})
        await self._database.prune_thread(tn)
        del self._threads[tn]
        del self._msgs[tn]

    async def analyze_text(self, thread, tn, msg, threshold=0) -> tuple[dict, dict]:
        if msg > threshold:
            for doc in self.__analyzer.anyalze([' '.join(thread['link_kw'] + msg.msgs)], 5):
                thread['kw'] = [k for k, v in doc.user_data['kw'].items()]
                thread['polarity'] = doc.user_data['sentiment']['polarity']
                thread['subjectivity'] = doc.user_data['sentiment']['subjectivity']
            docs = self.__analyzer.anyalze(msg.msgs[msg.offset:], 5, keywords=False)
            idx = 0
            db_write_list = []
            for n, m in enumerate(msg.msgs[msg.offset:]):
                if m != '':
                    pn = n + msg.offset
                    thread['posts'][pn]['polarity'] = docs[idx][0]
                    thread['posts'][pn]['subjectivity'] = docs[idx][1]
                    db_write_list.append((pn, (docs[idx][0], docs[idx][1])))
                    idx += 1
            msg.new = 0
            msg.offset = len(msg.msgs)
            await self._database.update_analysis(tn, thread['kw'], thread['polarity'], thread['subjectivity'],
                                                 db_write_list)
        return thread, msg

    @staticmethod
    def _update_stats(sd: dict, d: dict) -> dict:
        for k, v in d.items():
            if isinstance(v, dict):
                sd[k] = Crawler._update_stats(sd[k], v) if k in sd.keys() else v
            else:
                sd[k] = v if k not in sd.keys() else v + sd[k]
        return sd

    @staticmethod
    def __print_country_stats(sd: dict) -> None:
        print('\033[4mFlag: Posts:    %      Words:   Words/Post:\033[0m')
        for cnt, (f, d) in enumerate(sorted(sd['flags']['C'].items(), key=lambda item: item[1]['posts'], reverse=True)):
            if cnt == 14 or d['posts'] < 3:
                break
            psts, pstsp = str(d['posts']).ljust(5), str(round(100.0 * d['posts'] / sd['new_posts'], 1)).ljust(5)
            wrds, wrdsppst = str(d['words']).ljust(5), str(round(d['words'] / d['posts'], 1)).ljust(5)
            print(f"{f}:   {psts}\t{pstsp}%     {wrds}    {wrdsppst}")

    @staticmethod
    def __print_fetch_stats(sd: dict, deltat: float):
        print(f'\n\033[4m                      New:                {deltat}   \033[0m',
              f"\nPosts: {sd['new_posts']}\t\tThreads: {sd['new_threads']}\t\tTot. Words: {sd['words']}")  # ,

    async def __async_fetch(self) -> str:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.__json_url) as resp:
                    chan_api_str = await resp.text()
        except (
                ClientHttpProxyError, ServerTimeoutError, ServerDisconnectedError, ServerConnectionError,
                ContentTypeError) as err:
            print(err.code, err)
            return ''
        chan_api_json = json.loads(chan_api_str)
        chan_api_json[0]['threads'] = chan_api_json[0]['threads'][2:]
        return chan_api_json

    def __check_thread(self, tn: int):
        turl = self._thread_api_base + str(tn) + '.json'
        try:
            thread_api = urlopen(turl).read()
        except HTTPError as err:
            if err.code == 404:
                print('\nthread {0} err 404'.format(turl))
            thread_api = ''
        return thread_api

    class CleanedMessages:
        def __init__(self):
            self.new = 0
            self.offset = 0
            self.msgs = []

        def append(self, element: str) -> None:
            self.msgs.append(element)
            if element != '':
                self.new += 1

        def extend(self, elements: list[str, ...]) -> None:
            for element in elements:
                if element != '':
                    self.msgs.append(element)
                    self.new += 1

        def __bool__(self) -> bool:
            return self.new > 0

        def __len__(self) -> int:
            return len(self.msgs)

        def __gt__(self, other: int) -> bool:
            return self.new > other

        def __lt__(self, other: int) -> bool:
            return self.new < other

        def __le__(self, other: int) -> bool:
            return self.new <= other

        def __ge__(self, other: int) -> bool:
            return self.new >= other

        def __eq__(self, other: int) -> bool:
            return self.new == other
