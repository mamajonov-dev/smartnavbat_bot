from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandHelp
from data.config import MANAGER_IDS
from loader import dp
from functions.functions import get_staff_by_telegram_id



@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    barber = await get_staff_by_telegram_id(message.chat.id)
#     if barber:
#         text = """📖 Barber qo‘llanmasi
#
# Assalomu alaykum ✂️
# Siz barber sifatida botdan foydalanishingiz mumkin.
#
# 📌 Imkoniyatlar:
#
# 📅 Band qilinuvlar
# — Sizga yozilgan mijozlarni ko‘rasiz
# — Yoziluvni tasdiqlash yoki bekor qilish mumkin
#
# ⏰ Eslatma tizimi:
# — Mijozga avtomatik reminder yuboriladi
# — Kelmagan mijozlar no-show sifatida belgilanadi
#
# 🚫 No-show tizimi:
# — 3 marta kelmagan mijoz avtomatik blacklist qilinadi
#
# 📊 Statistika:
# — Qancha yoziluv
# — Qancha bekor qilingan
# — No-show soni
#
# 🔒 Faollik:
# Agar “active = FALSE” bo‘lsa, siz mijozlarga ko‘rinmaysiz."""

    if message.chat.id in MANAGER_IDS:
        text = """
    🤖 BOT YO‘RIQNOMASI
    
    /start username → Barber sahifasi
    📅 Bugun yozilish → slot tanlash
    
    /barber → Barber panel
    /add_barber → Menejer uchun
    
    • 1 kunda 2 ta yozilish
    • 10 minut oldin eslatma
    """
    else:
        text = """
            📖 Foydalanuvchi qo‘llanmasi

Assalomu alaykum 👋
Bu bot orqali siz o‘zingizga qulay barberga yozilishingiz mumkin.

📌 Qanday ishlaydi:

1️⃣ 📍 Lokatsiya yuboring — sizga yaqin barberlar chiqadi
2️⃣ ✂️ Barber tanlang
3️⃣ 🕒 Vaqtni tanlang
4️⃣ ✅ Bronni tasdiqlang

⏰ Eslatma:
• Yozilgan vaqtdan 20 minut oldin sizga eslatma keladi
• Agar javob bermasangiz, bron bekor qilinadi
• 3 marta kelmasangiz, akkauntingiz bloklanadi 🚫

📋 Buyurtmalar:
“📋 Buyurtmalarim” orqali aktiv va eski yoziluvlarni ko‘rishingiz mumkin.

❌ Bekor qilish:
Bronni vaqtigacha bekor qilishingiz mumkin.

🔎 Qidirish:
“🔎 Barber qidirish” orqali ism bo‘yicha qidirishingiz mumkin.
            """
    await message.answer(text)
