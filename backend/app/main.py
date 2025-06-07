import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from dotenv import load_dotenv

# Chame esta função AQUI, o mais cedo possível, antes de qualquer outra importação
# do seu próprio projeto que possa depender de variáveis de ambiente.
load_dotenv()

# Agora, o resto das suas importações e a configuração do app
from app.core.clients import get_supabase_client
from app.core.config import settings
from app.routers import api_router
# 🔥 Setup de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.main")


# 🔧 Log das configurações carregadas
logger.info("Configurações importadas de config.py:")
logger.info(f"SUPABASE_URL: {settings.SUPABASE_URL}")
logger.info(f"Ambiente: {settings.ENVIRONMENT}")


# 🚀 Criando a aplicação FastAPI
app = FastAPI(
    title="AgenteIA API",
    description="API do assistente virtual Sisandinho, utilizando IA + RAG + OpenAI + Weaviate + Supabase.",
    version="1.0.0"
)


# 🌐 Configurando CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🔥 Em produção, restrinja para ["https://seusite.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 🔗 Registrando todos os routers centralizados no __init__.py dos routers
app.include_router(api_router)


# ✅ Health Check
@app.get("/api/health")
async def health_check():
    """
    ✅ Verifica se o servidor está funcionando e se os serviços externos estão conectados.
    """
    health_info = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }

    # 🔍 Supabase
    try:
        supabase = get_supabase_client()
        if supabase:
            health_info["services"]["supabase"] = "connected"
        else:
            health_info["services"]["supabase"] = "not initialized"
            health_info["status"] = "degraded"
    except Exception as e:
        health_info["services"]["supabase"] = f"error: {str(e)}"
        health_info["status"] = "degraded"

    # 🔍 OpenAI
    import os
    if os.getenv("OPENAI_API_KEY"):
        health_info["services"]["openai"] = "key configured"
    else:
        health_info["services"]["openai"] = "key missing"
        health_info["status"] = "degraded"

    return health_info


# 🔧 Diagnóstico de Rotas
@app.get("/api/debug/routes", include_in_schema=False)
async def list_all_routes():
    """🔧 Lista todas as rotas registradas na aplicação."""
    routes = []
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name if hasattr(route, "name") else None
            })
    logger.info(f"Total de rotas registradas: {len(routes)}")
    return {"total_routes": len(routes), "routes": routes}


# 🏠 Endpoint raiz
@app.get("/api")
def read_root():
    return {"message": "🚀 API do AgenteIA está funcionando perfeitamente"}
