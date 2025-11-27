# 📱 Sistema Configurado para Compartilhamento

## ✅ O Que Foi Feito

1. **CORS configurado** no backend para aceitar requisições de qualquer origem
2. **Detecção automática de URL** no frontend
3. **Arquivo de configuração** (`config.js`) para fácil customização
4. **Scripts de inicialização** do ngrok criados
5. **Documentação completa** em múltiplos arquivos

---

## 🎯 Como Usar Agora (Passo a Passo Simples)

### Opção 1: Localhost (Apenas você)
✅ **Já funciona!** Apenas acesse: `http://localhost:3000`

---

### Opção 2: Ngrok (Compartilhar com outros)

#### Passo 1: Inicie os Túneis
Abra **2 terminais** e execute:

**Terminal 1:**
```bash
ngrok http 8000
```
Anote a URL (ex: `https://abc123.ngrok-free.app`)

**Terminal 2:**
```bash
ngrok http 3000
```
Anote a URL (ex: `https://xyz789.ngrok-free.app`)

#### Passo 2: Configure o Backend
Edite `frontend/config.js` (linha 14):
```javascript
window.APP_CONFIG.API_URL = 'https://abc123.ngrok-free.app/api';
```
⚠️ **Use a URL do Terminal 1 (porta 8000)**

#### Passo 3: Reinicie o Frontend
```bash
docker compose restart frontend
```

#### Passo 4: Compartilhe
Envie a **URL do Terminal 2** (frontend) para outras pessoas:
```
https://xyz789.ngrok-free.app
```

---

## 🔍 Verificar se Está Funcionando

1. Abra a URL do frontend no navegador
2. Pressione **F12** → aba **Console**
3. Procure por:
   ```
   📡 API URL: https://...
   ```
4. A URL deve ser a do ngrok (não localhost)

---

## 📁 Arquivos Importantes

- **`frontend/config.js`** → Configure a URL do backend aqui
- **`QUICK-START-NGROK.md`** → Guia rápido de 5 minutos
- **`NGROK-SETUP.md`** → Documentação completa com troubleshooting
- **`start-ngrok.bat`** (Windows) → Script automático para iniciar túneis
- **`start-ngrok.sh`** (Linux/Mac) → Script automático para iniciar túneis

---

## 🎬 Comandos Úteis

```bash
# Ver status dos containers
docker compose ps

# Ver logs do backend
docker compose logs backend -f

# Ver logs do frontend
docker compose logs frontend -f

# Reiniciar tudo
docker compose restart

# Parar tudo
docker compose down

# Reconstruir e iniciar
docker compose up -d --build
```

---

## ⚡ Dicas Importantes

### Para Localhost (Desenvolvimento)
✅ Nada precisa ser configurado
✅ Acesse: `http://localhost:3000`

### Para Ngrok (Compartilhar)
⚠️ As URLs do ngrok mudam toda vez que você reinicia
⚠️ Você precisa atualizar o `config.js` sempre
⚠️ Compartilhe sempre a URL do **frontend** (porta 3000)

### Para Produção (Permanente)
💡 Considere hospedar em:
- **Heroku** (grátis para começar)
- **Railway** (deploy simples)
- **AWS/Azure/GCP** (mais controle)
- **DigitalOcean** (VPS barato)

---

## 🆘 Problemas?

### Backend não responde
```bash
# Verifique se está rodando
docker compose ps

# Veja os logs
docker compose logs backend

# Reinicie
docker compose restart backend
```

### Frontend não carrega dados
1. Abra o Console (F12)
2. Procure por erros em vermelho
3. Verifique se a URL do backend está correta no `config.js`
4. Teste a URL diretamente: `https://seu-backend.ngrok-free.app/health`

### Ngrok não funciona
```bash
# Instale ou atualize
# Windows: baixe em https://ngrok.com/download
# Mac: brew install ngrok
# Linux: snap install ngrok

# Configure o token
ngrok config add-authtoken SEU_TOKEN
```

---

## 📞 Testando

### Teste Local
```bash
curl http://localhost:8000/health
```

### Teste Ngrok
```bash
curl https://seu-backend.ngrok-free.app/health
```

Resposta esperada:
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "3.0.0"
}
```

---

## 🎉 Pronto!

Agora seu sistema pode ser acessado por qualquer pessoa através da URL do ngrok!

**Lembre-se:**
- URLs do ngrok são temporárias (mudam ao reiniciar)
- Para uso permanente, considere hospedar em um servidor
- Mantenha seu token do Digisac seguro (arquivo `.env`)

---

**Documentação Adicional:**
- `QUICK-START-NGROK.md` - Guia de 5 minutos
- `NGROK-SETUP.md` - Documentação completa
- `README.md` - Informações gerais do projeto
