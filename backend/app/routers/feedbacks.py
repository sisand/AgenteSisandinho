# app/routers/feedbacks.py
"""
Router para expor os endpoints de registro de feedback dos usuários.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Literal

# --- CORREÇÃO: Importa o modelo de dados do local centralizado ---
from app.models.api import RequisicaoFeedback

from app.services.feedbacks import salvar_feedback_db
from app.core.security import get_api_key

router = APIRouter()

# A classe de requisição foi removida daqui e movida para models/api.py

# --- CORREÇÃO: Nome da função e variável da requisição atualizados ---
@router.post("/", status_code=status.HTTP_201_CREATED)
def registrar_feedback(requisicao: RequisicaoFeedback, api_key: str = Depends(get_api_key)):
    """Endpoint para registrar o feedback de um usuário sobre uma resposta da IA."""
    sucesso = salvar_feedback_db(
        id_mensagem=requisicao.id_mensagem,
        tipo_feedback=requisicao.tipo_feedback
    )
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao salvar o feedback no banco de dados."
        )
    return {"status": "sucesso", "mensagem": "Feedback registrado com sucesso."}

