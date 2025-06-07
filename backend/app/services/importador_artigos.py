# app/services/importador_artigos.py

import logging
import asyncio
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone # Adicionado timezone
import requests
from fastapi import HTTPException
from app.core.clients import get_weaviate_client, get_openai_client
from weaviate.classes.config import Property, DataType
from app.core.config import settings
from weaviate.collections.classes.filters import Filter
from weaviate.collections.classes.data import DataObject
import re


logger = logging.getLogger(__name__)

# Definições de variáveis globais do módulo
base_url = settings.MOVI_LIST_URL
token = settings.MOVI_TOKEN  # <--- AQUI O TOKEN É DEFINIDO
base_detail_url = settings.MOVI_DETAIL_URL


# ... (base_url, token, base_detail_url, logger permanecem os mesmos) ...
# ... (converter_iso_para_data, buscar_lista_artigos, buscar_detalhes_artigo, gerar_embedding_conteudo como na refatoração anterior) ...

# ===================================================================================
# FUNÇÕES CHAVE MODIFICADAS/REVISADAS
# ===================================================================================

def converter_iso_para_data(data_iso: str) -> Optional[str]:
    """
    Converte data ISO para formato string YYYY-MM-DDTHH:MM:SSZ,
    truncando microssegundos para 6 dígitos se necessário.
    """
    if not data_iso:
        return None

    # Regex para capturar:
    # Grupo 1: Data e hora até segundos (YYYY-MM-DDTHH:MM:SS)
    # Grupo 2: Parte dos microssegundos, opcional (começando com '.')
    # Grupo 3: Timezone (Z, +HH:MM, ou -HH:MM), opcional
    match = re.match(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(\.\d+)?(Z|[+-]\d{2}:\d{2})?$', data_iso.strip())

    # Pré-sanitização de problemas conhecidos
    data_iso = data_iso.strip()
    data_iso = re.sub(r'--', '-', data_iso)  # Corrige duplo traço

    if not match:
        logger.warning(f"⚠️ Formato de data ISO não reconhecido inicialmente: '{data_iso}'. Retornando None.")
        return None

    parte_data_segundos = match.group(1)
    microssegundos_str_com_ponto = match.group(2) # Ex: ".1234567" ou None
    timezone_str_original = match.group(3)       # Ex: "Z", "+03:00" ou None

    data_iso_ajustada = parte_data_segundos

    if microssegundos_str_com_ponto:
        ms_digits = microssegundos_str_com_ponto[1:] 
        if len(ms_digits) > 6:
            ms_digits = ms_digits[:6] # Trunca para 6 dígitos
        if ms_digits: 
             data_iso_ajustada += f".{ms_digits}"

    if timezone_str_original:
        if timezone_str_original.upper() == "Z":
            data_iso_ajustada += "+00:00"
        else:
            data_iso_ajustada += timezone_str_original
    else:
        data_iso_ajustada += "+00:00" # Assume UTC se nenhum timezone for fornecido
        
    try:
        dt = datetime.fromisoformat(data_iso_ajustada)
        if dt.tzinfo is None: 
            dt_utc = dt.replace(tzinfo=timezone.utc)
        else:
            dt_utc = dt.astimezone(timezone.utc)
            
        return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError as e:
        logger.warning(f"⚠️ Erro ao converter data ISO '{data_iso}' (ajustada para '{data_iso_ajustada}'): {e}. Retornando None.")
        return None
    
async def buscar_lista_artigos(pagina: int = 1, limite: int = 50) -> List[Dict[str, Any]]:
    """Busca lista paginada de artigos do Movidesk."""
    try:
        logger.info(f"🔍 Buscando página {pagina} (limite {limite})...")
        params = {"token": token, "page": pagina - 1, "pageSize": limite}
        response = requests.get(base_url, params=params, headers={"Content-Type": "application/json"}, timeout=600000)
        response.raise_for_status()
        data = response.json()
        artigos = data.get("items", data) if isinstance(data, dict) else data

        if not isinstance(artigos, list):
            logger.error(f"❌ Resposta não é uma lista (Página {pagina}): {type(artigos)} - {str(artigos)[:500]}")
            return []

        logger.info(f"✅ Página {pagina} retornou {len(artigos)} artigos.")
        return artigos

    except Exception as e:
        logger.error(f"❌ Erro ao buscar lista de artigos (Página {pagina}): {str(e)}")
        return []



async def buscar_detalhes_artigo(artigo_id: int) -> Optional[Dict[str, Any]]:
    """Busca detalhes de um artigo específico."""
    try:
        logger.info(f"🔍 Buscando detalhes do artigo ID: {artigo_id}")
        url = f"{base_detail_url}/{artigo_id}"
        params = {"token": token}
        response = requests.get(url, headers={"Content-Type": "application/json"}, params=params, timeout=600000)
        response.raise_for_status()
        artigo = response.json()

        if not isinstance(artigo, dict):
            logger.error(f"❌ Resposta inválida (artigo ID {artigo_id}): {str(artigo)[:500]}")
            return None

        logger.info(f"✅ Artigo {artigo_id} - Título: {artigo.get('title', '(sem título)')}")
        return artigo

    except Exception as e:
        logger.error(f"❌ Erro ao buscar detalhes do artigo {artigo_id}: {str(e)}")
        return None

async def gerar_embedding_conteudo(conteudo: str) -> Optional[List[float]]:
    if not conteudo or not conteudo.strip(): # Verifica se o conteúdo é vazio ou só espaços
        logger.warning("⚠️ Conteúdo vazio ou apenas espaços fornecido para geração de embedding. Pulando.")
        return None
    try:
        logger.debug(f"🧠 Iniciando geração de embedding para conteúdo de {len(conteudo)} caracteres.")
        openai_client = get_openai_client()
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002", # settings.OPENAI_EMBEDDING_MODEL
            input=conteudo.replace("\n", " ") # Normalização simples sugerida pela OpenAI
        )
        embedding = response.data[0].embedding
        logger.debug("✅ Embedding gerado com sucesso.")
        return embedding
    except Exception as e:
        # Adicionar mais detalhes sobre o erro da OpenAI, se possível
        # e.g. if hasattr(e, 'response') and e.response is not None: logger.error(e.response.text)
        logger.error(f"❌ Erro ao gerar embedding: {str(e)}")
        return None

def verificar_artigo_precisa_atualizar(collection, artigo_id: int, movidesk_updated_date_str: Optional[str]) -> bool:
    logger.info(f"🔍 Verificando necessidade de atualização para Artigo ID: {artigo_id}")
    logger.debug(f"🕑 Data de atualização (Movidesk string): {movidesk_updated_date_str}")

    try:
        where_filter = Filter.by_property("movidesk_id").equal(artigo_id)
        response = collection.query.fetch_objects(filters=where_filter, limit=1)
        
        existing_objects = response.objects
        if not existing_objects:
            logger.info(f"🆕 Artigo ID {artigo_id} não encontrado no Weaviate. Marcado para importação.")
            return True

        weaviate_properties = existing_objects[0].properties
        weaviate_updated_date_val = weaviate_properties.get("updatedDate")
        
        logger.debug(f"🕑 Data de atualização (Weaviate raw value): {weaviate_updated_date_val}, Tipo: {type(weaviate_updated_date_val)}")

        if not movidesk_updated_date_str:
            logger.warning(f"⚠️ Artigo ID {artigo_id} (Movidesk) não tem 'updatedDate'. Forçando atualização.")
            return True

        if weaviate_updated_date_val is None:
            logger.info(f"ℹ️ Artigo ID {artigo_id} existe no Weaviate mas sem 'updatedDate'. Movidesk tem data. Marcado para atualização.")
            return True
            
        # Converter a data do Weaviate (que pode ser string ou datetime dependendo de como foi inserida e recuperada)
        if isinstance(weaviate_updated_date_val, str):
            # Se for string, tentar converter para datetime UTC
            weaviate_dt_str_iso = weaviate_updated_date_val
            if weaviate_dt_str_iso.endswith("Z"):
                weaviate_dt_str_iso = weaviate_dt_str_iso[:-1] + "+00:00"
            try:
                weaviate_dt_utc = datetime.fromisoformat(weaviate_dt_str_iso)
                if weaviate_dt_utc.tzinfo is None: # Garantir que é timezone-aware
                    weaviate_dt_utc = weaviate_dt_utc.replace(tzinfo=timezone.utc)
            except ValueError:
                 logger.error(f"❌ Data do Weaviate para artigo {artigo_id} é string mas não pôde ser convertida: '{weaviate_updated_date_val}'. Forçando atualização.")
                 return True
        elif isinstance(weaviate_updated_date_val, datetime):
            # Se já é datetime, garantir que é UTC
            if weaviate_updated_date_val.tzinfo is None:
                weaviate_dt_utc = weaviate_updated_date_val.replace(tzinfo=timezone.utc)
            else:
                weaviate_dt_utc = weaviate_updated_date_val.astimezone(timezone.utc)
        else:
            logger.error(f"❌ Tipo de data do Weaviate inesperado para artigo {artigo_id}: {type(weaviate_updated_date_val)}. Forçando atualização.")
            return True

        # Converter string da data do Movidesk ("YYYY-MM-DDTHH:MM:SSZ") para datetime UTC
        movidesk_dt_str_iso = movidesk_updated_date_str
        if movidesk_dt_str_iso.endswith("Z"):
            movidesk_dt_str_iso = movidesk_dt_str_iso[:-1] + "+00:00"
        
        movidesk_dt_utc = datetime.fromisoformat(movidesk_dt_str_iso)
        
        # Compara os dois objetos datetime UTC (ignorando microssegundos para evitar falsos positivos)
        if movidesk_dt_utc.replace(microsecond=0) != weaviate_dt_utc.replace(microsecond=0):
            logger.info(f"🔄 Artigo ID {artigo_id} precisa ser atualizado. Data Movidesk: {movidesk_dt_utc}, Data Weaviate: {weaviate_dt_utc}")
            return True
        else:
            logger.info(f"✅ Artigo ID {artigo_id} está atualizado (Datas: {movidesk_dt_utc}). Será pulado.")
            return False

    except ValueError as ve: # Captura erros de datetime.fromisoformat se a string for inválida
        logger.error(f"❌ Erro de formatação de data ao comparar (Artigo ID {artigo_id}). Movidesk str: '{movidesk_updated_date_str}'. Erro: {ve}. Forçando atualização.")
        return True
    except Exception as e:
        logger.error(f"❌ Erro crítico ao verificar necessidade de atualização do artigo {artigo_id}: {str(e)}. Forçando atualização.")
        return True

async def verificar_e_criar_schema(resetar_base: bool = True):
    """Verifica e cria o schema 'Article' no Weaviate."""
    client = get_weaviate_client()
    collection_name = "Article" # Idealmente de settings.WEAVIATE_COLLECTION_NAME
    try:
        existe = client.collections.exists(collection_name)
        if resetar_base and existe:
            logger.info(f"🗑️ Excluindo collection '{collection_name}'...")
            client.collections.delete(collection_name)
            logger.info(f"🗑️ Collection '{collection_name}' excluída com sucesso.")
            await asyncio.sleep(2) 
            existe = False

        if not existe:
            logger.info(f"✨ Criando schema para collection '{collection_name}'...")
            client.collections.create(
                name=collection_name,
                properties=[
                    Property(name="title", data_type=DataType.TEXT, description="Título do artigo"),
                    Property(name="content", data_type=DataType.TEXT, description="Conteúdo HTML completo do artigo"),
                    Property(name="resumo", data_type=DataType.TEXT, description="Resumo curto do artigo"),
                    Property(name="url", data_type=DataType.TEXT, description="URL pública do artigo"),
                    Property(name="status", data_type=DataType.TEXT, description="Status do artigo (ex: Publicado)"),
                    Property(name="movidesk_id", data_type=DataType.INT, description="ID do artigo no Movidesk"),
                    Property(name="createdDate", data_type=DataType.DATE, description="Data de criação do artigo"),
                    Property(name="updatedDate", data_type=DataType.DATE, description="Data da última atualização do artigo"),
                ]
            )
            logger.info(f"✨ Schema '{collection_name}' criado com sucesso.")
            await asyncio.sleep(1)
        else:
            logger.info(f"ℹ️ Collection '{collection_name}' já existe (reset_base=False ou falha na exclusão).")
    except Exception as e:
        logger.error(f"❌ Erro fatal ao verificar/criar schema '{collection_name}': {str(e)}")
        raise 

async def importar_artigos_movidesk(progresso_callback=None, reset_base: bool = True):
    logger.info(f"🚀 Iniciando importação (reset_base={reset_base})")
    try:
        # Inicialização
        client = get_weaviate_client()
        await verificar_e_criar_schema(resetar_base=reset_base)
        collection = client.collections.get("Article")

        # Contadores
        total_geral_inseridos_weaviate = 0
        total_processados_para_atualizacao = 0
        total_pulados_ja_atualizado_no_weaviate = 0
        total_pulados_outros_motivos = 0


        pagina_atual_movidesk = 1  # <-- Adicione aqui (ou mantenha)
        ids_adicionados_ao_batch_nesta_execucao = set() 
        TAMANHO_BATCH = int(os.getenv("MOVIDESK_API_BATCH_SIZE", 30))

        while True:
            logger.info(f"🔄 Processando página {pagina_atual_movidesk} do Movidesk (batch size: {TAMANHO_BATCH})...")
            artigos_da_pagina_api = await buscar_lista_artigos(pagina_atual_movidesk, limite=TAMANHO_BATCH)

            if not artigos_da_pagina_api:
                logger.info(f"✅ Fim da paginação da API Movidesk — página {pagina_atual_movidesk} não retornou artigos.")
                break

            batch_para_inserir_nesta_iteracao: List[DataObject] = []

            for idx, item_da_lista_api in enumerate(artigos_da_pagina_api, 1):
                artigo_id_api = item_da_lista_api.get("id")
                titulo_lista_api = item_da_lista_api.get("title", "(Título não disponível na lista)")
                status_lista_api = item_da_lista_api.get("articleStatus", "(Status não disponível na lista)")

                logger.info(f"🔎 Item {idx}/{len(artigos_da_pagina_api)} (Pág. {pagina_atual_movidesk}): ID {artigo_id_api}, Título Lista: '{titulo_lista_api}'")

                if not artigo_id_api:
                    logger.warning("⚠️ Item da lista Movidesk sem ID. Pulando.")
                    total_pulados_outros_motivos += 1
                    continue

                if artigo_id_api in ids_adicionados_ao_batch_nesta_execucao:
                    logger.warning(f"🔁 Artigo ID {artigo_id_api} ('{titulo_lista_api}') já foi adicionado ao batch nesta execução (provável duplicata da API Movidesk). Pulando.")
                    total_pulados_outros_motivos += 1
                    continue

                detalhes_artigo_api = await buscar_detalhes_artigo(artigo_id_api)
                if not detalhes_artigo_api or not detalhes_artigo_api.get("contentText", "").strip():
                    logger.warning(f"⚠️ Artigo ID {artigo_id_api} ('{titulo_lista_api}') sem detalhes válidos ou sem contentText. Pulando.")
                    total_pulados_outros_motivos += 1
                    continue

                updated_date_movidesk_str_fmt = converter_iso_para_data(detalhes_artigo_api.get("updatedDate"))

                if not reset_base:
                    if not verificar_artigo_precisa_atualizar(collection, artigo_id_api, updated_date_movidesk_str_fmt):
                        total_pulados_ja_atualizado_no_weaviate += 1
                        continue
                else:
                    logger.debug(f"✅ [RESET] Inclusão de artigo ID {artigo_id_api} (reset_base=True).")

                total_processados_para_atualizacao += 1

                conteudo_embedding = detalhes_artigo_api.get("contentText", "").strip()
                vetor_embedding = await gerar_embedding_conteudo(conteudo_embedding)
                if not vetor_embedding:
                    logger.error(f"❌ Falha ao gerar embedding para Artigo ID {artigo_id_api} ('{detalhes_artigo_api.get('title')}'). Pulando.")
                    total_pulados_outros_motivos += 1
                    continue

                props_objeto_weaviate = {
                    "movidesk_id": artigo_id_api,
                    "title": detalhes_artigo_api.get("title", ""),
                    "content": conteudo_embedding,
                    "resumo": detalhes_artigo_api.get("shortContent", "") or "",
                    "status": str(detalhes_artigo_api.get("articleStatus", "") or detalhes_artigo_api.get("statusDescription", "Desconhecido")),
                    "url": f"{os.getenv('BASE_ARTICLE_URL', 'http://localhost/artigo')}/{artigo_id_api}/{detalhes_artigo_api.get('slug', '')}",
                    "createdDate": converter_iso_para_data(detalhes_artigo_api.get("createdDate")),
                    "updatedDate": updated_date_movidesk_str_fmt
                }

                batch_para_inserir_nesta_iteracao.append(
                    DataObject(properties=props_objeto_weaviate, vector=vetor_embedding)
                )
                ids_adicionados_ao_batch_nesta_execucao.add(artigo_id_api)
                logger.debug(f"➕ Artigo ID {artigo_id_api} ('{props_objeto_weaviate['title']}') adicionado ao batch.")

                if progresso_callback:
                    await progresso_callback({
                        "status": "em_progresso", "pagina_atual_movidesk": pagina_atual_movidesk,
                        "item_processado_na_pagina": idx, "total_itens_na_pagina_api": len(artigos_da_pagina_api),
                        "total_geral_inseridos_weaviate": total_geral_inseridos_weaviate,
                        "total_processados_para_atualizacao": total_processados_para_atualizacao,
                        "total_pulados_ja_atualizado_no_weaviate": total_pulados_ja_atualizado_no_weaviate,
                        "total_pulados_outros_motivos": total_pulados_outros_motivos,
                        "ultimo_artigo_adicionado_batch": props_objeto_weaviate['title']
                    })

            if batch_para_inserir_nesta_iteracao:
                try:
                    logger.info(f"📦 Enviando batch de {len(batch_para_inserir_nesta_iteracao)} artigos para Weaviate...")
                    collection.data.insert_many(objects=batch_para_inserir_nesta_iteracao)
                    total_geral_inseridos_weaviate += len(batch_para_inserir_nesta_iteracao)
                    logger.info(f"🚀 Batch de {len(batch_para_inserir_nesta_iteracao)} artigos inserido. Total Weaviate: {total_geral_inseridos_weaviate}")
                    await asyncio.sleep(0.2)
                except Exception as e_insert:
                    logger.error(f"❌❌ Erro CRÍTICO ao inserir batch no Weaviate: {e_insert}. Artigos neste batch podem não ter sido salvos.")
                    raise

            pagina_atual_movidesk += 1

        # Finalização
        logger.info("🎉 Importação concluída!")
        summary = (
            f"Resumo FINAL da Importação:\n"
            f"  - Total de páginas processadas: {pagina_atual_movidesk - 1}\n"
            f"  - Total de artigos efetivamente inseridos/atualizados no Weaviate: {total_geral_inseridos_weaviate}\n"
            f"  - Total de artigos que passaram pela lógica para atualização/inserção: {total_processados_para_atualizacao}\n"
            f"  - Total de artigos pulados (já atualizados no Weaviate): {total_pulados_ja_atualizado_no_weaviate}\n"
            f"  - Total de artigos pulados (outros motivos: erro, sem conteúdo, duplicata da API lista): {total_pulados_outros_motivos}"
        )

        logger.info(summary)

        return {
            "status": "sucesso",
            "total_paginas": pagina_atual_movidesk - 1,
            "total_geral_inseridos_weaviate": total_geral_inseridos_weaviate,
            "total_logica_atualizacao": total_processados_para_atualizacao,
            "total_pulados_ja_atualizado": total_pulados_ja_atualizado_no_weaviate,
            "total_pulados_outros": total_pulados_outros_motivos,
            "mensagem": "Importação finalizada com sucesso."
        }


    except Exception as e:
        logger.exception(f"❌ ERRO FATAL DURANTE IMPORTAÇÃO: {str(e)}")
        if progresso_callback:
            await progresso_callback({
                "status": "erro",
                "mensagem": f"Erro fatal: {str(e)}"
            })
        raise HTTPException(status_code=500, detail=f"Erro fatal durante a importação: {str(e)}")