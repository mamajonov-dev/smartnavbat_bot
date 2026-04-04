from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import db
from functions.functions import get_available_slots
def confirm_button():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(text='✅ Ha', callback_data='tasdiqlash_yes'),
        InlineKeyboardButton(text='❌ Yo\'q', callback_data='tasdiqlash_no')
    )
    return markup

async def services_inline_button():
    async with db.pool.acquire() as conn:
        services = await conn.fetch("""
            SELECT id, name, has_business FROM services
        """)

    markup = InlineKeyboardMarkup()
    for service in services:
        markup.add(
            InlineKeyboardButton(f'{service[1]}', callback_data=f'service_{service[0]}_{service[2]}')
        )
    return markup

async def companies_inline_button(service_id, district_id):
    async with db.pool.acquire() as conn:
        companies = await conn.fetch("""
            SELECT id, name  FROM companies WHERE service_id=$1 AND district_id=$2
        """, service_id, district_id)
    markup = InlineKeyboardMarkup()
    for company in companies:
        markup.add(
            InlineKeyboardButton(f'{company[1]}', callback_data=f'choose_company_{company[0]}')
        )
    markup.add(
        InlineKeyboardButton(f'⬅ Asosiy menu', callback_data=f'main_menu')
    )

    return markup

async def staff_inline_button(district_id=None, company_id=None, service_id=None):
    if company_id:
        async with db.pool.acquire() as conn:
            staffs = await conn.fetch("""
                SELECT company_id, id, name  FROM staff WHERE company_id=$1
            """, company_id)
    else:
        async with db.pool.acquire() as conn:
            staffs = await conn.fetch("""
                SELECT company_id, id, name   FROM staff WHERE service_id=$1 AND district_id=$2
            """, service_id, district_id)
    markup = InlineKeyboardMarkup()
    for staff in staffs:
        markup.add(
            InlineKeyboardButton(f'{staff[2]}', callback_data=f'choose_staff_{staff[0]}_{staff[1]}_{staff[2]}')
        )
    markup.add(
        InlineKeyboardButton(f'⬅ Asosiy menu', callback_data=f'main_menu')
    )
    return markup

from db import TZ
async def offline_slots_keyboard(staff, user_id, day_type):
    slots = await get_available_slots(staff, user_id, day_type)
    kb = InlineKeyboardMarkup(row_width=3)
    for slot in slots:
        time_str = slot.astimezone(TZ).strftime("%H:%M")
        kb.insert(
            InlineKeyboardButton(
                text=time_str,
                callback_data=f"offline_slot_{time_str}"
            )
        )
    return kb


def edit_company_button():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(text='Name', callback_data='name'),
        InlineKeyboardButton(text='Location', callback_data='location'),
        InlineKeyboardButton(text='Telegram id', callback_data='telegram_id'),
        InlineKeyboardButton(text='Telefon', callback_data='phone'),
        InlineKeyboardButton(text='Viloyat', callback_data='region'),

    )
    return markup


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def regions_keyboard(regions):
    kb = InlineKeyboardMarkup(row_width=2)
    for region in regions:
        kb.insert(
            InlineKeyboardButton(
                text=region["name_uz"],
                callback_data=f"region:{region['id']}"
            )
        )

    return kb

def districts_keyboard(districts):
    kb = InlineKeyboardMarkup(row_width=2)
    for district in districts:
        kb.insert(
            InlineKeyboardButton(
                text=district["name_uz"],
                callback_data=f"district:{district['id']}"
            )
        )
    kb.add(InlineKeyboardButton(text="🔙 Orqaga", callback_data="district:back_to_regions"))
    return kb

def companies_keyboard(companies):
    kb = InlineKeyboardMarkup(row_width=1)
    for company in companies:
        kb.add(
            InlineKeyboardButton(
                text=company["name"],
                callback_data=f"company:{company['id']}"
            )
        )
    kb.add(InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_districts"))
    return kb