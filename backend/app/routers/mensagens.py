from fastapi import APIRouter, Path, Query, Body, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.services.mensagens import salvar_mensagem, buscar_mensagens_sessao

router = APIRouter()

class MensagemCreate(BaseModel):
    usuario_id: int
    sessao_id: int
    pergunta: str
    resposta: str
    metadados: Optional[Dict[str, Any]] = None

@router.get("/{sessao_id}")
def get_mensagens_sessao(
    sessao_id: int = Path(..., description="ID da sessão para buscar mensagens")
):
    """
    Busca todas as mensagens de uma sessão.
    
    Args:
        sessao_id: ID da sessão
        
    Returns:
        Lista de mensagens da sessão
    """
    mensagens = buscar_mensagens_sessao(sessao_id)
    return {"mensagens": mensagens}

@router.post("/")
def criar_mensagem(mensagem: MensagemCreate = Body(...)):
    """
    Cria uma nova mensagem.
    
    Args:
        mensagem: Dados da mensagem
        
    Returns:
        Status da operação
    """
    success = salvar_mensagem(
        mensagem.usuario_id,
        mensagem.sessao_id,
        mensagem.pergunta,
        mensagem.resposta,
        mensagem.metadados
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao salvar mensagem")
    
    return {"status": "success", "message": "Mensagem salva com sucesso"}
