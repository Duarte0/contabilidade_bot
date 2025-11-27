window.APP_CONFIG = {
    // Usa caminho relativo - o nginx faz proxy para o backend
    API_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8000/api'
        : '/api',  // Usa proxy do nginx quando via ngrok
    
    SEARCH_DEBOUNCE_MS: 400,
    
    DEFAULT_CLIENTE_LIMIT: 200,
    ATIVIDADES_LIMIT: 10,
    
    TOAST_DURATION_MS: 5000
};

// NGROK: Não precisa configurar mais nada!
// O nginx do frontend faz proxy automático para o backend

console.log('📡 API URL configurada:', window.APP_CONFIG.API_URL);
