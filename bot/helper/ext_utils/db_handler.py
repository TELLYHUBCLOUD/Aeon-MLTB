from importlib import import_module

from aiofiles import open as aiopen
from aiofiles.os import path as aiopath
from motor.motor_asyncio import AsyncIOMotorClient as AsyncMongoClient
from pymongo.errors import PyMongoError
from pymongo.server_api import ServerApi

from bot import LOGGER, qbit_options, rss_dict, user_data
from bot.core.aeon_client import TgClient
from bot.core.config_manager import Config


class DbManager:
    """A class to manage interactions with the MongoDB database."""

    def __init__(self):
        """Initializes the DbManager, setting initial connection state."""
        self._return = True
        self._conn = None
        self.db = None

    async def connect(self):
        """Establishes a connection to the MongoDB database using DATABASE_URL."""
        try:
            if self._conn is not None:
                await self._conn.close()
            self._conn = AsyncMongoClient(
                Config.DATABASE_URL,
                server_api=ServerApi("1"),
            )
            self.db = self._conn.luna
            self._return = False
            LOGGER.info("Successfully connected to the database.")
        except PyMongoError as e:
            LOGGER.error(f"Error in DB connection: {e}")
            self.db = None
            self._return = True
            self._conn = None

    async def disconnect(self):
        """Closes the MongoDB connection."""
        self._return = True
        if self._conn is not None:
            await self._conn.close()
            LOGGER.info("Database connection closed.")
        self._conn = None

    async def update_deploy_config(self):
        """Updates or creates the deployment configuration in the database
        based on the current 'config.py' settings.
        """
        if self._return:
            return
        settings = import_module("config")
        config_file = {
            key: value.strip() if isinstance(value, str) else value
            for key, value in vars(settings).items()
            if not key.startswith("__")
        }
        await self.db.settings.deployConfig.replace_one(
            {"_id": TgClient.ID},
            config_file,
            upsert=True,
        )

    async def update_config(self, dict_):
        if self._return:
            return
        await self.db.settings.config.update_one(
            {"_id": TgClient.ID},
            {"$set": dict_},
            upsert=True,
        )

    async def update_aria2(self, key, value):
        if self._return:
            return
        await self.db.settings.aria2c.update_one(
            {"_id": TgClient.ID},
            {"$set": {key: value}},
            upsert=True,
        )

    async def update_qbittorrent(self, key, value):
        if self._return:
            return
        await self.db.settings.qbittorrent.update_one(
            {"_id": TgClient.ID},
            {"$set": {key: value}},
            upsert=True,
        )

    async def save_qbit_settings(self):
        if self._return:
            return
        await self.db.settings.qbittorrent.update_one(
            {"_id": TgClient.ID},
            {"$set": qbit_options},
            upsert=True,
        )

    async def update_private_file(self, path):
        if self._return:
            return
        db_path = path.replace(".", "__")
        if await aiopath.exists(path):
            async with aiopen(path, "rb+") as pf:
                pf_bin = await pf.read()
            await self.db.settings.files.update_one(
                {"_id": TgClient.ID},
                {"$set": {db_path: pf_bin}},
                upsert=True,
            )
            if path == "config.py":
                await self.update_deploy_config()
        else:
            await self.db.settings.files.update_one(
                {"_id": TgClient.ID},
                {"$unset": {db_path: ""}},
                upsert=True,
            )

    async def update_nzb_config(self):
        if self._return:
            return
        async with aiopen("sabnzbd/SABnzbd.ini", "rb+") as pf:
            nzb_conf = await pf.read()
        await self.db.settings.nzb.replace_one(
            {"_id": TgClient.ID},
            {"SABnzbd__ini": nzb_conf},
            upsert=True,
        )

    async def update_user_data(self, user_id):
        """Updates user-specific data in the database, excluding certain sensitive keys
        like tokens from the main user_data dict before persisting.
        It preserves existing THUMBNAIL, RCLONE_CONFIG, TOKEN_PICKLE from DB if not in memory.
        """
        if self._return:
            return
        data = user_data.get(user_id, {})
        data = data.copy()
        for key in ("THUMBNAIL", "RCLONE_CONFIG", "TOKEN_PICKLE", "TOKEN", "TIME"):
            data.pop(key, None)
        pipeline = [
            {
                "$replaceRoot": {
                    "newRoot": {
                        "$mergeObjects": [
                            data,
                            {
                                "$arrayToObject": {
                                    "$filter": {
                                        "input": {"$objectToArray": "$$ROOT"},
                                        "as": "field",
                                        "cond": {
                                            "$in": [
                                                "$$field.k",
                                                [
                                                    "THUMBNAIL",
                                                    "RCLONE_CONFIG",
                                                    "TOKEN_PICKLE",
                                                ],
                                            ],
                                        },
                                    },
                                },
                            },
                        ],
                    },
                },
            },
        ]
        await self.db.users.update_one({"_id": user_id}, pipeline, upsert=True)

    async def update_user_doc(self, user_id, key, path=""):
        if self._return:
            return
        if path:
            async with aiopen(path, "rb+") as doc:
                doc_bin = await doc.read()
            await self.db.users.update_one(
                {"_id": user_id},
                {"$set": {key: doc_bin}},
                upsert=True,
            )
        else:
            await self.db.users.update_one(
                {"_id": user_id},
                {"$unset": {key: ""}},
                upsert=True,
            )

    async def rss_update_all(self):
        if self._return:
            return
        for user_id in list(rss_dict.keys()):
            await self.db.rss[TgClient.ID].replace_one(
                {"_id": user_id},
                rss_dict[user_id],
                upsert=True,
            )

    async def rss_update(self, user_id):
        if self._return:
            return
        await self.db.rss[TgClient.ID].replace_one(
            {"_id": user_id},
            rss_dict[user_id],
            upsert=True,
        )

    async def rss_delete(self, user_id):
        if self._return:
            return
        await self.db.rss[TgClient.ID].delete_one({"_id": user_id})

    async def add_incomplete_task(self, cid, link, tag):
        if self._return:
            return
        await self.db.tasks[TgClient.ID].insert_one(
            {"_id": link, "cid": cid, "tag": tag},
        )

    async def get_pm_uids(self):
        if self._return:
            return None
        return [doc["_id"] async for doc in self.db.pm_users[TgClient.ID].find({})]

    async def update_pm_users(self, user_id):
        """Adds a user_id to the pm_users collection if not already present,
        logging the addition.
        """
        if self._return:
            return
        if not bool(await self.db.pm_users[TgClient.ID].find_one({"_id": user_id})):
            await self.db.pm_users[TgClient.ID].insert_one({"_id": user_id})
            LOGGER.info(f"New PM user added: {user_id}")

    async def rm_pm_user(self, user_id):
        if self._return:
            return
        await self.db.pm_users[TgClient.ID].delete_one({"_id": user_id})

    async def update_user_tdata(self, user_id, token, time):
        if self._return:
            return
        await self.db.access_token.update_one(
            {"_id": user_id},
            {"$set": {"TOKEN": token, "TIME": time}},
            upsert=True,
        )

    async def update_user_token(self, user_id, token):
        if self._return:
            return
        await self.db.access_token.update_one(
            {"_id": user_id},
            {"$set": {"TOKEN": token}},
            upsert=True,
        )

    async def get_token_expiry(self, user_id):
        if self._return:
            return None
        user_data = await self.db.access_token.find_one({"_id": user_id})
        if user_data:
            return user_data.get("TIME")
        return None

    async def delete_user_token(self, user_id):
        if self._return:
            return
        await self.db.access_token.delete_one({"_id": user_id})

    async def get_user_token(self, user_id):
        if self._return:
            return None
        user_data = await self.db.access_token.find_one({"_id": user_id})
        if user_data:
            return user_data.get("TOKEN")
        return None

    async def delete_all_access_tokens(self):
        if self._return:
            return
        await self.db.access_token.delete_many({})

    async def rm_complete_task(self, link):
        if self._return:
            return
        await self.db.tasks[TgClient.ID].delete_one({"_id": link})

    async def get_incomplete_tasks(self):
        notifier_dict = {}
        if self._return:
            return notifier_dict
        if await self.db.tasks[TgClient.ID].find_one():
            rows = self.db.tasks[TgClient.ID].find({})
            async for row in rows:
                if row["cid"] in list(notifier_dict.keys()):
                    if row["tag"] in list(notifier_dict[row["cid"]]):
                        notifier_dict[row["cid"]][row["tag"]].append(row["_id"])
                    else:
                        notifier_dict[row["cid"]][row["tag"]] = [row["_id"]]
                else:
                    notifier_dict[row["cid"]] = {row["tag"]: [row["_id"]]}
        await self.db.tasks[TgClient.ID].drop()
        return notifier_dict

    async def trunc_table(self, name):
        if self._return:
            return
        await self.db[name][TgClient.ID].drop()


database = DbManager()
