import asyncio
from database import engine, Base
import models 

async def init_models():
    async with engine.begin() as conn:
        # print("Удаление старых таблиц")
        # await conn.run_sync(Base.metadata.drop_all)
        
        print("Создание новых таблиц")
        await conn.run_sync(Base.metadata.create_all)
        
    print("kus1 Ок")

if __name__ == "__main__":
    asyncio.run(init_models())
