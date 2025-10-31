import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)

from core.database import DatabaseManager
from services.digisac_service import DigisacAPI
from utils.utils import formatar_mensagem_cobranca
from core.config import DATABASE_PATH

def main():
    db = DatabaseManager(DATABASE_PATH)
    digisac = DigisacAPI()
    
    clientes_para_cobrar = db.get_clientes_para_cobrar_hoje()
    
    print(f"Clientes para cobrar hoje: {len(clientes_para_cobrar)}")
    
    for cliente_id, contact_id, nome, descricao, valor, conta_id in clientes_para_cobrar:
        print(f"Enviando cobrança para: {nome}")
        
        mensagem = formatar_mensagem_cobranca(nome, descricao, valor)
        sucesso = digisac.enviar_mensagem(contact_id, mensagem)
        status = "enviado" if sucesso else "erro"
        
        db.registrar_cobranca(cliente_id, conta_id, mensagem, status)
        print(f"Status: {status}")

if __name__ == "__main__":
    main()