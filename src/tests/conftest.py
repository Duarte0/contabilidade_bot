import pytest
import tempfile
import os
import sys
from pathlib import Path

# Adicionar src ao path para imports
SRC_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SRC_DIR))

from core.database import DatabaseManager

@pytest.fixture
def temp_db():
    """Cria banco temporário para testes"""
    fd, temp_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # DatabaseManager já cria as tabelas no __init__
    db = DatabaseManager(temp_path)
    
    yield db
    
    # FORÇAR FECHAMENTO DE CONEXÕES
    if hasattr(db, '_connection'):
        if db._connection:
            db._connection.close()
    
    # Cleanup com retry para Windows
    import time
    for i in range(5):  # Tentar até 5 vezes
        try:
            os.unlink(temp_path)
            break
        except PermissionError:
            time.sleep(0.1)  # Esperar 100ms
    else:
        print(f"⚠️  Não foi possível deletar {temp_path}")

@pytest.fixture
def sample_cliente(temp_db):
    """Cria cliente de exemplo"""
    cliente_id = temp_db.inserir_cliente("Cliente Teste", "contact_test")
    return cliente_id

@pytest.fixture
def sample_conta(temp_db, sample_cliente):
    """Cria conta de exemplo"""
    conta_id = temp_db.inserir_conta_fixa(sample_cliente, "Serviço Teste", 100.0, 15)
    return conta_id