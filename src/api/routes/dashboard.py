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

@router.get("/stats/periodo")
async def obter_estatisticas_periodo(
    mes: int,
    ano: int,
    db: DatabaseManager = Depends(get_db)
):
    """Obtém estatísticas filtradas por mês/ano específico"""
    try:
        if mes < 1 or mes > 12:
            raise HTTPException(status_code=400, detail="Mês inválido")
        if ano < 2000 or ano > 2100:
            raise HTTPException(status_code=400, detail="Ano inválido")
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Envios no período
            cursor.execute("""
                SELECT COUNT(*) FROM historico_envios
                WHERE EXTRACT(MONTH FROM data_envio) = %s
                  AND EXTRACT(YEAR FROM data_envio) = %s
            """, (mes, ano))
            envios_periodo = cursor.fetchone()[0] or 0
            
            # Envios por tipo
            cursor.execute("""
                SELECT tipo, COUNT(*) 
                FROM historico_envios
                WHERE EXTRACT(MONTH FROM data_envio) = %s
                  AND EXTRACT(YEAR FROM data_envio) = %s
                GROUP BY tipo
            """, (mes, ano))
            por_tipo = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Taxa de sucesso
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN status = 'enviado' THEN 1 END)::float /
                    NULLIF(COUNT(*), 0) * 100
                FROM historico_envios
                WHERE EXTRACT(MONTH FROM data_envio) = %s
                  AND EXTRACT(YEAR FROM data_envio) = %s
            """, (mes, ano))
            taxa_sucesso = cursor.fetchone()[0] or 0.0
            
            return {
                "mes": mes,
                "ano": ano,
                "total_envios": envios_periodo,
                "por_tipo": por_tipo,
                "taxa_sucesso": round(taxa_sucesso, 2)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas do período: {str(e)}")

@router.get("/atividades-recentes")
async def obter_atividades_recentes(
    limit: int = 20,
    tipo: str | None = None,
    mes: int | None = None,
    ano: int | None = None,
    db: DatabaseManager = Depends(get_db)
):
    """Obtém atividades recentes do sistema.
    Parâmetros:
        - limit: quantidade máxima de registros (default 20)
        - tipo: filtra pelo tipo de mensagem (financeira, documento, geral)
        - mes: filtra pelo mês (1-12)
        - ano: filtra pelo ano (ex: 2025)
    """
    try:
        # Validar tipo se fornecido
        tipos_validos = {"financeira", "documento", "geral"}
        if tipo is not None and tipo not in tipos_validos:
            raise HTTPException(status_code=400, detail="Tipo inválido. Use: financeira, documento ou geral")
        
        # Validar mes e ano se fornecidos
        if mes is not None and (mes < 1 or mes > 12):
            raise HTTPException(status_code=400, detail="Mês inválido. Use valores entre 1 e 12")
        if ano is not None and (ano < 2000 or ano > 2100):
            raise HTTPException(status_code=400, detail="Ano inválido")

        with db.get_connection() as conn:
            cursor = conn.cursor()

            base_query = """
                SELECT 
                    he.tipo,
                    c.nome as cliente_nome,
                    he.status,
                    he.data_envio as data,
                    LEFT(he.mensagem, 100) as preview
                FROM historico_envios he
                JOIN clientes c ON he.cliente_id = c.id
                WHERE 1=1
            """

            params = []
            
            # Filtro de período: se mes/ano fornecidos, usa-os; senão últimos 7 dias
            if mes is not None and ano is not None:
                base_query += " AND EXTRACT(MONTH FROM he.data_envio) = %s AND EXTRACT(YEAR FROM he.data_envio) = %s"
                params.extend([mes, ano])
            else:
                base_query += " AND he.data_envio >= CURRENT_DATE - INTERVAL '7 days'"
            
            if tipo:
                base_query += " AND he.tipo = %s"
                params.append(tipo)

            base_query += " ORDER BY he.data_envio DESC LIMIT %s"
            params.append(limit)

            cursor.execute(base_query, tuple(params))

            atividades = []
            for row in cursor.fetchall():
                atividades.append({
                    "tipo": row[0],
                    "cliente": row[1],
                    "status": row[2],
                    "data": row[3].isoformat() if row[3] else None,
                    "preview": row[4]
                })

            return {"total": len(atividades), "atividades": atividades}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter atividades: {str(e)}")
