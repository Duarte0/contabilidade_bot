import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)

from services.digisac_service import DigisacAPI
from core.config import WEBHOOK_URL

def setup_webhook_completo():
    digisac = DigisacAPI()
    
    print("Configurando webhook Digisac")
    print(f"URL base: {WEBHOOK_URL}")

    webhook_url = f"{WEBHOOK_URL}/webhook/digisac"
    
    payload = {
        "name": "INOV - Cobranças Automáticas",
        "url": webhook_url,
        "type": "general",
        "active": True,
        "events": ["message.received", "message.updated", "message.created"]
    }

    print(f"URL do webhook: {webhook_url}")
    print(f"Payload: {payload}")

    try:
        response = digisac._make_request('POST', '/me/webhooks', payload)
        if response and response.status_code in [200, 201]:
            webhook_data = response.json()
            print("Webhook criado")
            print(f"ID: {webhook_data.get('id')}")
        else:
            print(f"Falha: {response.status_code if response else 'Sem resposta'}")
            if response:
                print(f"Resposta: {response.text}")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    setup_webhook_completo()