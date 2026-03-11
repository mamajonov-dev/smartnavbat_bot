from datetime import datetime
from zoneinfo import ZoneInfo


TZ = ZoneInfo("Asia/Tashkent")

from data.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

pool = None

async def connect_db():
    global pool
    pool = await asyncpg.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        min_size=1,
        max_size=10
    )

async def close_db():
    global pool
    if pool:
        await pool.close()





# =====================
# INIT TABLES
# =====================
async def init_db():
    async with pool.acquire() as conn:

        # =========================
        # Users / Foydalanuvchilar
        # =========================
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY,
            name TEXT,
            no_show_count INT DEFAULT 0,
            blocked BOOLEAN DEFAULT FALSE,
            status VARCHAR(20) DEFAULT 'pending',
            telegram_id BIGINT
        )
        """)

        # =========================
        # Services / Xizmatlar
        # =========================
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            has_business BOOLEAN DEFAULT FALSE
        )
        """)
        # await conn.execute("""
        #         INSERT INTO services(name, has_business)
        #         VALUES ($1, $2)
        #
        #         """, 'Klinikalar', True)

        # =========================
        # Companies / Bizneslar
        # =========================
        await conn.execute("""      
        CREATE TABLE IF NOT EXISTS companies (
            id SERIAL PRIMARY KEY,
            service_id INT REFERENCES services(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            work_start TIME DEFAULT '09:00',
            work_end TIME DEFAULT '21:00',
            tomorrow_closed BOOLEAN DEFAULT FALSE,
            active BOOLEAN DEFAULT TRUE,
            subscription_until TIMESTAMPTZ,
            telegram_id TYPE BIGINT
        )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_companies_service_id ON companies(service_id);")

        # =========================
        # Staff / Ustalar
        # =========================
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            id SERIAL PRIMARY KEY,
            service_id INT REFERENCES services(id) ON DELETE CASCADE,
            company_id INT REFERENCES companies(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            active BOOLEAN DEFAULT TRUE,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            work_start TIME DEFAULT '09:00',
            work_end TIME DEFAULT '21:00',
            tomorrow_closed BOOLEAN DEFAULT FALSE,
            subscription_until TIMESTAMPTZ,
            telegram_id TYPE BIGINT
            
        )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_staff_company_id ON staff(company_id);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_staff_service_id ON staff(service_id);")

        # =========================
        # Booking status ENUM
        # =========================
        await conn.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'booking_status') THEN
                CREATE TYPE booking_status AS ENUM ('pending','confirmed','cancelled');
            END IF;
        END$$;
        """)

        # =========================
        # Bookings / Bronlar
        # =========================
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id SERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
            staff_id INT REFERENCES staff(id) ON DELETE CASCADE,
            slot_time TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now(),
            status booking_status DEFAULT 'pending',
            reminder_sent BOOLEAN DEFAULT FALSE,
            name TEXT,
            phone TEXT,
            extra_phone TEXT,
            UNIQUE(staff_id, slot_time)
        )
        """)

        await conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS unique_active_slot
        ON bookings(staff_id, slot_time)
        WHERE status IN ('pending','confirmed');
        """)

        await conn.execute("CREATE INDEX IF NOT EXISTS idx_bookings_staff_id ON bookings(staff_id);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_bookings_slot_time ON bookings(slot_time);")


from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import asyncpg
import asyncio
async def update_subscription(new_date, company_id=None, staff_id=None):
    async with pool.acquire() as conn:
        if company_id:
            await conn.execute("""
                UPDATE companies 
                SET subscription_until=$1 
                WHERE id=$2
            """, new_date, company_id)

            await conn.execute("""
                UPDATE staff 
                SET subscription_until=$1 
                WHERE company_id=$2
            """, new_date, company_id)

        else:
            await conn.execute("""
                UPDATE staff 
                SET subscription_until=$1 
                WHERE id=$2
            """, new_date, staff_id)

