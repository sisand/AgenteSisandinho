import requests
import logging

logger = logging.getLogger(__name__)

def make_request(url, method="GET", data=None, headers=None, timeout=30):
    """
    Função genérica para fazer requisições HTTP
    """
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=timeout)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=timeout)
        else:
            raise ValueError(f"Método HTTP não suportado: {method}")
            
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na requisição HTTP: {str(e)}")
        raise
