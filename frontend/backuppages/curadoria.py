import streamlit as st
from services.api_client import buscar_tickets, carregar_acoes_ticket, salvar_curadoria
from services.api_client import api_carregar_sessoes, carregar_mensagens_sessao, api_obter_detalhes_sessao
import datetime
import logging
import pytz
import time

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

st.subheader("\U0001F9E0 Curadoria IA e Manual")

aba = st.radio("Escolha o tipo de curadoria:", ["Curadoria de Tickets", "Curadoria Manual", "Histórico de Sessões IA"])

if aba == "Curadoria de Tickets":
    limite = st.number_input("Quantidade de tickets a buscar", min_value=1, max_value=50, value=10)
    if st.button("Buscar Tickets"):
        tickets = buscar_tickets(limite)
        if tickets:
            for ticket in tickets.get("tickets", []):
                st.markdown(f"- **ID:** {ticket['id']} | **Assunto:** {ticket['subject']}")
                if st.button(f"Ver Ações do Ticket {ticket['id']}", key=f"acao_{ticket['id']}"):
                    acoes = carregar_acoes_ticket(ticket['id'])
                    if acoes:
                        st.markdown(f"### Ações do Ticket {ticket['id']}")
                        for acao in acoes:
                            st.markdown(f"- **Ação:** {acao['descricao']} | **Data:** {acao['data']}")
                    else:
                        st.info("Nenhuma ação encontrada para este ticket.")
        else:
            st.info("Nenhum ticket encontrado.")

elif aba == "Curadoria Manual":
    ticket_id = st.text_input("ID do Ticket")
    curador = st.text_input("Nome do Curador")
    question = st.text_area("Pergunta do Cliente")
    answer = st.text_area("Resposta do Agente")
    if st.button("Salvar Curadoria"):
        if ticket_id and curador and question and answer:
            resultado = salvar_curadoria(ticket_id, curador, question, answer)
            st.success("Curadoria salva com sucesso!" if resultado else "Erro ao salvar curadoria.")
        else:
            st.warning("Preencha todos os campos antes de salvar.")

elif aba == "Histórico de Sessões IA":
    usuario_id = 1
    
    # Implementar caching para evitar recarregar sessões desnecessariamente
    if "cached_sessoes" not in st.session_state or st.button("🔄 Recarregar sessões", help="Buscar novamente as sessões no servidor"):
        with st.spinner("Carregando sessões. Isso pode levar alguns segundos..."):
            inicio_carregar_sessoes = time.time()
            logger.info(f"Curadoria: Iniciando carregamento de sessões para usuário_id={usuario_id}")
            
            # Adicionar opção de limitar a quantidade de sessões retornadas
            max_sessoes = 20  # Pode ser um parâmetro configurável pelo usuário
            sessoes = api_carregar_sessoes(usuario_id, limite=max_sessoes)
            
            tempo_carregar_sessoes = time.time() - inicio_carregar_sessoes
            logger.info(f"Curadoria: Carregamento de {len(sessoes)} sessões concluído em {tempo_carregar_sessoes:.2f} segundos")
            
            # Guardar no cache do Streamlit
            st.session_state.cached_sessoes = sessoes
            st.session_state.cached_time = datetime.datetime.now().strftime("%H:%M:%S")
    else:
        sessoes = st.session_state.cached_sessoes
        st.info(f"Usando {len(sessoes)} sessões carregadas em cache às {st.session_state.cached_time}")
    
    if not sessoes:
        st.warning("Nenhuma sessão encontrada para este usuário.")
    else:
        # Ordenar sessões do mais recente para o mais antigo
        sessoes_ordenadas = sorted(sessoes, key=lambda s: s.get('inicio', ''), reverse=True)
        
        # Extrair IDs e labels
        sessao_ids = [s.get('id') for s in sessoes_ordenadas]
        sessao_labels = [f"Sessão #{s.get('id')} • {s.get('inicio', '').replace('T', ' ')[:16]}" for s in sessoes_ordenadas]

        sessao_idx = st.selectbox("Selecione uma sessão para análise:", range(len(sessao_labels)), 
                                 format_func=lambda i: sessao_labels[i] if i < len(sessao_labels) else None)
        sessao_id = sessao_ids[sessao_idx]

        try:
            # Medir tempo para obter detalhes da sessão
            inicio_detalhes = time.time()
            logger.info(f"Curadoria: Obtendo detalhes da sessão {sessao_id}")
            detalhes = api_obter_detalhes_sessao(sessao_id) or {}
            tempo_detalhes = time.time() - inicio_detalhes
            logger.info(f"Curadoria: Detalhes da sessão obtidos em {tempo_detalhes:.2f} segundos")
            
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

        try:
            # Medir tempo para carregar mensagens
            inicio_carregar_mensagens = time.time()
            logger.info(f"Curadoria: Carregando mensagens da sessão {sessao_id}")
            raw = carregar_mensagens_sessao(sessao_id)
            tempo_carregar_mensagens = time.time() - inicio_carregar_mensagens
            logger.info(f"Curadoria: {len(raw)} mensagens carregadas em {tempo_carregar_mensagens:.2f} segundos")
            
            # Medir tempo para processar mensagens
            inicio_processar = time.time()
            msgs = []
            for m in raw:
                tempo = m.get("created_at", "")[:16].replace("T", " ")
                msgs.append({"role": "user", "content": m.get("pergunta", ""), "time": tempo})
                msgs.append({"role": "assistant", "content": m.get("resposta", ""), "time": tempo, "prompt": m.get("prompt_usado", "")})
            tempo_processar = time.time() - inicio_processar
            logger.info(f"Curadoria: Processamento de mensagens concluído em {tempo_processar:.2f} segundos")
            
        except Exception as e:
            logger.error(f"Erro carregar mensagens: {e}")
            msgs = []

        # Medir tempo para renderizar mensagens
        inicio_renderizar = time.time()
        logger.info(f"Curadoria: Iniciando renderização de {len(msgs)} mensagens")
        
        for idx, msg in enumerate(msgs):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg["role"] == "assistant" and msg.get("prompt"):
                    with st.expander("\U0001F4C4 Ver prompt usado"):
                        st.code(msg["prompt"], language="markdown")
            
            # Log a cada 10 mensagens para não sobrecarregar
            if idx > 0 and idx % 10 == 0:
                logger.info(f"Curadoria: Renderizadas {idx}/{len(msgs)} mensagens")
                
        tempo_renderizar = time.time() - inicio_renderizar
        logger.info(f"Curadoria: Renderização concluída em {tempo_renderizar:.2f} segundos")
        
        # Log resumo dos tempos
        logger.info(f"Curadoria: RESUMO DE TEMPOS - Sessão {sessao_id}:")
        logger.info(f"  - Carregar detalhes: {tempo_detalhes:.2f}s")
        logger.info(f"  - Carregar mensagens: {tempo_carregar_mensagens:.2f}s")
        logger.info(f"  - Processar mensagens: {tempo_processar:.2f}s")
        logger.info(f"  - Renderizar mensagens: {tempo_renderizar:.2f}s")
        logger.info(f"  - TEMPO TOTAL: {tempo_detalhes + tempo_carregar_mensagens + tempo_processar + tempo_renderizar:.2f}s")
