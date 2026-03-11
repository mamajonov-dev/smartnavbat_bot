from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import db

def confirm_button():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(text='✅ Ha', callback_data='confirm_yes'),
        InlineKeyboardButton(text='❌ Yo\'q', callback_data='confirm_no')
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

async def companies_inline_button(service_id):
    async with db.pool.acquire() as conn:
        companies = await conn.fetch("""
            SELECT id, name  FROM companies WHERE service_id=$1
        """, service_id)
    markup = InlineKeyboardMarkup()
    for company in companies:
        markup.add(
            InlineKeyboardButton(f'{company[1]}', callback_data=f'choose_company_{company[0]}')
        )
    markup.add(
        InlineKeyboardButton(f'⬅ Asosiy menu', callback_data=f'main_menu')
    )

    return markup

async def staff_inline_button(company_id=None, service_id=None):
    if company_id:
        async with db.pool.acquire() as conn:
            staffs = await conn.fetch("""
                SELECT *  FROM staff WHERE company_id=$1
            """, company_id)
    else:
        async with db.pool.acquire() as conn:
            staffs = await conn.fetch("""
                SELECT *  FROM staff WHERE service_id=$1
            """, service_id)
    markup = InlineKeyboardMarkup()
    for staff in staffs:
        markup.add(
            InlineKeyboardButton(f'{staff[3]}', callback_data=f'choose_staff_{staff[2]}_{staff[0]}_{staff[3]}')
        )
    markup.add(
        InlineKeyboardButton(f'⬅ Asosiy menu', callback_data=f'main_menu')
    )
    return markup


