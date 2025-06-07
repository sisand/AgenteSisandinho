from app.utils.database import get_supabase_client
from app.utils.logger import get_logger
from app.utils.time_utils import get_brazil_time

logger = get_logger(__name__)

# Migrado de backend\domain\feedback.py (assumindo)
def salvar_feedback(mensagem_id, tipo_feedback, comentario=None):
    """
    Salva o feedback do usuário sobre uma resposta.
    
    Args:
        mensagem_id: ID da mensagem à qual o feedback se refere
        tipo_feedback: Tipo de feedback (positivo, negativo)
        comentario: Comentário opcional
    """
    try:
        # Preservando a lógica original
        supabase = get_supabase_client()
        
        # Garantir dados corretos
        if not mensagem_id or not tipo_feedback:
            logger.warning("Tentativa de salvar feedback sem mensagem_id ou tipo")
            return False
            
        # Estrutura para insert
        dados = {
            "mensagem_id": mensagem_id,
            "tipo": tipo_feedback,
            "comentario": comentario or "",
            "data_registro": get_brazil_time().isoformat()
        }
        
        # Inserir no Supabase
        supabase.table("feedbacks").insert(dados).execute()
        logger.info(f"✅ Feedback {tipo_feedback} salvo com sucesso para mensagem {mensagem_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao salvar feedback: {str(e)}")
        return False
