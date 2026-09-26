import asyncio
import logging
from config import settings
from database import engine, Base
import models 

logger = logging.getLogger(__name__)

async def init_models():
    async with engine.begin() as conn:
        # logger.info("Удаление старых таблиц")
        # await conn.run_sync(Base.metadata.drop_all)
        
        logger.info("Создание новых таблиц")
        await conn.run_sync(Base.metadata.create_all)
        

if __name__ == "__main__":
    asyncio.run(init_models())
