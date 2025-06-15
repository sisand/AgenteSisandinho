# frontend/app.py

import streamlit as st
import pandas as pd
import os
import requests
import streamlit_authenticator as stauth
import copy 

from services.api_client import (
    enviar_pergunta,
    carregar_feedbacks,
    carregar_parametros,
    carregar_historico,
    buscar_tickets,
    salvar_curadoria,
    listar_artigos,
    importar_artigos,
    atualizar_prompt, # Corrigido para usar a função de atualização
    carregar_prompts,
    api_carregar_sessoes,
)

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Sisandinho - Assistente IA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")

# --- INICIALIZAÇÃO DO SISTEMA DE LOGIN ---
try:
    usernames_raw = st.secrets["credentials"]["usernames"]
    usernames = {
        username: {
            "email": info["email"],
            "name": info["name"],
            "password": info["password"]
        }
        for username, info in usernames_raw.items()
    }
    credentials = {"usernames": usernames}

    authenticator = stauth.Authenticate(
        credentials,
        st.secrets["cookie"]["name"],
        st.secrets["cookie"]["key"],
        st.secrets["cookie"]["expiry_days"]
    )

except KeyError as e:
    st.error(f"❌ Erro de configuração: chave '{e.args[0]}' não encontrada no secrets.toml.")
    st.stop()
except Exception as e:
    st.error(f"❌ Erro inesperado ao iniciar autenticação: {e}")
    st.stop()


# --- RENDERIZAÇÃO DO FORMULÁRIO DE LOGIN ---
col1, col2, col3 = st.columns([1.5, 2, 1.5])
with col2:
    name, authentication_status, username = authenticator.login('main')

# --- LÓGICA DE CONTROLE DE ACESSO ---
if not authentication_status:
    with col2:
        if authentication_status == False:
            st.error('Usuário ou senha incorreto.')
        elif authentication_status == None:
            st.warning('Por favor, digite seu usuário e senha para acessar.')
    st.stop()


# CABEÇALHO SUPERIOR
st.markdown(f"<h1 style='text-align: center; color: #00A86B;'>🧠 Sisandinho - Bem-vindo(a), {name}!</h1>", unsafe_allow_html=True)
st.markdown("---")

# SIDEBAR DE NAVEGAÇÃO
with st.sidebar:
    st.markdown(f"Usuário: **{name}**")
    authenticator.logout('Logout', 'main', key='unique_logout_key')
    
    st.markdown("## ⚙️ Painel de Controle")
    pagina = st.radio(
        "Escolha uma seção:",
        ["🔍 Chat & IA", "📚 Base de Conhecimento", "🗂️ Curadoria", "📊 Gestão", "⚙️ Configurações"]
    )
    st.markdown("---")
    
    st.info("Versão 1.0 - Sisandinho 🚀")

# ====================================================================================
# LÓGICA DAS PÁGINAS
# ====================================================================================

if pagina.startswith("🔍"):
    st.subheader("💬 Chat Inteligente com IA")
    st.markdown("Converse com o Sisandinho, seu especialista no ERP Vision.")

    if 'id_sessao' in st.session_state:
        st.caption(f"Sessão: {st.session_state.get('id_sessao')} | Início: {st.session_state.get('data_inicio_sessao')} às {st.session_state.get('hora_inicio_sessao')}")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if isinstance(message["content"], dict):
                st.markdown(message["content"].get("resposta", "*Ocorreu um erro ao processar a resposta.*"))
                if message["content"].get("artigos"):
                    with st.expander("📚 Fontes Consultadas"):
                        for artigo in message["content"]["artigos"]:
                            st.markdown(f"📄 [{artigo['title']}]({artigo['url']})")
            else:
                st.markdown(message["content"])

    if prompt := st.chat_input("Digite sua pergunta sobre o Vision..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🧠 Pensando..."):
                try:
                    email_do_usuario_logado = credentials["usernames"][username]["email"]
                    resposta_json = enviar_pergunta(prompt, email_usuario=email_do_usuario_logado, nome_usuario=name)
                except requests.exceptions.JSONDecodeError:
                    st.error("❌ Ocorreu um erro de comunicação com o servidor. A resposta não pôde ser processada. Verifique os logs do backend.")
                    st.stop()
                except Exception as e:
                    st.error(f"❌ Erro inesperado ao contatar a API: {e}")
                    st.stop()

            if "error" in resposta_json:
                st.error(f"Ocorreu um erro: {resposta_json['error']}")
            else:
                precisa_recarregar = False
                if 'id_sessao' not in st.session_state:
                    st.session_state['id_sessao'] = resposta_json.get('id_sessao')
                    st.session_state['data_inicio_sessao'] = resposta_json.get('data_inicio_sessao')
                    st.session_state['hora_inicio_sessao'] = resposta_json.get('hora_inicio_sessao')
                    precisa_recarregar = True

                st.markdown(resposta_json.get("resposta", "Recebi uma resposta vazia."))
                if resposta_json.get("artigos"):
                    with st.expander("📚 Fontes Consultadas", expanded=True):
                        for artigo in resposta_json["artigos"]:
                            st.markdown(f"📄 **[{artigo['title']}]({artigo['url']})**")
                
                st.session_state.messages.append({"role": "assistant", "content": resposta_json})
                
                if precisa_recarregar:
                    st.rerun()

# 📚 PÁGINA: BASE DE CONHECIMENTO
elif pagina.startswith("📚"):
    st.subheader("📚 Base de Conhecimento")
    st.markdown("Consulte e gerencie os artigos que alimentam a IA.")

    USUARIO_ADMIN = "anderson" 
    tabs_list = ["📄 Visualizar Artigos"]
    if username == USUARIO_ADMIN: 
        tabs_list.append("🔄 Importar Artigos")
    
    tab_view, *other_tabs = st.tabs(tabs_list) 

    with tab_view:
        st.subheader("🔎 Consultar Artigos na Base de Conhecimento")
        col1, col2 = st.columns([4, 1])
        with col1:
            termo_busca = st.text_input("Buscar artigos por título ou conteúdo:", key="busca_artigos",
            help="Digite um termo e clique em 'Buscar'")
        with col2:
            st.write("") 
            buscar = st.button("Buscar Artigos", type="primary", use_container_width=True)
        
        if 'termo_busca_cache' not in st.session_state:
            st.session_state.termo_busca_cache = ""
        if 'pagina_artigos' not in st.session_state:
            st.session_state.pagina_artigos = 1
            
        def carregar_dados_pagina():
            with st.spinner("Buscando..."):
                dados = listar_artigos(
                    termo_busca=st.session_state.get('termo_busca_cache', ""), 
                    pagina=st.session_state.pagina_artigos, 
                    limite=10 
                )
                st.session_state.artigos_atuais = dados.get("artigos", [])
                st.session_state.total_paginas_artigos = dados.get("total_paginas", 1)
                if not st.session_state.get('termo_busca_cache', ""):
                    st.session_state.total_itens_artigos = dados.get("total_itens", 0)

        if 'artigos_atuais' not in st.session_state:
            carregar_dados_pagina()
        
        if buscar or st.session_state.get('termo_busca_cache') != termo_busca:
            st.session_state.termo_busca_cache = termo_busca
            st.session_state.pagina_artigos = 1 
            carregar_dados_pagina()

        if 'artigos_atuais' in st.session_state and st.session_state.artigos_atuais:
            total_a_exibir = st.session_state.get('total_itens_artigos', 0)
            st.info(f"Mostrando **{len(st.session_state.artigos_atuais)}** de **{total_a_exibir}** artigos encontrados.")
            
            for artigo in st.session_state.artigos_atuais:
                with st.expander(f"**{artigo.get('title', 'Artigo sem título')}**"):
                    st.markdown(f"**URL:** [{artigo.get('url', '#')}]({artigo.get('url', '#')})")
                    st.write(f"**Resumo:** {artigo.get('resumo', 'Não disponível.')}")
        else:
            st.warning("Nenhum artigo encontrado.")

        if st.session_state.get('total_paginas_artigos', 1) > 1:
            st.markdown("---")
            total_paginas = st.session_state.total_paginas_artigos
            pagina_atual = st.session_state.pagina_artigos
            col_pag1, col_pag2, col_pag3 = st.columns([2, 3, 2])
            with col_pag1:
                if pagina_atual > 1:
                    if st.button("⬅️ Página Anterior", use_container_width=True):
                        st.session_state.pagina_artigos -= 1; carregar_dados_pagina(); st.rerun()
            with col_pag2:
                st.write(f"Página **{pagina_atual}** de **{total_paginas}**")
            with col_pag3:
                if pagina_atual < total_paginas:
                    if st.button("Próxima Página ➡️", use_container_width=True):
                        st.session_state.pagina_artigos += 1; carregar_dados_pagina(); st.rerun()

    if username == USUARIO_ADMIN and other_tabs:
        with other_tabs[0]:
            st.info("Importe novos artigos do Movidesk para o Weaviate.")
            reset_base = st.checkbox("⚠️ Resetar TODA a base do Weaviate?", value=False)
            if 'importacao_em_andamento' not in st.session_state:
                st.session_state.importacao_em_andamento = False
            if st.button("🚀 Iniciar Importação", type="primary", disabled=st.session_state.importacao_em_andamento):
                with st.spinner("Enviando solicitação..."):
                    resultado = importar_artigos(reset_base)
                    if "error" in resultado:
                        st.error(f"❌ {resultado['error']}")
                        st.session_state.importacao_em_andamento = False 
                    else:
                        st.success(f"✅ {resultado.get('message', 'Solicitação enviada!')}")
                        st.session_state.importacao_em_andamento = True
                st.rerun()
            if st.session_state.importacao_em_andamento:
                st.warning("🔄 Importação em andamento no servidor.")
                if st.button("Liberar botão de importação"):
                    st.session_state.importacao_em_andamento = False
                    st.rerun() 

# 🗂️ PÁGINA: CURADORIA E TREINAMENTO
elif pagina.startswith("🗂️"):
    st.subheader("🗂️ Curadoria e Treinamento")
    st.markdown("Gerencie feedbacks dos usuários e os prompts do sistema.")

    tab_feedbacks, tab_prompts = st.tabs(["📝 Feedbacks de Usuários", "⚙️ Gerenciar Prompts"])

    with tab_feedbacks:
        st.info("Analise os feedbacks para identificar pontos de melhoria.")
        feedbacks = carregar_feedbacks()
        if feedbacks and isinstance(feedbacks, list):
            st.dataframe(pd.DataFrame(feedbacks), use_container_width=True)
        else:
            st.warning("Nenhum feedback encontrado.")

    with tab_prompts:
        st.info("Edite os 'prompts de sistema' que definem a personalidade da IA.")
        
        prompts = carregar_prompts()
        if not prompts or not isinstance(prompts, list):
            st.warning("Nenhum prompt encontrado.")
        else:
            st.dataframe(pd.DataFrame(prompts), use_container_width=True)
            
            if "prompt_selecionado" not in st.session_state:
                st.session_state.prompt_selecionado = None

            prompt_options = {p['nome']: p for p in prompts}
            prompt_selecionado_nome = st.selectbox(
                "Escolha um prompt na lista abaixo para editar:", 
                options=["Nenhum"] + list(prompt_options.keys())
            )

            if prompt_selecionado_nome and prompt_selecionado_nome != "Nenhum":
                st.session_state.prompt_selecionado = prompt_options[prompt_selecionado_nome]
            else:
                 st.session_state.prompt_selecionado = None

            st.markdown("---")

            conteudo_para_editar = ""
            if st.session_state.prompt_selecionado:
                conteudo_para_editar = st.session_state.prompt_selecionado.get('conteudo', '')
                st.markdown(f"**Editando prompt:** `{st.session_state.prompt_selecionado.get('nome')}`")
            
            novo_prompt = st.text_area(
                "Conteúdo do Prompt:", 
                value=conteudo_para_editar,
                height=250,
                key="editor_prompt"
            )
            
            if st.button("💾 Salvar Prompt", type="primary"):
                if st.session_state.prompt_selecionado:
                    id_prompt_para_salvar = st.session_state.prompt_selecionado.get('id')
                    nome_prompt = st.session_state.prompt_selecionado.get('nome')
                    
                    resultado = atualizar_prompt(id_prompt=id_prompt_para_salvar, nome=nome_prompt, conteudo=novo_prompt)
                    
                    if "error" in resultado:
                        st.error(f"Erro ao salvar: {resultado['error']}")
                    else:
                        st.success(f"✅ Prompt '{nome_prompt}' atualizado com sucesso!")
                        st.session_state.prompt_selecionado = None
                        st.rerun()
                else:
                    st.warning("Selecione um prompt da lista para poder salvar.")

# 📊 PÁGINA: GESTÃO E MONITORAMENTO
elif pagina.startswith("📊"):
    st.subheader("📊 Gestão e Monitoramento")
    st.markdown("Visualize o histórico de interações e outros dados operacionais.")
    
    tab_hist, tab_tickets = st.tabs(["💬 Histórico de Perguntas", "🧾 Tickets Movidesk"])

    with tab_hist:
        historico = carregar_historico()
        if historico and isinstance(historico, list):
            st.dataframe(pd.DataFrame(historico), use_container_width=True)
        else:
            st.warning("Nenhum histórico encontrado.")

    with tab_tickets:
        tickets = buscar_tickets()
        if tickets and isinstance(tickets, list):
            st.dataframe(pd.DataFrame(tickets), use_container_width=True)
        else:
            st.warning("Nenhum ticket encontrado.")

# ⚙️ PÁGINA: CONFIGURAÇÕES
elif pagina.startswith("⚙️"):
    st.subheader("⚙️ Configurações do Sistema")
    st.markdown("Visualize os parâmetros carregados do banco de dados.")

    parametros = carregar_parametros()
    if parametros and isinstance(parametros, list):
        params_dict = {p['nome']: p['valor'] for p in parametros}
        st.json(params_dict)
    else:
        st.warning("Nenhum parâmetro encontrado.")
    
    if st.button("🔄 Recarregar Parâmetros do Banco"):
        st.info("Funcionalidade de recarga a ser implementada.")


# 🔚 RODAPÉ GLOBAL
st.markdown("---")
st.caption("🧠 Sisandinho - Powered by Sisand © 2025")

