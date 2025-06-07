def montar_prompt_padrao(pergunta: str, contexto: list[str]) -> str:
    """
    Monta um prompt padrão usando a pergunta do usuário e os trechos dos artigos encontrados.
    """
    return (
        "Você é um assistente da Sisand. Use as informações abaixo para responder de forma didática e objetiva.\n\n"
        "Contexto:\n"
        + "\n\n".join(contexto) +
        f"\n\nPergunta: {pergunta}\n\nResposta:"
    )
