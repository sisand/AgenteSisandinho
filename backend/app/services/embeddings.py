from app.utils.logger import get_logger
from app.core.clients import get_weaviate_client
from typing import List, Dict, Any, Optional

logger = get_logger(__name__)

async def buscar_artigos_similares(query: str, limite: int = 5) -> List[Dict[str, Any]]:
    """
    Busca artigos similares à consulta usando embeddings.
    
    Args:
        query: Texto da consulta
        limite: Número máximo de resultados
        
    Returns:
        Lista de artigos similares
    """
    try:
        client = get_weaviate_client()
        if not client:
            logger.error("Cliente Weaviate não disponível")
            return []
        
        # Executar busca semântica
        logger.info(f"Buscando artigos similares para: '{query[:50]}...'")
        
        collection = client.collections.get("Article")
        results = collection.query.near_text(
            query=query,
            limit=limite,
            include_vector=False
        )
        
        # Processar resultados
        artigos = []
        for obj in results.objects:
            artigos.append({
                "id": obj.uuid,
                "titulo": obj.properties.get("title", "Sem título"),
                "conteudo": obj.properties.get("content", "Sem conteúdo"),
                "url": obj.properties.get("url", ""),
                "data_criacao": obj.properties.get("creation_date", "")
            })
            
        logger.info(f"Encontrados {len(artigos)} artigos similares")
        return artigos
    
    except Exception as e:
        logger.error(f"Erro ao buscar artigos similares: {str(e)}")
        return []

def buscar_embeddings(query: Optional[str] = None, limite: int = 50) -> List[Dict[str, Any]]:
    """
    Busca embeddings existentes no sistema.
    
    Args:
        query: Filtro opcional por texto
        limite: Número máximo de resultados
        
    Returns:
        Lista de embeddings
    """
    try:
        client = get_weaviate_client()
        if not client:
            logger.error("Cliente Weaviate não disponível")
            return []
            
        # Listar embeddings existentes
        collection = client.collections.get("Article")
        
        if query:
            results = collection.query.near_text(
                query=query,
                limit=limite
            )
        else:
            results = collection.query.fetch_objects(
                limit=limite
            )
        
        # Processar resultados
        embeddings = []
        for obj in results.objects:
            embeddings.append({
                "id": obj.uuid,
                "titulo": obj.properties.get("title", "Sem título"),
                "categoria": obj.properties.get("category", "Geral"),
                "url": obj.properties.get("url", ""),
                "tamanho": len(obj.properties.get("content", ""))
            })
            
        return embeddings
    
    except Exception as e:
        logger.error(f"Erro ao buscar embeddings: {str(e)}")
        return []
