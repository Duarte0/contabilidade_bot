from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

# Enums
class TipoCobranca(str, Enum):
    FINANCEIRA = "financeira"
    DOCUMENTO = "documento"

class TipoDocumento(str, Enum):
    EXTRATO_BANCARIO = "extrato_bancario"
    NOTA_FISCAL = "nota_fiscal"
    RECIBO = "recibo"
    COMPROVANTE = "comprovante"
    FOLHA_PAGAMENTO = "folha_pagamento"
    GUIA_IMPOSTOS = "guia_impostos"
    OUTROS = "outros"

class StatusCliente(str, Enum):
    ATIVO = "ativo"
    INADIMPLENTE = "inadimplente"
    SUSPENSO = "suspenso"
    CANCELADO = "cancelado"

# Models Base
class ErrorResponse(BaseModel):
    error: str
    timestamp: str

class SuccessResponse(BaseModel):
    message: str
    data: Optional[Dict[str, Any]] = None

# Cliente Models
class ClienteBase(BaseModel):
    nome: str
    digisac_contact_id: str
    telefone: Optional[str] = None
    email: Optional[str] = None

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None

class ClienteResponse(ClienteBase):
    id: int
    created_at: Optional[datetime] = None
    status: Optional[str] = "ativo"
    
    class Config:
        from_attributes = True

# Cobrança Models
class CobrancaBase(BaseModel):
    cliente_id: int
    tipo: TipoCobranca
    mensagem: str
    agendar_para: Optional[date] = None

class CobrancaCreate(CobrancaBase):
    pass

class CobrancaBatchCreate(BaseModel):
    clientes_ids: List[int]
    tipo: TipoCobranca
    mensagem_padrao: str
    mensagens_customizadas: Optional[Dict[int, str]] = {}
    enviar_agora: bool = True
    agendar_para: Optional[date] = None

class CobrancaResponse(BaseModel):
    id: int
    cliente_id: int
    cliente_nome: str
    mensagem: str
    status: str
    data_envio: datetime
    erro_detalhe: Optional[str] = None

# Documento Models
class DocumentoSolicitacaoBase(BaseModel):
    cliente_id: int
    tipo_documento: TipoDocumento
    descricao: str
    dia_solicitacao: int = Field(..., ge=1, le=31)
    mes_referencia: Optional[str] = None

class DocumentoSolicitacaoCreate(DocumentoSolicitacaoBase):
    pass

class DocumentoBatchCreate(BaseModel):
    clientes_ids: List[int]
    tipo_documento: TipoDocumento
    descricao: str
    mensagem_padrao: str
    mensagens_customizadas: Optional[Dict[int, str]] = {}
    enviar_agora: bool = True

class DocumentoSolicitacaoResponse(BaseModel):
    id: int
    cliente_id: int
    cliente_nome: str
    tipo_documento: str
    descricao: str
    dia_solicitacao: int
    prox_data_solicitacao: Optional[date] = None
    documento_recebido: bool = False
    ativo: bool = True

# Template Models
class TemplateBase(BaseModel):
    nome: str
    template_text: str
    variaveis: Optional[str] = None

class TemplateCreate(TemplateBase):
    pass

class TemplateUpdate(BaseModel):
    template_text: Optional[str] = None
    variaveis: Optional[str] = None
    ativo: Optional[bool] = None

class TemplateResponse(TemplateBase):
    id: int
    ativo: bool = True
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Preview Models
class PreviewRequest(BaseModel):
    template_name: str
    cliente_id: int
    variaveis_extras: Optional[Dict[str, Any]] = {}

class PreviewResponse(BaseModel):
    cliente_nome: str
    mensagem_renderizada: str
    variaveis_utilizadas: Dict[str, Any]

# Batch Send Models
class BatchSendRequest(BaseModel):
    clientes_ids: List[int]
    tipo: TipoCobranca
    template_name: Optional[str] = None
    mensagem_padrao: Optional[str] = None
    mensagens_customizadas: Optional[Dict[int, str]] = {}
    enviar_agora: bool = True
    
    @validator('mensagem_padrao', 'template_name')
    def check_message_source(cls, v, values):
        if not v and not values.get('template_name'):
            raise ValueError('Forneça template_name ou mensagem_padrao')
        return v

class BatchSendResponse(BaseModel):
    total_clientes: int
    enviados: int
    erros: int
    detalhes: List[Dict[str, Any]]

# Dashboard Models
class DashboardStats(BaseModel):
    total_clientes: int
    clientes_ativos: int
    clientes_inadimplentes: int
    cobrancas_mes: int
    documentos_pendentes: int
    taxa_resposta: float

class ClienteListFilter(BaseModel):
    nome: Optional[str] = None
    status: Optional[StatusCliente] = None
    tem_cobranca_pendente: Optional[bool] = None
    tem_documento_pendente: Optional[bool] = None
    limit: int = 50
    offset: int = 0
