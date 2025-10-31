import os
from dotenv import load_dotenv

load_dotenv()

DIGISAC_TOKEN = os.getenv('DIGISAC_API_TOKEN')
DATABASE_PATH = 'contas.db'
API_BASE_URL = 'https://inov.digisac.chat/api/v1'
WEBHOOK_SECRET = os.getenv('DIGISAC_WEBHOOK_SECRET', '')
WEBHOOK_URL = os.getenv('DIGISAC_WEBHOOK_URL', '')