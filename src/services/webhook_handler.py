from datetime import datetime
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)

import hashlib
import hmac
from flask import Flask, request, jsonify
from core.database import DatabaseManager
from core.config import DATABASE_PATH, WEBHOOK_SECRET

app = Flask(__name__)
db = DatabaseManager(DATABASE_PATH)

def verify_webhook_signature(payload, signature):
    if not WEBHOOK_SECRET or not signature:
        return True
    
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)

@app.route('/webhook/digisac', methods=['POST'])
def handle_digisac_webhook():
    print("DEBUG - Webhook recebido")
    
    signature = request.headers.get('X-Digisac-Signature')
    
    if not verify_webhook_signature(request.get_data(), signature):
        return jsonify({'error': 'Assinatura inválida'}), 401
    
    data = request.json
    
    event_type = data.get('event')
    print(f"DEBUG - Event type: {event_type}")
    
    if event_type in ['message.received', 'message.created']:  
        _process_message_received(data)
    elif event_type == 'message.updated':
        _process_message_updated(data)
    else:
        print(f"DEBUG - Event type desconhecido: {event_type}")
    
    return jsonify({'status': 'processed'})

def _process_message_received(data):
    message = data.get('data', {})
    contact_id = message.get('contactId')
    text = message.get('text', '').lower()
    
    print(f"DEBUG - Contact ID recebido: {contact_id}")
    print(f"DEBUG - Mensagem: {text}")
    
    cliente = db.get_cliente_by_contact_id(contact_id)
    
    if not cliente:
        print(f"DEBUG - Cliente não encontrado para contact_id: {contact_id}")
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nome, digisac_contact_id FROM clientes')
            todos_clientes = cursor.fetchall()
            print("DEBUG - Clientes no banco:")
            for nome, contact in todos_clientes:
                print(f"  {nome}: {contact}")
        return
    
    print(f"DEBUG - Cliente encontrado: {cliente.nome}")
    
    pagamento_keywords = ['paguei', 'pagamento', 'pago', 'transferência', 'transferi', 'depositei']
    
    if any(f" {keyword} " in f" {text} " for keyword in pagamento_keywords):
        print(f"DEBUG - Pagamento detectado para {cliente.nome}")
        _registrar_pagamento_detectado(cliente.id, text)

def _process_message_updated(data):
    pass

def _get_valor_conta_cliente(cliente_id):
    """Busca o valor da conta ativa do cliente"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT valor FROM contas_fixas 
            WHERE cliente_id = ? AND ativo = 1 
            ORDER BY id DESC LIMIT 1
        ''', (cliente_id,))
        result = cursor.fetchone()
        return result[0] if result else None

def _registrar_pagamento_detectado(cliente_id, mensagem):
    valor = _get_valor_conta_cliente(cliente_id)
    
    if not valor:
        print(f"ERRO: Não encontrou valor para cliente {cliente_id}")
        return
    
    db.registrar_pagamento(
        cliente_id=cliente_id,
        valor=valor,
        data_pagamento=datetime.now().strftime('%Y-%m-%d'),
        mes_referencia=datetime.now().strftime('%Y-%m')
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)