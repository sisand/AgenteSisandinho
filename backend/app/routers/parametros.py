from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.core.cache import obter_todos_parametros
from app.core.security import get_api_key

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
def rota_obter_parametros(api_key: str = Depends(get_api_key)):
    """Retorna todos os parâmetros do sistema que estão em cache."""
    return obter_todos_parametros()