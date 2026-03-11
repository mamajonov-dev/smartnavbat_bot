# from environs import Env
#
# # Теперь используем вместо библиотеки python-dotenv библиотеку environs
# env = Env()
# env.read_env()
import os

from dotenv import load_dotenv
load_dotenv()
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Забираем значение типа str
ADMINS = [os.getenv("ADMINS")]  # Тут у нас будет список из админов
IP = os.getenv("ip")  # Тоже str, но для айпи адреса хоста
MANAGER_IDS = [int(os.getenv('MANAGER_IDS'))]

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")