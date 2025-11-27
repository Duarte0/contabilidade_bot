from fastapi import APIRouter, HTTPException, Depends

from ..models import DashboardStats
from core.database import DatabaseManager
from datetime import datetime, timedelta

router = APIRouter()

def get_db():
    return DatabaseManager()

@router.get("/stats", response_model=DashboardStats)
async def obter_estatisticas(db: DatabaseManager = Depends(get_db)):
    """Obtém estatísticas gerais do sistema para o dashboard"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total de clientes
            cursor.execute("SELECT COUNT(*) FROM clientes")
            total_clientes = cursor.fetchone()[0]
            
            # Clientes ativos
            cursor.execute("SELECT COUNT(*) FROM clientes WHERE status = 'ativo'")
            clientes_ativos = cursor.fetchone()[0] or 0
            
            # Clientes inativos/suspensos
            cursor.execute("SELECT COUNT(*) FROM clientes WHERE status != 'ativo'")
            clientes_inativos = cursor.fetchone()[0] or 0
            
            # Envios do mês
            cursor.execute("""
                SELECT COUNT(*) FROM historico_envios
                WHERE data_envio >= DATE_TRUNC('month', CURRENT_DATE)
            """)
            cobrancas_mes = cursor.fetchone()[0] or 0
            
            # Envios pendentes
            cursor.execute("SELECT COUNT(*) FROM historico_envios WHERE status = 'pendente'")
            documentos_pendentes = cursor.fetchone()[0] or 0
            
            # Taxa de sucesso nos últimos 30 dias
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN status = 'enviado' THEN 1 END)::float /
                    NULLIF(COUNT(*), 0) * 100
                FROM historico_envios
                WHERE data_envio >= CURRENT_DATE - INTERVAL '30 days'
            """)
            taxa_resposta = cursor.fetchone()[0] or 0.0
            
            return DashboardStats(
                total_clientes=total_clientes,
                clientes_ativos=clientes_ativos,
                clientes_inadimplentes=clientes_inativos,
                cobrancas_mes=cobrancas_mes,
                documentos_pendentes=documentos_pendentes,
                taxa_resposta=round(taxa_resposta, 2)
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")

@router.get("/atividades-recentes")
async def obter_atividades_recentes(limit: int = 20, db: DatabaseManager = Depends(get_db)):
    """Obtém atividades recentes do sistema"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    he.tipo,
                    c.nome as cliente_nome,
                    he.status,
                    he.data_envio as data,
                    LEFT(he.mensagem, 100) as preview
                FROM historico_envios he
                JOIN clientes c ON he.cliente_id = c.id
                WHERE he.data_envio >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY he.data_envio DESC
                LIMIT %s
            """, (limit,))
            
            atividades = []
            for row in cursor.fetchall():
                atividades.append({
                    "tipo": row[0],
                    "cliente": row[1],
                    "status": row[2],
                    "data": row[3].isoformat() if row[3] else None,
                    "preview": row[4]
                })
            
            return {
                "total": len(atividades),
                "atividades": atividades
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter atividades: {str(e)}")
