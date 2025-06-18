# frontend/app.py

import streamlit as st
import pandas as pd
import os
import requests
import streamlit_authenticator as stauth
import copy
import plotly.express as px # Import para gráficos
from datetime import date, timedelta

from services.api_client import (
    enviar_pergunta,
    carregar_feedbacks,
    carregar_metricas,
    enviar_feedback,
    listar_artigos,
    importar_artigos,
    atualizar_prompt,
    carregar_prompts,
    carregar_parametros,
    atualizar_parametro
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


# --- RENDERIZAÇÃO DO FORMULÁRIO DE LOGIN E CONTROLE DE FLUXO ---

# Cria 3 colunas para centralizar o formulário. A do meio (col2) é onde o login aparecerá.
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    name, authentication_status, username = authenticator.login('main')

    if authentication_status == False:
        st.error('Usuário ou senha incorreto.')
        st.stop()
    elif authentication_status == None:
        st.warning('Por favor, digite seu usuário e senha para acessar.')
        st.stop()

# O restante do código abaixo só será executado se o login for bem-sucedido
if authentication_status:
    # ##########################################################################
    # ### INÍCIO DA APLICAÇÃO PRINCIPAL (SÓ EXECUTA APÓS LOGIN) ###
    # ##########################################################################

    # CABEÇALHO SUPERIOR
    st.markdown(f"<h1 style='text-align: center; color: #00A86B;'>🧠 Sisandinho - Bem-vindo(a), {name}!</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # SIDEBAR DE NAVEGAÇÃO
    with st.sidebar:
        st.markdown(f"Usuário: **{name}**")
        authenticator.logout('Logout', 'main', key='unique_logout_key')

        st.markdown("## ⚙️ Painel de Controle")

        USUARIO_ADMIN = "anderson"
        paginas_disponiveis = ["🔍 Chat & IA", "📚 Base de Conhecimento", "🗂️ Curadoria", "📊 Gestão"]
        if username == USUARIO_ADMIN:
            paginas_disponiveis.append("⚙️ Configurações")

        pagina = st.radio(
            "Escolha uma seção:",
            paginas_disponiveis
        )

        st.markdown("---")
        st.info("Versão 1.0 - Sisandinho 🚀")

        caminho_do_script = os.path.dirname(os.path.abspath(__file__))
        caminho_da_imagem = os.path.join(caminho_do_script, "assets", "sisandinho.png")
        st.sidebar.image(caminho_da_imagem, caption='Sisandinho, seu assistente!', width=150)

    # ====================================================================================
    # LÓGICA DAS PÁGINAS
    # ====================================================================================

    if pagina.startswith("🔍"):
        st.subheader("💬 Chat Inteligente com IA")
        if 'id_sessao' in st.session_state:
            st.caption(f"Sessão: {st.session_state.get('id_sessao')} | Início: {st.session_state.get('data_inicio_sessao')} às {st.session_state.get('hora_inicio_sessao')}")
        if "messages" not in st.session_state:
            st.session_state.messages = []
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                content = message["content"]
                resposta_texto = content.get("resposta", content) if isinstance(content, dict) else content
                st.markdown(resposta_texto)
                if message["role"] == "assistant" and isinstance(content, dict):
                    id_mensagem = content.get("id_mensagem")
                    if content.get("artigos"):
                        with st.expander("📚 Fontes Consultadas", expanded=True):
                            for artigo in content["artigos"]:
                                st.markdown(f"📄 [{artigo.get('title', 'Link sem título')}]({artigo.get('url')})")
                    if id_mensagem:
                        col1_feedback, col2_feedback, _ = st.columns([1, 1, 8])
                        with col1_feedback:
                            if st.button("👍", key=f"like_{id_mensagem}"):
                                enviar_feedback(id_mensagem, "positivo"); st.toast("Obrigado pelo seu feedback!")
                        with col2_feedback:
                            if st.button("👎", key=f"dislike_{id_mensagem}"):
                                enviar_feedback(id_mensagem, "negativo"); st.toast("Obrigado! Vamos usar seu feedback para melhorar.")
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
                    precisa_recarregar = 'id_sessao' not in st.session_state
                    if precisa_recarregar:
                        st.session_state['id_sessao'] = resposta_json.get('id_sessao')
                        st.session_state['data_inicio_sessao'] = resposta_json.get('data_inicio_sessao')
                        st.session_state['hora_inicio_sessao'] = resposta_json.get('hora_inicio_sessao')
                    st.session_state.messages.append({"role": "assistant", "content": resposta_json})
                    st.rerun()

    elif pagina.startswith("📚"):
        st.subheader("📚 Base de Conhecimento")
        st.markdown("Consulte e gerencie os artigos que alimentam a IA.")
        tabs_list = ["📄 Visualizar Artigos"]
        if username == USUARIO_ADMIN:
            tabs_list.append("🔄 Importar Artigos")
        tabs = st.tabs(tabs_list)
        with tabs[0]:
            st.subheader("🔎 Consultar Artigos na Base de Conhecimento")
            col1_busca, col2_busca = st.columns([4, 1])
            with col1_busca:
                termo_busca = st.text_input("Buscar artigos por título ou conteúdo:", key="busca_artigos", help="Digite um termo e clique em 'Buscar'")
            with col2_busca:
                st.write("")
                buscar = st.button("Buscar Artigos", type="primary", use_container_width=True)
            if 'termo_busca_cache' not in st.session_state:
                st.session_state.termo_busca_cache = ""
            if 'pagina_artigos' not in st.session_state:
                st.session_state.pagina_artigos = 1
            def carregar_dados_pagina():
                with st.spinner("Buscando..."):
                    dados = listar_artigos(termo_busca=st.session_state.get('termo_busca_cache', ""), pagina=st.session_state.pagina_artigos, limite=10)
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
        if username == USUARIO_ADMIN and len(tabs) > 1:
            with tabs[1]:
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

    elif pagina.startswith("🗂️"):
        st.subheader("🗂️ Curadoria e Treinamento")
        st.markdown("Gerencie feedbacks dos usuários e os prompts do sistema.")
        tabs_disponiveis = ["📝 Feedbacks de Usuários"]
        if username == USUARIO_ADMIN:
            tabs_disponiveis.append("⚙️ Gerenciar Prompts")
        tabs = st.tabs(tabs_disponiveis)
        with tabs[0]:
            st.info("Analise os feedbacks para identificar pontos de melhoria.")
            feedbacks = carregar_feedbacks()
            if feedbacks and isinstance(feedbacks, list):
                st.dataframe(pd.DataFrame(feedbacks), use_container_width=True)
            else:
                st.warning("Nenhum feedback encontrado.")
        if username == USUARIO_ADMIN and len(tabs) > 1:
            with tabs[1]:
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

    elif pagina.startswith("📊"):
        st.subheader("📊 Gestão e Monitoramento")
        st.markdown("#### Filtrar por Período")
        col1_gestao, col2_gestao = st.columns(2)
        with col1_gestao:
            data_inicio = st.date_input("Data de Início", value=date.today() - timedelta(days=30))
        with col2_gestao:
            data_fim = st.date_input("Data de Fim", value=date.today())
        if data_inicio > data_fim:
            st.error("A data de início não pode ser posterior à data de fim.")
        else:
            with st.spinner(f"Carregando métricas de {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}..."):
                metricas = carregar_metricas(data_inicio, data_fim)
            if "error" in metricas:
                st.error(f"Não foi possível carregar as métricas: {metricas['error']}")
            else:
                st.markdown(f"### Visão Geral do Período")
                col1_metricas, col2_metricas, col3_metricas = st.columns(3)
                col1_metricas.metric("Total de Usuários (Geral)", metricas.get("total_usuarios", 0))
                col2_metricas.metric("Sessões no Período", metricas.get("total_sessoes_periodo", 0))
                col3_metricas.metric("Mensagens no Período", metricas.get("total_mensagens_periodo", 0))
                st.markdown("---")
                st.markdown("### Evolução do Desempenho")
                historico = metricas.get("historico_desempenho", [])
                if historico:
                    df_historico = pd.DataFrame(historico).set_index('Data')
                    st.line_chart(df_historico)
                else:
                    st.info("Não há dados suficientes no período para exibir a evolução do desempenho.")
                st.markdown("---")
                st.markdown("### Análise em Tempo Real (Últimas 10 Interações)")
                ultimas_interacoes = metricas.get("ultimas_interacoes", [])
                if ultimas_interacoes:
                    df_interacoes = pd.DataFrame(ultimas_interacoes)
                    st.dataframe(df_interacoes, use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhuma interação recente para exibir.")
                st.markdown("### Desempenho e Custos")
                col1_desempenho, col2_desempenho = st.columns(2)
                with col1_desempenho:
                    st.markdown("##### Velocidade (s)")
                    sub_col1, sub_col2, sub_col3 = st.columns(3)
                    sub_col1.metric("Médio", f"{metricas.get('tempo_medio_resposta_s', 0):.2f}")
                    sub_col2.metric("Máximo", f"{metricas.get('tempo_maximo_resposta_s', 0):.2f}")
                    sub_col3.metric("P95", f"{metricas.get('tempo_percentil_95_s', 0):.2f}", help="95% das respostas foram mais rápidas que este valor.")
                with col2_desempenho:
                    st.markdown("##### Custos Operacionais (USD)")
                    sub_col1_custo, sub_col2_custo = st.columns(2)
                    sub_col1_custo.metric("Custo Total", f"$ {metricas.get('custo_total_usd_periodo', 0):.4f}")
                    sub_col2_custo.metric("Custo Médio / Msg", f"$ {metricas.get('custo_medio_por_msg_usd', 0):.6f}")
                st.markdown("---")
                st.markdown("### Qualidade e Eficácia")
                col1_qualidade, col2_qualidade = st.columns(2)
                with col1_qualidade:
                    st.markdown("##### Qualidade (Feedback)")
                    positivos = metricas.get("feedbacks_positivos_periodo", 0)
                    negativos = metricas.get("feedbacks_negativos_periodo", 0)
                    if (positivos + negativos) > 0:
                        df_feedback = pd.DataFrame({"Tipo": ["Positivos", "Negativos"], "Quantidade": [positivos, negativos]})
                        fig = px.pie(df_feedback, values='Quantidade', names='Tipo', color_discrete_map={'Positivos':'#00A86B', 'Negativos':'#FF4B4B'})
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Ainda não há feedbacks registrados no período.")
                with col2_qualidade:
                    st.markdown("##### Eficácia do RAG")
                    percent_rag = metricas.get("percentual_respostas_com_rag_periodo", 0)
                    st.metric("Respostas com Contexto (RAG)", f"{percent_rag:.2f}%")
                    top_categorias = metricas.get("top_5_categorias_periodo", [])
                    if top_categorias:
                        st.markdown("###### Top 5 Categorias Buscadas")
                        df_cat = pd.DataFrame(top_categorias)
                        st.dataframe(df_cat, use_container_width=True, hide_index=True)
                st.markdown("---")
                st.markdown("### Engajamento dos Usuários")
                top_users = metricas.get("top_10_usuarios_periodo", [])
                if top_users:
                    st.markdown("##### Top 10 Usuários por Nº de Mensagens no Período")
                    df_users = pd.DataFrame(top_users)
                    st.dataframe(df_users, use_container_width=True, hide_index=True)
                else:
                    st.info("Sem dados de engajamento no período.")

    elif pagina.startswith("⚙️"):
        st.subheader("⚙️ Configurações do Sistema")
        st.markdown("Altere os parâmetros que controlam o comportamento do Sisandinho.")
        parametros = carregar_parametros()
        if "error" in parametros:
            st.error(f"Erro ao carregar parâmetros: {parametros['error']}")
        elif parametros:
            st.info("Altere o valor de um parâmetro e clique em 'Salvar' para aplicá-lo em tempo real.")
            for nome_param, valor in parametros.items():
                st.markdown("---")
                col1_param, col2_param, col3_param = st.columns([2, 3, 1])
                with col1_param:
                    st.markdown(f"**{nome_param}**")
                with col2_param:
                    novo_valor = st.text_input(label="Valor", value=str(valor), key=f"param_{nome_param}", label_visibility="collapsed")
                with col3_param:
                    if st.button("Salvar", key=f"btn_param_{nome_param}", use_container_width=True):
                        with st.spinner("Salvando..."):
                            resultado = atualizar_parametro(nome_param, novo_valor)
                            if "error" in resultado:
                                st.error(f"Falha: {resultado['error']}")
                            else:
                                st.success("Salvo!")
        else:
            st.warning("Nenhum parâmetro encontrado.")

    # 🔚 RODAPÉ GLOBAL
    st.markdown("---")
    st.caption("🧠 Sisandinho - Powered by Sisand © 2025")

    # ########################################################################
    # ### FIM DA APLICAÇÃO PRINCIPAL ###
    # ########################################################################