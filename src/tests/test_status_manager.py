import pytest
from datetime import datetime, timedelta
from services.cliente_status_manager import ClienteStatusManager

class TestStatusManager:
    
    def test_verificar_inadimplencia_sem_pagamento(self, temp_db, sample_cliente):
        manager = ClienteStatusManager(temp_db)
        
        # Cliente sem pagamento deve ser inadimplente
        resultado = manager.verificar_inadimplencia(sample_cliente)
        assert resultado == True
    
    def test_verificar_inadimplencia_com_pagamento_recente(self, temp_db, sample_cliente):
        manager = ClienteStatusManager(temp_db)
        
        # Registrar pagamento recente
        temp_db.registrar_pagamento(
            sample_cliente, 
            100.0, 
            datetime.now().strftime('%Y-%m-%d')
        )
        
        resultado = manager.verificar_inadimplencia(sample_cliente)
        assert resultado == False
    
    def test_verificar_inadimplencia_com_pagamento_antigo(self, temp_db, sample_cliente):
        manager = ClienteStatusManager(temp_db)
        
        # Registrar pagamento antigo (35 dias)
        data_antiga = (datetime.now() - timedelta(days=35)).strftime('%Y-%m-%d')
        temp_db.registrar_pagamento(sample_cliente, 100.0, data_antiga)
        
        resultado = manager.verificar_inadimplencia(sample_cliente)
        assert resultado == True
    
    def test_get_template_por_status(self, temp_db, sample_cliente):
        manager = ClienteStatusManager(temp_db)
        
        # Sem pagamento = template inadimplente
        template_inadimplente = manager.get_template_por_status(sample_cliente)
        assert template_inadimplente == 'cobranca_inadimplente'
        
        # Com pagamento recente = template padrão
        temp_db.registrar_pagamento(sample_cliente, 100.0, datetime.now().strftime('%Y-%m-%d'))
        template_normal = manager.get_template_por_status(sample_cliente)
        assert template_normal == 'cobranca_padrao'