import db
from zoneinfo import ZoneInfo

DATABASE_URL = "postgresql://postgres:1234@localhost:5433/postgres"
from datetime import datetime, timedelta

TZ = ZoneInfo("Asia/Tashkent")


async def get_staff_by_username(username):
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM staff WHERE telegram_id=$1",
            username
        )
        return dict(row) if row else None

async def get_staff_by_telegram_id(tg_id):
    async with db.pool.acquire() as conn:
        staff =  await conn.fetchrow(
            "SELECT * FROM staff WHERE telegram_id=$1",
            tg_id
        )
        return staff

async def get_company_by_telegram_id(tg_id):
    async with db.pool.acquire() as conn:
        staff =  await conn.fetchrow(
            "SELECT * FROM companies WHERE telegram_id=$1",
            tg_id
        )
        return staff


async def get_staff_by__id(staff_id):
    async with db.pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM staff WHERE id=$1",
            staff_id
        )
async def get_comapny_by__id(company_id):
    async with db.pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM companies WHERE id=$1",
            company_id
        )


async def check_subscription(staff_id=None, company_id=None):
    if company_id:
        async with db.pool.acquire() as conn:
            status = await conn.fetchval("""
                SELECT subscription_until FROM companies
                WHERE id=$1
            """, company_id)
        print(status)
    elif staff_id:
        async with db.pool.acquire() as conn:
            status = await conn.fetchval("""
                SELECT subscription_until FROM staff
                WHERE id=$1
            """, staff_id)
    # sub = datetime.fromisoformat(barber["subscription_until"])

    return status > datetime.now(TZ)


async def get_available_slots(staff, user_id, day_type):
    now = datetime.now(TZ)
    if day_type == "today":
        day = now.date()
    else:
        day = (now + timedelta(days=1)).date()
    if staff["tomorrow_closed"]:
        return []


    start_hour, start_minute = map(int, staff["work_start"].strftime("%H:%M").split(":"))
    end_hour, end_minute = map(int, staff["work_end"].strftime("%H:%M").split(":"))

    start_time = datetime(day.year, day.month, day.day,
                          start_hour, start_minute, tzinfo=TZ)
    end_time = datetime(day.year, day.month, day.day,
                        end_hour, end_minute, tzinfo=TZ)

    now = datetime.now(TZ)
    slots = []

    async with db.pool.acquire() as conn:

        # foydalanuvchi bugun nechta slot olgan
        user_count = await conn.fetchval("""
            SELECT COUNT(*) FROM bookings
            WHERE user_id=$1
            AND staff_id=$2
            AND DATE(slot_time)=$3
            AND source=$4
        """, user_id, staff["id"], day, 'user')

        if user_count >= 2:
            return []

        current = start_time

        while current < end_time:

            if current > now:

                # exists = await conn.fetchval("""
                #     SELECT COUNT(*) FROM bookings
                #     WHERE barber_id=$1 AND slot_time=$2
                # """, barber["id"], current)
                exists = await conn.fetchval("""
                    SELECT COUNT(*) FROM bookings
                    WHERE staff_id=$1
                    AND slot_time=$2
                    AND status IN ('pending','confirmed')
                """, staff["id"], current)
                if exists == 0:
                    slots.append(current)

            current += timedelta(minutes=30)

    return slots

async def create_booking(staff_id, user_id, slot_time, name, phone, extra_phone):
    async with db.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users(id, name)
            VALUES($1,$2)
            ON CONFLICT (id) DO NOTHING
        """, user_id, name)
    async with db.pool.acquire() as conn:
        exists = await conn.fetchval("""
            SELECT COUNT(*) FROM bookings
            WHERE staff_id=$1
            AND slot_time=$2
            AND status IN ('pending','confirmed')
        """, staff_id, slot_time)
        if exists >= 1:
            return False

        today = slot_time.date()

        user_count = await conn.fetchval("""
            SELECT COUNT(*) FROM bookings
            WHERE user_id=$1
            AND staff_id=$2
            AND DATE(slot_time)=$3
            AND status IN ('pending','confirmed')
        """, user_id, staff_id, today)
        if user_count >= 2:
            return False

        await conn.execute("""
            INSERT INTO bookings
            (staff_id, user_id, slot_time, created_at, name, phone, extra_phone)
            VALUES ($1,$2,$3,$4,$5,$6,$7)
            ON CONFLICT (staff_id, slot_time) WHERE status IN ('pending','confirmed') DO NOTHING
        """, staff_id, user_id, slot_time, datetime.now(TZ), name, phone, extra_phone)

        return True
async def create_booking_forstaff(staff_id, user_id, slot_time, name, phone, extra_phone):

    async with db.pool.acquire() as conn:
        try:
            await conn.execute("""
                INSERT INTO bookings
                (staff_id, user_id, slot_time, created_at, name, phone, extra_phone, source)
                VALUES ($1,$2,$3,$4,$5,$6,$7, $8)
                ON CONFLICT (staff_id, slot_time) WHERE status IN ('pending','confirmed') DO NOTHING
            """, staff_id, user_id, slot_time, datetime.now(TZ), name, phone, extra_phone, 'staff')
            return True
        except:
            return False

import math


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c  # masofa metrda

