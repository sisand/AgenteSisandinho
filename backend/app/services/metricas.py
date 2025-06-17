# app/services/metricas.py
import logging
import numpy as np
from typing import Dict, Any, List, Optional
from collections import Counter
from datetime import date, timedelta

from app.core.clients import get_supabase_client

logger = logging.getLogger(__name__)

def _apply_date_filter(query, data_inicio: Optional[date], data_fim: Optional[date]):
    """Função auxiliar para aplicar filtros de data a uma query Supabase."""
    if data_inicio:
        query = query.gte("criado_em", data_inicio.isoformat())
    if data_fim:
        # Adiciona +1 dia ao data_fim para incluir o dia inteiro na consulta
        end_date = data_fim + timedelta(days=1)
        query = query.lt("criado_em", end_date.isoformat())
    return query

def coletar_metricas_gerais(data_inicio: Optional[date] = None, data_fim: Optional[date] = None) -> Dict[str, Any]:
    try:
        supabase = get_supabase_client()
        
        # Filtra sessões e mensagens pelo período selecionado
        sessoes_query = supabase.table("sessoes").select("count", count="exact")
        sessoes_query = _apply_date_filter(sessoes_query, data_inicio, data_fim)
        sessions_result = sessoes_query.execute()

        mensagens_query = supabase.table("mensagens").select("count", count="exact")
        mensagens_query = _apply_date_filter(mensagens_query, data_inicio, data_fim)
        messages_result = mensagens_query.execute()
        
        # Total de usuários não é filtrado por data
        users_result = supabase.table("usuarios").select("count", count="exact").execute()

        return {
            "total_usuarios": users_result.count,
            "total_sessoes_periodo": sessions_result.count,
            "total_mensagens_periodo": messages_result.count,
        }
    except Exception as e:
        logger.error(f"Erro ao coletar métricas gerais: {e}")
        return {}

def coletar_metricas_feedback(data_inicio: Optional[date] = None, data_fim: Optional[date] = None) -> Dict[str, Any]:
    try:
        supabase = get_supabase_client()
        query = supabase.table("feedbacks").select("id, tipo")
        query = _apply_date_filter(query, data_inicio, data_fim)
        feedbacks_result = query.execute()
        
        total_feedbacks = len(feedbacks_result.data)
        positivos = sum(1 for f in feedbacks_result.data if f.get('tipo') == 'positivo')
        negativos = total_feedbacks - positivos
        
        return {
            "total_feedbacks_periodo": total_feedbacks,
            "feedbacks_positivos_periodo": positivos,
            "feedbacks_negativos_periodo": negativos,
            "percentual_positivos_periodo": round((positivos / total_feedbacks) * 100, 2) if total_feedbacks > 0 else 0,
        }
    except Exception as e:
        logger.error(f"Erro ao coletar métricas de feedback: {e}")
        return {}

def coletar_metricas_desempenho(data_inicio: Optional[date] = None, data_fim: Optional[date] = None) -> Dict[str, Any]:
    try:
        supabase = get_supabase_client()
        query = supabase.table("mensagens").select("metadados").order("criado_em", desc=True).limit(500)
        query = _apply_date_filter(query, data_inicio, data_fim)
        result = query.execute()
        
        if not result.data: return {}
        tempos = [float(item["metadados"].get("tempo_processamento")) for item in result.data if isinstance(item.get("metadados"), dict) and item["metadados"].get("tempo_processamento") is not None]
        if not tempos: return {}
            
        return {
            "tempo_medio_resposta_s": round(np.mean(tempos), 2),
            "tempo_minimo_resposta_s": round(min(tempos), 2),
            "tempo_maximo_resposta_s": round(max(tempos), 2),
            "tempo_percentil_95_s": round(np.percentile(tempos, 95), 2),
            "amostras_coletadas": len(tempos)
        }
    except Exception as e:
        logger.error(f"Erro ao coletar métricas de desempenho: {e}")
        return {}

def coletar_metricas_engajamento(data_inicio: Optional[date] = None, data_fim: Optional[date] = None) -> Dict[str, Any]:
    try:
        supabase = get_supabase_client()
        query = supabase.table("mensagens").select("usuario_id(id, nome)")
        query = _apply_date_filter(query, data_inicio, data_fim)
        mensagens_response = query.execute()
        
        if not mensagens_response.data: return {"top_10_usuarios": []}
        
        user_names = [msg['usuario_id']['nome'] for msg in mensagens_response.data if msg.get('usuario_id') and msg['usuario_id'].get('nome')]
        user_counts = Counter(user_names)
        
        top_10_list = [{"nome": name, "mensagens": count} for name, count in user_counts.most_common(10)]
        return {"top_10_usuarios_periodo": top_10_list}
    except Exception as e:
        logger.error(f"Erro ao coletar métricas de engajamento: {e}")
        return {}

def coletar_metricas_custo_e_rag(data_inicio: Optional[date] = None, data_fim: Optional[date] = None) -> Dict[str, Any]:
    try:
        supabase = get_supabase_client()
        query = supabase.table("mensagens").select("metadados").eq("tipo_resposta", "ia")
        query = _apply_date_filter(query, data_inicio, data_fim)
        result = query.execute()
        
        if not result.data:
            return {"custo_total_usd": 0, "custo_medio_por_msg_usd": 0, "percentual_respostas_com_rag": 0, "top_5_categorias": []}
        
        all_metadata = [item['metadados'] for item in result.data if isinstance(item.get('metadados'), dict)]
        
        total_cost = sum(meta.get('custo_total', 0) for meta in all_metadata if meta.get('custo_total') is not None)
        rag_count = sum(1 for meta in all_metadata if meta.get('rag_utilizado') is True)
        total_ia_messages = len(all_metadata)
        
        classifications = [meta.get('classificacao') for meta in all_metadata if meta.get('classificacao')]
        classification_counts = Counter(classifications)
        top_5_categories = [{"categoria": cat, "quantidade": count} for cat, count in classification_counts.most_common(5)]
        
        return {
            "custo_total_usd_periodo": round(total_cost, 6),
            "percentual_respostas_com_rag_periodo": round((rag_count / total_ia_messages) * 100, 2) if total_ia_messages > 0 else 0,
            "top_5_categorias_periodo": top_5_categories
        }
    except Exception as e:
        logger.error(f"Erro ao coletar métricas de custo e RAG: {e}")
        return {}

def obter_todas_metricas(data_inicio: Optional[date] = None, data_fim: Optional[date] = None) -> Dict[str, Any]:
    """Orquestra a coleta de todas as métricas para um determinado período."""
    logger.info(f"Coletando métricas para o período de {data_inicio} a {data_fim}")
    
    # Agora todas as funções recebem o filtro de data
    metricas_gerais = coletar_metricas_gerais(data_inicio, data_fim)
    metricas_feedback = coletar_metricas_feedback(data_inicio, data_fim)
    metricas_desempenho = coletar_metricas_desempenho(data_inicio, data_fim)
    metricas_engajamento = coletar_metricas_engajamento(data_inicio, data_fim)
    metricas_custo_rag = coletar_metricas_custo_e_rag(data_inicio, data_fim)
    
    return {
        **metricas_gerais, 
        **metricas_feedback, 
        **metricas_desempenho,
        **metricas_engajamento,
        **metricas_custo_rag
    }
