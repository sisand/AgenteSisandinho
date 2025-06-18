# app/routers/artigos.py
"""
Router para gestão de artigos da base de conhecimento.
"""
from fastapi import APIRouter, Body, Path, Query, HTTPException, status
from typing import Dict, Any, List, Optional

# --- CORREÇÃO: Importa os modelos centralizados ---
from app.models.api import RequisicaoCriarArtigo, RequisicaoAtualizarArtigo

# Importa as funções de serviço assíncronas
from app.services.artigos import buscar_artigos, criar_artigo, atualizar_artigo, excluir_artigo

router = APIRouter()

# --- CORREÇÃO: Endpoints agora são async e usam os modelos corretos ---

@router.get("/", response_model=List[Dict[str, Any]])
async def listar_artigos_endpoint(
    query: Optional[str] = Query(None, description="Texto para busca semântica"),
    categoria: Optional[str] = Query(None, description="Filtrar por uma categoria específica"),
    limite: int = Query(50, description="Número máximo de resultados")
):
    """Lista artigos na base de conhecimento, com filtros opcionais."""
    artigos = await buscar_artigos(query=query, categoria=categoria, limite=limite)
    return artigos

@router.post("/", status_code=status.HTTP_201_CREATED)
async def criar_artigo_endpoint(artigo: RequisicaoCriarArtigo = Body(...)):
    """Adiciona um novo artigo à base de conhecimento."""
    resultado = await criar_artigo(
        titulo=artigo.titulo,
        conteudo=artigo.conteudo,
        categoria=artigo.categoria,
        url=artigo.url,
        resumo=artigo.resumo,
        id_externo=artigo.id_externo
    )
    if "error" in resultado:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=resultado["error"])
    return resultado

@router.put("/{artigo_id}")
async def atualizar_artigo_endpoint(
    artigo_id: str = Path(..., description="O UUID do artigo a ser atualizado"),
    artigo: RequisicaoAtualizarArtigo = Body(...)
):
    """Atualiza um artigo existente."""
    resultado = await atualizar_artigo(
        artigo_id=artigo_id,
        titulo=artigo.titulo,
        conteudo=artigo.conteudo,
        categoria=artigo.categoria,
        url=artigo.url,
        resumo=artigo.resumo
    )
    if "error" in resultado:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=resultado["error"])
    return resultado

@router.delete("/{artigo_id}")
async def remover_artigo_endpoint(
    artigo_id: str = Path(..., description="O UUID do artigo a ser removido")
):
    """Remove um artigo da base de conhecimento."""
    resultado = await excluir_artigo(artigo_id=artigo_id)
    if "error" in resultado:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=resultado["error"])
    return resultado
