from fastapi import APIRouter, Body
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.services.fluxo_chat import processar_pergunta


router = APIRouter()


from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class RequisicaoPerguntaChat(BaseModel):
    pergunta: str = Field(..., description="Texto da pergunta do usuário")
    usuario_id: Optional[int] = Field(None, description="ID do usuário")
    contexto_anterior: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Histórico anterior no formato [{'role': 'user' ou 'assistant', 'content': 'texto'}]"
    )
    temperatura: float = Field(
        default=0.7,
        description="Criatividade da resposta (0.0 = resposta exata, 1.0 = mais criativa)"
    )


class RespostaPerguntaChat(BaseModel):
    resposta: str = Field(..., description="Texto da resposta gerada")
    categoria: str = Field(..., description="Categoria detectada: fiscal, oficina, financeiro, etc.")
    artigos: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Artigos utilizados se houve busca (RAG). Caso não, retorna lista vazia."
    )
    tempo_processamento: float = Field(..., description="Tempo total de processamento")
    prompt_usado: str = Field(..., description="Prompt completo enviado para o modelo")



@router.post(
    "/perguntar",
    response_model=RespostaPerguntaChat,
    summary="Faz uma pergunta para o assistente inteligente",
    description="""
O pipeline classifica a pergunta, decide se precisa consultar a base de conhecimento (RAG)
ou se pode gerar a resposta diretamente com o modelo fine-tune.

Controla histórico, persistência no Supabase e gera resposta.
"""
)
async def perguntar_chat(request: RequisicaoPerguntaChat = Body(...)):
    resposta = await processar_pergunta(
        usuario_id=request.usuario_id,
        pergunta=request.pergunta
    )
    return resposta
