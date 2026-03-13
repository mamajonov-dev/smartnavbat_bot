from aiogram.types import (KeyboardButton,
                           ReplyKeyboardMarkup,
                           InlineKeyboardButton,
                           InlineKeyboardMarkup)


async def main_menu_button():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("📝 Navbatga yozilish"),
        KeyboardButton("🔎 Qidirish")
    )
    kb.add(
        KeyboardButton("📋 Buyurtmalarim")
    )
    return kb


def cancelbutton():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("❌ Bekor qilish")
    return kb


def main_menu_inline(staff_id):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("📅 Bugun yozilish", callback_data=f"today_booking_{staff_id}"),
        InlineKeyboardButton("📅 Ertaga yozilish", callback_data=f"tomorrow_booking_{staff_id}")
    )
    kb.add(
        InlineKeyboardButton(f'🏠 Asosiy menu', callback_data=f'main_menu')
    )
    return kb


def location_button():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("✂️ Lokatsiya jo'natish", request_location=True))
    # kb.add("📅 Bugun yozilish")
    kb.add("Bekor qilish")
    return kb


def search_barber_button():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🔎 Qidirish"))
    kb.add("Asosiy menu")
    return kb


def staff_menu_button():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("📅 Bugungi navbatlarni ko\'rish"),
        KeyboardButton("📅 Ertangi navbatlarni ko\'rish")
    )
    kb.add(
        KeyboardButton(text="➕ Offline mijoz qo‘shish"),
        KeyboardButton("🔗 Referal link yaratish")
    )
    return kb

# def booking_day_reply_keyboard():
#     kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, one_time_keyboard=True)
#     kb.add(
#         KeyboardButton("📅 Bugungi navbatlarni ko\'rish"),
#         KeyboardButton("📅 Ertangi navbatlarni ko\'rish")
#     )
#     return kb
