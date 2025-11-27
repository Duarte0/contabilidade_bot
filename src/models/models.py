"""
Modelos de dados simplificados - Sistema de Envio de Mensagens
Apenas os modelos essenciais para o funcionamento do sistema
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class Cliente:
    """Cliente/Contato do sistema"""
    id: int
    nome: str
    digisac_contact_id: str
    telefone: str = None
    email: str = None
    created_at: Optional[str] = None

@dataclass
class MessageTemplate:
    """Template de mensagem reutilizável"""
    id: int
    nome: str
    template_text: str
    variaveis: Optional[str]
    ativo: bool = True
    tipo: str = 'financeira'  
