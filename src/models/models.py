from dataclasses import dataclass
from typing import Optional

@dataclass
class Cliente:
    id: int
    nome: str
    digisac_contact_id: str
    telefone: str = None
    email: str = None
    created_at: Optional[str] = None

@dataclass
class ContaFixa:
    id: int
    cliente_id: int
    descricao: str
    valor: float
    dia_vencimento: int
    ativo: bool = True
    
    from dataclasses import dataclass
from typing import Optional

@dataclass
class Cliente:
    id: int
    nome: str
    digisac_contact_id: str
    telefone: str = None
    email: str = None

@dataclass
class ContaFixa:
    id: int
    cliente_id: int
    descricao: str
    valor: float
    dia_vencimento: int
    ativo: bool = True

@dataclass
class ClienteStatus:
    id: int
    cliente_id: int
    status: str  # ativo, inadimplente, suspenso
    last_payment_date: Optional[str]
    payment_preferences: Optional[str]
    dias_tolerancia: int = 0

@dataclass
class MessageTemplate:
    id: int
    nome: str
    template_text: str
    variaveis: Optional[str]
    ativo: bool = True
    
@dataclass
class ContaConfig:
    id: int
    conta_id: int
    frequencia: str
    prox_data_cobranca: Optional[str] = None
    feriados_ajustar: bool = True