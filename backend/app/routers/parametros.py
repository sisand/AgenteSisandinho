# ==============================================================================
# ARQUIVO 2 (ALTERADO): app/routers/parametros.py
# ==============================================================================
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from pydantic import BaseModel

from app.core.cache import PARAMETROS_CACHE
from app.services.parametros import atualizar_parametro # <-- Importa o novo serviço
from app.core.security import get_api_key

router = APIRouter()

class ParametroUpdateRequest(BaseModel):
    valor: Any

@router.get("/")
def obter_parametros(api_key: str = Depends(get_api_key)) -> Dict[str, Any]:
    """Retorna todos os parâmetros do sistema que estão em cache."""
    return PARAMETROS_CACHE

@router.put("/{nome_parametro}")
def rota_atualizar_parametro(
    nome_parametro: str, 
    dados: ParametroUpdateRequest, 
    api_key: str = Depends(get_api_key)
):
    """Atualiza o valor de um parâmetro específico."""
    sucesso = atualizar_parametro(nome=nome_parametro, valor=dados.valor)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar o parâmetro '{nome_parametro}'."
        )
    return {"status": "sucesso", "mensagem": f"Parâmetro '{nome_parametro}' atualizado com sucesso."}