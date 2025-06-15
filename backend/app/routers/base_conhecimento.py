# app/routers/base_conhecimento.py

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
import math

from app.core.clients import get_weaviate_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/artigos", summary="Listar Artigos com Busca e Paginação")
async def listar_artigos_base_conhecimento(
    termo_busca: Optional[str] = Query(None, description="Termo para buscar no título ou conteúdo dos artigos."),
    pagina: int = Query(1, ge=1, description="Número da página de resultados a ser retornada."),
    limite: int = Query(10, ge=1, le=100, description="Número de artigos por página.")
):
    """
    Busca artigos da base de conhecimento com suporte a busca por texto (BM25) e paginação.
    Retorna os artigos da página solicitada e informações de totalização.
    """
    try:
        client = get_weaviate_client()
        collection = client.collections.get("Article")
        
        # Calcula o 'offset' para a paginação
        offset = (pagina - 1) * limite

        # Define as propriedades que queremos retornar
        return_properties = ["title", "url", "resumo", "content"] # Adicionado 'content' para o expander

        response = None
        total_itens = 0

        # Se houver um termo de busca, usa a busca por palavra-chave (BM25)
        if termo_busca:
            logger.info(f"Buscando artigos com o termo: '{termo_busca}', página: {pagina}")
            response = collection.query.bm25(
                query=termo_busca,
                limit=limite,
                offset=offset,
                return_properties=return_properties
            )
            # A busca BM25 não retorna um total, então uma abordagem seria fazer um count separado
            # ou simplesmente não mostrar o total na busca, o que é mais performático.
            # Por simplicidade, não calcularemos o total exato durante a busca.
            total_paginas = pagina + 1 # Assumimos que há uma próxima página
            
        # Se não, apenas lista todos os artigos de forma paginada
        else:
            logger.info(f"Listando todos os artigos, página: {pagina}")
            
            # Para obter o total de artigos, usamos a função de agregação
            aggregate_result = collection.aggregate.over_all(total_count=True)
            total_itens = aggregate_result.total_count
            total_paginas = math.ceil(total_itens / limite) if total_itens > 0 else 1
            
            response = collection.query.fetch_objects(
                limit=limite,
                offset=offset,
                # NOTA: fetch_objects não aceita return_properties, ele retorna o objeto inteiro
            )
        
        # Extrai as propriedades dos objetos retornados
        artigos = [obj.properties for obj in response.objects]
        
        return {
            "artigos": artigos,
            "total_paginas": total_paginas,
            "total_itens": total_itens
        }

    except Exception as e:
        logger.error(f"❌ Erro ao listar artigos da base de conhecimento: {e}")
        # Lançar uma exceção HTTP para que o erro seja claro no frontend
        raise HTTPException(status_code=500, detail=str(e))