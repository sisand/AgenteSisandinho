# app/routers/prompts.py
"""
Router para os endpoints da API relacionados com a gestão de Prompts.
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

# Importa o modelo de requisição centralizado
from app.models.api import RequisicaoPrompt

# Importa as funções de serviço refatoradas
from app.services.prompts import criar_novo_prompt, atualizar_prompt_por_id, listar_prompts_ativos

router = APIRouter()

@router.get("/ativos", response_model=List[Dict[str, Any]])
def rota_listar_prompts_ativos():
    """Endpoint para listar todos os prompts ativos no sistema."""
    return listar_prompts_ativos()


@router.put("/{id_prompt}")
def rota_atualizar_prompt(id_prompt: int, dados_prompt: RequisicaoPrompt):
    """Endpoint para atualizar um prompt existente, identificado pelo seu ID."""
    sucesso = atualizar_prompt_por_id(
        id_prompt=id_prompt, 
        nome=dados_prompt.nome, 
        conteudo=dados_prompt.conteudo
    )
    
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Ocorreu um erro interno ao tentar atualizar o prompt."
        )
        
    return {"status": "sucesso", "mensagem": "Prompt atualizado com sucesso."}


@router.post("/", status_code=status.HTTP_201_CREATED)
def rota_criar_prompt(dados_prompt: RequisicaoPrompt):
    """Endpoint para criar um novo prompt no sistema."""
    sucesso = criar_novo_prompt(
        nome=dados_prompt.nome,
        conteudo=dados_prompt.conteudo
    )

    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro ao criar o prompt."
        )
    
    return {"status": "sucesso", "mensagem": "Prompt criado com sucesso."}

