# app/routers/metricas.py
from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, Optional
from datetime import date

# Importa todas as funções de serviço, incluindo as novas
from app.services.metricas import (
    obter_todas_metricas,
    coletar_metricas_gerais,
    coletar_metricas_feedback,
    coletar_metricas_desempenho,
    coletar_metricas_engajamento,
    coletar_metricas_custo_e_rag
)
from app.core.security import get_api_key

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
def obter_metricas_consolidadas(
    api_key: str = Depends(get_api_key),
    data_inicio: Optional[date] = Query(None, description="Data de início (YYYY-MM-DD)"),
    data_fim: Optional[date] = Query(None, description="Data de fim (YYYY-MM-DD)")
):
    """Busca um compilado de todas as métricas do sistema, com filtro de data opcional."""
    return obter_todas_metricas(data_inicio, data_fim)

# --- Endpoints Granulares ---

@router.get("/gerais", response_model=Dict[str, Any])
def obter_metricas_gerais(
    api_key: str = Depends(get_api_key), 
    data_inicio: Optional[date] = Query(None), 
    data_fim: Optional[date] = Query(None)
):
    """Endpoint específico para métricas gerais de uso."""
    return coletar_metricas_gerais(data_inicio, data_fim)

@router.get("/feedback", response_model=Dict[str, Any])
def obter_metricas_de_feedback(
    api_key: str = Depends(get_api_key), 
    data_inicio: Optional[date] = Query(None), 
    data_fim: Optional[date] = Query(None)
):
    """Endpoint específico para métricas de feedback dos usuários."""
    return coletar_metricas_feedback(data_inicio, data_fim)

@router.get("/desempenho", response_model=Dict[str, Any])
def obter_metricas_de_desempenho(
    api_key: str = Depends(get_api_key), 
    data_inicio: Optional[date] = Query(None), 
    data_fim: Optional[date] = Query(None)
):
    """Endpoint específico para métricas de desempenho técnico."""
    return coletar_metricas_desempenho(data_inicio, data_fim)

# --- NOVOS ENDPOINTS ADICIONADOS ---

@router.get("/engajamento", response_model=Dict[str, Any])
def obter_metricas_de_engajamento(
    api_key: str = Depends(get_api_key), 
    data_inicio: Optional[date] = Query(None), 
    data_fim: Optional[date] = Query(None)
):
    """Endpoint específico para métricas de engajamento dos usuários."""
    return coletar_metricas_engajamento(data_inicio, data_fim)

@router.get("/custo-rag", response_model=Dict[str, Any])
def obter_metricas_de_custo_e_rag(
    api_key: str = Depends(get_api_key), 
    data_inicio: Optional[date] = Query(None), 
    data_fim: Optional[date] = Query(None)
):
    """Endpoint específico para métricas de custo e eficácia do RAG."""
    return coletar_metricas_custo_e_rag(data_inicio, data_fim)
