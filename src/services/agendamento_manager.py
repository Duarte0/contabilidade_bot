from datetime import datetime, timedelta
from .feriados_manager import FeriadosManager

class AgendamentoManager:
    def __init__(self, db):
        self.db = db
        self.feriados_manager = FeriadosManager()
    
    def calcular_proxima_data_cobranca(self, conta_config):
        hoje = datetime.now()
        
        if conta_config.frequencia == 'semanal':
            proxima_data = hoje + timedelta(days=7)
        elif conta_config.frequencia == 'quinzenal':
            proxima_data = hoje + timedelta(days=15)
        elif conta_config.frequencia == 'mensal':
            proxima_data = hoje.replace(month=hoje.month + 1)
        elif conta_config.frequencia == 'bimestral':
            proxima_data = hoje.replace(month=hoje.month + 2)
        else:
            proxima_data = hoje.replace(day=conta_config.dia_vencimento)
        
        if conta_config.feriados_ajustar:
            proxima_data = self.feriados_manager.ajustar_data_util(proxima_data)
        
        return proxima_data
    
    def get_clientes_para_cobrar_hoje(self):
        hoje = datetime.now().date()
        clientes_para_cobrar = []
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.id, c.digisac_contact_id, c.nome, cf.descricao, cf.valor, cf.id
                FROM clientes c
                JOIN contas_fixas cf ON c.id = cf.cliente_id
                LEFT JOIN contas_config cc ON cf.id = cc.conta_id
                WHERE (cc.prox_data_cobranca = ? OR 
                      (cc.prox_data_cobranca IS NULL AND cf.dia_vencimento = ?))
                AND cf.ativo = 1
            ''', (hoje, hoje.day))
            
            clientes_para_cobrar = cursor.fetchall()
        
        return clientes_para_cobrar
    
    def atualizar_proxima_cobranca(self, conta_id):
        conta_config = self.db.get_conta_config(conta_id)
        if conta_config:
            proxima_data = self.calcular_proxima_data_cobranca(conta_config)
            self.db.update_proxima_cobranca(conta_id, proxima_data)