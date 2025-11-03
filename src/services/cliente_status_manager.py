from datetime import datetime

class ClienteStatusManager:
    def __init__(self, db):
        self.db = db

    def verificar_inadimplencia(self, cliente_id, dias_tolerancia=30):
        ultimo_pagamento = self.db.get_historico_pagamentos_cliente(cliente_id)
        
        if not ultimo_pagamento:
            return False
            
        ultima_data = datetime.strptime(ultimo_pagamento, '%Y-%m-%d').date()
        dias_sem_pagamento = (datetime.now().date() - ultima_data).days
        
        return dias_sem_pagamento > dias_tolerancia

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