# app/routers/importacao.py

import logging
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Depends, status

from app.core.security import get_api_key
# --- Importa tanto a função quanto a variável de estado do serviço ---
from app.services.importador_artigos import importar_artigos_movidesk, import_status

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/artigos", 
    tags=["Importação"], 
    status_code=status.HTTP_202_ACCEPTED,
    summary="Inicia a importação de artigos do Movidesk em segundo plano"
)
async def endpoint_importar_artigos(
    background_tasks: BackgroundTasks,
    reset_base: bool = Query(False, description="Se True, reseta a base no Weaviate antes de importar."),
    api_key: str = Depends(get_api_key)
):
    """
    Agenda a tarefa de importação de artigos para ser executada em segundo plano.
    
    - Retorna **202 Accepted** imediatamente se a tarefa for agendada.
    - Retorna **409 Conflict** se uma importação já estiver em andamento.
    """
    logger.info("🚀 Endpoint de importação de artigos chamado.")
    
    # --- VERIFICAÇÃO DA TRAVA ANTES DE AGENDAR A TAREFA ---
    if import_status["in_progress"]:
        logger.warning("Requisição de importação bloqueada pois uma já está em andamento.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Uma importação já está em andamento. Aguarde a conclusão da anterior antes de iniciar uma nova."
        )

    try:
        # Função de callback para logar o progresso no console do backend
        async def progresso_callback(progresso):
            logger.info(f"📊 Progresso da importação (background): {progresso}")

        # Agenda a tarefa se a trava estiver livre
        background_tasks.add_task(
            importar_artigos_movidesk,
            progresso_callback=progresso_callback,
            reset_base=reset_base
        )
        
        # Retorna a resposta imediata de sucesso para o frontend
        return {"message": "Solicitação de importação aceita. O processo foi iniciado em segundo plano."}
        
    except Exception as e:
        logger.error(f"❌ Erro ao agendar a tarefa de importação: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar a importação: {str(e)}")