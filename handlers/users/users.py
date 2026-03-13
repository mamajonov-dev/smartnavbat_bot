from aiogram import types
from aiogram.types import (
    Message, CallbackQuery,
    KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from datetime import datetime
from typing import Union
from loader import bot, dp
from functions.functions import *
from functions.statistics import *
from states.states import *
from data.config import *
from keyboards.default.asosiymenu import main_menu_button, main_menu_inline, cancelbutton, search_barber_button
from keyboards.inline.inline_keyboards import services_inline_button, companies_inline_button, staff_inline_button


@dp.message_handler(lambda m: m.text == "📋 Buyurtmalarim")
async def my_bookings(message: types.Message):
    async with db.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, slot_time, status
            FROM bookings
            WHERE user_id=$1
            ORDER BY slot_time ASC
        """, message.from_user.id)

    if not rows:
        return await message.answer("Sizda buyurtmalar yo‘q.")

    for row in rows:
        booking_id = row["id"]
        time_str = row["slot_time"].astimezone(TZ).strftime("%Y.%d.%m - %H:%M")
        status = row["status"]

        kb = InlineKeyboardMarkup()
        if status == "pending":
            kb.add(
                InlineKeyboardButton(
                    "❌ Bekor qilish",
                    callback_data=f"user_cancel_{booking_id}"
                )
            )
        if status == 'cancelled':
            status = '❌ Bekor qilingan'
        elif status == 'pending':
            status = '🕒 Kutish jarayonida'
        else:
            status = '✅ Tasdiqlangan'
        text = f"🕒 {time_str}\nHolati: {status}"

        await message.answer(text, reply_markup=kb)


@dp.callback_query_handler(lambda call: 'main_menu' in call.data)
async def back_to_main_menu(callback: CallbackQuery):
    chatid = callback.message.chat.id
    markup = await services_inline_button()
    await bot.send_message(chat_id=chatid, text='Asosiy menu', reply_markup=markup)
    await callback.message.delete()


@dp.message_handler(text='📝 Navbatga yozilish')
async def show_services(message: Message):
    servive_button = await services_inline_button()
    await message.answer('📋 Iltimos, xizmat turini tanlang', reply_markup=servive_button)


@dp.callback_query_handler(lambda c: c.data.startswith("service"))
async def choose_service(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data.split("_")
    service_id = int(data[1])
    has_business = data[2].lower() in ("true", "1", "yes")
    chatid = callback.message.chat.id
    if has_business:
        markup = await companies_inline_button(service_id)
        await bot.send_message(chat_id=chatid, text='🏢 Iltimos, tashkilotni tanlang', reply_markup=markup)
    else:
        markup = await staff_inline_button(service_id=service_id)
        await bot.send_message(chat_id=chatid, text='Xizmat ko\'rsatuvchini tanlang', reply_markup=markup)
    await callback.message.delete()


@dp.callback_query_handler(lambda c: c.data.startswith("choose_company"))
async def choose_service(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data.split("_")
    company_id = int(data[-1])
    status = await check_subscription(company_id=company_id)
    if not status:
        return await callback.answer("Obuna tugagan", show_alert=True)

    chatid = callback.message.chat.id
    markup = await staff_inline_button(company_id=company_id)
    await bot.send_message(chat_id=chatid, text='Xizmat ko\'rsatuvchini tanlang', reply_markup=markup)
    await callback.message.delete()


@dp.callback_query_handler(lambda call: 'choose_staff_' in call.data)
async def choose_staff(callback: CallbackQuery, state: FSMContext):
    chatid = callback.message.chat.id
    data = callback.data.split('_')
    company_id = data[2]
    staff_id = int(data[3])
    staff_name = data[4]
    # if not barber:
    #     return await callback.answer("Topilmadi", show_alert=True)
    status = await check_subscription(staff_id=staff_id)
    if not status:
        return await callback.answer("Obuna tugagan", show_alert=True)

    await callback.message.delete()
    await callback.message.answer(
        f" <b>{staff_name}</b>\nBugungi yozilish",
        reply_markup=main_menu_inline(staff_id)
    )

    async with db.pool.acquire() as conn:
        staff = await conn.fetchrow("""
                SELECT latitude, longitude, telegram_id
                FROM staff
                WHERE id=$1
            """, staff_id)

    if not staff:
        return await callback.answer("Topilmadi", show_alert=True)

    await state.update_data(staff_id=staff_id)
    await state.update_data(company_id=company_id)
    await state.update_data(latitude=staff['latitude'])
    await state.update_data(longitude=staff['longitude'])
    await state.update_data(telegram_id=staff['telegram_id'])

    await BookingInfoState.staff.set()



@dp.callback_query_handler(state=BookingInfoState.staff)
@dp.message_handler(state=BookingInfoState.staff)
async def booking_handler(update: Union[types.CallbackQuery, types.Message], state: FSMContext):
    markup = await main_menu_button()
    if isinstance(update, types.CallbackQuery):
        data = update.data

        if data.startswith(("today_booking", "tomorrow_booking")):
            state = dp.current_state(user=update.from_user.id)
            user_data = await state.get_data()


            staff_id = user_data["staff_id"]

            # qaysi kun tanlandi
            day_type = data.split("_")[0]  # today yoki tomorrow

            async with db.pool.acquire() as conn:
                staff = await conn.fetchrow(
                    "SELECT id,work_start,work_end,tomorrow_closed,telegram_id FROM staff WHERE id=$1",
                    staff_id
                )

            if not staff:
                await state.finish()
                return await update.message.answer(
                    "Xizmat ko\'rsatuvchi topilmadi",
                    reply_markup=markup
                )

            # slotlarni olish
            slots = await get_available_slots(
                staff,
                update.from_user.id,
                day_type  # today yoki tomorrow
            )

            await state.update_data(
                telegram_id=staff['telegram_id'],
                staff_id=staff_id
            )

            if not slots:
                await update.message.delete()
                await state.finish()
                return await update.message.answer(
                    "Bo‘sh slot yo‘q",
                    reply_markup=markup
                )

            kb = InlineKeyboardMarkup(row_width=3)

            for slot in slots:
                time_str = slot.astimezone(TZ).strftime("%H:%M")

                kb.insert(
                    InlineKeyboardButton(
                        text=time_str,
                        callback_data=f"slot_{day_type}_{time_str}"
                    )
                )

            await bot.send_message(
                chat_id=update.message.chat.id,
                text='Bekor qilish uchun pastdagi tugmani bosing',
                reply_markup=cancelbutton()
            )

            await update.message.delete()

            await update.message.answer(
                "⏰ Qulay vaqtni tanlang",
                reply_markup=kb
            )

            await BookingInfoState.time.set()

        else:
            await update.message.answer(
                'Asosiy menu',
                reply_markup=markup
            )
            await state.finish()
    #
    # if isinstance(update, types.CallbackQuery):
    #     data = update.data
    #     if data.startswith("today_booking"):
    #         state = dp.current_state(user=update.from_user.id)
    #
    #         data = await state.get_data()
    #
    #         staff_id = data["staff_id"]
    #
    #         async with db.pool.acquire() as conn:
    #             staff = await conn.fetchrow(
    #                 "SELECT * FROM staff WHERE id=$1",
    #                 staff_id
    #             )
    #         if not staff:
    #             await state.finish()
    #             return await update.message.answer("Hodim  topilmadi", reply_markup=markup)
    #
    #         slots = await get_available_slots(staff, update.message.from_user.id)
    #         await state.update_data(telegram_id=staff['telegram_id'])
    #         # await state.update_data(barber=barber)
    #         await state.update_data(staff_id=staff_id)
    #         await state.update_data(telegram_id=staff['telegram_id'])
    #         if not slots:
    #             await update.message.delete()
    #             await state.finish()
    #             return await update.message.answer("Bo‘sh slot yo‘q ", reply_markup=markup)
    #
    #         kb = InlineKeyboardMarkup(row_width=3)
    #         for slot in slots:
    #             time_str = slot.astimezone(TZ).strftime("%H:%M")
    #             kb.insert(InlineKeyboardButton(
    #                 text=time_str,
    #                 callback_data=f"slot_{time_str}"
    #             ))
    #         await bot.send_message(chat_id=update.message.chat.id, text='Bekor qilish uchun pastdagi tugmani bosing',
    #                                reply_markup=cancelbutton())
    #         await update.message.delete()
    #         await update.message.answer("Bo‘sh vaqtni tanlang:", reply_markup=kb)
    #         await BookingInfoState.time.set()
    #     else:
    #         await update.message.answer('Asosiy menu', reply_markup=markup)
    #         await state.finish()
    #
    elif isinstance(update, types.Message):
        if update.text == '❌ Bekor qilish' or update.text == '/start' or update.text == '/help':
            await update.answer("❌ Bron qilish bekor qilindi.", reply_markup=markup)
            await state.finish()
            return
        else:
            await update.answer("Iltimos, buyruqni tugma orqali tanlang", reply_markup=cancelbutton())
            await BookingInfoState.staff.set()


# @dp.callback_query_handler(lambda c: c.data.startswith("slot_"))
# @dp.callback_query_handler(lambda c: c.data.startswith("slot_"),state=BookingInfoState.time)
# async def slot_handler(callback: types.CallbackQuery, state: FSMContext):
#
@dp.callback_query_handler(state=BookingInfoState.time)
@dp.message_handler(state=BookingInfoState.time)
async def slot_handler(update: Union[types.CallbackQuery, types.Message], state: FSMContext):
    # 🔹 Agar inline button bosilgan bo‘lsa
    markup = await main_menu_button()
    if isinstance(update, types.CallbackQuery):
        data = update.data
        if data.startswith("slot_"):

            _, day_type, slot_time = data.split("_")
            await state.update_data(day_type=day_type)
            await state.update_data(slot_time_str=slot_time)
            await update.message.delete()
            await update.message.answer(
                f"Telefon raqamingizni kiriting:", reply_markup=cancelbutton()
            )
            await BookingInfoState.phone.set()
            await update.answer()

        else:
            await update.message.answer('Asosiy menu', reply_markup=markup)
            await state.finish()
            # 🔹 Agar oddiy message kelgan bo‘lsa
    elif isinstance(update, types.Message):
        if update.text == '❌ Bekor qilish' or update.text == '/start' or update.text == '/help':
            await update.answer("❌ Bron qilish bekor qilindi.", reply_markup=markup)
            await state.finish()

        else:
            await update.answer("Iltimos, vaqtni tugma orqali tanlang")
            await BookingInfoState.time.set()
    # slot_str = callback.data.split("_")[1]
    # today = datetime.now(TZ).date()

    # await state.update_data(slot_time_str=slot_str)
    # await callback.message.answer("Ismingizni kiriting:")
    # await BookingInfoState.name.set()


# @dp.message_handler(state=BookingInfoState.name)
# async def booking_name(message: types.Message, state: FSMContext):
#     markup = await main_menu_button()
#     if message.text == '❌ Bekor qilish' or message.text == '/start' or message.text == '/help':
#         await state.finish()
#         await message.answer("❌ Bron qilish bekor qilindi.", reply_markup=markup)
#     else:
#         await state.update_data(name=message.text)
#         await message.answer("Telefon raqamingizni kiriting (faqat raqam, minimal 7, maksimal 15):")
#         await BookingInfoState.phone.set()


# @dp.message_handler(state=BookingInfoState.phone)
# async def booking_phone(message: types.Message, state: FSMContext):
#     markup = await main_menu_button()
#     if message.text == '❌ Bekor qilish' or message.text == '/start' or message.text == '/help':
#         await state.finish()
#         await message.answer("❌ Bron qilish bekor qilindi.", reply_markup=markup)
#     else:
#         phone = message.text.strip().replace(" ", "").replace("-", "")
#         if not phone.isdigit() or not (7 <= len(phone) <= 15):
#             await message.answer("❌ Telefon raqam xato. Qayta kiriting (faqat raqam, 7-15 raqam):")
#             await BookingInfoState.phone.set()
#
#         await state.update_data(phone=phone)
#         await message.answer("Qo‘shimcha telefon raqamingizni kiriting (agar yo‘q bo‘lsa: 0):")
#         await BookingInfoState.extra_phone.set()


@dp.message_handler(state=BookingInfoState.phone)
async def booking_extra_phone(message: types.Message, state: FSMContext):
    markup = await main_menu_button()
    if message.text == '❌ Bekor qilish' or message.text == '/start' or message.text == '/help':
        await state.finish()
        await message.answer("❌ Bron qilish bekor qilindi.", reply_markup=markup)
    else:
        extra_phone = message.text.strip().replace(" ", "").replace("-", "")

        # if extra_phone != "0" and (not extra_phone.isdigit() or not (7 <= len(extra_phone) <= 15)):
        if not extra_phone.isdigit() or not (7 <= len(extra_phone) <= 15):
            await message.answer("❌ Telefon raqam xato. Qayta kiriting (faqat raqam, 7-15 raqam):")
            await BookingInfoState.phone.set()
        else:

            data = await state.get_data()

            slot_str = data["slot_time_str"]
            # name = data["name"]
            # phone = data["phone"]
            day_type = data["day_type"]  # today yoki tomorrow

            now = datetime.now(TZ)

            if day_type == "today":
                day = now.date()
            else:
                day = (now + timedelta(days=1)).date()

            hour, minute = map(int, slot_str.split(":"))

            slot_time = datetime(
                day.year,
                day.month,
                day.day,
                hour,
                minute,
                tzinfo=TZ
            )

            staff_id = data["staff_id"]
            company_id = data["company_id"]
            telegram_id = data["telegram_id"]
            latitude = data["latitude"]
            longitude = data["longitude"]

            if not data:
                await state.finish()
                return await message.answer(
                    "Avval barber link orqali kiring.",
                    reply_markup=markup
                )
            success = await create_booking(
                staff_id=staff_id,
                user_id=message.from_user.id,
                slot_time=slot_time,
                name=message.from_user.full_name,
                phone=extra_phone,
                extra_phone=message.from_user.username
            )
            staff = await get_staff_by_telegram_id(telegram_id)
            if success:
                try:
                    await bot.send_message(chat_id=telegram_id,
                                           text=f"""📢 Yangi bron!

👤 Mijoz: <b>{message.from_user.full_name}</b>   
👨‍🔧 Xizmat ko'rsatuvchi: {staff['name']}
⏰ Vaqt:  {slot_time.today().date()} <b>{slot_str}</b>
📞 Telefon: {extra_phone}
☎️ telegram: @{message.from_user.username}
""")
                except:
                    pass

                await message.answer(
                    f"""✅ Siz muvaffaqiyatli yozildingiz!

👨‍🔧 Xizmat ko'rsatuvchi:  <b>{staff['name']}</b>
⏰ Vaqt: {slot_time.today().date()} <b>{slot_str}</b>

Iltimos, belgilangan vaqtda keling.
Rahmat! 🙌

❗️Eslatma! ⏰ Yozilgan vaqtingizdan 20 minut oldin sizga tasdiqlash uchun eslatma yuboriladi. Agar 10 daqiqa ichida tasdiqlmaangiz bron avtomatik bekor qilinadi.

Xizmat ko\'rsatuvchi joylashgan manzil 👇👇👇""",
                    reply_markup=markup)
                await message.answer_location(latitude=latitude, longitude=longitude)

            else:
                await message.answer("Bu Xizmat ko\'rsatuvchiga 2 tadan ortiq vaqt band qila olmaysiz",
                                     reply_markup=markup)
            await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith(("confirm_", "cancel_")))
async def confirm_or_cancel(callback: types.CallbackQuery):
    booking_id = int(callback.data.split("_")[1])
    action = callback.data.split("_")[0]

    async with db.pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT user_id, staff_id, slot_time, status
            FROM bookings
            WHERE id=$1
        """, booking_id)

        if not row or row["status"] != "pending":
            return await callback.answer("Bu buyurtma faol emas", show_alert=True)

        new_status = 'confirmed' if action == 'confirm' else 'cancelled'
        await conn.execute("""
            UPDATE bookings
            SET status=$1
            WHERE id=$2
        """, new_status, booking_id)

        barber_tg = await conn.fetchval("SELECT telegram_id FROM staff WHERE id=$1", row["staff_id"])
        text_barber = f"🟢 Mijoz keladi: {row['slot_time'].astimezone(TZ).strftime('%H:%M')}" if action == 'confirm' else f"🔴 Mijoz kelmaydi: {row['slot_time'].astimezone(TZ).strftime('%H:%M')}"

    await callback.message.edit_text("✅ Tasdiqlandi" if action == 'confirm' else "❌ Bekor qilindi")
    await callback.answer()
    try:
        await bot.send_message(barber_tg, text_barber)
    except:
        pass


@dp.callback_query_handler(lambda c: c.data.startswith("user_cancel_"))
async def user_cancel(callback: types.CallbackQuery):
    booking_id = int(callback.data.split("_")[2])
    markup = await main_menu_button()
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT b.user_id, b.staff_id, b.slot_time, b.status, br.telegram_id
            FROM bookings b
            JOIN staff br ON br.id = b.staff_id
            WHERE b.id=$1 AND b.user_id=$2
        """, booking_id, callback.from_user.id)

        if not row:
            return await callback.answer("Topilmadi", show_alert=True)

        if row["status"] != "pending":
            return await callback.answer("Bekor qilib bo‘lmaydi", show_alert=True)

        await conn.execute("""
            UPDATE bookings
            SET status='cancelled'
            WHERE id=$1
        """, booking_id)

    # ⏰ Local vaqtga o‘tkazamiz
    slot_time = row["slot_time"].astimezone(TZ)
    time_str = slot_time.strftime("%H:%M")

    # ✅ Userga javob
    await callback.message.edit_text("❌ Buyurtma bekor qilindi", reply_markup=markup)
    await callback.answer()

    # 🔔 Barberga xabar
    try:
        await bot.send_message(
            row["telegram_id"],
            f"🔴 Mijoz {slot_time} dagi yozilishni bekor qildi."
        )
    except:
        pass


@dp.message_handler(text="🔎 Qidirish")
async def search_barber_start(message: Message):
    await message.answer("🔎 Xodim nomini yozing:", reply_markup=cancelbutton())
    await SearchBarber.waiting_for_name.set()


@dp.message_handler(state=SearchBarber.waiting_for_name)
async def search_barber_process(message: Message, state: FSMContext):
    main_markup = await main_menu_button()
    if message.text == '❌ Bekor qilish' or message.text == '/start' or message.text == '/help':
        await message.answer('❌ Qidiruv bekor qilindi', reply_markup=main_markup)
        await state.finish()
    else:
        query = message.text.strip()
        async with db.pool.acquire() as conn:
            staffs = await conn.fetch("""
                SELECT id, name, company_id
                FROM staff
                WHERE active = TRUE
                AND name ILIKE '%' || $1 || '%'
                ORDER BY name
                LIMIT 10
            """, query)
            companies = await conn.fetch(
                """
                SELECT id, name
                FROM companies
                WHERE active = TRUE
                AND name ILIKE '%' || $1 || '%'
                ORDER BY name
                LIMIT 10
                """, query
            )
        if not staffs and not companies:
            await message.answer("""❌ Bunday ma'llumot topilmadi.\nSiz izlagan xodim topilmasa, "🔎 Qidirish" tugmasini bosing""", reply_markup=main_markup)
            await state.finish()
        else:
            kb = InlineKeyboardMarkup(row_width=1)
            if staffs:
                for staff in staffs:
                    kb.add(
                        InlineKeyboardButton(
                            text=f"✂️ {staff['name']}",
                            callback_data=f"choose_staff_{staff['company_id']}_{staff['id']}_{staff['name']}"
                        )
                    )
            if companies:
                for company in companies:
                    kb.add(
                        InlineKeyboardButton(
                            text=f"✂️ {company['name']}",
                            callback_data=f"choose_company_{company['id']}"
                        )
                    )
            await message.answer("Topilgan xodimlar 👇", reply_markup=kb)
            await message.answer('Xodimni tanlang', reply_markup=main_markup)
            await state.finish()
