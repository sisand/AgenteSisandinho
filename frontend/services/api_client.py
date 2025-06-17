# frontend/services/api_client.py

import streamlit as st
import requests
import logging
from typing import Dict, List, Any, Optional
from datetime import date # <-- CORREÇÃO: Importa o tipo 'date'

logger = logging.getLogger(__name__)

# --- FUNÇÃO CENTRAL E ÚNICA PARA CHAMADAS DE API ---

def api_call(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict] = None,
    params: Optional[Dict] = None,
    timeout: int = 45
) -> Dict:
    """
    Função centralizada para fazer chamadas à API do backend, incluindo autenticação.
    """
    try:
        base_url = st.secrets["api"]["base_url"]
        api_key = st.secrets["api"]["internal_api_key"]
    except KeyError as e:
        error_msg = f"Configuração ausente no secrets.toml: {e}"
        logger.error(error_msg)
        return {"error": error_msg}

    # O prefixo /api é adicionado aqui para consistência
    url = f"{base_url}/api/{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": api_key
    }

    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=data,
            params=params,
            timeout=timeout
        )
        response.raise_for_status()
        return response.json() if response.content else {}

    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", e.response.text)
        except requests.exceptions.JSONDecodeError:
            detail = e.response.text
        msg = f"Erro da API ({e.response.status_code}): {detail}"
        logger.error(msg)
        return {"error": msg}
    except requests.exceptions.RequestException as e:
        msg = f"Erro de conexão com a API: {e}"
        logger.error(msg)
        return {"error": msg}

# ===================================================================================
# FUNÇÕES ESPECÍFICAS POR ENDPOINT
# ===================================================================================

def enviar_pergunta(pergunta: str, email_usuario: str, nome_usuario: str) -> Dict:
    """Envia uma pergunta para o endpoint de chat."""
    payload = {
        "pergunta": pergunta,
        "email_usuario": email_usuario,
        "nome_usuario": nome_usuario
    }
    return api_call("chat/perguntar", method="POST", data=payload)

def importar_artigos(reset_base: bool) -> Dict:
    """Dispara a importação de artigos em segundo plano no backend."""
    return api_call("importacao/artigos", method="POST", params={"reset_base": reset_base}, timeout=15)

def listar_artigos(termo_busca: Optional[str], pagina: int, limite: int) -> Dict:
    """Busca artigos na base de conhecimento."""
    params = {"termo_busca": termo_busca, "pagina": pagina, "limite": limite}
    params = {k: v for k, v in params.items() if v is not None and v != ""}
    return api_call("base-conhecimento/artigos", method="GET", params=params)

def carregar_prompts() -> List[Dict]:
    """Carrega a lista de prompts ativos."""
    response = api_call("prompts/ativos")
    return response if isinstance(response, list) else []

def atualizar_prompt(id_prompt: int, nome: str, conteudo: str) -> Dict:
    """Atualiza um prompt existente."""
    payload = {"nome": nome, "conteudo": conteudo}
    return api_call(f"prompts/{id_prompt}", method="PUT", data=payload)

def carregar_parametros() -> List[Dict]:
    """Carrega os parâmetros do sistema a partir do backend."""
    response = api_call("parametros/")
    return response if isinstance(response, list) else []

def carregar_historico() -> List[Dict]:
    """Busca o histórico de conversas."""
    return api_call("historico/")

def buscar_tickets() -> List[Dict]:
    """Busca tickets (exemplo)."""
    return api_call("tickets/")

def salvar_curadoria(ticket_id, curador, pergunta, resposta) -> Dict:
    """Salva uma nova curadoria."""
    payload = {"ticket_id": ticket_id, "curador": curador, "pergunta": pergunta, "resposta": resposta}
    return api_call("curadoria/", method="POST", data=payload)

def api_carregar_sessoes(usuario_id, limite) -> Dict:
    """Carrega as sessões de um usuário."""
    params = {"usuario_id": usuario_id, "limite": limite}
    return api_call("sessoes/", params=params)

def carregar_metricas(data_inicio: Optional[date] = None, data_fim: Optional[date] = None) -> Dict:
    """Busca as métricas consolidadas, enviando o filtro de data para o backend."""
    params = {}
    if data_inicio:
        params["data_inicio"] = data_inicio.isoformat()
    if data_fim:
        params["data_fim"] = data_fim.isoformat()
        
    return api_call("metrics/", params=params)

def enviar_feedback(id_mensagem: int, tipo: str) -> Dict:
    """Envia um feedback (positivo ou negativo) para o backend."""
    payload = {"id_mensagem": id_mensagem, "tipo_feedback": tipo}
    return api_call("feedback/", method="POST", data=payload) # <-- CORRIGIDO AQUI

def carregar_feedbacks() -> List[Dict]:
    """Busca a lista de feedbacks do backend."""
    response = api_call("feedback/") # <-- CORRIGIDO AQUI
    return response if isinstance(response, list) else []

# Adicione aqui as outras funções que seu app pode precisar
def listar_artigos(termo_busca: Optional[str], pagina: int, limite: int) -> Dict:
    params = {"termo_busca": termo_busca, "pagina": pagina, "limite": limite}
    params = {k: v for k, v in params.items() if v is not None and v != ""}
    return api_call("base-conhecimento/artigos", params=params)

