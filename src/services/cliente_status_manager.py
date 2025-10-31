from datetime import datetime, timedelta
from core.database import DatabaseManager

class ClienteStatusManager:
    def __init__(self, db):
        self.db = db

    def verificar_inadimplencia(self, cliente_id):
        """Verifica se cliente está inadimplente baseado no último pagamento"""
        status = self.db.get_cliente_status(cliente_id)
        
        if not status or not status.last_payment_date:
            return True 
            
        ultimo_pagamento = datetime.strptime(status.last_payment_date, '%Y-%m-%d')
        dias_sem_pagamento = (datetime.now() - ultimo_pagamento).days
        
        return dias_sem_pagamento > status.dias_tolerancia

    def atualizar_status_automatico(self):
        """Atualiza status de todos os clientes baseado em pagamentos"""
        clientes = self.db.get_all_clientes()
        
        for cliente in clientes:
            if self.verificar_inadimplencia(cliente.id):
                self.db.update_cliente_status(cliente.id, 'inadimplente')
            else:
                self.db.update_cliente_status(cliente.id, 'ativo')

    def get_template_por_status(self, cliente_id):
        """Seleciona template apropriado baseado no status"""
        if self.verificar_inadimplencia(cliente_id):
            return 'cobranca_inadimplente'
        else:
            return 'cobranca_padrao'