"""
Router para gestão de artigos da base de conhecimento.
"""

from fastapi import APIRouter, Body, Path, Query, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.services.artigos import buscar_artigos, criar_artigo, atualizar_artigo, excluir_artigo

router = APIRouter()

class ArtigoCreate(BaseModel):
    titulo: str = Field(..., description="Título do artigo")
    conteudo: str = Field(..., description="Conteúdo do artigo")
    categoria: str = Field("Geral", description="Categoria do artigo")
    url: Optional[str] = Field("", description="URL de origem")
    resumo: Optional[str] = Field("", description="Resumo do artigo")
    id_externo: Optional[str] = Field("", description="ID externo para rastreamento")

class ArtigoUpdate(BaseModel):
    titulo: Optional[str] = Field(None, description="Novo título")
    conteudo: Optional[str] = Field(None, description="Novo conteúdo")
    categoria: Optional[str] = Field(None, description="Nova categoria")
    url: Optional[str] = Field(None, description="Nova URL")
    resumo: Optional[str] = Field(None, description="Novo resumo")

@router.get("/")
async def listar_artigos(
    query: Optional[str] = Query(None, description="Texto para busca"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoria"),
    limite: int = Query(50, description="Número máximo de resultados")
):
    """
    Lista artigos na base de conhecimento, com opção de filtro por texto e categoria.
    """
    artigos = await buscar_artigos(
        query=query,
        categoria=categoria,
        limite=limite
    )
    return {"artigos": artigos}

@router.post("/")
async def adicionar_artigo(artigo: ArtigoCreate = Body(...)):
    """
    Adiciona um novo artigo à base de conhecimento.
    """
    resultado = await criar_artigo(
        titulo=artigo.titulo,
        conteudo=artigo.conteudo,
        categoria=artigo.categoria,
        url=artigo.url,
        resumo=artigo.resumo,
        id_externo=artigo.id_externo
    )
    
    if "error" in resultado:
        raise HTTPException(status_code=500, detail=resultado["error"])
        
    return resultado

@router.put("/{artigo_id}")
async def editar_artigo(
    artigo_id: str = Path(..., description="ID do artigo"),
    artigo: ArtigoUpdate = Body(...)
):
    """
    Atualiza um artigo existente.
    """
    resultado = await atualizar_artigo(
        artigo_id=artigo_id,
        titulo=artigo.titulo,
        conteudo=artigo.conteudo,
        categoria=artigo.categoria,
        url=artigo.url,
        resumo=artigo.resumo
    )
    
    if "error" in resultado:
        raise HTTPException(status_code=500, detail=resultado["error"])
        
    return resultado

@router.delete("/{artigo_id}")
async def remover_artigo(
    artigo_id: str = Path(..., description="ID do artigo")
):
    """
    Remove um artigo da base de conhecimento.
    """
    resultado = await excluir_artigo(artigo_id=artigo_id)
    
    if "error" in resultado:
        raise HTTPException(status_code=500, detail=resultado["error"])
        
    return resultado
