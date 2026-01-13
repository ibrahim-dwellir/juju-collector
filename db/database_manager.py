from os import environ
from databases import Database
from logging import getLogger, DEBUG

class QueryDumper(Database):
    """ A primitive database wrapper that logs all queries and responses."""
    def __init__(self, *args, **wqargs):
        super().__init__(*args, **wqargs)
        self.logger = getLogger("Database")
        self.logger.setLevel(DEBUG)

    async def execute(self, *args, **kwargs):
        ret = await super().execute(*args, **kwargs)
        self.logger.debug(f"execute({args}, {kwargs}) -> {ret}")
        return ret
    
    async def fetch_all(self, *args, **kwargs):
        ret = await super().fetch_all(*args, **kwargs)
        self.logger.debug(f"fetch_all({args}, {kwargs}) -> {ret}")
        return ret
    
    async def fetch_one(self, *args, **kwargs):
        ret = await super().fetch_one(*args, **kwargs)
        self.logger.debug(f"fetch_one({args}, {kwargs}) -> {ret}")
        return ret

class DatabaseManager:
    def __init__(self, db_url=None, owner=None, record=False):
        self.logger = getLogger("DatabaseManager")
        if not db_url or not owner:
            raise ValueError("Database configuration is missing.")
        if record or environ.get("RECORD_QUERIES"):
            self.logger.info("Recording queries")
            self.db = QueryDumper(db_url)
        else:
            self.db = Database(db_url)
        self.owner_id = int(owner)
        self.entry = None
        self.transaction = None

    async def connect(self):
        await self.db.connect()
        await self.start_transaction()
        self.entry = await self.get_entry()
        return self.entry

    async def start_transaction(self):
        self.transaction = await self.db.transaction()
        return self.transaction

    async def commit(self):
        if self.transaction:
            await self.transaction.commit()
            self.transaction = None

    async def rollback(self):
        if self.transaction:
            await self.transaction.rollback()
            self.transaction = None

    async def disconnect(self):
        if self.transaction:
            try:
                await self.transaction.rollback()
            finally:
                self.transaction = None
        await self.db.disconnect()

    async def get_entry(self):
        return await self.db.execute("INSERT INTO entry (owner) values (:owner) returning id", {"owner": self.owner_id})

    async def view(self, name):
        rows = await self.db.fetch_all(
            "SELECT version FROM versions WHERE component = :name AND supported=TRUE",
            {"name": f"views:{name}"}
        )
        return [row["version"] for row in rows]
    
    async def procedure(self, name):
        rows = await self.db.fetch_all(
            "SELECT version FROM versions WHERE component = :name AND supported=TRUE",
            {"name": f"procs:{name}"}
        )
        return [row["version"] for row in rows]
    
    async def best_view(self, name):
        versions = await self.view(name)
        return max(versions) if versions else None
    
    async def best_procedure(self, name):
        versions = await self.procedure(name)
        return max(versions) if versions else None
