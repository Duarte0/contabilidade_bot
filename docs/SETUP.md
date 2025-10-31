# Configuração Completa

## 1. Obter Credenciais Digisac
- Acesse https://seu_negocio.digisac.chat
- Gere token API em Configurações > API
- Configure webhook

## 2. Desenvolvimento Local
```bash
# Instalar ngrok
npm install -g ngrok

# Configurar ngrok
ngrok authtoken seu_token
ngrok http 5000