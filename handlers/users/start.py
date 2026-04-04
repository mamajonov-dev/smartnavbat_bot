from aiogram import types

from aiogram.dispatcher import FSMContext
from keyboards.default.asosiymenu import *
from keyboards.inline.inline_keyboards import services_inline_button, staff_inline_button
from states.states import BookingInfoState

from loader import dp
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Tashkent")
from functions.functions import *
import db

@dp.message_handler(commands='start')
async def start_handler(message: types.Message, state: FSMContext):
    args = message.get_args()

    # 🔹 USER DB ga yozib qo‘yish (agar kerak bo‘lsa)
    async with db.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users(id, name, username)
            VALUES($1,$2, $3)
            ON CONFLICT (id) DO NOTHING
        """, message.from_user.id, message.from_user.full_name, message.from_user.username)

    # =====================================
    # 1️⃣ LINK ORQALI KIRGAN BO‘LSA
    # =====================================
    if args:
        staff = await get_staff_by_telegram_id(int(args))
        company = await get_company_by_telegram_id(int(args))
        if not staff:
            return await message.answer("Xizmat ko\'rsatuvchi topilmadi.")
        status_check = await check_subscription(staff_id=staff['id'])
        if not status_check:
            return await message.answer("Xizmat ko\'rsatuvchi obunasi tugagan.")
        if company:
            # await BookingInfoState.staff.set()
            markup = await staff_inline_button(company_id=company['id'])
            await message.answer(
                f"Xizmat ko\'rsatuvchi tashkilot: <b>{company['name']}</b>\nBugungi yozilish. Buyruqni tanlang",
                reply_markup=markup
            )
            await state.update_data(company_id=company['id'])
            await state.update_data(latitude=company['latitude'])
            await state.update_data(longitude=company['longitude'])
            await state.update_data(telegram_id=company['telegram_id'])
        else:
            await state.update_data(staff_id=staff['id'])
            await state.update_data(company_id=staff['company_id'])
            await state.update_data(latitude=staff['latitude'])
            await state.update_data(longitude=staff['longitude'])
            await state.update_data(telegram_id=staff['telegram_id'])

            await BookingInfoState.day.set()
            await message.answer(
                f"Xizmat ko\'rsatuvchi: <b>{staff['name']}</b>\nBugungi yozilish. Buyruqni tanlang",
                reply_markup=main_menu_inline(staff['id'])
            )
    else:
        markup = await main_menu_button()
        text = """
👋 Assalomu alaykum!

<b>SmartNavbat</b> botiga xush kelibsiz.

Bu bot orqali siz xizmatlarga qulay vaqtga yozilishingiz mumkin.

📌 Qanday ishlaydi:

1️⃣ Service tanlang  
2️⃣ Hodimni tanlang  
3️⃣ Vaqtni tanlang  
4️⃣ Bronni tasdiqlang

⏰ Yozilgan vaqtingizdan 10 minut oldin sizga eslatma yuboriladi.

✅ Qulay va tez navbat tizimi.
        """
        await message.answer(
                text,
                reply_markup=markup
            )


@dp.message_handler(text='Asosiy menu')
async def mainmenu(message: types.Message):
    markup = await main_menu_button()
    await message.answer('Asosiy menu', reply_markup=markup)

