# ==============================================================================
# ARQUIVO 4 (NOVO): app/routers/parametros.py
# ==============================================================================
from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.core.cache import PARAMETROS_CACHE # Importa o cache diretamente
from app.core.security import get_api_key

router = APIRouter()

@router.get("/")
def obter_parametros(api_key: str = Depends(get_api_key)) -> Dict[str, Any]:
    """Retorna todos os parâmetros do sistema que estão em cache."""
    return PARAMETROS_CACHE