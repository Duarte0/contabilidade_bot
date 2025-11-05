import psycopg2
import logging
from contextlib import contextmanager
from typing import List, Optional, Tuple, Any, Dict
from datetime import datetime
from models.models import Cliente, ClienteStatus, ContaConfig, ContaFixa, MessageTemplate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, connection_string: str = None):
        from .config import POSTGRES_CONNECTION_STRING
        self.connection_string = connection_string or POSTGRES_CONNECTION_STRING
        self._init_pool()
        self.init_database()

    def _init_pool(self):
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
        """Inicializa todas as tabelas do sistema com constraints"""
        tables = [
            '''
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                digisac_contact_id TEXT UNIQUE NOT NULL,
                telefone TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS contas_fixas (
                id SERIAL PRIMARY KEY,
                cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
                descricao TEXT NOT NULL,
                valor DECIMAL(10,2) NOT NULL CHECK (valor > 0),
                dia_vencimento INTEGER NOT NULL CHECK (dia_vencimento BETWEEN 1 AND 31),
                ativo BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS contas_config (
                id SERIAL PRIMARY KEY,
                conta_id INTEGER UNIQUE NOT NULL REFERENCES contas_fixas(id) ON DELETE CASCADE,
                frequencia TEXT DEFAULT 'mensal' CHECK (frequencia IN ('diaria', 'semanal', 'quinzenal', 'mensal', 'bimestral')),
                prox_data_cobranca DATE,
                feriados_ajustar BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS historico_cobrancas (
                id SERIAL PRIMARY KEY,
                cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
                conta_id INTEGER NOT NULL REFERENCES contas_fixas(id) ON DELETE CASCADE,
                data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                mensagem TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('enviado', 'erro', 'pendente')),
                tentativas INTEGER DEFAULT 1,
                erro_detalhe TEXT
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS cliente_status (
                id SERIAL PRIMARY KEY,
                cliente_id INTEGER UNIQUE NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
                status TEXT DEFAULT 'ativo' CHECK (status IN ('ativo', 'inadimplente', 'suspenso', 'cancelado')),
                last_payment_date DATE,
                dias_tolerancia INTEGER DEFAULT 30,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS historico_pagamentos (
                id SERIAL PRIMARY KEY,
                cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
                valor DECIMAL(10,2) NOT NULL CHECK (valor > 0),
                data_pagamento DATE NOT NULL,
                mes_referencia TEXT NOT NULL,
                confirmado BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS interacoes_cliente (
                id SERIAL PRIMARY KEY,
                cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
                tipo_interacao TEXT NOT NULL CHECK (tipo_interacao IN (
                    'pagamento_detectado', 'duvida', 'reclamacao', 'outro',
                    'confirmacao', 'urgencia_contato', 'parcelamento', 'duvida_generica',
                    'duvida_valor', 'duvida_data'
                )),
                mensagem TEXT NOT NULL,
                resolvido BOOLEAN DEFAULT false,
                data_interacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''',
            '''
            CREATE TABLE IF NOT EXISTS message_templates (
                id SERIAL PRIMARY KEY,
                nome TEXT UNIQUE NOT NULL,
                template_text TEXT NOT NULL,
                variaveis TEXT,
                ativo BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        ]

        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_clientes_contact_id ON clientes(digisac_contact_id)',
            'CREATE INDEX IF NOT EXISTS idx_contas_fixas_cliente_id ON contas_fixas(cliente_id)',
            'CREATE INDEX IF NOT EXISTS idx_contas_config_conta_id ON contas_config(conta_id)',
            'CREATE INDEX IF NOT EXISTS idx_contas_config_prox_data ON contas_config(prox_data_cobranca)',
            'CREATE INDEX IF NOT EXISTS idx_historico_cobrancas_cliente_id ON historico_cobrancas(cliente_id)',
            'CREATE INDEX IF NOT EXISTS idx_historico_cobrancas_data_envio ON historico_cobrancas(data_envio)',
            'CREATE INDEX IF NOT EXISTS idx_historico_pagamentos_cliente_id ON historico_pagamentos(cliente_id)',
            'CREATE INDEX IF NOT EXISTS idx_historico_pagamentos_data ON historico_pagamentos(data_pagamento)',
            'CREATE INDEX IF NOT EXISTS idx_cliente_status_cliente_id ON cliente_status(cliente_id)',
            'CREATE INDEX IF NOT EXISTS idx_cliente_status_last_payment ON cliente_status(last_payment_date)'
        ]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for table_sql in tables:
                try:
                    cursor.execute(table_sql)
                except Exception as e:
                    logger.warning(f"Tabela possivelmente já existe: {e}")
            
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    logger.warning(f"Índice possivelmente já existe: {e}")
            

    def inserir_cliente(self, nome: str, digisac_contact_id: str, telefone: str = None, email: str = None) -> int:
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
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nome, digisac_contact_id, telefone, email 
                FROM clientes WHERE digisac_contact_id = %s
            ''', (contact_id,))
            result = cursor.fetchone()
            return Cliente(*result) if result else None

    def get_cliente_by_id(self, cliente_id: int) -> Optional[Cliente]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nome, digisac_contact_id, telefone, email 
                FROM clientes WHERE id = %s
            ''', (cliente_id,))
            result = cursor.fetchone()
            return Cliente(*result) if result else None

    def get_all_clientes(self) -> List[Cliente]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, nome, digisac_contact_id, telefone, email FROM clientes')
            return [Cliente(*row) for row in cursor.fetchall()]

    def inserir_conta_fixa(self, cliente_id: int, descricao: str, valor: float, dia_vencimento: int) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO contas_fixas (cliente_id, descricao, valor, dia_vencimento)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            ''', (cliente_id, descricao, valor, dia_vencimento))
            return cursor.fetchone()[0]

    def get_contas_fixas_cliente(self, cliente_id: int) -> List[ContaFixa]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, cliente_id, descricao, valor, dia_vencimento, ativo 
                FROM contas_fixas WHERE cliente_id = %s AND ativo = true
            ''', (cliente_id,))
            return [ContaFixa(*row) for row in cursor.fetchall()]

    def get_conta_config(self, conta_id: int) -> Optional[ContaConfig]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, conta_id, frequencia, prox_data_cobranca, feriados_ajustar
                FROM contas_config WHERE conta_id = %s
            ''', (conta_id,))
            result = cursor.fetchone()
            return ContaConfig(*result) if result else None

    def update_proxima_cobranca(self, conta_id: int, proxima_data: datetime):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO contas_config (conta_id, prox_data_cobranca) 
                VALUES (%s, %s)
                ON CONFLICT (conta_id) 
                DO UPDATE SET 
                    prox_data_cobranca = EXCLUDED.prox_data_cobranca,
                    updated_at = CURRENT_TIMESTAMP
            ''', (conta_id, proxima_data.strftime('%Y-%m-%d')))

    def update_conta_config(self, conta_id: int, frequencia: str = None, 
                          prox_data_cobranca: datetime = None, feriados_ajustar: bool = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Buscar configuração atual
            current = self.get_conta_config(conta_id)
            
            if not current:
                cursor.execute('''
                    INSERT INTO contas_config (conta_id, frequencia, prox_data_cobranca, feriados_ajustar)
                    VALUES (%s, %s, %s, %s)
                ''', (conta_id, frequencia or 'mensal', 
                      prox_data_cobranca.strftime('%Y-%m-%d') if prox_data_cobranca else None, 
                      feriados_ajustar or True))
            else:
                update_fields = []
                update_data = []
                
                if frequencia is not None:
                    update_fields.append("frequencia = %s")
                    update_data.append(frequencia)
                
                if prox_data_cobranca is not None:
                    update_fields.append("prox_data_cobranca = %s")
                    update_data.append(prox_data_cobranca.strftime('%Y-%m-%d'))
                
                if feriados_ajustar is not None:
                    update_fields.append("feriados_ajustar = %s")
                    update_data.append(feriados_ajustar)
                
                if update_fields:
                    update_fields.append("updated_at = CURRENT_TIMESTAMP")
                    update_data.append(conta_id)
                    cursor.execute(f'''
                        UPDATE contas_config 
                        SET {', '.join(update_fields)}
                        WHERE conta_id = %s
                    ''', update_data)

    def get_clientes_para_cobrar_hoje(self) -> List[Tuple]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            hoje = datetime.now().date()
            
            cursor.execute('''
                SELECT c.id, c.digisac_contact_id, c.nome, cf.descricao, cf.valor, cf.id
                FROM clientes c
                JOIN contas_fixas cf ON c.id = cf.cliente_id
                LEFT JOIN contas_config cc ON cf.id = cc.conta_id
                WHERE (cc.prox_data_cobranca = %s OR 
                      (cc.prox_data_cobranca IS NULL AND cf.dia_vencimento = %s))
                AND cf.ativo = true
            ''', (hoje, hoje.day))
            
            return cursor.fetchall()

    def registrar_cobranca(self, cliente_id: int, conta_id: int, mensagem: str, 
                          status: str, tentativas: int = 1, erro_detalhe: str = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO historico_cobrancas 
                (cliente_id, conta_id, mensagem, status, tentativas, erro_detalhe)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (cliente_id, conta_id, mensagem, status, tentativas, erro_detalhe))

    def registrar_pagamento(self, cliente_id: int, valor: float, data_pagamento: str, 
                        mes_referencia: str = None, confirmado: bool = False) -> int:
        if isinstance(data_pagamento, str):
            data_pagamento = datetime.strptime(data_pagamento, '%Y-%m-%d').date()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if not mes_referencia:
                mes_referencia = datetime.now().strftime('%Y-%m')
                
            cursor.execute('''
                INSERT INTO historico_pagamentos 
                (cliente_id, valor, data_pagamento, mes_referencia, confirmado)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            ''', (cliente_id, valor, data_pagamento, mes_referencia, confirmado))
            pagamento_id = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT INTO cliente_status 
                (cliente_id, status, last_payment_date, updated_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (cliente_id) 
                DO UPDATE SET 
                    status = EXCLUDED.status, 
                    last_payment_date = EXCLUDED.last_payment_date,
                    updated_at = EXCLUDED.updated_at
            ''', (cliente_id, 'ativo', data_pagamento))
            
            return pagamento_id

    def get_ultimo_pagamento_cliente(self, cliente_id: int) -> Optional[str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT data_pagamento 
                FROM historico_pagamentos 
                WHERE cliente_id = %s 
                ORDER BY data_pagamento DESC 
                LIMIT 1
            ''', (cliente_id,))
            result = cursor.fetchone()
            return result[0] if result else None

    def get_cliente_status(self, cliente_id: int) -> Optional[ClienteStatus]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, cliente_id, status, last_payment_date, dias_tolerancia
                FROM cliente_status WHERE cliente_id = %s
            ''', (cliente_id,))
            result = cursor.fetchone()
            return ClienteStatus(*result) if result else None

    def update_cliente_status(self, cliente_id: int, status: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO cliente_status (cliente_id, status, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (cliente_id) 
                DO UPDATE SET 
                    status = EXCLUDED.status, 
                    updated_at = EXCLUDED.updated_at
            ''', (cliente_id, status))

    def registrar_interacao(self, cliente_id: int, tipo_interacao: str, mensagem: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO interacoes_cliente (cliente_id, tipo_interacao, mensagem)
                VALUES (%s, %s, %s)
            ''', (cliente_id, tipo_interacao, mensagem))

    def inserir_template(self, nome: str, template_text: str, variaveis: str = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO message_templates (nome, template_text, variaveis)
                VALUES (%s, %s, %s)
                ON CONFLICT (nome) 
                DO UPDATE SET 
                    template_text = EXCLUDED.template_text, 
                    variaveis = EXCLUDED.variaveis,
                    ativo = true,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            ''', (nome, template_text, variaveis))
            return cursor.fetchone()[0]

    def get_template_by_name(self, nome: str) -> Optional[MessageTemplate]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nome, template_text, variaveis, ativo 
                FROM message_templates WHERE nome = %s AND ativo = true
            ''', (nome,))
            result = cursor.fetchone()
            return MessageTemplate(*result) if result else None

    def get_all_templates(self) -> List[MessageTemplate]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nome, template_text, variaveis, ativo 
                FROM message_templates WHERE ativo = true
            ''')
            return [MessageTemplate(*row) for row in cursor.fetchall()]

    def get_clientes_inadimplentes(self, dias_tolerancia: int = 30) -> List[Tuple]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.id, c.nome, c.digisac_contact_id, cs.last_payment_date,
                       EXTRACT(DAY FROM (CURRENT_DATE - cs.last_payment_date)) as dias_atraso
                FROM clientes c
                JOIN cliente_status cs ON c.id = cs.cliente_id
                WHERE cs.status = 'inadimplente' 
                OR (cs.last_payment_date IS NULL OR 
                    CURRENT_DATE - cs.last_payment_date > %s)
            ''', (dias_tolerancia,))
            return cursor.fetchall()

    def get_estatisticas_cobrancas(self, dias: int = 30) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'enviado' THEN 1 END) as enviadas,
                    COUNT(CASE WHEN status = 'erro' THEN 1 END) as erros,
                    COUNT(CASE WHEN status = 'pendente' THEN 1 END) as pendentes
                FROM historico_cobrancas 
                WHERE data_envio >= CURRENT_DATE - INTERVAL '%s days'
            ''', (dias,))
            result = cursor.fetchone()
            return {
                'total': result[0],
                'enviadas': result[1],
                'erros': result[2],
                'pendentes': result[3]
            }

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
        if self.pool:
            self.pool.closeall()


class DatabaseError(Exception):
    """Exceção base para erros de banco de dados"""
    pass

class DatabaseConnectionError(DatabaseError):
    """Erro de conexão com o banco"""
    pass

class DatabaseTimeoutError(DatabaseError):
    """Timeout em operação do banco"""
    pass