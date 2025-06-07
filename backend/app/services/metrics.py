"""
Serviço de métricas.
Coleta e analisa métricas de uso e desempenho do sistema.
"""

from typing import Dict, Any, List
import datetime
from app.utils.logger import get_logger
from app.utils.database import get_supabase_client
from app.utils.time_utils import get_brazil_time

logger = get_logger(__name__)

async def coletar_metricas_gerais() -> Dict[str, Any]:
    """
    Coleta métricas gerais sobre o uso do sistema.
    
    Returns:
        Dicionário com métricas gerais
    """
    try:
        supabase = get_supabase_client()
        metrics = {}
        
        # Total de usuários
        users_result = supabase.table("usuarios").select("count", count="exact").execute()
        metrics["total_usuarios"] = users_result.count if hasattr(users_result, "count") else 0
        
        # Total de sessões
        sessions_result = supabase.table("sessoes").select("count", count="exact").execute()
        metrics["total_sessoes"] = sessions_result.count if hasattr(sessions_result, "count") else 0
        
        # Total de mensagens
        messages_result = supabase.table("mensagens").select("count", count="exact").execute()
        metrics["total_mensagens"] = messages_result.count if hasattr(messages_result, "count") else 0
        
        # Total de feedbacks
        feedbacks_result = supabase.table("feedbacks").select("count", count="exact").execute()
        metrics["total_feedbacks"] = feedbacks_result.count if hasattr(feedbacks_result, "count") else 0
        
        # Sessões ativas hoje
        today = get_brazil_time().date().isoformat()
        active_sessions_result = (
            supabase.table("sessoes")
            .select("count", count="exact")
            .gte("ultima_atividade", f"{today}T00:00:00")
            .execute()
        )
        metrics["sessoes_ativas_hoje"] = active_sessions_result.count if hasattr(active_sessions_result, "count") else 0
        
        logger.info("Métricas gerais coletadas com sucesso")
        return metrics
        
    except Exception as e:
        logger.error(f"Erro ao coletar métricas gerais: {str(e)}")
        return {"error": str(e)}

async def coletar_metricas_feedback() -> Dict[str, Any]:
    """
    Coleta métricas de feedback.
    
    Returns:
        Dicionário com métricas de feedback
    """
    try:
        supabase = get_supabase_client()
        metrics = {}
        
        # Total de feedbacks
        feedbacks_result = supabase.table("feedbacks").select("count", count="exact").execute()
        total_feedbacks = feedbacks_result.count if hasattr(feedbacks_result, "count") else 0
        metrics["total_feedbacks"] = total_feedbacks
        
        if total_feedbacks > 0:
            # Feedbacks positivos
            positive_result = (
                supabase.table("feedbacks")
                .select("count", count="exact")
                .eq("tipo", "positivo")
                .execute()
            )
            positive_count = positive_result.count if hasattr(positive_result, "count") else 0
            metrics["feedbacks_positivos"] = positive_count
            
            # Feedbacks negativos
            negative_result = (
                supabase.table("feedbacks")
                .select("count", count="exact")
                .eq("tipo", "negativo")
                .execute()
            )
            negative_count = negative_result.count if hasattr(negative_result, "count") else 0
            metrics["feedbacks_negativos"] = negative_count
            
            # Calcular porcentagens
            metrics["percentual_positivos"] = round((positive_count / total_feedbacks) * 100, 2)
            metrics["percentual_negativos"] = round((negative_count / total_feedbacks) * 100, 2)
        
        logger.info("Métricas de feedback coletadas com sucesso")
        return metrics
        
    except Exception as e:
        logger.error(f"Erro ao coletar métricas de feedback: {str(e)}")
        return {"error": str(e)}

async def coletar_metricas_desempenho() -> Dict[str, Any]:
    """
    Coleta métricas de desempenho do sistema.
    
    Returns:
        Dicionário com métricas de desempenho
    """
    try:
        supabase = get_supabase_client()
        metrics = {}
        
        # Últimos 100 tempos de resposta
        result = (
            supabase.table("mensagens")
            .select("metadados")
            .order("data_criacao", desc=True)
            .limit(100)
            .execute()
        )
        
        if result.data:
            # Extrair tempos de resposta
            tempos = []
            for item in result.data:
                if item.get("metadados") and isinstance(item["metadados"], dict):
                    tempo = item["metadados"].get("tempo_processamento")
                    if tempo is not None:
                        tempos.append(float(tempo))
            
            if tempos:
                # Calcular métricas
                metrics["tempo_medio_resposta"] = round(sum(tempos) / len(tempos), 2)
                metrics["tempo_minimo_resposta"] = round(min(tempos), 2)
                metrics["tempo_maximo_resposta"] = round(max(tempos), 2)
                metrics["amostras_tempo"] = len(tempos)
                
        logger.info("Métricas de desempenho coletadas com sucesso")
        return metrics
        
    except Exception as e:
        logger.error(f"Erro ao coletar métricas de desempenho: {str(e)}")
        return {"error": str(e)}

async def obter_todas_metricas() -> Dict[str, Any]:
    """
    Obtém todas as métricas disponíveis.
    
    Returns:
        Dicionário combinado com todas as métricas
    """
    # Coletar todas as métricas em paralelo
    metricas_gerais = await coletar_metricas_gerais()
    metricas_feedback = await coletar_metricas_feedback()
    metricas_desempenho = await coletar_metricas_desempenho()
    
    # Combinar resultados
    metricas = {
        "timestamp": get_brazil_time().isoformat(),
        **metricas_gerais,
        **metricas_feedback,
        **metricas_desempenho
    }
    
    return metricas
