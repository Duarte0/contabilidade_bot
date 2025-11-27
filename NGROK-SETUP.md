# 🌐 Como Compartilhar o Sistema com Outras Pessoas

## Problema
Por padrão, o sistema só funciona no seu computador (localhost). Para que outras pessoas acessem, é necessário expor os serviços para a internet.

## Solução: Usando Ngrok

### Passo 1: Preparação

1. **Instale o ngrok** (se ainda não tiver):
   - Windows: Baixe em https://ngrok.com/download
   - Linux/Mac: `brew install ngrok` ou baixe manualmente

2. **Crie uma conta gratuita** em https://dashboard.ngrok.com/signup

3. **Configure seu token de autenticação**:
   ```bash
   ngrok config add-authtoken SEU_TOKEN_AQUI
   ```

### Passo 2: Inicie os Serviços

1. **Inicie o Docker Compose**:
   ```bash
   docker compose up -d
   ```

2. **Aguarde os serviços subirem** (cerca de 30 segundos)

### Passo 3: Crie os Túneis Ngrok

**Opção A: Manual (Recomendado para entender o processo)**

Abra **dois terminais diferentes**:

**Terminal 1 - Backend:**
```bash
ngrok http 8000
```

**Terminal 2 - Frontend:**
```bash
ngrok http 3000
```

**Opção B: Script Automático (Windows)**
```bash
./start-ngrok.bat
```

**Opção C: Script Automático (Linux/Mac)**
```bash
chmod +x start-ngrok.sh
./start-ngrok.sh
```

### Passo 4: Anote as URLs

Cada túnel ngrok vai mostrar algo assim:

```
Forwarding   https://abc123.ngrok.io -> http://localhost:3000
```

Você terá duas URLs:
- **Frontend**: `https://abc123.ngrok.io` (porta 3000)
- **Backend**: `https://xyz789.ngrok.io` (porta 8000)

### Passo 5: Configure o Frontend (IMPORTANTE!)

Edite o arquivo `frontend/app.js` e atualize a URL do backend:

```javascript
// ANTES (só funciona localmente)
const API_URL = 'http://localhost:8000/api';

// DEPOIS (funciona via ngrok)
const API_URL = 'https://xyz789.ngrok.io/api';  // Use a URL do seu backend ngrok
```

**OU** use a detecção automática já configurada

```javascript
const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000/api'
    : 'https://xyz789.ngrok.io/api';  // Substitua pela sua URL real
```

### Passo 6: Compartilhe

**Compartilhe APENAS a URL do frontend** com outras pessoas:
```
https://abc123.ngrok.io
```

Elas poderão acessar normalmente pelo navegador!

## 🔒 Solução Melhorada: URL Dinâmica

Se você já aplicou a atualização automática no `app.js`, o frontend detecta automaticamente se está rodando via ngrok ou localhost. Neste caso:

1. Certifique-se de que AMBOS os túneis estão rodando
2. Compartilhe a URL do frontend
3. A comunicação com o backend será automática!

## ⚠️ Limitações do Ngrok (Plano Gratuito)

- URLs mudam a cada vez que você inicia o ngrok
- Limite de conexões simultâneas
- Túneis expiram após 2 horas de inatividade
- Latência pode ser maior

## 🚀 Solução para Produção

Para uso permanente, considere hospedar em um servidor:

### Opções de Deploy:
1. **Heroku**: Deploy gratuito de Docker
2. **Railway**: Deploy simples com Docker
3. **AWS/Azure/Google Cloud**: Mais controle e escalabilidade
4. **DigitalOcean**: VPS com Docker

### Vantagens:
- URL permanente e personalizada
- Melhor performance
- Sem limite de tempo
- Mais profissional

## 📝 Checklist Rápido

- [ ] Docker containers rodando (`docker compose ps`)
- [ ] Ngrok instalado e configurado
- [ ] Dois túneis ngrok ativos (frontend e backend)
- [ ] URL do backend atualizada no frontend
- [ ] CORS configurado para aceitar requisições externas
- [ ] URL do frontend compartilhada com usuários

## 🔧 Troubleshooting

### "Requisição bloqueada por CORS"
✅ Já corrigido! O backend está configurado para aceitar todas as origens.

### "Cannot connect to backend"
- Verifique se o túnel do backend está ativo
- Confirme que a URL no `app.js` está correta
- Teste a URL do backend diretamente: `https://xyz789.ngrok.io/health`

### "Túnel expira rapidamente"
- Use uma conta ngrok autenticada (aumenta o tempo)
- Considere o plano pago do ngrok para túneis permanentes
- Ou migre para uma solução de hospedagem

### "Frontend carrega mas não mostra dados"
- Abra o Console do navegador (F12)
- Verifique se há erros de conexão
- Confirme que as URLs dos túneis estão corretas

## 📞 Suporte

Se tiver problemas, verifique:
1. Logs do Docker: `docker compose logs`
2. Console do navegador (F12)
3. Dashboard do ngrok: http://localhost:4040

---

**Dica Pro**: Para evitar reconfigurar toda vez, considere usar variáveis de ambiente ou um arquivo de configuração que pode ser atualizado facilmente.
