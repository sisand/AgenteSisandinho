from app.utils.http_client import make_request
from app.utils.logger import get_logger

logger = get_logger(__name__)

def buscar_tickets(limite=10):
    """
    Busca tickets do Movidesk.
    """
    try:
        url = "https://api.movidesk.com/public/v1/tickets"
        response = make_request(url, method="GET")
        return response.json()
    except Exception as e:
        logger.error(f"Erro ao buscar tickets do Movidesk: {str(e)}")
        return []
