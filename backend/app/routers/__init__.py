from fastapi import APIRouter

from app.routers import (
    chat,
    sessoes,
    usuarios,
    prompts,
    artigos,
    movidesk,
    embeddings,
    curadoria,
    importacao,
    status,
    base_conhecimento,
    feedbacks,
    metricas
)

api_router = APIRouter()

# 🔥 Registrando todos os routers
api_router.include_router(chat.router, prefix="/api/chat", tags=["Chat Inteligente"])
api_router.include_router(sessoes.router, prefix="/api/sessoes", tags=["Sessões"])
api_router.include_router(usuarios.router, prefix="/api/usuarios", tags=["Usuários"])
api_router.include_router(prompts.router, prefix="/api/prompts", tags=["Prompts"])
api_router.include_router(artigos.router, prefix="/api/artigos", tags=["Artigos"])
api_router.include_router(feedbacks.router, prefix="/api/feedback", tags=["Feedback"])
api_router.include_router(movidesk.router, prefix="/api/movidesk", tags=["Movidesk"])
api_router.include_router(embeddings.router, prefix="/api/embeddings", tags=["Embeddings"])
api_router.include_router(curadoria.router, prefix="/api/curadoria", tags=["Curadoria"])
api_router.include_router(importacao.router, prefix="/api/importacao", tags=["Importação"])
api_router.include_router(metricas.router, prefix="/api/metrics", tags=["Métricas"])
api_router.include_router(status.router, prefix="/api/status", tags=["Status"])
api_router.include_router(base_conhecimento.router, prefix="/api/base-conhecimento", tags=["Base de Conhecimento"])
