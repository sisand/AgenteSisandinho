# app/modelos/api.py
"""
Modelos de dados (schemas) Pydantic para a API.

Este arquivo é a fonte única de verdade para todas as estruturas de requisição e 
resposta utilizadas pelos endpoints da API, promovendo consistência e facilitando a manutenção.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime


# ==============================================================================
# Modelos para os Endpoints de Chat (Ex: /perguntar)
# ==============================================================================

class RequisicaoChat(BaseModel):
    """Define o corpo esperado para uma requisição de pergunta vinda do frontend."""
    pergunta: str = Field(
        ..., 
        description="O texto da pergunta feita pelo usuário.",
        example="Como configuro o fuso horário no sistema?"
    )
    email_usuario: str = Field(
        ..., 
        description="E-mail do usuário, utilizado como identificador único para o login.",
        example="joao.silva@email.com"
    )
    nome_usuario: str = Field(
        ..., 
        description="Nome do usuário que está interagindo com o assistente.",
        example="João da Silva"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "pergunta": "Qual é o plano de suporte mais recomendado?",
                "email_usuario": "ana.pereira@exemplo.com",
                "nome_usuario": "Ana Pereira"
            }
        }

class RespostaChat(BaseModel):
    """Define a estrutura da resposta que a API retornará para o endpoint de chat."""
    id_mensagem: int = Field(..., description="O ID único da mensagem de resposta da IA.")
    id_sessao: int = Field(..., description="O ID da sessão de chat atual.")
    data_inicio_sessao: str = Field(..., description="Data de início da sessão no formato DD/MM/AAAA.")
    hora_inicio_sessao: str = Field(..., description="Hora de início da sessão no formato HH:MM:SS.")
    resposta: str = Field(..., description="A resposta textual gerada pelo assistente de IA.")
    categoria: str = Field(..., description="A categoria da pergunta, classificada pelo sistema (ex: 'fiscal', 'comercial').")
    artigos: List[Dict[str, Any]] = Field(default=[], description="Uma lista de artigos da base de conhecimento usados como fonte (contexto RAG).")
    tempo_processamento: float = Field(..., description="Tempo total em segundos que o servidor levou para processar a pergunta.")
    prompt_usado: str = Field(..., description="O nome do template de prompt que foi utilizado para gerar a resposta.")

    class Config:
        json_schema_extra = {
            "example": {
                "id_sessao": 123,
                "data_inicio_sessao": "15/06/2025",
                "hora_inicio_sessao": "16:45:10",
                "resposta": "O plano mais recomendado para suas necessidades é o Plano Premium, que oferece suporte 24/7.",
                "categoria": "Dúvidas sobre Planos",
                "artigos": [],
                "tempo_processamento": 2.53,
                "prompt_usado": "chat_padrao"
            }
        }


# ==============================================================================
# Modelos para os Endpoints de Prompt (/prompts)
# ==============================================================================
class RequisicaoPrompt(BaseModel):
    """Corpo da requisição para criar ou atualizar um prompt."""
    nome: str = Field(..., description="O nome único do prompt.")
    conteudo: str = Field(..., description="O texto completo do prompt de sistema.")


# ==============================================================================
# Modelos para os Endpoints de Sessão (Ex: /sessoes/*)
# ==============================================================================

class RequisicaoSessao(BaseModel):
    """Define o corpo para a requisição de criação/obtenção de sessão."""
    id_usuario: int = Field(..., description="ID do usuário para o qual a sessão será criada ou obtida.")

class RespostaSessao(BaseModel):
    """Define a resposta padrão para operações de sessão, como a criação."""
    id: int = Field(..., description="O ID da sessão criada ou obtida.")
    mensagem: str = Field(..., description="Mensagem indicando o resultado da operação.")
    sucesso: bool = Field(..., description="Indica se a operação foi bem-sucedida.")

class RespostaInfoSessao(BaseModel):
    """Define a resposta para o endpoint que busca informações da sessão ativa."""
    numero_sessao: int = Field(..., description="O ID numérico da sessão ativa.")
    data_inicio: str = Field(..., description="Data de início da sessão no formato DD/MM/AAAA.")
    hora_inicio: str = Field(..., description="Hora de início da sessão no formato HH:MM:SS.")
    
    class Config:
        json_schema_extra = {
            "example": {
                "numero_sessao": 101,
                "data_inicio": "15/06/2025",
                "hora_inicio": "10:30:00"
            }
        }
# ==============================================================================
# Modelos para os Endpoints de Feedback (/feedbacks)
# ==============================================================================

class RequisicaoFeedback(BaseModel):
    id_mensagem: int = Field(..., description="O ID da mensagem que está sendo avaliada.")
    tipo_feedback: Literal["positivo", "negativo"] = Field(..., description="O tipo de feedback: 'positivo' ou 'negativo'.")
    
# ==============================================================================
# Modelos para os Endpoints de Artigos (/artigos)
# ==============================================================================

class RequisicaoCriarArtigo(BaseModel):
    """Corpo da requisição para criar um novo artigo."""
    titulo: str = Field(..., description="Título do artigo")
    conteudo: str = Field(..., description="Conteúdo completo do artigo")
    categoria: str = Field("Geral", description="Categoria para organização")
    url: Optional[str] = Field(None, description="URL de origem do artigo")
    resumo: Optional[str] = Field(None, description="Resumo curto do artigo")
    id_externo: Optional[str] = Field(None, description="ID de um sistema externo para referência")

class RequisicaoAtualizarArtigo(BaseModel):
    """Corpo da requisição para atualizar um artigo existente."""
    titulo: Optional[str] = Field(None, description="Novo título do artigo")
    conteudo: Optional[str] = Field(None, description="Novo conteúdo do artigo, irá gerar novo embedding")
    categoria: Optional[str] = Field(None, description="Nova categoria do artigo")
    url: Optional[str] = Field(None, description="Nova URL do artigo")
    resumo: Optional[str] = Field(None, description="Novo resumo do artigo")