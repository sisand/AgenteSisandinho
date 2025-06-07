from fastapi import APIRouter
from app.services.feedback import salvar_feedback

router = APIRouter()

@router.post("/")
def registrar_feedback(feedback_data: dict):
    """
    Salva feedback do usuário sobre uma resposta.
    
    Parâmetros:
        feedback_data: Objeto com campos:
            - mensagem_id: ID da mensagem
            - feedback: tipo de feedback (positivo, negativo)
            - comentario: comentário opcional
    """
    resultado = salvar_feedback(
        feedback_data.get("mensagem_id"), 
        feedback_data.get("feedback"),
        feedback_data.get("comentario")
    )
    return {"success": resultado}

@router.get("/")
def listar_feedbacks():
    """
    Endpoint temporário para listar feedbacks.
    """
    # Implementação simplificada - substitua pela lógica real
    return [
        {"id": 1, "tipo": "positivo", "comentario": "Muito bom!"},
        {"id": 2, "tipo": "negativo", "comentario": "Precisa melhorar."}
    ]