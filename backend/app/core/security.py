# app/core/security.py
"""
Módulo de segurança para a API, incluindo a validação de chaves.
"""
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
import logging

# Importa a função para obter as configurações da aplicação
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Define que a chave de API será procurada no cabeçalho 'X-Api-Key'
api_key_header = APIKeyHeader(name="X-Api-Key", auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Dependência que valida a chave de API recebida na requisição.
    
    Esta função agora verifica se a chave fornecida está numa lista de chaves permitidas,
    definida na variável de ambiente 'ALLOWED_API_KEYS'.
    
    Raises:
        HTTPException: Se a chave não for fornecida ou não for válida.
        
    Returns:
        A chave de API se ela for válida.
    """
    settings = get_settings()

    # 1. Verifica se a variável com a lista de chaves está configurada
    allowed_keys_str = settings.ALLOWED_API_KEYS
    if not allowed_keys_str:
        logger.critical("Nenhuma chave de API permitida está configurada no ambiente (ALLOWED_API_KEYS).")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="O servidor não está configurado corretamente para autenticação."
        )

    # 2. Transforma a string de chaves separadas por vírgula numa lista
    # Ex: "key1,key2" -> ["key1", "key2"]
    valid_api_keys = [key.strip() for key in allowed_keys_str.split(",")]

    # 3. Verifica se uma chave foi fornecida no cabeçalho da requisição
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Chave de API não fornecida."
        )

    # 4. Verifica se a chave fornecida está na lista de chaves válidas
    if api_key not in valid_api_keys:
        logger.warning(f"Tentativa de acesso com chave de API inválida: {api_key}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Chave de API inválida ou não autorizada."
        )

    # 5. Se tudo estiver correto, retorna a chave
    logger.info(f"Acesso autorizado para a chave de API terminada em '...{api_key[-4:]}'.")
    return api_key

