import streamlit as st
from services.api_client import carregar_embeddings

st.subheader("🧠 Visualizar Embeddings")

embeddings = carregar_embeddings()

if "error" in embeddings:
    st.error(embeddings["error"])
elif embeddings:
    st.success("Embeddings carregados com sucesso!")
    st.json(embeddings)  # Substituir por visualização gráfica futura
else:
    st.info("Nenhum embedding encontrado.")
