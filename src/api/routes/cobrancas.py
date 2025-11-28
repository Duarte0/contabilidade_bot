from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any
from datetime import datetime
import logging

from ..models import (
    BatchSendRequest, BatchSendResponse,
    PreviewRequest, PreviewResponse,
    SuccessResponse
)
from core.database import DatabaseManager
from services.digisac_service import DigisacAPI
from services.template_manager import TemplateManager

router = APIRouter()
logger = logging.getLogger(__name__)

def get_db():
    return DatabaseManager()

@router.post("/preview", response_model=PreviewResponse)
async def preview_mensagem(
    request: PreviewRequest,
    db: DatabaseManager = Depends(get_db)
):
    """
    Pré-visualiza a mensagem renderizada para um cliente
    Útil para testar antes de enviar em lote
    """
    try:
        # Buscar cliente
        cliente = db.get_cliente_by_id(request.cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # Buscar template
        template_manager = TemplateManager(db)
        template = db.get_template_by_name(request.template_name)
        
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{request.template_name}' não encontrado")
        
        # Montar contexto
        context = {
            'nome': cliente.nome,
            **request.variaveis_extras
        }
        
        # Renderizar
        mensagem = template_manager.engine.render_template(request.template_name, context)
        
        return PreviewResponse(
            cliente_nome=cliente.nome,
            mensagem_renderizada=mensagem,
            variaveis_utilizadas=context
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar preview: {str(e)}")

@router.post("/enviar-lote", response_model=BatchSendResponse)
async def enviar_mensagens_lote(
    request: BatchSendRequest,
    background_tasks: BackgroundTasks,
    db: DatabaseManager = Depends(get_db)
):
    """
    **ENDPOINT PRINCIPAL**: Envia mensagens em lote para múltiplos clientes
    
    Fluxo:
    1. Valida todos os clientes
    2. Para cada cliente:
       - Usa mensagem customizada OU mensagem padrão OU template
       - Renderiza com variáveis do cliente
       - Envia via Digisac
    3. Registra histórico (sucesso ou erro)
    4. Retorna resumo detalhado
    
    Parâmetros:
    - clientes_ids: Lista de IDs dos clientes
    - tipo: 'financeira' ou 'documento'
    - template_name: Nome do template (opcional)
    - mensagem_padrao: Mensagem padrão (opcional, se não usar template)
    - mensagens_customizadas: Dict {cliente_id: mensagem} para customizações
    - enviar_agora: True para enviar imediatamente
    """
    try:
        digisac = DigisacAPI()
        template_manager = TemplateManager(db)
        
        # Validar clientes
        clientes = []
        for cliente_id in request.clientes_ids:
            cliente = db.get_cliente_by_id(cliente_id)
            if not cliente:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Cliente ID {cliente_id} não encontrado"
                )
            clientes.append(cliente)
        
        # Resultados
        resultados = []
        enviados = 0
        erros = 0
        
        for cliente in clientes:
            try:
                # Determinar mensagem a usar
                mensagem = None
                
                # 1. Prioridade: mensagem customizada
                if request.mensagens_customizadas and cliente.id in request.mensagens_customizadas:
                    mensagem = request.mensagens_customizadas[cliente.id]
                    fonte = "customizada"
                
                # 2. Usar template
                elif request.template_name:
                    context = {'nome': cliente.nome}
                    
                    # Adicionar contexto adicional se fornecido
                    if hasattr(request, 'variaveis_extras') and request.variaveis_extras:
                        context.update(request.variaveis_extras)
                    
                    mensagem = template_manager.engine.render_template(
                        request.template_name, 
                        context
                    )
                    fonte = f"template:{request.template_name}"
                
                # 3. Usar mensagem padrão
                elif request.mensagem_padrao:
                    # Criar contexto com todas as variáveis
                    context = {'nome': cliente.nome}
                    
                    # Adicionar variáveis extras se fornecidas
                    if hasattr(request, 'variaveis_extras') and request.variaveis_extras:
                        context.update(request.variaveis_extras)
                    
                    # Renderizar mensagem padrão com as variáveis
                    mensagem = template_manager.engine._render_text(
                        request.mensagem_padrao, 
                        context
                    )
                    fonte = "padrao"
                
                else:
                    raise ValueError("Nenhuma mensagem fornecida")
                
                if not mensagem:
                    raise ValueError("Mensagem vazia após renderização")
                
                # Enviar mensagem
                if request.enviar_agora:
                    sucesso = digisac.enviar_mensagem(
                        cliente.digisac_contact_id, 
                        mensagem
                    )
                    
                    if sucesso:
                        enviados += 1
                        status = "enviado"
                        erro_msg = None
                    else:
                        erros += 1
                        status = "erro"
                        erro_msg = "Falha no envio via API Digisac"
                else:
                    # Apenas agendar
                    status = "agendado"
                    erro_msg = None
                    sucesso = True
                
                # Registrar histórico
                # Define template_usado baseado na fonte da mensagem
                if request.template_name:
                    template_label = request.template_name
                elif request.mensagens_customizadas and cliente.id in request.mensagens_customizadas:
                    template_label = "Customizada"
                else:
                    template_label = "Padrão"
                
                db.registrar_envio(
                    cliente_id=cliente.id,
                    tipo=request.tipo,
                    template_usado=template_label,
                    mensagem=mensagem,
                    status=status,
                    erro_detalhe=erro_msg
                )
                
                # Resultado individual
                resultados.append({
                    "cliente_id": cliente.id,
                    "cliente_nome": cliente.nome,
                    "status": status,
                    "mensagem": mensagem[:100] + "..." if len(mensagem) > 100 else mensagem,
                    "fonte_mensagem": fonte,
                    "erro": erro_msg
                })
                
                logger.info(f"{'✅' if sucesso else '❌'} {cliente.nome}: {status}")
                
            except Exception as e:
                erros += 1
                erro_msg = str(e)
                
                resultados.append({
                    "cliente_id": cliente.id,
                    "cliente_nome": cliente.nome,
                    "status": "erro",
                    "mensagem": None,
                    "fonte_mensagem": None,
                    "erro": erro_msg
                })
                
                logger.error(f"❌ Erro ao processar {cliente.nome}: {erro_msg}")
        
        return BatchSendResponse(
            total_clientes=len(clientes),
            enviados=enviados,
            erros=erros,
            detalhes=resultados
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no envio em lote: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no envio em lote: {str(e)}")

@router.get("/status/{task_id}")
async def verificar_status_envio(task_id: str):
    """
    Verifica status de um envio em lote (para envios assíncronos futuros)
    """
    # TODO: Implementar com Redis/Celery para envios assíncronos
    return {
        "task_id": task_id,
        "status": "completed",
        "message": "Funcionalidade em desenvolvimento"
    }
