from calendar import monthrange
from datetime import datetime, timedelta
from .feriados_manager import FeriadosManager

class AgendamentoManager:
    def __init__(self, db):
        self.db = db
        self.feriados_manager = FeriadosManager()
    
    def calcular_proxima_data_cobranca(self, conta_config, data_referencia=None):
        if data_referencia is None:
            data_referencia = datetime.now()
        
        if conta_config.frequencia == 'semanal':
            proxima_data = data_referencia + timedelta(days=7)
        elif conta_config.frequencia == 'quinzenal':
            proxima_data = data_referencia + timedelta(days=15)
        elif conta_config.frequencia == 'mensal':
            if conta_config.prox_data_cobranca is None:
                try:
                    data_vencimento_mes_atual = data_referencia.replace(day=conta_config.dia_vencimento)
                    data_vencimento_date = data_vencimento_mes_atual.date()
                    data_referencia_date = data_referencia.date()

                    if data_vencimento_date >= data_referencia_date:
                        proxima_data = data_vencimento_mes_atual
                    else:
                        proxima_data = self._calcular_proximo_mes(data_referencia, conta_config.dia_vencimento)
                        
                except ValueError:
                    proxima_data = self._calcular_proximo_mes(data_referencia, conta_config.dia_vencimento)
            else:
                proxima_data = self._calcular_proximo_mes(data_referencia, conta_config.dia_vencimento)
        
        elif conta_config.frequencia == 'bimestral':
            if conta_config.prox_data_cobranca is None:
                try:
                    data_vencimento_mes_atual = data_referencia.replace(day=conta_config.dia_vencimento)
                    if data_vencimento_mes_atual.date() >= data_referencia.date():
                        proxima_data = data_vencimento_mes_atual
                    else:
                        proxima_data = self._calcular_proximo_mes_bimestral(data_referencia, conta_config.dia_vencimento)
                except ValueError:
                    proxima_data = self._calcular_proximo_mes_bimestral(data_referencia, conta_config.dia_vencimento)
            else:
                proxima_data = self._calcular_proximo_mes_bimestral(data_referencia, conta_config.dia_vencimento)
        else:
            if conta_config.prox_data_cobranca is None:
                try:
                    data_vencimento_mes_atual = data_referencia.replace(day=conta_config.dia_vencimento)
                    if data_vencimento_mes_atual.date() >= data_referencia.date():
                        proxima_data = data_vencimento_mes_atual
                    else:
                        proxima_data = self._calcular_proximo_mes(data_referencia, conta_config.dia_vencimento)
                except ValueError:
                    proxima_data = self._calcular_proximo_mes(data_referencia, conta_config.dia_vencimento)
            else:
                proxima_data = self._calcular_proximo_mes(data_referencia, conta_config.dia_vencimento)

        if conta_config.feriados_ajustar:
            proxima_data = self.feriados_manager.ajustar_data_util(proxima_data)
        
        return proxima_data.date()
    
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
    
    def inicializar_proximas_cobrancas(self):
        """Inicializa todas as próximas datas de cobrança para contas sem configuração"""

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT cf.id, cc.frequencia, cc.dia_vencimento, cc.feriados_ajustar
                FROM contas_fixas cf
                LEFT JOIN contas_config cc ON cf.id = cc.conta_id
                WHERE cc.prox_data_cobranca IS NULL AND cf.ativo = 1
            ''')
            
            contas_sem_data = cursor.fetchall()
            
            for conta_id, frequencia, dia_vencimento, feriados_ajustar in contas_sem_data:
                from models.models import ContaConfig
                conta_config = ContaConfig(
                    id=None,
                    conta_id=conta_id,
                    frequencia=frequencia or 'mensal',
                    dia_vencimento=dia_vencimento,
                    prox_data_cobranca=None,
                    feriados_ajustar=feriados_ajustar or 1
                )
                
                proxima_data = self.calcular_proxima_data_cobranca(conta_config)
                self.db.update_proxima_cobranca(conta_id, proxima_data)
            
            print(f"Próximas cobranças inicializadas: {len(contas_sem_data)}")
            
    def _calcular_proximo_mes(self, data_referencia, dia_vencimento):
        """Calcula data no próximo mês considerando dias do mês"""
        if data_referencia.month == 12:
            primeiro_prox_mes = data_referencia.replace(year=data_referencia.year + 1, month=1, day=1)
        else:
            primeiro_prox_mes = data_referencia.replace(month=data_referencia.month + 1, day=1)
        
        from calendar import monthrange
        _, ultimo_dia = monthrange(primeiro_prox_mes.year, primeiro_prox_mes.month)
        dia_final = min(dia_vencimento, ultimo_dia)
        
        return primeiro_prox_mes.replace(day=dia_final)
            
    
        