from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
import logging

from .routes import clientes, cobrancas, templates, dashboard
from .models import ErrorResponse
from core.database import DatabaseManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="Sistema de Envio de Mensagens WhatsApp",
    description="API para envio de mensagens em lote via WhatsApp (Digisac)",
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens (ajuste para produção)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas
app.include_router(clientes.router, prefix="/api/clientes", tags=["Clientes"])
app.include_router(cobrancas.router, prefix="/api/cobrancas", tags=["Mensagens"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])

# Dependency para obter database
def get_db():
    db = DatabaseManager()
    try:
        yield db
    finally:
        pass

# Health check
@app.get("/health", tags=["System"])
async def health_check():
    """Verifica saúde do sistema"""
    try:
        db = DatabaseManager()
        db_status = db.health_check()
        
        return {
            "status": "healthy" if db_status else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected" if db_status else "disconnected",
            "version": "3.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )

# Root
@app.get("/", tags=["System"])
async def root():
    """Endpoint raiz"""
    return {
        "message": "Sistema de Envio de Mensagens WhatsApp API",
        "version": "3.0.0",
        "docs": "/api/docs",
        "health": "/health"
    }

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erro interno do servidor",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
