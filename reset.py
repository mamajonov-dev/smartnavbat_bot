# reset_bot_storage.py
import asyncio
from loader import dp
from aiogram.contrib.fsm_storage.memory import MemoryStorage

async def reset_bot_storage():
    # ⚡ Hozirgi storage-ni yopish va tozalash
    await dp.storage.close()
    await dp.storage.wait_closed()
    print("Oldingi storage yopildi va tozalandi ✅")

    # ⚡ Yangi bo'sh storage yaratish
    dp.storage = MemoryStorage()
    print("Yangi bo'sh MemoryStorage o'rnatildi ✅")

if __name__ == "__main__":
    asyncio.run(reset_bot_storage())
    print("Botning barcha foydalanuvchi state va data-lari tozalandi 🎉")