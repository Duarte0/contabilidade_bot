import sys
import os
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)

from core.database import DatabaseManager
from core.config import DATABASE_PATH

def popular_banco_exemplo():
    db = DatabaseManager(DATABASE_PATH)
    
    clientes_unicos = [
    {"nome": "Guilherme Duarte", "digisac_contact_id": "824abf74-979a-478b-8947-6c7f40a2087c", "teste": True},
    ]
    
    for cliente in clientes_unicos:
        cliente_id = db.inserir_cliente(
            nome=cliente["nome"],
            digisac_contact_id=cliente["digisac_contact_id"]
        )
        
        if cliente_id:
            if cliente["teste"]:
                dia_vencimento = datetime.now().day
            else:
                dia_vencimento = 10
            
            db.inserir_conta_fixa(
                cliente_id=cliente_id,
                descricao="Contabilidade Mensal",
                valor=500.00,
                dia_vencimento=dia_vencimento
            )
    
    print("Clientes inseridos. Apenas Guilherme Duarte ativo para teste.")

if __name__ == "__main__":
    popular_banco_exemplo()