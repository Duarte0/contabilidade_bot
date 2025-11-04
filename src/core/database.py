import os
from typing import List, Optional, Tuple
from datetime import datetime
from models.models import Cliente, ClienteStatus, ContaConfig, ContaFixa, MessageTemplate

class DatabaseManager:
    def __init__(self, use_postgres=True):
        self.use_postgres = use_postgres
        
        if use_postgres:
            from .config import POSTGRES_CONNECTION_STRING
            from .database_postgres import PostgreSQLManager
            self.db = PostgreSQLManager(POSTGRES_CONNECTION_STRING)
        else:
            from .config import DATABASE_PATH
            from .database_sqlite import SQLiteManager
            self.db = SQLiteManager(DATABASE_PATH)
    
    def get_connection(self):
        return self.db.get_connection()

    def init_database(self):
        return self.db.init_database()

    def inserir_cliente(self, nome: str, digisac_contact_id: str, telefone: str = None, email: str = None) -> int:
        return self.db.inserir_cliente(nome, digisac_contact_id, telefone, email)

    def get_cliente_by_contact_id(self, contact_id: str) -> Optional[Cliente]:
        return self.db.get_cliente_by_contact_id(contact_id)

    def get_all_clientes(self) -> List[Cliente]:
        return self.db.get_all_clientes()

    def inserir_conta_fixa(self, cliente_id: int, descricao: str, valor: float, dia_vencimento: int) -> int:
        return self.db.inserir_conta_fixa(cliente_id, descricao, valor, dia_vencimento)

    def get_contas_fixas_cliente(self, cliente_id: int) -> List[ContaFixa]:
        return self.db.get_contas_fixas_cliente(cliente_id)

    def get_conta_config(self, conta_id: int) -> Optional[ContaConfig]:
        return self.db.get_conta_config(conta_id)

    def update_proxima_cobranca(self, conta_id: int, proxima_data: datetime):
        return self.db.update_proxima_cobranca(conta_id, proxima_data)

    def update_conta_config(self, conta_id: int, frequencia: str = None, prox_data_cobranca: datetime = None, feriados_ajustar: bool = None):
        return self.db.update_conta_config(conta_id, frequencia, prox_data_cobranca, feriados_ajustar)

    def get_clientes_para_cobrar_hoje(self) -> List[Tuple]:
        return self.db.get_clientes_para_cobrar_hoje()

    def registrar_cobranca(self, cliente_id: int, conta_id: int, mensagem: str, status: str):
        return self.db.registrar_cobranca(cliente_id, conta_id, mensagem, status)

    def registrar_pagamento(self, cliente_id: int, valor: float, data_pagamento: str, mes_referencia: str = None):
        return self.db.registrar_pagamento(cliente_id, valor, data_pagamento, mes_referencia)

    def get_ultimo_pagamento_cliente(self, cliente_id: int) -> Optional[str]:
        return self.db.get_ultimo_pagamento_cliente(cliente_id)

    def get_cliente_status(self, cliente_id: int) -> Optional[ClienteStatus]:
        return self.db.get_cliente_status(cliente_id)

    def update_cliente_status(self, cliente_id: int, status: str):
        return self.db.update_cliente_status(cliente_id, status)

    def registrar_interacao(self, cliente_id: int, tipo_interacao: str, mensagem: str):
        return self.db.registrar_interacao(cliente_id, tipo_interacao, mensagem)

    def inserir_template(self, nome: str, template_text: str, variaveis: str = None) -> int:
        return self.db.inserir_template(nome, template_text, variaveis)

    def get_template_by_name(self, nome: str) -> Optional[MessageTemplate]:
        return self.db.get_template_by_name(nome)

    def get_all_templates(self) -> List[MessageTemplate]:
        return self.db.get_all_templates()

    def get_clientes_inadimplentes(self, dias_tolerancia: int = 30) -> List[Tuple]:
        return self.db.get_clientes_inadimplentes(dias_tolerancia)
        
    def get_cliente_by_id(self, cliente_id: int) -> Optional[Cliente]:
        return self.db.get_cliente_by_id(cliente_id)