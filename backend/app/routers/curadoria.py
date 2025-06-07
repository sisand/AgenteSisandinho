"""
Router para o sistema de curadoria de conteúdo.
"""

from fastapi import APIRouter, Body, Path, Query, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.services.curadoria import salvar_curadoria, listar_curadorias, avaliar_curadoria

router = APIRouter()

class CuradoriaCreate(BaseModel):
    ticket_id: str = Field(..., description="ID do ticket no Movidesk")
    curador: str = Field(..., description="Nome do curador")
    pergunta: str = Field(..., description="Pergunta do cliente")
    resposta: str = Field(..., description="Resposta curada")
    metadados: Optional[Dict[str, Any]] = Field(None, description="Dados adicionais")

class AvaliacaoCuradoria(BaseModel):
    avaliacao: str = Field(..., description="Avaliação (aprovado/rejeitado)")
    comentario: Optional[str] = Field(None, description="Comentário opcional")

@router.post("/")
async def criar_curadoria(curadoria: CuradoriaCreate = Body(...)):
    """
    Salva uma nova curadoria de conteúdo.
    """
    resultado = await salvar_curadoria(
        ticket_id=curadoria.ticket_id,
        curador=curadoria.curador,
        pergunta=curadoria.pergunta,
        resposta=curadoria.resposta,
        metadados=curadoria.metadados
    )
    
    if "error" in resultado:
        raise HTTPException(status_code=500, detail=resultado["error"])
        
    return resultado

@router.get("/")
async def obter_curadorias(
    status: Optional[str] = Query(None, description="Filtro por status"),
    curador: Optional[str] = Query(None, description="Filtro por curador"),
    limite: int = Query(50, description="Número máximo de resultados")
):
    """
    Lista curadorias existentes com opção de filtro.
    """
    curadorias = await listar_curadorias(
        status=status,
        curador=curador,
        limite=limite
    )
    
    return {"curadorias": curadorias}

@router.put("/{curadoria_id}/avaliar")
async def avaliar(
    curadoria_id: int = Path(..., description="ID da curadoria"),
    avaliacao: AvaliacaoCuradoria = Body(...)
):
    """
    Avalia uma curadoria existente.
    """
    resultado = await avaliar_curadoria(
        curadoria_id=curadoria_id,
        avaliacao=avaliacao.avaliacao,
        comentario=avaliacao.comentario
    )
    
    if "error" in resultado:
        raise HTTPException(status_code=500, detail=resultado["error"])
        
    return resultado
