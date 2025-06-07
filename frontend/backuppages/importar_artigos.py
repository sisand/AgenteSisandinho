# IMPORTANTE: Não use outros comandos Streamlit antes deste!
import streamlit as st
import datetime
import time
import logging
from services.api_client import importar_artigos_movidesk, verificar_status_importacao

# Configuração inicial
try:
    st.set_page_config(page_title="Importação de Artigos", layout="wide")
except Exception:
    pass

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Título
st.title("📦 Importação de Artigos do Movidesk")

# Estado inicial
if "importacao_ativa" not in st.session_state:
    st.session_state.importacao_ativa = False
    st.session_state.logs = []
    st.session_state.status_atual = {}
    st.session_state.status_etapa = "⌛ Aguardando início da importação..."

# Funções auxiliares
def adicionar_log(mensagem):
    hora = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"{hora} - {mensagem}")
    st.session_state.logs = st.session_state.logs[-30:]

def formatar_tempo(segundos):
    if not segundos:
        return "calculando..."
    m, s = divmod(int(segundos), 60)
    return f"{m:02d}:{s:02d}"

# Checkboxes
col1, col2 = st.columns(2)
with col1:
    reset_base = st.checkbox("Resetar base de dados", value=False)
with col2:
    regerar_resumo = st.checkbox("Regenerar resumos", value=True)

# Botão de importação
if not st.session_state.importacao_ativa:
    if st.button("🚀 Iniciar Importação"):
        st.session_state.importacao_ativa = True
        st.session_state.logs = []
        st.session_state.status_etapa = "⌛ Aguardando início da importação..."
        adicionar_log("⏳ Iniciando importação...")

        try:
            resposta = importar_artigos_movidesk(reset_base, regerar_resumo)
            if "error" in resposta:
                adicionar_log(f"❌ Erro: {resposta['error']}")
                st.session_state.importacao_ativa = False
            else:
                adicionar_log("✅ Solicitação enviada com sucesso")
        except Exception as e:
            adicionar_log(f"❌ Erro ao iniciar: {str(e)}")
            st.session_state.importacao_ativa = False

# STATUS AO VIVO
status_area = st.empty()
status_mensagem = st.empty()

if st.session_state.importacao_ativa:
    try:
        status = verificar_status_importacao()
        st.session_state.status_atual = status
        status_valor = status.get("status", "idle")

        if status_valor == "in_progress":
            total = status.get("total_artigos", 0)
            importados = status.get("total_importados", 0)
            percentual = status.get("percentual", 0)
            tempo = formatar_tempo(status.get("tempo_estimado"))

            st.session_state.status_etapa = f"📦 {importados} de {total} artigos importados • {percentual:.2f}%"
            status_mensagem.text(f"⏱ Tempo restante estimado: {tempo}")

        elif status_valor == "completed":
            st.session_state.importacao_ativa = False
            st.session_state.status_etapa = "✅ Importação concluída com sucesso!"
            status_mensagem.empty()
            adicionar_log("✅ Importação finalizada com sucesso!")

        elif status_valor == "idle":
            st.session_state.status_etapa = "⌛ Aguardando início da importação..."
            status_mensagem.empty()

        else:
            st.session_state.status_etapa = f"⚠️ Status desconhecido: {status_valor}"
            status_mensagem.empty()

    except Exception as e:
        adicionar_log(f"⚠️ Erro ao verificar status: {str(e)}")
        st.session_state.importacao_ativa = False

# Renderizar status
with status_area.container():
    with st.status("🚚 Importando artigos...", state="running", expanded=True):
        st.write(st.session_state.status_etapa)

# LOGS
st.markdown("### 📝 Logs da Importação")
for log in reversed(st.session_state.logs):
    st.text(log)

# Botão para nova importação
if not st.session_state.importacao_ativa and st.session_state.status_atual.get("status") == "completed":
    if st.button("🔁 Nova Importação"):
        st.session_state.logs = []
        st.session_state.status_atual = {}
        st.session_state.status_etapa = ""
        st.rerun()
