# app/services/feedbacks.py
import logging
from typing import Literal
from app.core.clients import get_supabase_client
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def salvar_feedback_db(id_mensagem: int, tipo_feedback: Literal["positivo", "negativo"]) -> bool:
    """Salva um feedback (positivo ou negativo) para uma mensagem específica."""
    try:
        supabase = get_supabase_client()
        
        # --- CORREÇÃO AQUI: Usa 'mensagem_id' para corresponder ao seu banco de dados ---
        dados_feedback = {
            "mensagem_id": id_mensagem,
            "tipo": tipo_feedback,
            "criado_em": datetime.now(timezone.utc).isoformat()
        }
        
        supabase.table("feedbacks").insert(dados_feedback).execute()
        
        logger.info(f"Feedback '{tipo_feedback}' salvo para a mensagem ID {id_mensagem}.")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar feedback para a mensagem ID {id_mensagem}: {e}")
        return False
