# app/main.py

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from dotenv import load_dotenv # REMOVER ESTA LINHA
import os
from datetime import datetime

# Importa as configurações do Pydantic-settings (que já carrega o .env)
from app.core.config import get_settings # Adicionar esta importação

# Importa os módulos da aplicação
from app.core.clients import get_supabase_client, initialize_dynamic_clients
from app.core.dynamic_config import carregar_parametros_do_banco, obter_parametro
from app.routers import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Código que roda na inicialização ---
        
    # 1. Cria o cliente essencial (Supabase)
    supabase = get_supabase_client()
    
    # 2. Carrega os parâmetros do banco (agora de forma síncrona)
    carregar_parametros_do_banco(supabase)

       # 3. Com os parâmetros em memória, configura o logging dinamicamente
    log_level_str = obter_parametro("log_level", "INFO").upper()
    #log_level_str = "DEBUG"

    #log_level_from_db = obter_parametro("log_level", "INFO").upper()
    #print(f"--- ATENÇÃO: Nível de log forçado para DEBUG (valor no banco: {log_level_from_db}) ---") 

    logging.basicConfig(
        level=log_level_str,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True
    )
    # --- ADICIONE ESTA LINHA ---
    # Define que o logger específico da biblioteca 'httpx' só deve mostrar logs
    # a partir do nível WARNING, ignorando os de INFO e DEBUG.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Iniciando sequência de startup da aplicação...")
    logger.info(f"Nível de log configurado para: {log_level_str}")

    # 4. Inicializa os outros clientes que dependem dos parâmetros
    initialize_dynamic_clients()
    
    logger.info("✅ Aplicação iniciada e pronta para receber requisições!")
    
    yield # A aplicação fica rodando aqui
    
    # --- Código que roda no encerramento ---
    logger.info("🔌 Encerrando a aplicação...")


# Cria a aplicação FastAPI, registrando o lifespan
app = FastAPI(
    title="AgenteIA API",
    description="API do assistente virtual Sisandinho...",
    version="1.0.0",
    lifespan=lifespan
)

# Configurando CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrando todos os routers
app.include_router(api_router)


# Endpoint de Health Check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Endpoint raiz
@app.get("/api")
def read_root():
    return {"message": "🚀 API do AgenteIA está funcionando perfeitamente"}