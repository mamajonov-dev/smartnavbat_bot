from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandHelp
from data.config import MANAGER_IDS
from loader import dp
from functions.functions import get_staff_by_telegram_id


@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    barber = await get_staff_by_telegram_id(message.chat.id)
    text = ''
    if barber:
        text = """
        📌 <b>Staff uchun qisqa yo‘riqnoma</b>

        1️⃣ <b>Staff menyuni ochish</b>
        /staff komandasini yozing → Staff menyu ochiladi.

        ━━━━━━━━━━━━━━

        2️⃣ <b>Navbatni ko‘rish</b>

        📅 <b>Bugungi navbatlar</b>  
        "Bugungi navbatlarni ko‘rish" tugmasini bosing → bugun yozilgan mijozlar chiqadi.

        📅 <b>Ertangi navbatlar</b>  
        "Ertangi navbatlarni ko‘rish" tugmasini bosing → ertangi yozilgan mijozlar chiqadi.

        ━━━━━━━━━━━━━━

        3️⃣ <b>Offline mijoz qo‘shish</b>

        ➕ "Offline mijoz qo‘shish" tugmasini bosing  
        → bo‘sh vaqtni tanlang  
        → slot band bo‘ladi.

        ━━━━━━━━━━━━━━

        4️⃣ <b>Navbatni bekor qilish</b>

        Kerakli mijozni tanlang  
        → ❌ "Bekor qilish" tugmasini bosing  
        → navbat bekor qilinadi.

        ━━━━━━━━━━━━━━

        5️⃣ <b>Ish vaqtini o‘zgartirish</b>

        ⚙️ "Ish vaqti" tugmasini bosing  
        → ish boshlanish va tugash vaqtini kiriting.

        ━━━━━━━━━━━━━━

        6️⃣ <b>Bugun ishlamaslik</b>

        Ish tugash vaqtini hozirgi vaqtgacha o‘zgartiring  
        → bugungi navbat yopiladi.

        ━━━━━━━━━━━━━━

        7️⃣ <b>Ertaga ishlamaslik</b>

        "Ertaga ochiq (o‘zgartirish)" tugmasini bosing  
        → ertangi navbat yopiladi.

        ━━━━━━━━━━━━━━

        🔗 <b>Referal link</b>  
        Mijozlarni yozilish uchun referal link orqali yuborishingiz mumkin.

        ━━━━━━━━━━━━━━

        ⚠️ <b>Eslatma</b>

        • Bir vaqtga faqat bitta mijoz yoziladi  
        • Offline mijoz qo‘shilganda ma'lumot kiritish shart emas  
        • Xato bo‘lsa slotni bekor qilib qayta band qiling
        """
    else:

        text = """
            📖 <b>Foydalanuvchi qo‘llanmasi</b>

            Assalomu alaykum 👋  
            Bu bot orqali siz o‘zingizga qulay vaqtga yozilishingiz mumkin.

            ━━━━━━━━━━━━━━

            📌 <b>Qanday ishlaydi:</b>

            1️⃣ Service tanlang  
            2️⃣ Hodimni tanlang  
            3️⃣ 🕒 Vaqtni tanlang  
            4️⃣ ✅ Bronni tasdiqlang

            ━━━━━━━━━━━━━━

            📅 Tanlangan vaqt siz uchun band qilinadi.

            ⏰ Yozilgan vaqtingizdan  
            10 minut oldin sizga eslatma yuboriladi.

            ❗ Agar kela olmasangiz, oldindan bekor qiling.
            """
    if message.chat.id in MANAGER_IDS:
        text = """
        🤖 <b>BOT YO‘RIQNOMASI</b>

        📅 <b>Bugungi yozilish</b>  
        Mijozlar slot tanlab yozilishadi.

        ━━━━━━━━━━━━━━

        ⚙️ <b>Admin buyruqlari</b>

        👨‍💼 /staff  
        Barber panel

        ➕ /add_service  
        Yangi service qo‘shish

        ➕ /add_staff  
        Yangi hodim qo‘shish
        
        ➕ /add_region
        Yangi viloyat qo‘shish
        
        ➕ /add_district  
        Yangi tuman qo‘shish
        
        🏢 /add_company  
        Yangi tashkilot qo‘shish

        💳 /add_subscription  
        Obunani uzaytirish (kun kiritiladi)

        📋 /view_staff  
        Hodimlar ro‘yxati

        🏢 /view_company  
        Tashkilotlar ro‘yxati

        ✏️ /edit_staff  
        Hodim ma'lumotlarini o‘zgartirish

        ✏️ /edit_company  
        Tashkilot ma'lumotlarini o‘zgartirish
        
        /bookings 20
        Bookinlarni ko'rish
        
        /users 
        Userlarni ko'rish
        
        ━━━━━━━━━━━━━━

        📌 <b>Kerakli ma'lumotlar</b>

        👤 Ism: Umid Barber  
        📱 Telegram ID: 2244567  
        📍 Lokatsiya: Telegram orqali yuboriladi  
        🕒 Ish vaqti: 06:00 – 18:00  
        📞 Telefon: +998901234567  
        🔗 Username: @username

        ━━━━━━━━━━━━━━

        ⚠️ <b>Qoidalar</b>

        • Bir mijoz kuniga maksimal 2 marta yozilishi mumkin  
        • Mijozga 10 minut oldin eslatma yuboriladi
        """

    await message.answer(text)
