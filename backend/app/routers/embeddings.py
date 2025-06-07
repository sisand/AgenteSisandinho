from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from app.services.embeddings import buscar_embeddings, buscar_artigos_similares

router = APIRouter()

@router.get("/")
def listar_embeddings(
    query: Optional[str] = Query(None, description="Filtro por texto"),
    limite: int = Query(50, description="Número máximo de resultados")
):
    """
    Lista embeddings existentes no sistema.
    
    Args:
        query: Filtro de texto opcional
        limite: Número máximo de resultados
        
    Returns:
        Lista de embeddings encontrados
    """
    return buscar_embeddings(query, limite)

@router.get("/search")
async def pesquisar_artigos(
    query: str = Query(..., description="Texto para pesquisa semântica"),
    limite: int = Query(5, description="Número máximo de resultados")
):
    """
    Pesquisa artigos similares à consulta.
    
    Args:
        query: Texto para pesquisa semântica
        limite: Número máximo de resultados
        
    Returns:
        Lista de artigos similares
    """
    return await buscar_artigos_similares(query, limite)
