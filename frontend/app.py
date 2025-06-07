import streamlit as st
import pandas as pd
from services.api_client import (
    enviar_pergunta,
    carregar_feedbacks,
    carregar_parametros,
    carregar_historico,
    buscar_tickets,
    salvar_curadoria,
    listar_artigos,
    importar_artigos,
    salvar_prompt,
    carregar_prompts,
    api_carregar_sessoes,
)

# 🔥 CONFIGURAÇÃO GLOBAL DO APP
st.set_page_config(
    page_title="Sisandinho - Assistente IA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🏠 CABEÇALHO SUPERIOR
st.markdown(
    "<h1 style='text-align: center; color: #00A86B;'>🧠 Sisandinho - Assistente Virtual da Sisand</h1>",
    unsafe_allow_html=True
)
st.markdown("---")

# 🚦 SIDEBAR DE NAVEGAÇÃO
with st.sidebar:
    st.markdown("## ⚙️ Painel de Controle")
    pagina = st.radio(
        "Escolha uma seção:",
        [
            "🔍 Chat & IA",
            "📚 Base de Conhecimento",
            "🗂️ Curadoria e Treinamento",
            "📊 Gestão e Monitoramento",
            "⚙️ Configurações"
        ],
        index=0,
        help="Navegue entre as diferentes áreas de gerenciamento do assistente."
    )

    st.markdown("---")
    st.markdown("### 🟢 Status do Sistema")
    # Usando st.select_slider para um visual mais interessante
    status = st.select_slider(
        "Status:",
        options=["Online", "Manutenção", "Offline"],
        value="Online"
    )

    st.markdown("---")
    st.info("Versão 1.0 - Sisandinho 🚀")


# ====================================================================================
# 🔍 PÁGINA: CHAT & IA
if pagina.startswith("🔍"):
    st.subheader("💬 Chat Inteligente com IA")
    st.markdown("Converse com o Sisandinho, seu especialista no ERP Vision.")

    # Para manter o histórico na tela, usamos o session_state do Streamlit
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": {"resposta": "Olá! Como posso ajudar você hoje com o sistema Vision?"}}]

    # Exibe as mensagens do histórico
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if isinstance(message["content"], dict):
                st.markdown(message["content"]["resposta"])
                if message["content"].get("artigos"):
                    with st.expander("📚 Fontes Consultadas"):
                        for artigo in message["content"]["artigos"]:
                            st.markdown(f"📄 [{artigo['title']}]({artigo['url']})")
            else:
                st.markdown(message["content"])

    # Captura a nova pergunta do usuário
    if pergunta := st.chat_input("Digite sua pergunta sobre o Vision..."):
        st.session_state.messages.append({"role": "user", "content": pergunta})
        with st.chat_message("user"):
            st.markdown(pergunta)

        with st.chat_message("assistant"):
            with st.spinner("🧠 Pensando..."):
                resposta_json = enviar_pergunta(pergunta, usuario_id=1, usuario_nome="Anderson")
            
            st.markdown(resposta_json["resposta"])

            if resposta_json.get("artigos"):
                with st.expander("📚 Fontes Consultadas", expanded=True):
                    for artigo in resposta_json["artigos"]:
                        st.markdown(f"📄 **[{artigo['title']}]({artigo['url']})**")
            
            st.session_state.messages.append({"role": "assistant", "content": resposta_json})

# ====================================================================================
# 📚 PÁGINA: BASE DE CONHECIMENTO
elif pagina.startswith("📚"):
    st.subheader("📚 Base de Conhecimento")
    st.markdown("Consulte e gerencie os artigos que alimentam a IA.")

    # Usando st.tabs para uma navegação mais fluida e moderna
    tab_view, tab_import = st.tabs(["📄 Visualizar Artigos", "🔄 Importar Artigos"])

    with tab_view:
        st.info("Clique em um artigo para expandir e ver os detalhes.")
        artigos = listar_artigos()
        if artigos:
            # Usando st.expander para uma lista mais limpa
            for artigo in artigos:
                with st.expander(f"**{artigo['title']}**"):
                    st.write(f"**Resumo:** {artigo.get('resumo', 'Não disponível.')}")
                    st.markdown(f"**URL:** [{artigo.get('url', '#')}]({artigo.get('url', '#')})")
                    st.code(artigo.get('content', 'Conteúdo não disponível.'), language='markdown')
        else:
            st.warning("Nenhum artigo encontrado.")

    with tab_import:
        st.info("Importe novos artigos do Movidesk para o Weaviate.")
        st.warning("A importação pode levar alguns minutos e irá consumir tokens da OpenAI para gerar os embeddings.")
        reset_base = st.checkbox("⚠️ Resetar TODA a base do Weaviate antes de importar?", value=False)

        if st.button("🚀 Iniciar Importação", type="primary"):
            with st.spinner("⏳ Importando artigos... Este processo pode demorar."):
                try:
                    resultado = importar_artigos(reset_base)
                    st.success("✅ Importação concluída com sucesso!")
                    st.json(resultado)
                except Exception as e:
                    st.error(f"❌ Erro durante a importação: {str(e)}")

# ====================================================================================
# 🗂️ PÁGINA: CURADORIA E TREINAMENTO
elif pagina.startswith("🗂️"):
    st.subheader("🗂️ Curadoria e Treinamento")
    st.markdown("Gerencie feedbacks dos usuários e os prompts do sistema.")

    tab_feedbacks, tab_prompts = st.tabs(["📝 Feedbacks de Usuários", "⚙️ Gerenciar Prompts"])

    with tab_feedbacks:
        st.info("Analise os feedbacks para identificar pontos de melhoria na base de conhecimento ou no comportamento da IA.")
        feedbacks = carregar_feedbacks()
        if feedbacks:
            st.dataframe(pd.DataFrame(feedbacks), use_container_width=True)
        else:
            st.warning("Nenhum feedback encontrado.")

    with tab_prompts:
        st.info("Edite os 'prompts de sistema' que definem a personalidade e as instruções da IA.")
        prompts = carregar_prompts()
        if prompts:
            st.dataframe(pd.DataFrame(prompts), use_container_width=True)
        else:
            st.warning("Nenhum prompt encontrado.")
        
        st.markdown("---")
        novo_prompt = st.text_area("Adicionar ou Editar Prompt:", height=200)
        if st.button("💾 Salvar Prompt"):
            salvar_prompt(novo_prompt)
            st.success("Prompt salvo com sucesso!")

# ====================================================================================
# 📊 PÁGINA: GESTÃO E MONITORAMENTO
elif pagina.startswith("📊"):
    st.subheader("📊 Gestão e Monitoramento")
    st.markdown("Visualize o histórico de interações e outros dados operacionais do assistente.")
    
    tab_hist, tab_tickets = st.tabs(["💬 Histórico de Perguntas", "🧾 Tickets Movidesk"])

    with tab_hist:
        historico = carregar_historico()
        if historico:
            st.dataframe(pd.DataFrame(historico), use_container_width=True)
        else:
            st.warning("Nenhum histórico encontrado.")

    with tab_tickets:
        tickets = buscar_tickets()
        if tickets:
            st.dataframe(pd.DataFrame(tickets), use_container_width=True)
        else:
            st.warning("Nenhum ticket encontrado.")

# ====================================================================================
# ⚙️ PÁGINA: CONFIGURAÇÕES
elif pagina.startswith("⚙️"):
    st.subheader("⚙️ Configurações do Sisandinho")
    st.markdown("Parâmetros do sistema e comportamento da IA.")

    parametros = carregar_parametros()
    if parametros:
        st.json(parametros)
    else:
        st.warning("Nenhum parâmetro encontrado.")
    
    st.markdown("---")
    if st.button("🔄 Atualizar Parâmetros"):
        st.info("Funcionalidade de atualização a ser implementada.")

# ====================================================================================
# 🔚 RODAPÉ GLOBAL
st.markdown("---")
st.caption("🧠 Sisandinho - Powered by Sisand © 2025")