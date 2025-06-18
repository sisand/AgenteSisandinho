from fastapi import APIRouter, Depends

from app.models.api import RequisicaoChat, RespostaChat
from app.services.fluxo_chat import processar_pergunta
from app.services.usuarios import obter_ou_criar_usuario
from app.core.security import get_api_key

router = APIRouter()

@router.post("/perguntar", response_model=RespostaChat)
async def perguntar_chat(
    requisicao: RequisicaoChat, 
    api_key: str = Depends(get_api_key)
):
    """Endpoint de chat que retorna uma resposta JSON completa."""
    id_usuario = obter_ou_criar_usuario(requisicao.email_usuario, requisicao.nome_usuario)
    
    resposta_completa = await processar_pergunta(
        id_usuario=id_usuario,
        pergunta=requisicao.pergunta
    )
    
    return resposta_completa
