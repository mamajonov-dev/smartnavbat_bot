from aiogram import types
from aiogram.types import (
    Message, CallbackQuery,
    KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.dispatcher import FSMContext
from datetime import datetime, time, timedelta
from keyboards.default.asosiymenu import main_menu_button, cancelbutton, location_button
from keyboards.inline.inline_keyboards import (confirm_button, services_inline_button,
                                               companies_inline_button, staff_inline_button)

from loader import bot, dp
from functions.admin_functions import add_service_function
from functions.functions import get_staff_by__id, get_comapny_by__id
from functions.statistics import *
from states.states import (AddServiceState, AddCompanyState, AddClientState, SubscriptionState)
from data.config import MANAGER_IDS
import db


@dp.message_handler(commands=['add_service'])
async def add_service_start(message: types.Message):
    if message.from_user.id not in MANAGER_IDS:
        return await message.answer("Siz menejer emassiz.")
    await message.answer("Servis nomini kiriting:", reply_markup=cancelbutton())
    await AddServiceState.name.set()


@dp.message_handler(state=AddServiceState.name)
async def add_service_name(message: types.Message, state: FSMContext):
    if message.text == '❌ Bekor qilish' or message.text == '/start':
        markup = await main_menu_button()
        await message.answer('❌ Bekor qilindi', reply_markup=markup)
        await state.finish()
    else:
        await state.update_data(name=message.text)
        await message.answer("Biznes tarqmoq bormi", reply_markup=confirm_button())
        await AddServiceState.company.set()


@dp.callback_query_handler(state=AddServiceState.company)
async def add_company_service(callback: CallbackQuery, state: FSMContext):
    _, confirm = callback.data.split('_')
    data = await state.get_data()
    name = data['name']
    if confirm == 'yes':
        business = True
    else:
        business = False
    await add_service_function(name, business)
    await state.finish()
    await callback.answer('✅ Service qo\'shildi', show_alert=True)
    markup = await main_menu_button()
    await bot.send_message(chat_id=callback.message.chat.id, text='Asosiy menu', reply_markup=markup)


@dp.message_handler(commands=['add_company'])
async def add_company_start(message: types.Message):
    if message.from_user.id not in MANAGER_IDS:
        return await message.answer("Siz menejer emassiz.")
    await message.answer("Kompaniya telegram id kiriting:", reply_markup=cancelbutton())
    await AddCompanyState.telegram_id.set()


@dp.message_handler(state=AddCompanyState.telegram_id)
async def add_company_name(message: types.Message, state: FSMContext):
    markup = await main_menu_button()
    if message.text == '❌ Bekor qilish' or message.text == '/start':
        await message.answer('❌ Bekor qilindi', reply_markup=markup)
        await state.finish()
    else:
        try:
            await state.update_data(telegram_id=int(message.text))
            markup = await services_inline_button()
            await message.answer("Kompaniya nomini kiriting", reply_markup=markup)
            await AddCompanyState.name.set()
        except:
            await message.answer('Xatolik', reply_markup=markup)
            await state.finish()


@dp.message_handler(state=AddCompanyState.name)
async def add_company_name(message: types.Message, state: FSMContext):
    if message.text == '❌ Bekor qilish' or message.text == '/start':
        markup = await main_menu_button()
        await message.answer('❌ Bekor qilindi', reply_markup=markup)
        await state.finish()
    else:
        await state.update_data(name=message.text)
        markup = await services_inline_button()
        await message.answer("Servisni tanlang", reply_markup=markup)
        await AddCompanyState.service.set()


@dp.callback_query_handler(state=AddCompanyState.service)
async def select_company_service(callback: types.CallbackQuery, state: FSMContext):
    service_id = callback.data.split('_')[1]
    await state.update_data(service_id=service_id)
    await bot.send_message(chat_id=callback.message.chat.id,
                           text="Ish vaqtini yozing. Masalan: 09:00-18-00", reply_markup=cancelbutton())
    await AddCompanyState.work_time.set()


@dp.message_handler(state=AddCompanyState.work_time)
async def add_company_time(message: types.Message, state: FSMContext):
    if message.text == '❌ Bekor qilish' or message.text == '/start':
        markup = await main_menu_button()
        await message.answer('❌ Bekor qilindi', reply_markup=markup)
        await state.finish()
    else:
        start, end = message.text.split('-')
        try:
            s_hour, s_minute = map(int, start.strip().split(":"))
            e_hour, e_minute = map(int, end.strip().split(":"))
            if not (0 <= s_hour < 24 and 0 <= s_minute < 60) or not (0 <= e_hour < 24 and 0 <= e_minute < 60):
                raise ValueError
            start_time = time(s_hour, s_minute)
            end_time = time(e_hour, e_minute)
        except ValueError:
            await message.answer(
                "❌ Vaqt noto‘g‘ri formatda. Iltimos HH:MM-HH:MM ko‘rinishida kiriting (masalan 09:00).",
                reply_markup=cancelbutton())
            return
        await state.update_data(start_work=start_time)
        await state.update_data(end_work=end_time)
        await message.answer('Lokatsiyangizni jo\'nating', reply_markup=location_button())
        await AddCompanyState.location.set()


@dp.message_handler(state=AddCompanyState.location, content_types='location')
@dp.message_handler(state=AddCompanyState.location)
async def add_compamy_location(message: Message, state: FSMContext):
    if message.text == '❌ Bekor qilish' or message.text == '/start':
        markup = await main_menu_button()
        await message.answer('❌ Bekor qilindi', reply_markup=markup)
        await state.finish()
    else:
        if not message.location:
            return await message.answer('Lokatsiya jo\'nating', reply_markup=location_button())
        else:
            latitude = message.location.latitude
            longitude = message.location.longitude
            await state.update_data(latitude=latitude)
            await state.update_data(longitude=longitude)
            await AddCompanyState.confirm.set()
            await message.answer('Tasdiqlaysizmi?', reply_markup=confirm_button())


@dp.callback_query_handler(state=AddCompanyState.confirm)
async def confirm_add_company(callback: CallbackQuery, state: FSMContext):
    confirm = callback.data.split('_')[1]
    markup = await main_menu_button()
    if confirm == 'no':
        await bot.send_message('Bekor qilindi', reply_markup=markup)
        await state.finish()
    else:
        data = await state.get_data()
        name = data['name']
        service_id = int(data['service_id'])
        work_time_start = data['start_work']
        work_time_end = data['end_work']
        latitude = data['latitude']
        longitude = data['longitude']
        telegram_id = data['telegram_id']
        subscription_until = datetime.now(db.TZ) + timedelta(days=30)
        try:
            async with db.pool.acquire() as conn:
                await conn.execute("""
                            INSERT INTO companies(name, service_id, latitude, longitude, work_start, work_end, subscription_until,telegram_id)
                            VALUES ($1, $2,$3, $4,$5, $6,$7, $8)
                            """, name.lower(), service_id, latitude, longitude, work_time_start, work_time_end,
                                   subscription_until, telegram_id)
            await bot.send_message(chat_id=callback.message.chat.id, text='✅ Tashkilot qoshildi', reply_markup=markup)
        except:
            await bot.send_message(chat_id=callback.message.chat.id, text='Xatolik', reply_markup=markup)
    await state.finish()


# //////  ADD STAFF ////
@dp.message_handler(commands='add_staff')
async def add_staff(message: Message):
    await message.answer('Xizmat ko\'rsatuvchi ismi va kasbini kiriting', reply_markup=cancelbutton())
    await AddClientState.name.set()


@dp.message_handler(state=AddClientState.name)
async def add_name_client(message: Message, state: FSMContext):
    if message.text == '❌ Bekor qilish' or message.text == '/start':
        markup = await main_menu_button()
        await message.answer('❌ Bekor qilindi', reply_markup=markup)
        await state.finish()
    else:
        await state.update_data(name=message.text)
        markup = await services_inline_button()
        await message.answer('Servisni tanlang', reply_markup=markup)
        await AddClientState.service.set()


@dp.callback_query_handler(state=AddClientState.service)
async def add_service_client(callback: CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split('_')[1])
    await state.update_data(service_id=service_id)
    chatid = callback.message.chat.id
    async with db.pool.acquire() as conn:
        exists = await conn.fetchval("""
            SELECT has_business FROM services
            WHERE id=$1
        """, service_id)
    if exists == True:
        markup = await companies_inline_button(service_id)
        await bot.send_message(chat_id=chatid, text='Kompaniya tanglang', reply_markup=markup)
        await AddClientState.company.set()
    else:
        await bot.send_message(chat_id=chatid, text='Telegram id kiriting', reply_markup=cancelbutton())
        await state.update_data(company_id=None)
        await AddClientState.telegram_id.set()


@dp.message_handler(state=AddClientState.telegram_id)
async def add_telegramid_client(message: Message, state: FSMContext):
    markup = await main_menu_button()
    if message.text == '❌ Bekor qilish' or message.text == '/start':
        await message.answer('❌ Bekor qilindi', reply_markup=markup)
        await state.finish()
    else:
        if message.text.isdigit():
            await state.update_data(telegram_id=int(message.text))
        else:
            await state.finish()
            return await message.answer('Xatolik', reply_markup=markup)
        await message.answer('Ish vaqtini yozing: Masalan: 09:00-18:00', reply_markup=cancelbutton())
        await AddClientState.work_time.set()


@dp.message_handler(state=AddClientState.work_time)
async def add_client_time(message: types.Message, state: FSMContext):
    if message.text == '❌ Bekor qilish' or message.text == '/start':
        markup = await main_menu_button()
        await message.answer('❌ Bekor qilindi', reply_markup=markup)
        await state.finish()
    else:
        start, end = message.text.split('-')
        try:
            s_hour, s_minute = map(int, start.strip().split(":"))
            e_hour, e_minute = map(int, end.strip().split(":"))
            if not (0 <= s_hour < 24 and 0 <= s_minute < 60) or not (0 <= e_hour < 24 and 0 <= e_minute < 60):
                raise ValueError
            start_time = time(s_hour, s_minute)
            end_time = time(e_hour, e_minute)
        except ValueError:
            await message.answer(
                "❌ Vaqt noto‘g‘ri formatda. Iltimos HH:MM-HH:MM ko‘rinishida kiriting (masalan 09:00).",
                reply_markup=cancelbutton())
            return
        await state.update_data(work_start=start_time)
        await state.update_data(work_end=end_time)
        await message.answer('Lokatsiyangizni jo\'nating', reply_markup=location_button())
        await AddClientState.location.set()


@dp.message_handler(state=AddClientState.location, content_types='location')
@dp.message_handler(state=AddClientState.location)
async def add_client_location(message: Message, state: FSMContext):
    if message.text == '❌ Bekor qilish' or message.text == '/start':
        markup = await main_menu_button()
        await message.answer('❌ Bekor qilindi', reply_markup=markup)
        await state.finish()
    else:
        if not message.location:
            return await message.answer('Lokatsiya jo\'nating', reply_markup=location_button())
        else:
            latitude = message.location.latitude
            longitude = message.location.longitude
            await state.update_data(latitude=latitude)
            await state.update_data(longitude=longitude)
            await AddClientState.confirm.set()
            await message.answer('Tasdiqlaysizmi?', reply_markup=confirm_button())


@dp.callback_query_handler(state=AddClientState.company)
async def add_client_company(callback: CallbackQuery, state: FSMContext):
    company_id = int(callback.data.split('_')[-1])
    await state.update_data(company_id=company_id)
    chatid = callback.message.chat.id
    await bot.send_message(chat_id=chatid, text='Tasdiqlaysizmi?', reply_markup=confirm_button())
    await AddClientState.confirm.set()


@dp.callback_query_handler(state=AddClientState.confirm)
async def confirm_client(callback: CallbackQuery, state: FSMContext):
    confirm = callback.data.split('_')[1]
    markup = await main_menu_button()
    if confirm == 'no':
        await bot.send_message('Bekor qilindi', reply_markup=markup)
        await state.finish()
    else:
        data = await state.get_data()
        name = data['name']
        service_id = int(data['service_id'])
        work_time_start = None
        work_time_end = None
        latitude = None
        longitude = None
        telegram_id = None
        subscription_until = None
        if data.get("company_id"):
            company_id = data["company_id"]
            async with db.pool.acquire() as conn:
                company = await conn.fetchrow(
                    """SELECT * FROM companies WHERE id=$1""",
                    company_id
                )
            work_time_start = company['work_start']
            work_time_end = company['work_end']
            latitude = company['latitude']
            longitude = company['longitude']
            telegram_id = company['telegram_id']
            subscription_until = company['subscription_until']
        else:
            company_id = None
            work_time_start = data['work_start']
            work_time_end = data['work_end']
            latitude = data['latitude']
            longitude = data['longitude']
            telegram_id = data['telegram_id']
            subscription_until = datetime.now(db.TZ) + timedelta(days=30)
        async with db.pool.acquire() as conn:
            await conn.execute("""
                    INSERT INTO staff(service_id, company_id, name, latitude, longitude, work_start, work_end, subscription_until, telegram_id)
                        VALUES ($1, $2,$3, $4,$5, $6,$7, $8, $9)
                        """, service_id, company_id, name.lower(), latitude, longitude, work_time_start, work_time_end,
                               subscription_until, telegram_id)
        await state.finish()
        await bot.send_message(chat_id=callback.message.chat.id, text='Xizmat ko\'rsatuvchi joylandi',
                               reply_markup=markup)


@dp.message_handler(commands=['add_subscription'])
async def add_subscription(message: types.Message):
    markup = await services_inline_button()
    await message.answer('Service tanlang', reply_markup=markup)
    await SubscriptionState.service.set()


@dp.callback_query_handler(state=SubscriptionState.service)
async def add_subscription_service(callback: types.CallbackQuery):
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
    await SubscriptionState.staff.set()


@dp.callback_query_handler(state=SubscriptionState.staff)
async def add_subscription_staff(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(staff=callback.data)
    await bot.send_message(chat_id=callback.message.chat.id, text='Vaqtni kiriting', reply_markup=cancelbutton())
    await SubscriptionState.time.set()


@dp.message_handler(state=SubscriptionState.time)
async def add_subscription_day(message: Message, state: FSMContext):
    markup = await main_menu_button()
    if message.text == '❌ Bekor qilish' or message.text == '/start':

        await message.answer('❌ Bekor qilindi', reply_markup=markup)
        await state.finish()
    else:
        # {'staff': 'choose_company_1'}
        # {'staff': 'choose_staff_None_1_jack barber'}
        data = await state.get_data()
        staff = data['staff']
        print(staff)
        print(type(staff))
        user = None
        staff_id = None
        company_id = None
        if 'choose_staff' in staff:
            staff_id = int(staff.split('_')[3])
            user = await get_staff_by__id(staff_id)
        elif 'choose_company' in staff:
            company_id = int(staff.split('_')[2])
            user = await get_comapny_by__id(company_id)
        try:

            days = int(message.text)

            # user = db.get_user(user_id)
            print(user, 'user')
            if not user:
                await message.reply("Foydalanuvchi topilmadi.", reply_markup=markup)
                await state.finish()

            subscription_until = user['subscription_until']
            now = datetime.now(db.TZ)

            # agar obuna hali tugamagan bo'lsa
            if subscription_until and subscription_until > now:
                new_date = subscription_until + timedelta(days=days)
            else:
                new_date = now + timedelta(days=days)

            await db.update_subscription(new_date=new_date, company_id=company_id, staff_id=staff_id)

            await message.answer(
                f"✅ Obuna uzaytirildi\n\n"
                f"👤 User: {user['name']}\n"
                f"📅 Yangi tugash sanasi: {new_date}"
            )
            await state.finish()
        except Exception as e:
            await message.answer(f"Xatolik: {e}")
        await state.finish()
