# app/routers/importacao.py

import logging
from fastapi import APIRouter, HTTPException, Query
from app.services.importador_artigos import importar_artigos_movidesk

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/artigos", tags=["Importação"])
async def importar_artigos_endpoint(reset_base: bool = Query(False, description="Se True, reseta a base no Weaviate antes de importar.")):
    """
    Inicia o processo de importação dos artigos do Movidesk para o Weaviate.

    - Se `reset_base=True`, a base existente será apagada e reimportada do zero.
    - Caso contrário, artigos novos serão adicionados e existentes mantidos.

    Retorna:
    - Status da importação
    - Totais de artigos importados e atualizados
    """
    try:
        logger.info("🚀 Endpoint de importação de artigos chamado")
        
        # Progress callback para log local
        async def progresso_callback(progresso):
            logger.info(f"📊 Progresso: {progresso}")
            # Futuro: enviar para WebSocket ou SSE se necessário.

        resultado = await importar_artigos_movidesk(
            progresso_callback=progresso_callback,
            reset_base=reset_base
        )
        return resultado

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ Erro no endpoint de importação: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
