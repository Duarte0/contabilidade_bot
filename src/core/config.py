import os
from dotenv import load_dotenv

load_dotenv()

DIGISAC_TOKEN = os.getenv('DIGISAC_API_TOKEN')
DATABASE_PATH = 'contas.db'
API_BASE_URL = os.getenv('DIGISAC_API_URL')
WEBHOOK_SECRET = os.getenv('DIGISAC_WEBHOOK_SECRET')
WEBHOOK_URL = os.getenv('DIGISAC_WEBHOOK_URL')

POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'cobranca_db')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'senha123')

POSTGRES_CONNECTION_STRING = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"