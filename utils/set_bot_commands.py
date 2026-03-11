
import db
import asyncio
from datetime import datetime
from aiogram import types
from zoneinfo import ZoneInfo
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from loader import bot
TZ = ZoneInfo("Asia/Tashkent")
async def booking_manager_loop():
    """
    - 20 min oldin reminder tugmalar bilan
    - 10 min javob bermasa avtomatik cancel
    - No-show count update
    - 3 marta kelmasa blacklist
    """
    while True:
        now = datetime.now(TZ)

        async with db.pool.acquire() as conn:
            # 1️⃣ Pending va confirmed buyurtmalar
            bookings = await conn.fetch("""
                SELECT b.id, b.user_id, b.staff_id, b.slot_time, b.status, b.reminder_sent, u.no_show_count, u.blocked
                FROM bookings b
                JOIN users u ON u.id = b.user_id
                WHERE b.status IN ('pending','confirmed')
            """)

            for b in bookings:
                booking_id = b["id"]
                user_id = b["user_id"]
                staff_id = b["staff_id"]
                slot_time = b["slot_time"]
                status = b["status"]
                reminder_sent = b["reminder_sent"]
                blocked = b["blocked"] or False
                no_show_count = b["no_show_count"] or 0

                delta = (slot_time - now).total_seconds()

                # 🔹 Blocked user - skip
                # if blocked:
                #     continue

                # ======================
                # 20 min oldin reminder
                # ======================
                if 0 < delta <= 1200 and not reminder_sent:
                    kb = InlineKeyboardMarkup()
                    kb.add(
                        InlineKeyboardButton("✅ Kelaman", callback_data=f"confirm_{booking_id}"),
                        InlineKeyboardButton("❌ Kelmayman", callback_data=f"cancel_{booking_id}")
                    )
                    try:
                        await bot.send_message(
                            user_id,
                            f"⏰ {slot_time.astimezone(TZ).strftime('%H:%M')} ga yoziluvingiz bor.\nKelasizmi?",
                            reply_markup=kb
                        )
                        await conn.execute(
                            "UPDATE bookings SET reminder_sent=TRUE WHERE id=$1",
                            booking_id
                        )
                    except:
                        pass

                # ======================
                # 10 min javob bermasa avtomatik cancel
                # ======================
                if 0 < delta <= 600 and status == 'pending' and reminder_sent:
                    await conn.execute(
                        "UPDATE bookings SET status='cancelled' WHERE id=$1",
                        booking_id
                    )
                    try:
                        await bot.send_message(
                            user_id,
                            f"Siz tomondan javob bo\'lmaganligi sababli ⏰ {slot_time.astimezone(TZ).strftime('%H:%M')} dagi yoziluvingiz bekor qilindi",

                        )
                    except:
                        pass
                    # No-show count++
                    no_show_count += 1
                    await conn.execute(
                        "UPDATE users SET no_show_count=$1 WHERE id=$2",
                        no_show_count, user_id
                    )
                    # 3 marta bo‘lsa blacklist

                    # if no_show_count >= 3:
                    #     await conn.execute(
                    #         "UPDATE users SET blocked=TRUE WHERE id=$1",
                    #         user_id
                    #     )

                # ======================
                # Slot vaqti o‘tib ketgan, user kelmagan
                # ======================
                if slot_time < now and status in ('pending', 'confirmed'):
                    await conn.execute(
                        "UPDATE bookings SET status='cancelled' WHERE id=$1",
                        booking_id
                    )
                    no_show_count += 1
                    await conn.execute(
                        "UPDATE users SET no_show_count=$1 WHERE id=$2",
                        no_show_count, user_id
                    )
                    # if no_show_count >= 3:
                    #     await conn.execute(
                    #         "UPDATE users SET blocked=TRUE WHERE id=$1",
                    #         user_id
                    #     )

        await asyncio.sleep(60)  # 1 daqiqa kutish

async def check_no_show():
    now = datetime.now(TZ)
    async with db.pool.acquire() as conn:
        bookings = await conn.fetch("""
            SELECT id, user_id, slot_time, status
            FROM bookings
            WHERE status IN ('pending','confirmed')
        """)

        for b in bookings:
            if b["slot_time"] < now:
                await conn.execute("""
                    UPDATE bookings
                    SET status='no_show'
                    WHERE id=$1
                """, b["id"])
                # User no-show count++
                await conn.execute("""
                    UPDATE users
                    SET no_show_count = COALESCE(no_show_count,0)+1
                    WHERE id=$1
                """, b["user_id"])


async def blacklist_check(user_id):
    async with db.pool.acquire() as conn:
        count = await conn.fetchval("SELECT no_show_count FROM users WHERE id=$1", user_id)
        if count >= 3:
            # Userni block qilamiz
            await conn.execute("UPDATE users SET blocked=TRUE WHERE id=$1", user_id)


# async def set_default_commands(dp):
#     await dp.bot.set_my_commands(
#         [
#             types.BotCommand("start", "Botni ishga tushirish"),
#             types.BotCommand("help", "Yordam"),
#             types.BotCommand("buyurtmalarim", "Buyurtmalarim"),
#         ]
#     )

from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat


async def set_default_commands(dp):
    # 1️⃣ Oddiy foydalanuvchilar uchun global komandalar
    await dp.bot.set_my_commands(
        [
            BotCommand("start", "Botni ishga tushirish"),
            BotCommand("help", "Yordam")
        ],
        scope=BotCommandScopeDefault()
    )
    # 2️⃣ Barberlar uchun komandalarni DB orqali olish
    async with db.pool.acquire() as conn:
        barbers = await conn.fetch("SELECT telegram_id FROM staff WHERE active=TRUE")

    barber_commands = [
        BotCommand("start", "Botni ishga tushirish"),
        BotCommand("help", "Yordam"),
        BotCommand("staff", "Admin panel")
    ]
#
#     # Har bir barberga alohida komandalarni set qilish
#
