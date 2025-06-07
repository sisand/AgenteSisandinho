import streamlit as st
import sys
import os
from pathlib import Path

# Adicionar o diretório pai ao path para resolver importações
frontend_dir = Path(__file__).parent.parent
sys.path.append(str(frontend_dir))

# Agora podemos importar de módulos no diretório frontend
from services.api_client import enviar_pergunta, api_obter_ou_criar_sessao, carregar_mensagens_sessao, api_obter_detalhes_sessao
import datetime
import logging
import time
import pytz

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Marcar início de renderização para métricas
start_time = time.time()

# Verificar se o módulo está sendo executado como página principal ou importado
# Se importado por app.py, não mostrar título novamente
if not st.session_state.get('_is_imported_chat'):
    # Título e sessão (exibidos apenas quando executado como página principal)
    st.subheader("\U0001F4AC Chat Inteligente")

# Restante do código do chat
usuario_id = 1

# Obter ou criar sessão ativa (últimos 15 min)
sessao_id = api_obter_ou_criar_sessao(usuario_id)
logger.info(f"Sessão ativa: {sessao_id}")

# Se mudou de sessão, limpar histórico
if st.session_state.get('sessao_id') != sessao_id:
    st.session_state.mensagens = []
st.session_state.sessao_id = sessao_id

# Exibir info da sessão com tratamento de erro aprimorado
if sessao_id:
    try:
        # Se é sessão local, não tenta buscar detalhes
        if isinstance(sessao_id, str) and sessao_id.startswith("local_"):
            st.caption(f"💬 Sessão local temporária • {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
        else:
            detalhes = st.session_state.get('sessao_atual_detalhes', {})
            if detalhes.get('id') != sessao_id:
                logger.info(f"Obtendo detalhes da sessão {sessao_id}")
                detalhes = api_obter_detalhes_sessao(sessao_id) or {}
                st.session_state.sessao_atual_detalhes = detalhes
                logger.info(f"Detalhes da sessão {sessao_id} obtidos com sucesso")
            
            inicio = detalhes.get('inicio', '')
            if 'T' in inicio:
                dt_utc = datetime.datetime.fromisoformat(inicio.replace('Z', '+00:00'))
                fuso_brasilia = pytz.timezone("America/Sao_Paulo")
                dt_local = dt_utc.astimezone(fuso_brasilia)
                inicio_fmt = dt_local.strftime('%d/%m/%Y %H:%M')
            else:
                inicio_fmt = inicio
            st.caption(f"Sessão #{sessao_id} • Iniciada em {inicio_fmt}")
    except Exception as e:
        logger.warning(f"Erro detalhes sessão: {e}")
        st.caption(f"Sessão #{sessao_id}")

# Carregar mensagens existentes
if "mensagens" not in st.session_state:
    try:
        raw = carregar_mensagens_sessao(sessao_id)
        msgs = []
        for m in raw:
            tempo = m.get("created_at", "")[:16].replace("T", " ")
            msgs.append({"role": "user", "content": m.get("pergunta", ""), "time": tempo})
            msgs.append({"role": "assistant", "content": m.get("resposta", ""), "time": tempo, "prompt": m.get("prompt_usado", "")})
        st.session_state.mensagens = msgs
    except Exception as e:
        logger.error(f"Erro carregar mensagens: {e}")
        st.session_state.mensagens = []

# Campo de input e lógica de envio
if prompt := st.chat_input("Digite sua mensagem..."):
    agora = datetime.datetime.now().strftime("%H:%M")
    user_msg = {"role": "user", "content": prompt, "time": agora}
    st.session_state.mensagens.append(user_msg)

    try:
        with st.spinner("Processando..."):
            resp = enviar_pergunta(pergunta=prompt, usuario_id=usuario_id)

        resposta = resp.get("resposta", "Sem resposta.")
        tipo = resp.get("tipo", "desconhecido")
        prompt_usado = resp.get("prompt_usado", "")
        logger.info(f"\U0001F9E0 Tipo: {tipo} | Prompt presente: {'sim' if prompt_usado else 'não'}")

        assistant_msg = {
            "role": "assistant",
            "content": resposta,
            "time": agora,
            "prompt": prompt_usado
        }
        st.session_state.mensagens.append(assistant_msg)
    except Exception as e:
        logger.error(f"Erro ao responder: {e}")
        assistant_msg = {
            "role": "assistant",
            "content": "Erro interno.",
            "time": agora
        }
        st.session_state.mensagens.append(assistant_msg)

# Exibir histórico de mensagens após envio (garante que prompt usado apareça imediatamente)
for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("prompt"):
            with st.expander("\U0001F4C4 Ver prompt usado"):
                st.code(msg["prompt"], language="markdown")

# Métrica de performance
logger.info(f"Render em {time.time()-start_time:.2f}s")
