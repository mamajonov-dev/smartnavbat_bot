from aiogram import executor
import asyncio
from loader import dp,bot
import middlewares, filters, handlers
from utils.notify_admins import on_startup_notify
from utils.set_bot_commands import set_default_commands, booking_manager_loop, subscription_reminder_loop_company,subscription_reminder_loop_staff
import db


async def on_startup(dispatcher):
    await db.connect_db()
    await db.init_db()
    # Устанавливаем дефолтные команды
    await set_default_commands(dispatcher)

    await on_startup_notify(dispatcher)
    asyncio.create_task(booking_manager_loop())
    asyncio.create_task(subscription_reminder_loop_staff(bot))
    asyncio.create_task(subscription_reminder_loop_company(bot))

    print("Bot ishga tushdi 🚀")
async def on_shutdown(dispatcher):
    await db.close_db()
    print("Bot to'xtadi")

if __name__ == "__main__":
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown
    )


