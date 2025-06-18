# app/main.py
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importa o router principal que agrega todas as outras rotas
from app.routers import api_router

# --- ALTERAÇÃO AQUI ---
# Importa apenas do clients e do novo cache
from app.core.clients import get_supabase_client, initialize_dynamic_clients
from app.core.cache import carregar_parametros_para_cache, carregar_prompts_para_cache, obter_parametro

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação (startup e shutdown)."""
    
    # 1. Carrega os parâmetros e prompts para o cache em memória.
    supabase_client = get_supabase_client()
    carregar_parametros_para_cache(supabase_client)
    carregar_prompts_para_cache(supabase_client)
    
    # 2. Configura o logging, usando o nível definido nos parâmetros já cacheados.
    log_level_str = obter_parametro("log_level", default="INFO").upper()
    logging.basicConfig(
        level=log_level_str,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logger = logging.getLogger(__name__)

    logger.info("🚀 Iniciando sequência de startup da aplicação...")
    logger.info(f"Nível de log configurado para: {log_level_str}")
    
    # 3. Inicializa outros clientes que possam depender dos parâmetros em cache.
    initialize_dynamic_clients()
    
    logger.info("✅ Aplicação iniciada e pronta para receber requisições!")
    yield
    logger.info("🔌 Encerrando a aplicação...")

# --- INICIALIZAÇÃO DA APLICAÇÃO ---
app = FastAPI(
    title="AgenteIA API",
    description="API do assistente virtual Sisandinho...",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
def read_root():
    return {"message": "🚀 API do AgenteIA está funcionando perfeitamente"}
