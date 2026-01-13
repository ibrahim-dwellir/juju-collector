
from juju.controller import Controller
from db.database_manager import DatabaseManager

async def connect_to_juju(endpoint: str, username: str, password: str, cacert: str):
    c = Controller()
    await c.connect(
        endpoint=endpoint,
        username=username,
        password=password,
        cacert=cacert
    )
    return c

async def connect_to_db(url=None, owner_id=None):
    dbm = DatabaseManager(db_url=url, owner=owner_id)
    entry_id = await dbm.connect()
    return dbm, entry_id
