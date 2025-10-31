# Sistema de Cobrança Automática - Contabilidade

Sistema automatizado de cobrança para escritórios contábeis via WhatsApp com detecção de pagamentos em tempo real.

## Funcionalidades

- Cobrança automática via WhatsApp (Digisac API)
- Detecção automática de pagamentos através de webhook
- Templates de mensagem dinâmicos e personalizáveis
- Gestão de estado do cliente (ativo/inadimplente)
- Agendamento flexível com ajuste para feriados e finais de semana
- Sistema de relatórios e analytics
- API para integração com sistemas externos

## Tecnologias

- Python 3.8+
- Flask
- SQLite
- Digisac API


## Configuração Rápida

1. Clone o repositório
2. Configure variáveis de ambiente em `.env`
3. Execute `pip install -r requirements.txt`
4. Popule o banco com `python src/scripts/populate_db.py`
5. Inicie o webhook com `python src/services/webhook_handler.py`
6. Execute cobranças com `python src/main.py`

## Documentação

Consulte `docs/SETUP.md` para configuração detalhada do Digisac, webhook e ambiente de produção.
