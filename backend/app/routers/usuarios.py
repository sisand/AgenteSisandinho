from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.usuarios import obter_ou_criar_usuario

router = APIRouter()

class UsuarioCreate(BaseModel):
    login: str
    nome: Optional[str] = None

@router.post("/")
def criar_usuario(usuario: UsuarioCreate):
    """
    Cria um novo usuário ou retorna um existente.
    
    Args:
        usuario: Dados do usuário
        
    Returns:
        ID do usuário
    """
    try:
        usuario_id = obter_ou_criar_usuario(usuario.login, usuario.nome)
        return {"usuario_id": usuario_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
