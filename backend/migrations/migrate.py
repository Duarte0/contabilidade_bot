import os
import psycopg2
from pathlib import Path
import sys

sys.path.insert(0, '/app/src')
from core.config import POSTGRES_CONNECTION_STRING

class MigrationManager:
    def __init__(self):
        self.conn = psycopg2.connect(POSTGRES_CONNECTION_STRING)
        self.migrations_dir = Path(__file__).parent
        self._ensure_migrations_table()
    
    def _ensure_migrations_table(self):
        """Cria tabela para controlar migrations aplicadas"""
        with self.conn.cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id SERIAL PRIMARY KEY,
                    filename TEXT UNIQUE NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.conn.commit()
    
    def get_applied_migrations(self):
        """Retorna lista de migrations já aplicadas"""
        with self.conn.cursor() as cursor:
            cursor.execute('SELECT filename FROM schema_migrations ORDER BY filename')
            return [row[0] for row in cursor.fetchall()]
    
    def get_pending_migrations(self):
        """Retorna migrations pendentes"""
        applied = set(self.get_applied_migrations())
        all_migrations = sorted([
            f.name for f in self.migrations_dir.glob('*.sql')
            if f.name != 'template.sql'
        ])
        return [m for m in all_migrations if m not in applied]
    
    def apply_migration(self, filename):
        """Aplica uma migration"""
        filepath = self.migrations_dir / filename
        
        print(f"[MIGRATION] Aplicando: {filename}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql)
                
                cursor.execute(
                    'INSERT INTO schema_migrations (filename) VALUES (%s)',
                    (filename,)
                )
                
                self.conn.commit()
                print(f"[SUCCESS] Migration {filename} aplicada com sucesso!")
                
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] Erro ao aplicar migration {filename}: {e}")
            raise
    
    def run_migrations(self):
        """Executa todas as migrations pendentes"""
        pending = self.get_pending_migrations()
        
        if not pending:
            print("[INFO] Nenhuma migration pendente. Banco de dados está atualizado!")
            return
        
        print(f"\n[INFO] Encontradas {len(pending)} migration(s) pendente(s):\n")
        for m in pending:
            print(f"  - {m}")
        print()
        
        for migration in pending:
            self.apply_migration(migration)
        
        print(f"\n[SUCCESS] Todas as {len(pending)} migration(s) foram aplicadas com sucesso!")
    
    def status(self):
        """Mostra status das migrations"""
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        
        print("\n[STATUS] Migrations:\n")
        print(f"Aplicadas: {len(applied)}")
        for m in applied:
            print(f"  - {m}")
        
        print(f"\nPendentes: {len(pending)}")
        for m in pending:
            print(f"  - {m}")
        print()
    
    def close(self):
        """Fecha conexão"""
        self.conn.close()

if __name__ == '__main__':
    import sys
    
    manager = MigrationManager()
    
    try:
        if len(sys.argv) > 1 and sys.argv[1] == 'status':
            manager.status()
        else:
            manager.run_migrations()
    finally:
        manager.close()
