"""
Modelos de dados para o módulo de chat.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class PerguntaRequest(BaseModel):
    pergunta: str = Field(..., description="Texto da pergunta do usuário")
    usuario_id: Optional[int] = Field(None, description="ID do usuário")
    nome_usuario: Optional[str] = Field(None, description="Nome do usuário")
    contexto: Optional[List[Dict[str, Any]]] = Field([], description="Contexto de mensagens anteriores")
    sistema_prompt: Optional[str] = Field(None, description="Prompt de sistema personalizado")
    sessao_id: Optional[int] = Field(None, description="ID da sessão existente")
    
    class Config:
        schema_extra = {
            "example": {
                "pergunta": "Como faço para resetar minha senha?",
                "usuario_id": 123,
                "nome_usuario": "João Silva",
                "contexto": [],
                "sistema_prompt": None,
                "sessao_id": None
            }
        }

class RespostaChat(BaseModel):
    resposta: str = Field(..., description="Texto da resposta gerada")
    prompt_usado: Optional[str] = Field(None, description="Prompt usado para gerar a resposta")
    tokens_usados: Optional[int] = Field(None, description="Quantidade de tokens usados")
    tempo_processamento: Optional[float] = Field(None, description="Tempo de processamento em segundos")
    error: Optional[str] = Field(None, description="Mensagem de erro, se houver")
    
    class Config:
        schema_extra = {
            "example": {
                "resposta": "Para resetar sua senha, acesse a página de login e clique em 'Esqueci minha senha'.",
                "prompt_usado": "Você é um assistente virtual...",
                "tokens_usados": 150,
                "tempo_processamento": 1.25,
                "error": None
            }
        }
