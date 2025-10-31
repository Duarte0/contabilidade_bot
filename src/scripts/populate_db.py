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
    {"nome": "Elaine Cristina", "digisac_contact_id": "d976bbc9-2416-4c6e-8a6e-382eee12cc0d", "teste": False},
    {"nome": "Tylara Pinheiro", "digisac_contact_id": "688b8085-0ef0-41e5-af52-f0c4a838efb0", "teste": False},
    {"nome": "Ângela", "digisac_contact_id": "c18a87ce-d800-4809-8095-b2888049c24e", "teste": False},
    {"nome": "Financeiro", "digisac_contact_id": "6285f854-7607-427a-88ec-e43f146dac2c", "teste": False},
    {"nome": "Ricardo", "digisac_contact_id": "8f38c6b1-cec9-4c8b-8d34-5236ef8e6e31", "teste": False},
    {"nome": "Moema", "digisac_contact_id": "47489198-23ea-454d-a635-2bfc33ccf351", "teste": False},
    {"nome": "Posto De Molas Do Anderson Financeiro", "digisac_contact_id": "b27e8832-b376-420b-a818-f20c58a83715", "teste": False},
    {"nome": "Diego De Oliveira", "digisac_contact_id": "ab10162c-fd12-4697-8b53-954d40a1712d", "teste": False},
    {"nome": "Laura Rezende", "digisac_contact_id": "95c2c9c2-d07a-4184-9c3a-486067858bde", "teste": False},
    {"nome": "Fabrício", "digisac_contact_id": "db7f4339-d08e-4ed7-b54a-4684b392a9e6", "teste": False},
    {"nome": "Kelly Contadora", "digisac_contact_id": "624c03dc-05ef-4271-8e6e-fcfd30c0bab3", "teste": False},
    {"nome": "Ana Paula Reis", "digisac_contact_id": "0810242a-abcb-4456-9520-3b98acf327df", "teste": False},
    {"nome": "Renato Caldeira", "digisac_contact_id": "4b89ee8f-152c-46c1-87b7-45de9e4e3698", "teste": False},
    {"nome": "Margarida", "digisac_contact_id": "b286feb7-a692-425d-b61a-fb139c5ab638", "teste": False},
    {"nome": "Karina Dias", "digisac_contact_id": "df76d6ec-0cdd-4ea8-a247-71b10e82b404", "teste": False},
    {"nome": "Luciana", "digisac_contact_id": "abed3bad-dcfa-48d3-88dd-3194384041f2", "teste": False},
    {"nome": "Fatima Rehem", "digisac_contact_id": "f872aeab-5ab3-4e36-beed-0b2907e9a691", "teste": False},
    {"nome": "Regina Rodrigues", "digisac_contact_id": "e099c4d0-966f-4518-8508-a2416a031058", "teste": False},
    {"nome": "Rômulo Silva", "digisac_contact_id": "066c617e-80af-46fd-bec0-6080ed2c04bb", "teste": False}
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