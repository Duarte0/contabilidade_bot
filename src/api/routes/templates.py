from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime

from ..models import TemplateResponse, TemplateCreate, TemplateUpdate, SuccessResponse
from core.database import DatabaseManager

router = APIRouter()

def get_db():
    return DatabaseManager()

@router.get("/", response_model=List[TemplateResponse])
async def listar_templates(
    ativo: bool = True,
    db: DatabaseManager = Depends(get_db)
):
    """Lista todos os templates disponíveis"""
    try:
        templates = db.get_all_templates()
        
        return [
            TemplateResponse(
                id=t.id,
                nome=t.nome,
                template_text=t.template_text,
                variaveis=t.variaveis,
                ativo=t.ativo
            ) for t in templates if not ativo or t.ativo
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar templates: {str(e)}")

@router.get("/{template_name}", response_model=TemplateResponse)
async def obter_template(template_name: str, db: DatabaseManager = Depends(get_db)):
    """Obtém um template específico pelo nome"""
    try:
        template = db.get_template_by_name(template_name)
        if not template:
            raise HTTPException(status_code=404, detail="Template não encontrado")
        
        return TemplateResponse(
            id=template.id,
            nome=template.nome,
            template_text=template.template_text,
            variaveis=template.variaveis,
            ativo=template.ativo
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter template: {str(e)}")

@router.post("/", response_model=TemplateResponse, status_code=201)
async def criar_template(template: TemplateCreate, db: DatabaseManager = Depends(get_db)):
    """Cria um novo template"""
    try:
        template_id = db.inserir_template(
            nome=template.nome,
            template_text=template.template_text,
            variaveis=template.variaveis
        )
        
        return TemplateResponse(
            id=template_id,
            nome=template.nome,
            template_text=template.template_text,
            variaveis=template.variaveis,
            ativo=True
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao criar template: {str(e)}")

@router.put("/{template_name}", response_model=TemplateResponse)
async def atualizar_template(
    template_name: str,
    template_update: TemplateUpdate,
    db: DatabaseManager = Depends(get_db)
):
    """Atualiza um template existente"""
    try:
        template_atual = db.get_template_by_name(template_name)
        if not template_atual:
            raise HTTPException(status_code=404, detail="Template não encontrado")
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if template_update.template_text:
                updates.append("template_text = %s")
                params.append(template_update.template_text)
            
            if template_update.variaveis:
                updates.append("variaveis = %s")
                params.append(template_update.variaveis)
            
            if template_update.ativo is not None:
                updates.append("ativo = %s")
                params.append(template_update.ativo)
            
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(template_name)
                
                query = f"UPDATE message_templates SET {', '.join(updates)} WHERE nome = %s"
                cursor.execute(query, params)
        
        template_atualizado = db.get_template_by_name(template_name)
        
        return TemplateResponse(
            id=template_atualizado.id,
            nome=template_atualizado.nome,
            template_text=template_atualizado.template_text,
            variaveis=template_atualizado.variaveis,
            ativo=template_atualizado.ativo
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar template: {str(e)}")

@router.delete("/{template_name}", response_model=SuccessResponse)
async def deletar_template(template_name: str, db: DatabaseManager = Depends(get_db)):
    """Desativa um template (soft delete)"""
    try:
        template = db.get_template_by_name(template_name)
        if not template:
            raise HTTPException(status_code=404, detail="Template não encontrado")
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE message_templates SET ativo = false WHERE nome = %s",
                (template_name,)
            )
        
        return SuccessResponse(
            message=f"Template '{template_name}' desativado com sucesso",
            data={"template_name": template_name}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar template: {str(e)}")
