# app/routers/chat.py
"""
Router para o endpoint principal de chat com o assistente inteligente.
"""

from fastapi import APIRouter, Body, Depends

# --- Importações dos Modelos Centralizados com os nomes em Português ---
from app.models.api import RequisicaoChat, RespostaChat

# --- Importações dos Módulos de Serviço e Segurança ---
from app.services.fluxo_chat import processar_pergunta
from app.core.security import get_api_key
from app.services.usuarios import obter_ou_criar_usuario

router = APIRouter()

# --- Endpoint de Chat com Nomenclatura Atualizada ---

@router.post(
    "/perguntar",
    response_model=RespostaChat,  # <-- ALTERADO AQUI
    summary="Faz uma pergunta para o assistente inteligente",
    description="""
O pipeline completo:
- Autentica a requisição via Chave de API.
- Obtém ou cria o usuário no banco de dados com base no e-mail.
- Classifica a intenção da pergunta.
- Decide se precisa de RAG (busca na base de conhecimento).
- Gera a resposta e coleta métricas de analytics.
- Salva toda a interação no banco de dados.
""",
    tags=["Chat"] # Adicionando tag para organizar a documentação da API
)
async def perguntar_chat(
    requisicao: RequisicaoChat = Body(...), # <-- ALTERADO AQUI (e o nome da variável para 'requisicao')
    api_key: str = Depends(get_api_key)
) -> RespostaChat: # <-- ALTERADO AQUI
    """
    Endpoint principal de interação com o assistente.
    """
    # Passo 1: Obter ou criar o usuário com base no e-mail
    # Usando a nova variável 'requisicao' para acessar os dados.
    id_usuario = obter_ou_criar_usuario(
        requisicao.email_usuario, 
        requisicao.nome_usuario
    )

    # Passo 2: Chamar o fluxo principal com os dados necessários
    resposta_processada = await processar_pergunta(
        id_usuario=id_usuario,
        pergunta=requisicao.pergunta
    )

    # Passo 3: Retornar a resposta, que já vem no formato correto de RespostaChat
    return resposta_processada
