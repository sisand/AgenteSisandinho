"""
Router para gerenciamento de sessões de chat
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from app.services.sessoes import (
    obter_ou_criar_sessao,
    listar_sessoes_usuario
)
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

class SessaoRequest(BaseModel):
    usuario_id: int
    criar_nova: Optional[bool] = False

class SessaoResponse(BaseModel):
    id: Optional[int] = None
    mensagem: str
    sucesso: bool

# Garantir ordem correta das rotas - específicas primeiro, genéricas depois
@router.get("/detalhe/{sessao_id}", name="obter_detalhe_sessao_alternativo")
async def obter_detalhe_sessao_alternativo(sessao_id: int):
    """
    Obtém detalhes de uma sessão via rota alternativa.
    Endpoint compatível com o frontend que acessa /api/sessoes/detalhe/{id}
    """
    try:
        logger.info(f"Obtendo detalhes da sessão {sessao_id} via endpoint /detalhe/{sessao_id}")
        sessao = obter_detalhes_sessao(sessao_id)
        if not sessao:
            logger.warning(f"Sessão {sessao_id} não encontrada no endpoint /detalhe/{sessao_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sessão {sessao_id} não encontrada"
            )
        logger.info(f"Detalhes da sessão {sessao_id} obtidos com sucesso via endpoint /detalhe/{sessao_id}")
        return sessao
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter detalhes da sessão {sessao_id} via endpoint /detalhe/{sessao_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter detalhes da sessão: {str(e)}"
        )

@router.get("/{sessao_id}/detalhes", name="obter_detalhes_sessao_por_id")
async def obter_detalhes_sessao_por_id(sessao_id: int):
    """
    Obtém detalhes de uma sessão.
    Endpoint compatível com o frontend que acessa /api/sessoes/{id}/detalhes
    """
    try:
        logger.info(f"Obtendo detalhes da sessão {sessao_id} via endpoint /{sessao_id}/detalhes")
        sessao = obter_detalhes_sessao(sessao_id)
        if not sessao:
            logger.warning(f"Sessão {sessao_id} não encontrada no endpoint /{sessao_id}/detalhes")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sessão {sessao_id} não encontrada"
            )
        logger.info(f"Detalhes da sessão {sessao_id} obtidos com sucesso via endpoint /{sessao_id}/detalhes")
        return sessao
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter detalhes da sessão {sessao_id} via endpoint /{sessao_id}/detalhes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter detalhes da sessão: {str(e)}"
        )

@router.get("/{sessao_id}")
async def obter_sessao(sessao_id: int):
    """
    Obtém detalhes de uma sessão.
    Endpoint principal para obter detalhes de sessão
    """
    try:
        logger.info(f"Obtendo detalhes da sessão {sessao_id}")
        sessao = obter_detalhes_sessao(sessao_id)
        if not sessao:
            logger.warning(f"Sessão {sessao_id} não encontrada")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sessão {sessao_id} não encontrada"
            )
        logger.info(f"Detalhes da sessão {sessao_id} obtidos com sucesso")
        return sessao
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter detalhes da sessão: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter detalhes da sessão: {str(e)}"
        )

@router.post("/criar", response_model=SessaoResponse)
async def criar_sessao(request: SessaoRequest):
    """
    Cria uma nova sessão ou retorna uma existente.
    """
    try:
        logger.info(f"Solicitação para criar sessão para usuário {request.usuario_id}")
        
        # Garantimos que a função seja chamada com await já que é assíncrona
        sessao_id = await obter_ou_criar_sessao(
            usuario_id=request.usuario_id,
            criar_nova=request.criar_nova
        )
        
        logger.info(f"Sessão {sessao_id} obtida/criada com sucesso para usuário {request.usuario_id}")
        return {
            "id": sessao_id,
            "mensagem": "Sessão criada com sucesso" if request.criar_nova else "Sessão obtida com sucesso",
            "sucesso": True
        }
    except Exception as e:
        logger.error(f"Erro ao criar sessão: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar sessão: {str(e)}"
        )

@router.post("/atualizar/{sessao_id}")
async def atualizar_atividade(sessao_id: int):
    """
    Atualiza o timestamp de última atividade de uma sessão.
    """
    try:
        sucesso = await atualizar_ultima_atividade(sessao_id)
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sessão {sessao_id} não encontrada"
            )
        return {"mensagem": f"Sessão {sessao_id} atualizada com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar sessão: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar sessão: {str(e)}"
        )

@router.post("/encerrar/{sessao_id}")
async def encerrar_sessao_endpoint(sessao_id: int):
    """
    Encerra uma sessão ativa.
    """
    try:
        sucesso = encerrar_sessao(sessao_id)
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sessão {sessao_id} não encontrada ou já encerrada"
            )
        return {"mensagem": f"Sessão {sessao_id} encerrada com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao encerrar sessão: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao encerrar sessão: {str(e)}"
        )

@router.get("/usuario/{usuario_id}")
async def listar_sessoes(usuario_id: int, incluir_inativas: bool = False):
    """
    Lista todas as sessões de um usuário.
    """
    try:
        sessoes = listar_sessoes_usuario(usuario_id, incluir_inativas)
        return {"sessoes": sessoes, "total": len(sessoes)}
    except Exception as e:
        logger.error(f"Erro ao listar sessões: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar sessões: {str(e)}"
        )
