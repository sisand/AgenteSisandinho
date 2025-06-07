import logging
import time
from typing import Optional, List, Dict

from app.services.classificador import classificar_pergunta
from app.services.gerador_resposta import gerar_resposta
from app.core.clients import get_supabase_client
from app.core.clients import generate_chat_completion, gerar_embedding_openai, buscar_artigos_por_embedding



logger = logging.getLogger(__name__)

# 🔥 Histórico em memória (substituir futuramente por Redis, banco, etc.)
_historico_conversas: Dict[str, List[Dict[str, str]]] = {}

# 🔸 Adiciona mensagem no histórico
def adicionar_ao_historico(usuario_id: int, mensagem: str, eh_usuario: bool = True):
    """
    Adiciona uma mensagem ao histórico local.

    Args:
        usuario_id (int): ID do usuário.
        mensagem (str): Conteúdo da mensagem.
        eh_usuario (bool): True se for do usuário, False se for da IA.
    """
    if not usuario_id:
        return

    if usuario_id not in _historico_conversas:
        _historico_conversas[usuario_id] = []

    _historico_conversas[usuario_id].append({
        "role": "user" if eh_usuario else "assistant",
        "content": mensagem
    })

    if len(_historico_conversas[usuario_id]) > 20:
        _historico_conversas[usuario_id] = _historico_conversas[usuario_id][-20:]


# 🔸 Recupera o histórico do usuário
def obter_historico_usuario(usuario_id: int, max_mensagens: int = 3) -> str:
    """
    Retorna até N mensagens anteriores do usuário no formato texto.

    Args:
        usuario_id (int): ID do usuário.
        max_mensagens (int): Quantidade máxima de mensagens.

    Returns:
        str: Histórico concatenado.
    """
    if not usuario_id or usuario_id not in _historico_conversas:
        logger.info(f"📜 Sem histórico para o usuário {usuario_id}")
        return ""

    mensagens = _historico_conversas[usuario_id]
    perguntas = [
        m["content"] for m in reversed(mensagens)
        if m["role"] == "user"
    ][:max_mensagens]

    if not perguntas:
        logger.info(f"📜 Nenhuma pergunta relevante no histórico")
        return ""

    perguntas.reverse()
    historico = "\n".join(f"Usuário: {p}" for p in perguntas)
    logger.info(f"📜 Histórico recuperado: {historico}")
    return historico


# 🔸 Salva a interação no Supabase
async def salvar_interacao(
    usuario_id: Optional[int],
    pergunta: str,
    resposta: str,
    categoria: str = "geral"
):
    """
    Salva pergunta, resposta e categoria no Supabase.

    Args:
        usuario_id (Optional[int]): ID do usuário.
        pergunta (str): Pergunta feita.
        resposta (str): Resposta gerada.
        categoria (str): Classificação da pergunta.
    """
    try:
        client = get_supabase_client()

        data = {
            "usuario_id": usuario_id,
            "pergunta": pergunta,
            "resposta": resposta,
            "categoria": categoria
        }

        response = client.table("mensagens").insert(data).execute()

        if response.data:
            logger.info(f"✅ Interação salva no Supabase para usuário {usuario_id}")
        else:
            logger.warning(f"⚠️ Nenhum dado salvo no Supabase. Resposta: {response}")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar interação no Supabase: {e}")


# Cole esta função no lugar da sua 'processar_pergunta' atual em app/services/fluxo_chat.py

# 🔥 Pipeline principal
async def processar_pergunta(usuario_id: Optional[int], pergunta: str) -> Dict:
    """
    Pipeline principal que processa a pergunta (Versão Nível 1 - Especialista Confiável):
    - Classifica a intenção.
    - Decide se precisa de RAG ou não.
    - Gera resposta formatada e com fontes.
    - Salva no histórico e Supabase.
    """
    inicio = time.time()
    logger.info(f"🧠 Pergunta recebida: {pergunta}")

    adicionar_ao_historico(usuario_id, pergunta, eh_usuario=True)

    # 1️⃣ Classifica categoria
    categoria = await classificar_pergunta(pergunta)
    logger.info(f"📚 Classificação da pergunta: {categoria}")

    # 2️⃣ Decide se precisa de RAG
    precisa_rag = await classificar_precisa_rag(pergunta)
    logger.info(f"🔍 Precisa usar RAG? {precisa_rag}")

    artigos_encontrados = []
    resposta = ""

    # 3️⃣ Gera resposta com ou sem RAG
    if precisa_rag:
        logger.info("🚀 Buscando artigos no Weaviate...")
        artigos_encontrados = await buscar_artigos_weaviate(pergunta, categoria=categoria)
        logger.info(f"✅ {len(artigos_encontrados)} artigos encontrados.")

        # Lógica de RAG aprimorada
        if artigos_encontrados:
            # Monta o contexto para o LLM
            contexto = "\n\n---\n\n".join(
                [f"Título: {a['title']}\nURL: {a['url']}\nConteúdo: {a['content']}" for a in artigos_encontrados]
            )

            # Prepara os títulos para a citação de fontes
            titulos_fontes = "\n".join([f"* {a['title']}" for a in artigos_encontrados])

            # === MELHORIA NÍVEL 1: PROMPT DO SISTEMA ===
            # PROMPT FINAL E REFINADO
            system_prompt = """
            Você é um assistente especialista no ERP Vision, amigável e extremamente didático. Sua missão é fornecer respostas claras e precisas baseadas exclusivamente nos artigos da base de conhecimento fornecidos.

            **Instruções de Resposta:**
            1.  Analise a pergunta do usuário e o contexto dos artigos fornecidos.
            2.  Formule uma resposta direta e útil. Se a pergunta for sobre "como fazer", crie um passo a passo. Se for sobre "o que é", crie uma explicação concisa.
            3.  Use **Markdown** para formatar a resposta (use **negrito** para destacar menus, botões e conceitos importantes) para máxima clareza.
            4.  **IMPORTANTE: Não inclua os títulos dos artigos ou links no corpo da sua resposta principal.** A interface do usuário cuidará de exibir as fontes separadamente. A sua resposta deve ser um texto limpo, coeso e autônomo.
            5.  **NUNCA** invente informações. Se a resposta não estiver no contexto, informe que não encontrou a informação nos artigos.
            6.  Encerre de forma amigável, incentivando o usuário a fazer mais perguntas caso a dúvida não tenha sido totalmente esclarecida.
            """

            # === MELHORIA NÍVEL 1: MENSAGEM DO USUÁRIO ===
            # user_message ATUALIZADA (opcional, mas recomendado)
            user_message = f"""
            **Artigos da Base de Conhecimento (Contexto):**
            ---
            {contexto}
            ---

            **Pergunta do Usuário:**
            "{pergunta}"
            """

            resposta = await generate_chat_completion(
                system_prompt=system_prompt,
                user_message=user_message,
                temperature=0.2,  # Baixamos a temperatura para respostas mais factuais
                max_tokens=1024   # Aumentamos um pouco para acomodar a formatação
            )
        else:
            # Se o RAG foi acionado mas não encontrou artigos, caia para a resposta padrão
            logger.warning("⚠️ RAG solicitado, mas nenhum artigo encontrado. Usando resposta padrão.")
            precisa_rag = False # Força a entrada no bloco 'else' abaixo

    if not precisa_rag: # Ativado se o RAG não for necessário ou se falhou em encontrar artigos
        logger.info("💬 Respondendo sem RAG (conhecimento geral)...")
        system_prompt = "Você é um assistente amigável e prestativo especializado no ERP Vision. Responda à pergunta do usuário de forma clara e objetiva com base no seu conhecimento geral."
        user_message = pergunta

        resposta = await generate_chat_completion(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.7,
            max_tokens=800
        )

    # 4️⃣ Adiciona resposta ao histórico e salva interação
    adicionar_ao_historico(usuario_id, resposta, eh_usuario=False)
    await salvar_interacao(usuario_id, pergunta, resposta, categoria)

    tempo = round(time.time() - inicio, 2)

    # 5️⃣ Prepara retorno
    return {
        "resposta": resposta,
        "categoria": categoria,
        "artigos": artigos_encontrados,
        "tempo_processamento": tempo,
        "prompt_usado": "Prompt Nível 1 - Especialista Confiável" # Atualiza o nome do prompt
    }


async def classificar_precisa_rag(pergunta: str) -> bool:
    """
    Classifica se a pergunta precisa ou não de busca RAG (Weaviate).
    Retorna True (precisa RAG) ou False (não precisa).
    """

    system_prompt = "Você é um classificador. Para cada pergunta, responda apenas com SIM ou NÃO, conforme a necessidade de consultar artigos no RAG (Weaviate)."

    user_prompt = f"""
    Critérios:
    - Se a pergunta envolve informações dinâmicas, procedimentos detalhados, atualizações recentes ou dúvidas comuns de suporte → SIM.
    - Se a pergunta é genérica, social ou um processo padrão bem conhecido → NÃO.

    Exemplos:
    1. "Como lançar uma nota fiscal?" → NÃO
    2. "Como configurar o envio de XML para a contabilidade?" → SIM
    3. "Boa tarde, tudo bem?" → NÃO
    4. "Onde encontro os relatórios de comissão?" → SIM
    5. "Qual o telefone do suporte?" → NÃO

    Pergunta: "{pergunta}"
    Responda apenas SIM ou NÃO.
    """

    resposta = await generate_chat_completion(
        system_prompt=system_prompt,
        user_message=user_prompt,
        temperature=0,
        max_tokens=5
    )

    # Normaliza e interpreta
    resposta_limpa = resposta.strip().upper()

    if "SIM" in resposta_limpa:
        return True
    elif "NÃO" in resposta_limpa or "NAO" in resposta_limpa:
        return False
    else:
        # fallback defensivo → se a IA não responder certo, assume que não precisa RAG
        return False


# 👇 ESTA É A VERSÃO FINAL DA FUNÇÃO QUE ORQUESTRA TUDO 👇
# (Substitua a versão anterior que criamos)
async def buscar_artigos_weaviate(pergunta: str, categoria: str, limite: int = 3) -> list:
    """
    Orquestra a busca de artigos:
    1. Gera o embedding da pergunta.
    2. Busca os artigos no Weaviate usando o embedding e o filtro de categoria.
    """
    logger.info(f"Iniciando busca RAG para a pergunta: '{pergunta}'")
    
    # Passo 1: Gerar o embedding para a pergunta do usuário
    embedding = await gerar_embedding_openai(pergunta)
    
    # Verifica se a geração do embedding falhou
    if embedding is None:
        logger.warning("Não foi possível gerar o embedding da pergunta. Abortando busca RAG.")
        return []

    # Passo 2: Buscar artigos no Weaviate usando o embedding e a categoria
    logger.info("Buscando artigos no Weaviate com o embedding gerado...")
    artigos_encontrados = await buscar_artigos_por_embedding(
        embedding=embedding,
        categoria=categoria,
        limit=limite
    )
    
    return artigos_encontrados