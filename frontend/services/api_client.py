# frontend/services/api_client.py

import requests
import logging
import os
from typing import Dict, List, Any, Optional

# Configuração de logging
logger = logging.getLogger(__name__)

# API URL base - configurável via variável de ambiente
API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")
# Timeout padrão para a maioria das chamadas
API_TIMEOUT = 30 

def api_call(endpoint: str, method: str = "GET", data: Optional[Dict] = None, timeout: int = API_TIMEOUT) -> Dict:
    """
    Função genérica para chamadas à API do backend.
    """
    url = f"{API_BASE_URL}/{endpoint}"
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, timeout=timeout)
        elif method.upper() == "DELETE":
            response = requests.delete(url, timeout=timeout)
        else:
            return {"error": f"Método HTTP não suportado: {method}"}
            
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ReadTimeout:
        logger.error(f"Timeout na requisição para {url} após {timeout} segundos.")
        return {"error": f"A operação demorou mais que o esperado ({timeout}s) e o tempo de espera esgotou. O processo pode estar continuando no servidor."}
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição para {url}: {str(e)}")
        return {"error": f"Erro de comunicação com a API: {str(e)}"}


# ===================================================================================
# FUNÇÕES ESPECÍFICAS POR ENDPOINT
# ===================================================================================

def enviar_pergunta(pergunta: str, usuario_id: Optional[int] = None, usuario_nome: Optional[str] = None) -> Dict:
    """Envia pergunta para o assistente virtual."""
    data = {
        "pergunta": pergunta,
        "usuario_id": usuario_id,
        "nome_usuario": usuario_nome,
        "contexto": []
    }
    return api_call("api/chat/perguntar", method="POST", data=data)

def importar_artigos(reset_base: bool = False) -> Dict:
    """
    Chama o endpoint da API para iniciar a importação de artigos.
    Esta função usa um timeout estendido para acomodar a longa duração do processo.
    """
    logger.info(f"Iniciando chamada para importação de artigos (reset_base={reset_base}) com timeout estendido.")
    # Usando a função genérica 'api_call' para consistência
    # e passando um timeout bem longo (900s = 15 minutos)
    # APENAS para esta chamada específica.
    return api_call(
        # Este endpoint deve ser o que você criou com BackgroundTasks
        endpoint="api/admin/importar-artigos", 
        method="POST",
        data={"reset_base": reset_base},
        timeout=900  # Timeout de 15 minutos
    )
    
def carregar_feedbacks() -> List[Dict]:
    """Carrega feedbacks do sistema."""
    return api_call("api/feedback", method="GET")

def carregar_parametros() -> Dict:
    """Carrega parâmetros e métricas do sistema."""
    return api_call("api/metrics", method="GET")

def carregar_historico(usuario_id=None, com_mensagens=False, limite=20):
    """
    Carrega histórico de conversas de um usuário
    
    Args:
        usuario_id: ID do usuário para carregar o histórico
        com_mensagens: Se True, carrega também as mensagens de cada sessão (pode ser lento)
        limite: Limita o número de sessões a carregar
        
    Returns:
        Dicionário contendo sessões e opcionalmente suas mensagens
    """
    usuario = usuario_id if usuario_id else 1
    logger.info(f"Carregando histórico do usuário: {usuario} (com_mensagens={com_mensagens})")
    
    try:
        # Buscar sessões com limite para melhor performance
        sessoes_response = api_carregar_sessoes(usuario, limite=limite)
        
        if not sessoes_response or not isinstance(sessoes_response, list):
            logger.info(f"Nenhuma sessão encontrada para o usuário: {usuario}")
            return {"sessoes": []}
        
        logger.info(f"Carregadas {len(sessoes_response)} sessões")
            
        # Carregar mensagens apenas se solicitado
        if com_mensagens:
            logger.info("Carregando mensagens para cada sessão (pode ser lento)")
            for sessao in sessoes_response:
                sessao_id = sessao.get("id")  # Corrigido: usar "id" em vez de "sessao_id"
                if sessao_id:
                    mensagens = carregar_mensagens_sessao(sessao_id)
                    sessao["mensagens"] = mensagens
        
        return {"sessoes": sessoes_response}
        
    except Exception as e:
        logger.error(f"Erro ao processar histórico: {str(e)}")
        return {"error": f"Erro ao processar histórico: {str(e)}"}

def api_carregar_sessoes(usuario_id, limite=None):
    """
    Carrega sessões de um usuário com opção de limite para melhor desempenho
    
    Args:
        usuario_id: ID do usuário para carregar as sessões
        limite: Quantidade máxima de sessões a retornar (opcional)
        
    Returns:
        Lista de sessões do usuário ou lista vazia em caso de erro
    """
    try:
        # Converter para inteiro se ainda não for
        if not isinstance(usuario_id, int):
            usuario_id = int(usuario_id)
            
        logger.info(f"Preparando para carregar sessões do usuário ID: {usuario_id} (tipo: {type(usuario_id).__name__})")
        
        # Construir endpoint com parâmetros
        endpoint_params = [f"usuario_id={usuario_id}"]
        if limite:
            endpoint_params.append(f"limite={limite}")
        
        # Usar endpoint com barra final para evitar redirecionamento 307
        endpoint = f"api/sessoes/?{'&'.join(endpoint_params)}"
        
        logger.info(f"Carregando sessões com endpoint: {endpoint}")
        result = api_call(endpoint, method="GET")
        
        # Log detalhado da resposta
        if "error" in result:
            logger.warning(f"Endpoint {endpoint} falhou: {result.get('error')}")
            return []
        else:
            logger.info(f"Endpoint {endpoint} funcionou com sucesso")
            logger.info(f"✅ Utilizando endpoint: {endpoint} para carregar sessões")
            
            # Processar e retornar resultado
            processed = processar_resposta_sessoes(result)
            logger.info(f"Após processamento: tipo={type(processed).__name__}, contém {len(processed)} itens")
            return processed
            
    except Exception as e:
        logger.error(f"Erro ao carregar sessões: {str(e)}")
        return []

def processar_resposta_sessoes(resposta):
    """Helper para processar diferentes formatos possíveis de resposta de sessões"""
    if isinstance(resposta, dict):
        if "sessoes" in resposta:
            return resposta["sessoes"]
        elif "data" in resposta:
            return resposta["data"]
        else:
            # Se não tiver as chaves esperadas, considerar o próprio dicionário
            return [resposta]
    elif isinstance(resposta, list):
        return resposta
    else:
        logger.warning(f"Formato inesperado na resposta de sessões: {type(resposta)}")
        return []

def buscar_tickets(limite=10):
    """Busca tickets do Movidesk"""
    return api_call(f"api/movidesk-tickets?limite={limite}", method="GET")

def salvar_curadoria(ticket_id, curador, pergunta, resposta):
    """Salva curadoria de um ticket"""
    data = {
        "ticket_id": ticket_id,
        "curador": curador,
        "pergunta": pergunta,
        "resposta": resposta
    }
    return api_call("api/curadoria", method="POST", data=data)

def listar_artigos() -> List[Dict]:
    """Lista os artigos da base de conhecimento."""
    # Nota: Esta função não usava o api_call, vamos mantê-la consistente
    return api_call("api/base-conhecimento/artigos")


def salvar_prompt(nome, conteudo):
    """Salva conteúdo de um prompt"""
    data = {
        "conteudo": conteudo
    }
    # Endpoint correto: POST /api/prompts/{nome}
    logger.info(f"Salvando prompt '{nome}' com o endpoint correto")
    return api_call(f"api/prompts/{nome}", method="POST", data=data)

def carregar_prompts():
    """Carrega lista de prompts disponíveis"""
    # Endpoint correto: GET /api/prompts/ativos
    logger.info("Carregando prompts com o endpoint correto")
    response = api_call("api/prompts/ativos", method="GET")
    
    # Processamento do resultado
    if isinstance(response, dict):
        if "data" in response:
            return response["data"]
        elif "error" not in response:
            return [response]  # Caso seja retornado um único objeto
    
    return response if isinstance(response, list) else []

def carregar_embeddings():
    """Carrega embeddings disponíveis"""
    return api_call("api/embeddings", method="GET")

import requests

API_URL = "http://127.0.0.1:8000"  # ou a URL correta do seu backend

def importar_artigos(reset_base=False):
    """
    Inicia a importação de artigos do Movidesk para o Weaviate.

    Args:
        reset_base (bool): Se True, reseta a base no Weaviate.

    Returns:
        dict: Resposta da API com o status da importação.
    """
    try:
        # Dispara o POST com params (compatível com seu endpoint atual!)
        response = requests.post(
            f"{API_URL}/api/importacao/artigos",
            params={"reset_base": reset_base},
            timeout=30  # Curto, só para disparar a operação
        )
        response.raise_for_status()

        return response.json()
    
    except Exception as e:
        # Se der erro, retorna um dicionário de erro para o front exibir
        return {"error": f"Erro ao iniciar importação: {str(e)}"}


def carregar_acoes_ticket(ticket_id):
    """Carrega ações de um ticket específico"""
    return api_call(f"api/movidesk-tickets/{ticket_id}/acoes", method="GET")

def carregar_configuracoes():
    """Carrega configurações do sistema"""
    return api_call("api/configuracoes", method="GET")

def atualizar_configuracao(nome, valor):
    """Atualiza uma configuração específica"""
    data = {
        "nome": nome,
        "valor": valor
    }
    return api_call("api/configuracoes", method="PUT", data=data)

def atualizar_prompt(nome, conteudo):
    """Atualiza conteúdo de um prompt existente."""
    # Formato do payload
    data = {
        "nome": nome,
        "conteudo": conteudo,
        "ativo": True
    }
    
    # Tentar várias combinações de endpoints e métodos
    logger.info("Tentando atualizar prompt com várias combinações de endpoint/método")
    
    # 1. Tentar com PUT no endpoint padrão
    result = api_call(f"api/prompts/{nome}", method="PUT", data=data)
    if "error" not in result:
        return result
        
    # 2. Tentar com POST no endpoint principal (sem nome)
    logger.warning("PUT falhou, tentando com POST no endpoint principal")
    result = api_call("api/prompts", method="POST", data=data)
    if "error" not in result:
        return result
        
    # 3. Tentar com PUT no endpoint principal
    logger.warning("POST no endpoint principal falhou, tentando com PUT")
    result = api_call("api/prompts", method="PUT", data=data)
    if "error" not in result:
        return result
        
    # 4. Tentar com endpoint alternativo de atualização
    logger.warning("Tentando endpoint alternativo")
    result = api_call(f"api/prompts/atualizar/{nome}", method="POST", data=data)
    if "error" not in result:
        return result
    
    # Se todas as tentativas falharam, registrar todos os endpoints tentados
    logger.error("Todas as tentativas de atualizar o prompt falharam")
    return {
        "error": "Não foi possível atualizar o prompt após múltiplas tentativas com diferentes endpoints/métodos",
        "detalhes": "Tentados: PUT /prompts/{nome}, POST /prompts, PUT /prompts, POST /prompts/atualizar/{nome}"
    }

def carregar_prompt_especifico(nome):
    """Carrega um prompt específico pelo nome"""
    # Endpoint correto: GET /api/prompts/{nome}
    return api_call(f"api/prompts/{nome}", method="GET")

def carregar_mensagens_sessao(sessao_id):
    """
    Carrega apenas as mensagens de uma sessão específica
    
    Args:
        sessao_id: ID da sessão para buscar mensagens
        
    Returns:
        Lista de mensagens da sessão ou lista vazia em caso de erro
    """
    logger.info(f"Solicitando mensagens da sessão {sessao_id}")
    
    try:
        result = api_call(f"api/sessoes/{sessao_id}/mensagens", method="GET")
        
        if "error" in result:
            logger.warning(f"Erro ao buscar mensagens da sessão {sessao_id}: {result['error']}")
            return []
            
        logger.info(f"Recebidas {len(result) if isinstance(result, list) else '?'} mensagens")
        
        # Se o resultado for um dicionário, tente extrair a lista
        if isinstance(result, dict) and "mensagens" in result:
            return result["mensagens"]
        elif isinstance(result, list):
            return result
        else:
            logger.warning(f"Formato inesperado de resposta: {type(result).__name__}")
            return []
            
    except Exception as e:
        logger.error(f"Erro ao carregar mensagens: {str(e)}")
        return []

def verificar_status_importacao():
    """
    Verifica o status da importação de artigos em andamento.

    Returns:
        Dicionário com o status atual da importação ou erro
    """
    logger.info("Verificando status da importação de artigos")

    try:
        result = api_call("api/importar/status", method="GET")
        if "error" in result:
            logger.warning(f"Erro ao consultar status: {result.get('error')}")
        return result
    except Exception as e:
        logger.error(f"❌ Erro ao verificar status da importação: {str(e)}")
        return {"error": str(e)}


def api_obter_ou_criar_sessao(usuario_id):
    """
    Função API para obter ou criar uma sessão para o usuário.
    
    Args:
        usuario_id: ID do usuário para obter/criar sessão
        
    Returns:
        ID da sessão ou None em caso de erro
    """
    try:
        # Converte para inteiro se necessário
        if not isinstance(usuario_id, int):
            usuario_id = int(usuario_id)
            
        logger.info(f"Obtendo/criando sessão para usuário: {usuario_id}")
        
        # Primeiro tentar com o endpoint criar
        try:
            # Mudança: Tentar com payload no corpo em vez de query params
            result = api_call("api/sessoes/criar", method="POST", data={"usuario_id": usuario_id})
            if "error" not in result:
                if isinstance(result, dict):
                    if "id" in result:
                        logger.info(f"Sessão ativa: {result['id']}")
                        return result["id"]
        except Exception as e:
            logger.warning(f"Erro ao chamar endpoint de criar sessão: {str(e)}")
        
        # Se falhar, tentar endpoint GET simples
        try:
            result = api_call(f"api/sessoes/usuario/{usuario_id}?limit=1", method="GET")
            if "error" not in result and "sessoes" in result:
                sessoes = result["sessoes"]
                if sessoes and len(sessoes) > 0:
                    sessao_id = sessoes[0].get("id")
                    if sessao_id:
                        logger.info(f"Sessão ativa encontrada: {sessao_id}")
                        return sessao_id
        except Exception as e:
            logger.warning(f"Erro ao buscar sessões do usuário: {str(e)}")
        
        # Se todas as tentativas falharam, por último tentar criar uma sessão local fictícia
        # para não interromper a experiência do usuário
        logger.warning("Todos os endpoints para obter sessão falharam, usando sessão local")
        import time
        temp_id = int(time.time())
        logger.info(f"Usando sessão local temporária: {temp_id}")
        return temp_id
            
    except Exception as e:
        logger.error(f"Erro ao obter/criar sessão: {str(e)}")
        import time
        # Último recurso: retornar um ID baseado em timestamp
        return int(time.time())

def api_obter_detalhes_sessao(sessao_id):
    """
    Função API para obter detalhes de uma sessão específica
    
    Args:
        sessao_id: ID da sessão para obter detalhes
        
    Returns:
        Dados da sessão ou None em caso de erro
    """
    logger.info(f"Obtendo detalhes da sessão {sessao_id}")
    try:
        # Tentar com endpoint /detalhes primeiro
        result = api_call(f"api/sessoes/{sessao_id}/detalhes", method="GET")
        
        if "error" in result:
            # Se falhar, tentar com endpoint /detalhe
            logger.warning(f"Endpoint /detalhes falhou, tentando endpoint alternativo")
            result = api_call(f"api/sessoes/detalhe/{sessao_id}", method="GET")
        
        if "error" in result:
            logger.warning(f"Erro ao buscar detalhes da sessão {sessao_id}: {result['error']}")
            # Para manter compatibilidade, retornar dados básicos mesmo em caso de erro
            return {
                "id": sessao_id,
                "inicio": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),  # Formato ISO 8601 completo
                "ultima_atividade": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")  # Formato ISO 8601 completo
            }
            
        # Processar datas para evitar erros de formatação ISO
        try:
            # Garantir que campos de data estejam em formato ISO válido
            if 'created_at' in result and result['created_at']:
                # Normalizar formato de data ISO
                date_str = result['created_at']
                # Garante que temos 6 dígitos para microssegundos
                if '.' in date_str and len(date_str.split('.')[-1]) < 7 and 'Z' not in date_str:
                    micro = date_str.split('.')[-1]
                    base = date_str.split('.')[0]
                    # Adicionar zeros necessários e Z no final
                    result['created_at'] = f"{base}.{micro.ljust(6, '0')}Z"
                elif '.' in date_str and 'Z' not in date_str:
                    # Apenas adicionar Z
                    result['created_at'] = f"{date_str}Z"
            
            # Fazer o mesmo para ultima_atividade se existir
            if 'ultima_atividade' in result and result['ultima_atividade']:
                date_str = result['ultima_atividade']
                if '.' in date_str and len(date_str.split('.')[-1]) < 7 and 'Z' not in date_str:
                    micro = date_str.split('.')[-1]
                    base = date_str.split('.')[0]
                    result['ultima_atividade'] = f"{base}.{micro.ljust(6, '0')}Z"
                elif '.' in date_str and 'Z' not in date_str:
                    result['ultima_atividade'] = f"{date_str}Z"
        except Exception as e:
            logger.warning(f"Erro detalhes sessão: {str(e)}")
        
        logger.info(f"Detalhes da sessão {sessao_id} obtidos com sucesso")
        return result
    except Exception as e:
        logger.error(f"Erro ao obter detalhes da sessão: {str(e)}")
        return {
            "id": sessao_id,
            "inicio": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),  # Formato ISO 8601 completo
            "ultima_atividade": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")  # Formato ISO 8601 completo
        }