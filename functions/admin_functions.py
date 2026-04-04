
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Tashkent")
import db


async def add_service_function(name, business):
    async with db.pool.acquire() as conn:
        await conn.execute("""
                INSERT INTO services(name, has_business)
                VALUES ($1, $2)
                """, name.lower(), business)

async def add_region_function(name):
    async with db.pool.acquire() as conn:
        await conn.execute("""
                INSERT INTO regions (name_uz) 
                VALUES ($1)
                """, name.lower())
async def add_destrict_function(region_id, name):
    async with db.pool.acquire() as conn:
        await conn.execute("""
                INSERT INTO districts (region_id, name_uz) 
                VALUES ($1, $2)
                """,region_id, name.lower())



async def get_all_staffs_function():
    async with db.pool.acquire() as conn:
        staffs = await conn.fetch(
            """SELECT id, name, subscription_until, phone, telegram_id
            FROM staff
            WHERE company_id IS NULL
            ORDER BY subscription_until  DESC
            """
        )
        return staffs

async def get_all_company_function():
    async with db.pool.acquire() as conn:
        companies = await conn.fetch(
            """SELECT id, name, subscription_until, phone, telegram_id
            FROM companies
            ORDER BY subscription_until"""
        )
        return companies



