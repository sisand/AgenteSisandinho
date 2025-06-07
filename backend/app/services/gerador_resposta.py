import logging

logger = logging.getLogger(__name__)


async def gerar_resposta(pergunta: str, categoria: str) -> str:
    """
    Gera a resposta para a pergunta com base na categoria detectada.

    No momento, é uma resposta mockada (simulada).
    Futuramente será substituído por:
    - Fine-tune treinado
    - Busca por RAG (Weaviate)
    - Ou ambos combinados

    Args:
        pergunta (str): Texto da pergunta feita pelo usuário.
        categoria (str): Categoria identificada (fiscal, oficina, financeiro, etc.).

    Returns:
        str: Texto da resposta gerada.
    """
    logger.info(f"🎯 Gerando resposta para categoria: {categoria} | Pergunta: {pergunta}")

    # 🔥 Mock inicial — depois substituímos por geração real
    resposta = f"Estou processando sua pergunta sobre {categoria}. Em breve terei uma resposta mais completa."

    return resposta
