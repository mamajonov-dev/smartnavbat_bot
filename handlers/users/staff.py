from aiogram import types
from aiogram.types import (
    Message, CallbackQuery,
    KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from loader import bot, dp
from functions.functions import *
from functions.statistics import *
from states.states import *
from data.config import *
from keyboards.default.asosiymenu import *

@dp.message_handler(commands=['staff'])
async def barber_panel_menu(message: Message):
    staff = await get_staff_by_telegram_id(message.from_user.id)
    if not staff:
        return await message.answer("Siz barber emassiz.")

    else:
        if staff['company_id']:
            async with db.pool.acquire() as conn:
                company = await conn.fetchrow("""
                            SELECT name, tomorrow_closed, work_start, work_end
                            FROM companies
                            WHERE id=$1
                        """, staff["company_id"])
                print(company)
                name = company['name']
                tomorrow_closed = company['tomorrow_closed']
                work_start = company['work_start']
                work_end = company['work_end']
        else:
            tomorrow_closed = staff['tomorrow_closed']
            work_start = staff['work_start']
            work_end = staff['work_end']
            name = staff['name']

        status_text = "🔴 Ertaga yopiq" if tomorrow_closed else f"🟢 Ertaga ochiq"
        status_time = "🔴 Ertaga yopiq" if tomorrow_closed else f"🟢 Ertaga ochiq.\n🕒 Ish vaqti: {work_start} - {work_end}"
        text = f"👤<b>{name.title()}</b> - paneli\n\nErtaga: {status_time}"

        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton(
                f"{status_text} (o‘zgartirish)",
                callback_data="toggle_tomorrow"
            )
        )
        kb.add(InlineKeyboardButton(f"🕒 Ish vaqtini o‘zgartirish", callback_data="change_work_time"))
        await message.answer(text, reply_markup=kb)

        await message.answer('Admin menu', reply_markup=staff_menu_button())


@dp.message_handler(text="🔗 Referal link yaratish")
async def create_referal_link(message: Message):
    staff = await get_staff_by_telegram_id(message.chat.id)
    if staff:
        link = f"https://t.me/smartnavbat_bot?start={message.chat.id}"
        await message.answer(f'🔗 Sizning Referal havolangiz: \n\n\n{link}')

# 2️⃣ Message handler - reply keyboarddan tanlash
# ==============================================
@dp.message_handler(lambda m: m.text in ["📅 Ertangi navbatlarni ko\'rish", "📅 Bugungi navbatlarni ko\'rish"])
async def show_booking_day_reply(message: types.Message):
    user_id = message.from_user.id
    today = datetime.now(TZ).date()
    target_date = today if message.text == "📅 Bugungi navbatlarni ko\'rish" else today + timedelta(days=1)

    # Staff / hodimni olish
    async with db.pool.acquire() as conn:
        staff = await conn.fetchrow("""
            SELECT id, name, company_id
            FROM staff
            WHERE telegram_id=$1 AND active=TRUE
        """, user_id)

    if not staff:
        return await message.answer("Siz xizmat ko\'rsatuvchi emassiz yoki faol emas.")

    # Agar kompaniya bor bo‘lsa → kompaniya darajasida barcha hodimlar
    if staff["company_id"]:
        async with db.pool.acquire() as conn:
            staff_list = await conn.fetch("""
                SELECT id, name
                FROM staff
                WHERE company_id=$1 AND active=TRUE
                ORDER BY name
            """, staff["company_id"])
    else:
        staff_list = [staff]
    # target_date = bugun yoki ertangi sana
    async with db.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT s.id AS staff_id, s.name AS staff_name,
                   b.id AS booking_id, b.slot_time, b.status,
                   b.name AS customer_name, b.phone, b.extra_phone
            FROM staff s
            LEFT JOIN bookings b 
                   ON s.id = b.staff_id 
                   AND DATE(b.slot_time) = $1
                   AND b.status IN ('pending','confirmed')
            WHERE s.id = ANY($2::int[])
            ORDER BY s.name, b.slot_time
        """, target_date, [s["id"] for s in staff_list])
    print(rows)
    # Python tarafida staff bo‘yicha guruhlash
    from collections import defaultdict

    staff_bookings = defaultdict(list)
    staff_names = {}
    for row in rows:
        staff_id = row["staff_id"]
        staff_names[staff_id] = row["staff_name"]
        if row["booking_id"]:  # agar booking bo‘lsa
            staff_bookings[staff_id].append(row)

    # xabar yuborish
    for staff_id in staff_names:
        bookings = staff_bookings.get(staff_id, [])
        if not bookings:
            await message.answer(f"👤 {staff_names[staff_id]} — Bu kun mijoz yo‘q.")
            continue

        # text = f"👤 {staff_names[staff_id]} — {'Bugungi' if message.text == '📅 Bugun' else 'Ertangi'} mijozlar:\n\n"
        for b in rows:
            text = f"""👤 {staff_names[staff_id]} — {'Bugungi' if message.text == "📅 Bugungi navbatlarni ko'rish" else 'Ertangi'} mijozlar:\n\n"""
            # name = b['customer_name']
            # phone = b['phone']
            # extra_phone = b['extra_phone']
            booking_id = b["booking_id"]
            # time = b["slot_time"].astimezone(TZ).strftime("%H:%M")
            status = b["status"]
            slot_time = (
                b["slot_time"].astimezone(TZ).strftime("%H:%M")
                if b["slot_time"]
                else "Noma'lum"
            )
            # slot_time = b["slot_time"].astimezone(TZ).strftime("%H:%M")
            status_emoji = "🟢 Keladi" if b["status"] == "confirmed" else "🟡 Band qilingan"
            text += f"🕒 {slot_time}\n👤 {b['customer_name']}\nTelefon: {b['phone']}, {b['extra_phone']}\nHolati: {status_emoji}\n\n"
            kb = InlineKeyboardMarkup()
            if status == "pending" and b['slot_time'].astimezone(TZ) > datetime.now(TZ):
                kb.add(
                    InlineKeyboardButton(
                        "❌ Bekor qilish",
                        callback_data=f"staff_cancel_{booking_id}"
                    )
                )
            await message.answer(text, reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data == "change_work_time")
async def change_work_time(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "Yangi ish boshlanish vaqtini kiriting.\n\nMasalan:\n09:00", reply_markup=cancelbutton()
    )
    await EditTimeState.start.set()


@dp.message_handler(state=EditTimeState.start)
async def save_start_work_time(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await message.answer('Bekor qilindi. Asosiy menu', reply_markup=staff_menu_button())
        await state.finish()
        return
    else:

        try:
            hour, minute = map(int, message.text.strip().split(":"))
            if not (0 <= hour < 24 and 0 <= minute < 60):
                raise ValueError
            start_time = time(hour, minute)
        except ValueError:
            await message.answer("❌ Vaqt noto‘g‘ri formatda. Iltimos HH:MM ko‘rinishida kiriting (masalan 09:00).",
                                 reply_markup=cancelbutton())
            return

        # ✅ FSM ga saqlash
        # await state.update_data(start=start_time.strftime("%H:%M"))
        await state.update_data(start=message.text)

        await message.answer(
            "Yangi ish tugash vaqtini kiriting.\n\nMasalan:\n18:00",
            reply_markup=cancelbutton()
        )
        await EditTimeState.end.set()


from datetime import datetime, time

@dp.message_handler(state=EditTimeState.end)
async def save_end_work_time(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await message.answer('Bekor qilindi. Asosiy menu', reply_markup=staff_menu_button())
        await state.finish()
        return
    else:
        # ✅ Foydalanuvchi kiritgan end vaqtini tekshirish
        try:
            hour, minute = map(int, message.text.strip().split(":"))
            if not (0 <= hour < 24 and 0 <= minute < 60):
                raise ValueError
            end_time = time(hour, minute)
        except ValueError:
            await message.answer(
                "❌ Vaqt noto‘g‘ri formatda. Iltimos HH:MM ko‘rinishida kiriting (masalan 18:00).",
                reply_markup=cancelbutton()
            )
            return

        # ✅ FSM dan start vaqtini olish
        data = await state.get_data()
        try:
            start_time_str = data['start']
            start_hour, start_minute = map(int, start_time_str.split(":"))
            start_time = time(start_hour, start_minute)
        except Exception:
            await message.answer("❌ Start vaqti topilmadi, qayta boshlang.", reply_markup=staff_menu_button())
            await state.finish()
            return

        # ✅ Start < End tekshiruvi
        if end_time <= start_time:
            await message.answer("❌ Tugash vaqti boshlanish vaqtidan oldin bo‘lmasligi kerak.\nQayta kiriting:",
                                 reply_markup=cancelbutton())
            return

        # ✅ Barberni olish
        staff = await get_staff_by_telegram_id(message.from_user.id)
        print(staff)
        if not staff:
            await message.answer("❌ Xodim topilmadi.", reply_markup=staff_menu_button())
            await state.finish()
            return

        # ✅ DB ga saqlash
        async with db.pool.acquire() as conn:
            await conn.execute("""
                UPDATE staff
                SET work_start=$1, work_end=$2
                WHERE id=$3
            """, start_time, end_time, staff["id"])

        await message.answer("Ish vaqti yangilandi ✅", reply_markup=staff_menu_button())
        await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith("staff_cancel_"))
async def staff_cancel(callback: types.CallbackQuery):
    booking_id = int(callback.data.split("_")[2])

    async with db.pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT user_id, status
            FROM bookings
            WHERE id=$1
        """, booking_id)

        if not row:
            return await callback.answer("Topilmadi", show_alert=True)

        if row["status"] != "pending":
            return await callback.answer("Bekor qilib bo‘lmaydi", show_alert=True)

        await conn.execute("""
            UPDATE bookings
            SET status='cancelled'
            WHERE id=$1
        """, booking_id)

    # Userga habar beramiz
    try:
        await bot.send_message(
            row["user_id"],
            "❌ Xizmat ko'rsatuvchi tomonidan buyurtmangiz bekor qilindi."
        )
    except:
        pass

    await callback.message.edit_text("❌ Buyurtma bekor qilindi")
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data == "toggle_tomorrow")
async def toggle_tomorrow(callback: types.CallbackQuery):
    staff = await get_staff_by_telegram_id(callback.from_user.id)
    if not staff:
        return await callback.answer("Siz xodim emassiz ❌", show_alert=True)
    if staff['company_id']:
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                new_value = await conn.fetchval("""
                    UPDATE companies
                    SET tomorrow_closed = NOT tomorrow_closed
                    WHERE id=$1
                    RETURNING tomorrow_closed
                """, staff["company_id"])

                await conn.execute("""
                    UPDATE staff
                    SET tomorrow_closed=$1
                    WHERE company_id=$2
                """, new_value, staff["company_id"])
        # async with db.pool.acquire() as conn:
            # closed = await conn.fetchval("""
            #     SELECT tomorrow_closed
            #     FROM companies
            #     WHERE id=$1
            # """, staff["company_id"])
            #
            # new_value = not closed
            #
            # await conn.execute("""
            #     UPDATE companies
            #     SET tomorrow_closed=$1
            #     WHERE id=$2
            # """, new_value, staff["company_id"])
            # await conn.execute("""
            #     UPDATE staff
            #     SET tomorrow_closed=$1
            #      WHERE company_id=$2
            #     """, new_value, staff["company_id"])

    else:
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                new_value = await conn.fetchval("""
                    UPDATE staff
                    SET tomorrow_closed = NOT tomorrow_closed
                    WHERE id=$1
                    RETURNING tomorrow_closed
                """, staff["id"])
            # closed = await conn.fetchval("""
            #     SELECT tomorrow_closed
            #     FROM staff
            #     WHERE id=$1
            # """, staff["id"])
            #
            # new_value = not closed
            #
            # await conn.execute("""
            #     UPDATE staff
            #     SET tomorrow_closed=$1
            #     WHERE id=$2
            # """, new_value, staff["id"])

    # 🔹 Tugma matni
    status_text = "🔴 Ertaga yopiq" if new_value else "🟢 Ertaga ochiq"

    # 🔹 Yangi keyboard
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            f"{status_text} (o‘zgartirish)",
            callback_data="toggle_tomorrow"
        )
    )

    # 🔹 Faqat tugmani yangilash
    text = f"👤 {staff['name']} paneli\n\nErtaga: {status_text}"
    await callback.answer("Holat yangilandi ✅", show_alert=True)

    await callback.message.edit_text(text, reply_markup=kb)

    # await callback.message.edit_reply_markup(reply_markup=kb)



# @dp.message_handler(text='✂️ Barberlar')
# async def barbers(message: Message):
#     await message.answer("Lokatsiyangizni jo\'nating", reply_markup=location_button())
#     await LocationState.location.set()



@dp.message_handler(state=LocationState.location, content_types=['location'])
@dp.message_handler(state=LocationState.location)
async def getlocation(message: Message, state: FSMContext):
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude

        async with db.pool.acquire() as conn:
            barbers = await conn.fetch("""
                SELECT id, name, telegram_id, latitude, longitude
                FROM barbers
                WHERE active = TRUE
                  AND latitude IS NOT NULL
                  AND longitude IS NOT NULL
            """)

        if not barbers:
            await message.answer("❌ Sizga yaqin barber topilmadi.", reply_markup=search_barber_button())
            return

        # Masofa hisoblash
        distances = []
        for b in barbers:
            d = haversine(lat, lon, b["latitude"], b["longitude"])
            distances.append((b, d))

        # Eng yaqinlar
        distances.sort(key=lambda x: x[1])
        nearest = distances[:5]

        kb = InlineKeyboardMarkup(row_width=1)

        text = "💈 Eng yaqin barberlar:\n\n"
        for b, d in nearest:
            km = round(d / 1000, 2)
            text += f"• {b['name']} — {km} km\n"
            kb.add(
                InlineKeyboardButton(
                    text=f"✂️ {b['name']} ({km} km)",
                    callback_data=f"choose_barber_{b['id']}_{b['telegram_id']}"
                )
            )
        await message.answer(text, reply_markup=kb)
        await message.answer('Siz izlagan Barber topilmasa, "🔎 Barber qidirish" tugmasini bosing',
                             reply_markup=search_barber_button())
        await state.finish()
    else:
        if message.text == 'Bekor qilish':
            markup = await main_menu_button()
            await message.answer('Asosiy menu', reply_markup=markup)
            await state.finish()
        else:
            await message.answer('Buyruqlarni birini tanlang', reply_markup=location_button())
            await LocationState.location.set()

from keyboards.inline.inline_keyboards import offline_slots_keyboard
@dp.message_handler(text="➕ Offline mijoz qo‘shish")
async def add_offline_client(message: types.Message):
    staff = await get_staff_by_telegram_id(message.from_user.id)
    if not staff:
        return await message.answer("Siz staff emassiz.")

    kb = await offline_slots_keyboard(staff, message.chat.id, 'today')

    await message.answer("Band qilinadigan vaqtni tanlang:", reply_markup=kb)
@dp.callback_query_handler(lambda c: c.data.startswith("offline_slot_"))
async def offline_slot_book(callback: types.CallbackQuery):
    staff = await get_staff_by_telegram_id(callback.from_user.id)
    if not staff:
        return await callback.answer("Siz staff emassiz", show_alert=True)
    slot_str = callback.data.split("_", 2)[2]   # masalan 14:30
    today = datetime.now(TZ).date()
    hour, minute = map(int, slot_str.split(":"))
    slot_time = datetime(today.year, today.month, today.day, hour, minute, tzinfo=TZ)

    result = await create_booking_forstaff(
        staff_id=staff["id"],
        slot_time=slot_time,
        user_id=None,
        name="Offline mijoz",
        phone=None,
        extra_phone=None
    )
    if result is False:
        await callback.answer("Bu vaqt allaqachon band", show_alert=True)
    elif result is True:
        kb = await offline_slots_keyboard(staff, callback.message.chat.id, 'today')

        await callback.message.edit_text(
            f"✅ {slot_str} offline mijoz uchun band qilindi", reply_markup=kb
        )

        await callback.answer('"Slot muvaffaqiyatli band qilindi"', show_alert=True)

