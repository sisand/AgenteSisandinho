"""
Router para monitoramento de status do sistema
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, List
import time
import platform
import sys
from datetime import datetime, timedelta

from app.core.clients import (
    get_supabase_client,
    get_weaviate_client,
    get_openai_client
)
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Variável global para rastrear o tempo de atividade
START_TIME = time.time()

class ServiceStatus(BaseModel):
    service: str
    status: str
    error: str = None
    latency_ms: int = None
    details: Dict[str, Any] = None

class SystemStatus(BaseModel):
    status: str
    uptime: str
    services: List[ServiceStatus]
    environment: str
    python_version: str
    system_info: str
    timestamp: str

@router.get("/health", response_model=SystemStatus)
async def check_health():
    """
    Verifica o status de saúde do sistema e suas dependências.
    """
    logger.info("Verificando status do sistema")
    
    # Lista para armazenar status de serviços
    services = []
    overall_status = "ok"
    
    # 1. Verificar Supabase
    try:
        start = time.time()
        supabase = get_supabase_client()
        result = supabase.table("mensagens").select("id").limit(1).execute()
        latency_ms = int((time.time() - start) * 1000)
        
        services.append(ServiceStatus(
            service="supabase",
            status="ok",
            latency_ms=latency_ms,
            details={"mensagens_table": "acessível"}
        ))
    except Exception as e:
        overall_status = "degraded"
        services.append(ServiceStatus(
            service="supabase",
            status="error",
            error=str(e)
        ))
        logger.error(f"Erro ao verificar Supabase: {str(e)}")
    
    # 2. Verificar Weaviate
    try:
        start = time.time()
        client = get_weaviate_client()
        if not client:
            raise ValueError("Cliente não inicializado")
            
        collections = client.collections.list_all()
        latency_ms = int((time.time() - start) * 1000)
        
        services.append(ServiceStatus(
            service="weaviate",
            status="ok",
            latency_ms=latency_ms,
            details={"collections": list(collections.keys()) if collections else []}
        ))
    except Exception as e:
        overall_status = "degraded"
        services.append(ServiceStatus(
            service="weaviate",
            status="error",
            error=str(e)
        ))
        logger.error(f"Erro ao verificar Weaviate: {str(e)}")
    
    # 3. Verificar OpenAI
    try:
        start = time.time()
        client = get_openai_client()
        # Fazer uma chamada simples para testar
        response = client.models.list()
        latency_ms = int((time.time() - start) * 1000)
        
        services.append(ServiceStatus(
            service="openai",
            status="ok",
            latency_ms=latency_ms,
            details={"api_version": client.__version__ if hasattr(client, "__version__") else "unknown"}
        ))
    except Exception as e:
        overall_status = "degraded"
        services.append(ServiceStatus(
            service="openai",
            status="error",
            error=str(e)
        ))
        logger.error(f"Erro ao verificar OpenAI: {str(e)}")
    
    # Calcular tempo de atividade
    uptime_seconds = time.time() - START_TIME
    uptime = str(timedelta(seconds=int(uptime_seconds)))
    
    # Informações do ambiente
    environment = "production" if sys.argv[0].endswith("gunicorn") else "development"
    
    return SystemStatus(
        status=overall_status,
        uptime=uptime,
        services=services,
        environment=environment,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        system_info=platform.platform(),
        timestamp=datetime.now().isoformat()
    )
