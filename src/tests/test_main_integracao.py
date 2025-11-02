# tests/test_main_integracao.py
import pytest
from datetime import datetime
import sys
from unittest.mock import Mock, patch

def test_main_integracao(temp_db, monkeypatch):
    """Testa a integração completa do main.py"""
    
    mock_digisac = Mock()
    mock_digisac.enviar_mensagem.return_value = True
    
    mock_agendamento = Mock()
    mock_agendamento.get_clientes_para_cobrar_hoje.return_value = [
        (1, "contact_test", "Cliente Teste", "Serviço Teste", 150.0, 1)
    ]
    mock_agendamento.inicializar_proximas_cobrancas.return_value = None
    mock_agendamento.atualizar_proxima_cobranca.return_value = None
    
    mock_template = Mock()
    mock_template.aplicar_template_cliente.return_value = "Mensagem de teste renderizada"
    
    mock_status = Mock()
    mock_status.get_template_por_status.return_value = "cobranca_padrao"
    
    with patch('main.DigisacAPI', return_value=mock_digisac), \
         patch('main.AgendamentoManager', return_value=mock_agendamento), \
         patch('main.TemplateManager', return_value=mock_template), \
         patch('main.ClienteStatusManager', return_value=mock_status):
        
        from main import main
        
        try:
            main()
            assert True
        except Exception as e:
            pytest.fail(f"main() falhou com: {e}")
    
    mock_agendamento.get_clientes_para_cobrar_hoje.assert_called_once()
    mock_digisac.enviar_mensagem.assert_called_once()

def test_main_sem_clientes(temp_db, monkeypatch):
    """Testa main quando não há clientes para cobrar"""
    
    mock_agendamento = Mock()
    mock_agendamento.get_clientes_para_cobrar_hoje.return_value = []
    mock_agendamento.inicializar_proximas_cobrancas.return_value = None
    
    with patch('main.AgendamentoManager', return_value=mock_agendamento), \
         patch('main.DigisacAPI'): 
        
        from main import main
        
        try:
            main()
            assert True
        except Exception as e:
            pytest.fail(f"main() falhou com lista vazia: {e}")