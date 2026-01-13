import asyncio
import logging

from os import environ
from dotenv import load_dotenv

from util.connection_util import connect_to_db
from configs.logging_config import setup_logging
from readers.config_reader import ConfigReader
from services.collector_service import CollectorService
from writers import DatabaseWriter

load_dotenv()
setup_logging()

logger = logging.getLogger(__name__)

async def main():
    try:
        config_path = environ.get("CONFIG_PATH", "config.yaml")
        configs = ConfigReader.load_config(config_path)
    except FileNotFoundError:
        logger.error("Config file config.yaml not found.")
        return

    if not configs:
        logger.error("No controllers configured in config.yaml")
        return
    
    db_url = environ.get("DB_URL")
    if not db_url:
        logger.error("Database configuration is missing in environment variables.")
        return

    service = CollectorService()
    for controller_config in configs:
        try:
            dbm, entry_id = await connect_to_db(db_url, controller_config.owner_id)
            await service.run(controller_config, DatabaseWriter(dbm, entry_id))
        except Exception:
            logger.exception(
                "Controller run failed for %s", controller_config.controller
            )


if __name__ == "__main__":
    asyncio.run(main())
