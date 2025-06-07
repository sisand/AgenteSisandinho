import streamlit as st
from services.api_client import carregar_prompts, atualizar_prompt

st.subheader("⚙️ Editor de Prompts do Agente")

prompts = carregar_prompts()

if not prompts:
    st.warning("Não foi possível carregar os prompts.")
else:
    for prompt in prompts:
        with st.expander(f"Prompt: {prompt['nome']}"):
            conteudo = st.text_area(
                f"Conteúdo do Prompt",
                value=prompt.get("conteudo", ""),
                height=200,
                key=f"text_{prompt['nome']}"
            )
            if st.button(f"Salvar alterações", key=f"save_{prompt['nome']}"):
                resultado = atualizar_prompt(nome=prompt['nome'], conteudo=conteudo)
                if resultado.get("error"):
                    st.error(f"Erro: {resultado['error']}")
                else:
                    st.success("✅ Prompt atualizado com sucesso!")
