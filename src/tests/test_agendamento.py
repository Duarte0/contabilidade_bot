import pytest
from datetime import datetime
from services.agendamento_manager import AgendamentoManager
from models.models import ContaConfig

class TestAgendamento:
    
    @pytest.mark.parametrize("data_ref,dia_venc,esperado", [
        ("2025-01-31", 31, "2025-02-28"),  # Jan→Fev (31 não existe)
        ("2025-02-28", 31, "2025-03-31"),  # Fev→Mar (31 existe)
        ("2025-12-31", 15, "2026-01-15"),  # Dez→Jan
        ("2025-04-30", 1, "2025-05-02"),   # 1/05 feriado → 2/05
    ])
    def test_calculo_proxima_data_mensal(self, temp_db, data_ref, dia_venc, esperado):
        manager = AgendamentoManager(temp_db)
        config = ContaConfig(
            id=1, conta_id=1, frequencia="mensal", 
            dia_vencimento=dia_venc, feriados_ajustar=True
        )
        
        data_referencia = datetime.strptime(data_ref, "%Y-%m-%d")
        resultado = manager.calcular_proxima_data_cobranca(config, data_referencia)
        
        assert str(resultado) == esperado

    def test_ajuste_fim_semana(self, temp_db):
        manager = AgendamentoManager(temp_db)
        config = ContaConfig(
            id=1, conta_id=1, frequencia="mensal", 
            dia_vencimento=1, feriados_ajustar=True
        )
        
        data_referencia = datetime(2025, 1, 31)
        resultado = manager.calcular_proxima_data_cobranca(config, data_referencia)
        
        assert str(resultado) == "2025-02-03"