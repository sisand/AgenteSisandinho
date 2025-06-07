"""
Router para o sistema de métricas.
"""

from fastapi import APIRouter
from typing import Dict, Any

from app.services.metrics import coletar_metricas_gerais, coletar_metricas_feedback, coletar_metricas_desempenho, obter_todas_metricas

router = APIRouter()

@router.get("/")
async def todas_metricas():
    """
    Obtém todas as métricas disponíveis.
    """
    return await obter_todas_metricas()

@router.get("/gerais")
async def metricas_gerais():
    """
    Coleta métricas gerais sobre o uso do sistema.
    """
    return await coletar_metricas_gerais()

@router.get("/feedback")
async def metricas_feedback():
    """
    Coleta métricas de feedback dos usuários.
    """
    return await coletar_metricas_feedback()

@router.get("/desempenho")
async def metricas_desempenho():
    """
    Coleta métricas de desempenho do sistema.
    """
    return await coletar_metricas_desempenho()
