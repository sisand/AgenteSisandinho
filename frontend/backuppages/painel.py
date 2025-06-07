import streamlit as st
from services.api_client import carregar_parametros

st.subheader("📊 Painel de Métricas do Assistente")

# Carrega métricas do backend
metrics = carregar_parametros()

if metrics:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Perguntas", metrics.get("total_perguntas", 0))
    col2.metric("Tempo Médio de Resposta", f"{metrics.get('tempo_medio_resposta', 0):.2f}s")
    col3.metric("Feedbacks Recebidos", metrics.get("feedbacks_recebidos", 0))

    st.markdown("---")
    st.info("Essas métricas ajudam a monitorar o desempenho do agente em tempo real.")
else:
    st.warning("Não foi possível carregar as métricas do backend.")
