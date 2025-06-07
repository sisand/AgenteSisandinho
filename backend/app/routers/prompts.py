from fastapi import APIRouter, Body, Path, HTTPException
from typing import Optional
from pydantic import BaseModel

from app.services.prompts import buscar_prompt, atualizar_prompt, listar_prompts

router = APIRouter()


class PromptUpdate(BaseModel):
    nome: Optional[str] = None
    conteudo: str
    descricao: Optional[str] = None
    ativo: bool = True


@router.get("/ativos")
def get_prompts_ativos():
    """Retorna todos os prompts ativos no sistema"""
    return listar_prompts()


@router.get("/{nome}")
def get_prompt(nome: str = Path(..., description="Nome do prompt a ser buscado")):
    """
    Busca um prompt específico pelo nome.
    """
    prompt_content = buscar_prompt(nome)
    if "erro" in prompt_content.lower():
        raise HTTPException(status_code=404, detail=f"Prompt '{nome}' não encontrado")

    return {"nome": nome, "conteudo": prompt_content}


@router.put("/{nome}")
def update_prompt(
    nome: str = Path(..., description="Nome do prompt"),
    prompt_data: PromptUpdate = Body(...)
):
    """
    Atualiza ou cria um prompt.
    """
    success = atualizar_prompt(
        nome=nome,
        conteudo=prompt_data.conteudo,
        descricao=prompt_data.descricao
    )

    if not success:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar prompt '{nome}'")

    return {"status": "success", "message": f"Prompt '{nome}' atualizado com sucesso"}
