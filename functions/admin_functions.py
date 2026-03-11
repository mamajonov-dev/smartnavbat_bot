import db
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Tashkent")
import db


async def add_service_function(name, business):
    async with db.pool.acquire() as conn:
        await conn.execute("""
                INSERT INTO services(name, has_business)
                VALUES ($1, $2)
                """, name.lower(), business)


