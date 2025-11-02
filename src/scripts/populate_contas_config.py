import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)

from core.database import DatabaseManager
from core.config import DATABASE_PATH


def popular_contas_config():
    db = DatabaseManager(DATABASE_PATH)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO contas_config (conta_id, frequencia, dia_vencimento, feriados_ajustar)
            SELECT 
                cf.id as conta_id,
                'mensal' as frequencia,
                cf.dia_vencimento,
                1 as feriados_ajustar
            FROM contas_fixas cf
            WHERE cf.ativo = 1
        ''')
        
        print(f"Configurações de conta atualizadas: {cursor.rowcount}")

if __name__ == "__main__":
    popular_contas_config()