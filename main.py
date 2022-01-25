import asyncio
import datetime
from multiprocessing import Process
from crwlr.crawler import Crawler
import time


def backend_loop(interval: float) -> None:
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    crawler = Crawler(loop, board='a')
    loop.run_until_complete(crawler.chkdb())
    sec = datetime.datetime.now().second + 7
    if sec > 59:
        sec -= 60
    while True:
        if datetime.datetime.now().second == sec:
            t0 = time.time_ns()
            loop.run_until_complete(crawler.get_threads())
            sleep = interval - (float(time.time_ns() - t0) / 10.0e8)
            print(f'Sleep: {round(sleep, 1)} s\n\n')
            sleep = interval - (float(time.time_ns() - t0) / 10.0e8) - 2.0
            if sleep > 0.0:
                time.sleep(sleep)


if __name__ == "__main__":
    interval = 60.0
    p = Process(target=backend_loop(interval))
    p.start()


