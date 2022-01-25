from abc import ABC
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import pymongo


class DataBase(ABC):
    def __init__(self, loop: asyncio.events, user: str, db_name: str, host: str, port: int):
        self._user = user
        self._db = None
        self._host = host
        self._port = port
        self._client = None
        self._threads = None
        self._posts = None
        self._attachments = None
        self._fstats = None
        self._loop = loop
        asyncio.set_event_loop(self._loop)
        try:  # try to instantiate a client instance
            self._client = AsyncIOMotorClient(
                str(self._host) + ":" + str(self._port),
                # serverSelectionTimeoutMS=3000,
                # tls=True,
                # tlsAllowInvalidCertificates=True,
                # tlsCertificateKeyFile='./db/keys/tls/client.pem',
                username=self._user,
                password="poolsclosed",
                authSource=db_name, connect=True, io_loop=self._loop)
            database_names = self._client.list_database_names()
        except (TimeoutError, UserWarning, pymongo.mongo_client.ConfigurationError,
                pymongo.mongo_client.ServerSelectionTimeoutError) as err:
            print("pymongo ERROR:", err)
        else:
            print(f"\ndatabases:\n{database_names}")
            self._db = self._client[db_name]
            self._threads = self._db.threads
            self._posts = self._db.posts
            self._attachments = self._db.attachments
            self._fstats = self._db.fstats
