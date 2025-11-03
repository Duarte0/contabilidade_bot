from datetime import datetime, timedelta
from calendar import monthrange
from typing import Optional, List, Tuple
from .feriados_manager import FeriadosManager

class AgendamentoManager:
    def __init__(self, db):
        self.db = db
        self.feriados_manager = FeriadosManager()
    
    def calcular_proxima_data_cobranca(self, conta_config, data_referencia: Optional[datetime] = None) -> datetime.date:
        data_referencia = data_referencia or datetime.now()
        
        dia_vencimento = self._get_dia_vencimento(conta_config.conta_id)
        if not dia_vencimento:
            return data_referencia.date()
        
        if conta_config.frequencia in ['semanal', 'quinzenal']:
            dias = 7 if conta_config.frequencia == 'semanal' else 15
            proxima_data = data_referencia + timedelta(days=dias)
        else:
            if conta_config.prox_data_cobranca is None:
                proxima_data = self._calcular_primeira_cobranca(data_referencia, dia_vencimento)
            else:
                meses = 1 if conta_config.frequencia == 'mensal' else 2
                proxima_data = self._calcular_proximo_mes(data_referencia, dia_vencimento, meses)
        
        if conta_config.feriados_ajustar:
            proxima_data = self.feriados_manager.ajustar_data_util(proxima_data)
        
        return proxima_data.date()
    
    def _calcular_primeira_cobranca(self, data_referencia: datetime, dia_vencimento: int) -> datetime:
        try:
            data_vencimento = data_referencia.replace(day=dia_vencimento)
            if data_vencimento.date() >= data_referencia.date():
                return data_vencimento
        except ValueError:
            pass
        return self._calcular_proximo_mes(data_referencia, dia_vencimento, 1)
    
    def _calcular_proximo_mes(self, data_referencia: datetime, dia_vencimento: int, meses: int = 1) -> datetime:
        ano = data_referencia.year
        mes = data_referencia.month + meses
        
        if mes > 12:
            mes -= 12
            ano += 1
        
        _, ultimo_dia = monthrange(ano, mes)
        dia_final = min(dia_vencimento, ultimo_dia)
        
        return data_referencia.replace(year=ano, month=mes, day=dia_final)
    
    def _get_dia_vencimento(self, conta_id: int) -> Optional[int]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT dia_vencimento FROM contas_fixas WHERE id = ?', (conta_id,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def get_clientes_para_cobrar_hoje(self) -> List[Tuple]:
        hoje = datetime.now().date()
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.id, c.digisac_contact_id, c.nome, cf.descricao, cf.valor, cf.id
                FROM clientes c
                JOIN contas_fixas cf ON c.id = cf.cliente_id
                LEFT JOIN contas_config cc ON cf.id = cc.conta_id
                WHERE (cc.prox_data_cobranca = ? OR (cc.prox_data_cobranca IS NULL AND cf.dia_vencimento = ?))
                AND cf.ativo = 1
            ''', (hoje, hoje.day))
            
            return cursor.fetchall()
    
    def atualizar_proxima_cobranca(self, conta_id: int):
        if conta_config := self.db.get_conta_config(conta_id):
            proxima_data = self.calcular_proxima_data_cobranca(conta_config)
            self.db.update_proxima_cobranca(conta_id, proxima_data)
    
    def inicializar_proximas_cobrancas(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT cf.id, COALESCE(cc.frequencia, 'mensal'), COALESCE(cc.feriados_ajustar, 1)
                FROM contas_fixas cf
                LEFT JOIN contas_config cc ON cf.id = cc.conta_id
                WHERE cc.prox_data_cobranca IS NULL AND cf.ativo = 1
            ''')
            
            for conta_id, frequencia, feriados_ajustar in cursor.fetchall():
                from models.models import ContaConfig
                conta_config = ContaConfig(
                    id=None,
                    conta_id=conta_id,
                    frequencia=frequencia,
                    prox_data_cobranca=None,
                    feriados_ajustar=bool(feriados_ajustar)
                )
                
                proxima_data = self.calcular_proxima_data_cobranca(conta_config)
                self.db.update_proxima_cobranca(conta_id, proxima_data)