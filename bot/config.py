import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_USER = os.getenv('DB_USER')
TOKEN = os.getenv('TOKEN')
ADMIN = os.getenv('ADMIN')
MANAGER = os.getenv('MANAGER')
CLICK = os.getenv('CLICK')
