import psycopg2
import logging
from contextlib import contextmanager
from typing import List, Optional, Dict, Any
from datetime import datetime
from models.models import Cliente, MessageTemplate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gerenciador simplificado do banco de dados - Foco em envio de mensagens"""
    
    def __init__(self, connection_string: str = None):
        from .config import POSTGRES_CONNECTION_STRING
        self.connection_string = connection_string or POSTGRES_CONNECTION_STRING
        self._init_pool()
        self.init_database()

    def _init_pool(self):
        """Inicializa pool de conexões"""
        try:
            from psycopg2.pool import SimpleConnectionPool
            self.pool = SimpleConnectionPool(
                minconn=5,
                maxconn=20,
                dsn=self.connection_string,
                connect_timeout=10,
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=3
            )
        except ImportError:
            self.pool = None
            logger.warning("SimpleConnectionPool não disponível, usando conexões diretas")

    @contextmanager
    def get_connection(self):
        """Context manager para gerenciar conexões"""
        conn = None
        try:
            if self.pool:
                conn = self.pool.getconn()
            else:
                conn = psycopg2.connect(
                    self.connection_string,
                    connect_timeout=10
                )
            
            conn.autocommit = False
            yield conn
            conn.commit()
            
        except psycopg2.OperationalError as e:
            logger.error(f"Falha de conexão PostgreSQL: {e}")
            if conn:
                conn.rollback()
            raise DatabaseConnectionError(f"Erro de conexão com o banco: {e}")
        except psycopg2.Error as e:
            logger.error(f"Erro PostgreSQL: {e}")
            if conn:
                conn.rollback()
            raise DatabaseError(f"Erro de banco de dados: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn and self.pool:
                self.pool.putconn(conn)
            elif conn:
                conn.close()

    def init_database(self):
        """Inicializa schema simplificado - apenas 3 tabelas"""
        tables = [
            '''
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                digisac_contact_id TEXT UNIQUE NOT NULL,
                telefone TEXT,
                email TEXT,
                status TEXT DEFAULT 'ativo' CHECK (status IN ('ativo', 'inativo', 'suspenso')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS message_templates (
                id SERIAL PRIMARY KEY,
                nome TEXT UNIQUE NOT NULL,
                tipo TEXT DEFAULT 'financeira' CHECK (tipo IN ('financeira', 'documento', 'geral')),
                template_text TEXT NOT NULL,
                variaveis TEXT,
                ativo BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS historico_envios (
                id SERIAL PRIMARY KEY,
                cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
                tipo TEXT DEFAULT 'financeira' CHECK (tipo IN ('financeira', 'documento', 'geral')),
                template_usado TEXT,
                mensagem TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('enviado', 'erro', 'pendente')),
                data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tentativas INTEGER DEFAULT 1,
                erro_detalhe TEXT
            )
            '''
        ]

        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_clientes_contact_id ON clientes(digisac_contact_id)',
            'CREATE INDEX IF NOT EXISTS idx_clientes_nome ON clientes(nome)',
            'CREATE INDEX IF NOT EXISTS idx_clientes_telefone ON clientes(telefone)',
            'CREATE INDEX IF NOT EXISTS idx_clientes_status ON clientes(status)',
            'CREATE INDEX IF NOT EXISTS idx_templates_tipo ON message_templates(tipo) WHERE ativo = true',
            'CREATE INDEX IF NOT EXISTS idx_historico_envios_cliente_id ON historico_envios(cliente_id)',
            'CREATE INDEX IF NOT EXISTS idx_historico_envios_data_envio ON historico_envios(data_envio)',
            'CREATE INDEX IF NOT EXISTS idx_historico_envios_tipo ON historico_envios(tipo)',
            'CREATE INDEX IF NOT EXISTS idx_historico_envios_status ON historico_envios(status)'
        ]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for table_sql in tables:
                try:
                    cursor.execute(table_sql)
                except Exception as e:
                    logger.warning(f"Erro ao criar tabela: {e}")
            
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    logger.warning(f"Erro ao criar índice: {e}")

    # ========== CLIENTES ==========
    
    def inserir_cliente(self, nome: str, digisac_contact_id: str, telefone: str = None, email: str = None) -> int:
        """Insere ou atualiza um cliente"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO clientes (nome, digisac_contact_id, telefone, email)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (digisac_contact_id) DO UPDATE SET
                    nome = EXCLUDED.nome,
                    telefone = EXCLUDED.telefone,
                    email = EXCLUDED.email,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            ''', (nome, digisac_contact_id, telefone, email))
            result = cursor.fetchone()
            return result[0] if result else None

    def get_cliente_by_contact_id(self, contact_id: str) -> Optional[Cliente]:
        """Busca cliente por ID do Digisac"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nome, digisac_contact_id, telefone, email 
                FROM clientes WHERE digisac_contact_id = %s
            ''', (contact_id,))
            result = cursor.fetchone()
            return Cliente(*result) if result else None

    def get_cliente_by_id(self, cliente_id: int) -> Optional[Cliente]:
        """Busca cliente por ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nome, digisac_contact_id, telefone, email 
                FROM clientes WHERE id = %s
            ''', (cliente_id,))
            result = cursor.fetchone()
            return Cliente(*result) if result else None

    def get_cliente_por_telefone(self, telefone: str) -> Optional[Cliente]:
        """Busca cliente por telefone"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nome, digisac_contact_id, telefone, email 
                FROM clientes WHERE telefone = %s
            ''', (telefone,))
            result = cursor.fetchone()
            return Cliente(*result) if result else None

    def get_all_clientes(self) -> List[Cliente]:
        """Retorna todos os clientes"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, nome, digisac_contact_id, telefone, email FROM clientes')
            return [Cliente(*row) for row in cursor.fetchall()]
    
    def update_cliente_status(self, cliente_id: int, status: str):
        """Atualiza status do cliente (ativo/inativo/suspenso)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE clientes 
                SET status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', (status, cliente_id))

    # ========== TEMPLATES ==========

    def inserir_template(self, nome: str, template_text: str, variaveis: str = None, tipo: str = 'financeira') -> int:
        """Insere ou atualiza um template de mensagem"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO message_templates (nome, tipo, template_text, variaveis)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (nome) 
                DO UPDATE SET 
                    tipo = EXCLUDED.tipo,
                    template_text = EXCLUDED.template_text, 
                    variaveis = EXCLUDED.variaveis,
                    ativo = true,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            ''', (nome, tipo, template_text, variaveis))
            return cursor.fetchone()[0]

    def get_template_by_name(self, nome: str) -> Optional[MessageTemplate]:
        """Busca um template por nome"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nome, template_text, variaveis, ativo, tipo
                FROM message_templates WHERE nome = %s
            ''', (nome,))
            result = cursor.fetchone()
            if result:
                return MessageTemplate(
                    id=result[0],
                    nome=result[1],
                    template_text=result[2],
                    variaveis=result[3],
                    ativo=result[4],
                    tipo=result[5]
                )
            return None

    def get_all_templates(self) -> List[MessageTemplate]:
        """Retorna todos os templates (ativos e inativos)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nome, template_text, variaveis, ativo, tipo
                FROM message_templates
                ORDER BY tipo, nome
            ''')
            return [MessageTemplate(
                id=row[0],
                nome=row[1],
                template_text=row[2],
                variaveis=row[3],
                ativo=row[4],
                tipo=row[5]
            ) for row in cursor.fetchall()]

    # ========== HISTÓRICO DE ENVIOS ==========

    def registrar_envio(self, cliente_id: int, mensagem: str, status: str, 
                       tipo: str = 'financeira', template_usado: str = None,
                       tentativas: int = 1, erro_detalhe: str = None) -> int:
        """Registra um envio de mensagem no histórico"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO historico_envios 
                (cliente_id, tipo, template_usado, mensagem, status, tentativas, erro_detalhe)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (cliente_id, tipo, template_usado, mensagem, status, tentativas, erro_detalhe))
            return cursor.fetchone()[0]

    def get_historico_cliente(self, cliente_id: int, limit: int = 50) -> List[Dict]:
        """Retorna histórico de envios de um cliente"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, tipo, template_usado, mensagem, status, 
                       data_envio, tentativas, erro_detalhe
                FROM historico_envios
                WHERE cliente_id = %s
                ORDER BY data_envio DESC
                LIMIT %s
            ''', (cliente_id, limit))
            
            return [{
                'id': row[0],
                'tipo': row[1],
                'template_usado': row[2],
                'mensagem': row[3],
                'status': row[4],
                'data_envio': row[5],
                'tentativas': row[6],
                'erro_detalhe': row[7]
            } for row in cursor.fetchall()]

    def get_estatisticas_envios(self, dias: int = 30) -> Dict[str, Any]:
        """Retorna estatísticas de envios dos últimos N dias"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'enviado' THEN 1 END) as enviados,
                    COUNT(CASE WHEN status = 'erro' THEN 1 END) as erros,
                    COUNT(CASE WHEN status = 'pendente' THEN 1 END) as pendentes,
                    COUNT(CASE WHEN tipo = 'financeira' THEN 1 END) as financeiros,
                    COUNT(CASE WHEN tipo = 'documento' THEN 1 END) as documentos
                FROM historico_envios 
                WHERE data_envio >= CURRENT_DATE - INTERVAL '%s days'
            ''', (dias,))
            result = cursor.fetchone()
            return {
                'total': result[0],
                'enviados': result[1],
                'erros': result[2],
                'pendentes': result[3],
                'financeiros': result[4],
                'documentos': result[5]
            }

    # ========== UTILIDADES ==========

    def health_check(self) -> bool:
        """Verifica se o banco está respondendo"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                return True
        except Exception as e:
            logger.error(f"Health check falhou: {e}")
            return False

    def close_pool(self):
        """Fecha pool de conexões"""
        if self.pool:
            self.pool.closeall()


# ========== EXCEÇÕES ==========

class DatabaseError(Exception):
    """Exceção base para erros de banco de dados"""
    pass

class DatabaseConnectionError(DatabaseError):
    """Erro de conexão com o banco"""
    pass

class DatabaseTimeoutError(DatabaseError):
    """Timeout em operação do banco"""
    pass
