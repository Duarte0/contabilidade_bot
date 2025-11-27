from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime

from ..models import (
    ClienteResponse, ClienteCreate, ClienteUpdate, 
    ClienteListFilter, SuccessResponse
)
from core.database import DatabaseManager
from models.models import Cliente

router = APIRouter()

def get_db():
    return DatabaseManager()

@router.get("/", response_model=List[ClienteResponse])
async def listar_clientes(
    nome: Optional[str] = Query(None, description="Filtrar por nome"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: DatabaseManager = Depends(get_db)
):
    """Lista todos os clientes com filtros opcionais"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT c.id, c.nome, c.digisac_contact_id, c.telefone, c.email,
                       c.created_at, c.status
                FROM clientes c
                WHERE 1=1
            '''
            params = []
            
            if nome:
                # Normalizar busca removendo acentos (compatível com PostgreSQL)
                query += " AND LOWER(UNACCENT(c.nome)) LIKE LOWER(UNACCENT(%s))"
                params.append(f"%{nome}%")
            
            if status:
                query += " AND c.status = %s"
                params.append(status)
            
            query += " ORDER BY c.nome LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [
                ClienteResponse(
                    id=row[0],
                    nome=row[1],
                    digisac_contact_id=row[2],
                    telefone=row[3],
                    email=row[4],
                    created_at=row[5],
                    status=row[6]
                ) for row in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar clientes: {str(e)}")

@router.get("/{cliente_id}", response_model=ClienteResponse)
async def obter_cliente(cliente_id: int, db: DatabaseManager = Depends(get_db)):
    """Obtém detalhes de um cliente específico"""
    try:
        cliente = db.get_cliente_by_id(cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT status FROM clientes WHERE id = %s', (cliente_id,))
            result = cursor.fetchone()
            status = result[0] if result else 'ativo'
        
        return ClienteResponse(
            id=cliente.id,
            nome=cliente.nome,
            digisac_contact_id=cliente.digisac_contact_id,
            telefone=cliente.telefone,
            email=cliente.email,
            status=status
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter cliente: {str(e)}")

@router.post("/", response_model=ClienteResponse, status_code=201)
async def criar_cliente(cliente: ClienteCreate, db: DatabaseManager = Depends(get_db)):
    """Cria um novo cliente"""
    try:
        cliente_id = db.inserir_cliente(
            nome=cliente.nome,
            digisac_contact_id=cliente.digisac_contact_id,
            telefone=cliente.telefone,
            email=cliente.email
        )
        
        return ClienteResponse(
            id=cliente_id,
            nome=cliente.nome,
            digisac_contact_id=cliente.digisac_contact_id,
            telefone=cliente.telefone,
            email=cliente.email,
            status="ativo"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao criar cliente: {str(e)}")

@router.put("/{cliente_id}", response_model=ClienteResponse)
async def atualizar_cliente(
    cliente_id: int, 
    cliente_update: ClienteUpdate, 
    db: DatabaseManager = Depends(get_db)
):
    """Atualiza dados de um cliente"""
    try:
        cliente_atual = db.get_cliente_by_id(cliente_id)
        if not cliente_atual:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # Atualizar campos
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if cliente_update.nome:
                updates.append("nome = %s")
                params.append(cliente_update.nome)
            
            if cliente_update.telefone:
                updates.append("telefone = %s")
                params.append(cliente_update.telefone)
            
            if cliente_update.email:
                updates.append("email = %s")
                params.append(cliente_update.email)
            
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(cliente_id)
                
                query = f"UPDATE clientes SET {', '.join(updates)} WHERE id = %s"
                cursor.execute(query, params)
        
        # Retornar cliente atualizado
        cliente_atualizado = db.get_cliente_by_id(cliente_id)
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT status FROM clientes WHERE id = %s', (cliente_id,))
            result = cursor.fetchone()
            status = result[0] if result else 'ativo'
        
        return ClienteResponse(
            id=cliente_atualizado.id,
            nome=cliente_atualizado.nome,
            digisac_contact_id=cliente_atualizado.digisac_contact_id,
            telefone=cliente_atualizado.telefone,
            email=cliente_atualizado.email,
            status=status
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar cliente: {str(e)}")

@router.delete("/{cliente_id}", response_model=SuccessResponse)
async def deletar_cliente(cliente_id: int, db: DatabaseManager = Depends(get_db)):
    """Deleta um cliente (soft delete - marca como inativo)"""
    try:
        cliente = db.get_cliente_by_id(cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # Marcar como inativo ao invés de deletar
        db.update_cliente_status(cliente_id, "inativo")
        
        return SuccessResponse(
            message=f"Cliente {cliente.nome} marcado como inativo",
            data={"cliente_id": cliente_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar cliente: {str(e)}")

@router.get("/{cliente_id}/historico")
async def obter_historico_cliente(
    cliente_id: int,
    tipo: Optional[str] = Query(None, description="Filtrar por tipo: financeira, documento, geral"),
    limit: int = Query(50, ge=1, le=200),
    db: DatabaseManager = Depends(get_db)
):
    """Obtém histórico de envios do cliente"""
    try:
        cliente = db.get_cliente_by_id(cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # Usar o método do database manager
        envios = db.get_historico_cliente(cliente_id, limit=limit)
        
        # Filtrar por tipo se especificado
        if tipo:
            envios = [e for e in envios if e['tipo'] == tipo]
        
        return {
            "cliente": {
                "id": cliente.id,
                "nome": cliente.nome
            },
            "total": len(envios),
            "envios": envios
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter histórico: {str(e)}")
