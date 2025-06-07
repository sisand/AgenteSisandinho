"""
Modelos comuns usados em múltiplos lugares da aplicação.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class StatusResponse(BaseModel):
    status: str = Field(..., description="Status da operação (success, error)")
    message: Optional[str] = Field(None, description="Mensagem detalhada")
    error: Optional[str] = Field(None, description="Mensagem de erro, se houver")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Operação realizada com sucesso",
                "error": None
            }
        }

class PaginatedResponse(BaseModel):
    data: List[Dict[str, Any]] = Field(..., description="Lista de itens")
    total: int = Field(..., description="Total de itens disponíveis")
    page: int = Field(1, description="Página atual")
    page_size: int = Field(..., description="Tamanho da página")
    
    class Config:
        schema_extra = {
            "example": {
                "data": [{"id": 1, "nome": "Item 1"}, {"id": 2, "nome": "Item 2"}],
                "total": 100,
                "page": 1,
                "page_size": 25
            }
        }
