# app/main.py
"""
Ponto de entrada principal da aplicação FastAPI.
Gerencia o ciclo de vida e a inclusão de todas as rotas da API.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importa o router principal que agrega todas as outras rotas
from app.routers import api_router

# --- CORREÇÃO: Importa apenas do clients e do novo cache ---
from app.core.clients import get_supabase_client, initialize_dynamic_clients
from app.core.cache import carregar_parametros_para_cache, carregar_prompts_para_cache, obter_parametro

# --- GERENCIADOR DE CICLO DE VIDA (LIFESPAN) ---
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
    # Reduz o "ruído" de logs de bibliotecas HTTP.
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
    title="Sisandinho - Assistente IA API",
    description="API do assistente virtual Sisandinho, com RAG e IA generativa.",
    version="1.0.0",
    lifespan=lifespan # Associa o gerenciador de ciclo de vida à aplicação
)

# Configura o CORS para permitir requisições de qualquer origem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui todas as rotas definidas no seu arquivo routers/__init__.py
app.include_router(api_router)

# Endpoint raiz para verificação de status (health check)
@app.get("/")
def read_root():
    return {"message": "🚀 API do AgenteIA está funcionando perfeitamente"}
