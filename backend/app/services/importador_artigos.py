# app/services/importador_artigos.py (VERSÃO FINAL E DEFINITIVA)

import logging
import asyncio
import httpx
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
import re
from app.core.clients import get_weaviate_client, get_openai_client
from app.core.config import get_settings
from app.core.cache import obter_parametro
from weaviate.classes.config import Property, DataType
from weaviate.collections.classes.filters import Filter
from weaviate.collections.classes.data import DataObject
from weaviate.util import generate_uuid5
from weaviate.exceptions import WeaviateInsertManyAllFailedError
from dateutil import parser
import csv


logger = logging.getLogger(__name__)
import_status = {"in_progress": False, "message": "Nenhuma importação em andamento."}

# --- FUNÇÕES AUXILIARES ---
def converter_iso_para_timestamp_utc3(iso_str: str) -> float:
    """
    Converte string ISO variada em timestamp UTC-3.
    Usa parser.isoparse e ajusta fuso.
    """
    if not iso_str or not isinstance(iso_str, str):
        raise ValueError(f"Timestamp inválido: {iso_str!r}")
    dt = parser.isoparse(iso_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone(timedelta(hours=-3))).timestamp()


def normalizar_para_iso_brasilia(data_iso: str) -> Optional[str]:
    """
    Converte ISO Movidesk para string ISO no fuso de Brasília.
    """
    try:
        ts = converter_iso_para_timestamp_utc3(data_iso)
        dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=-3)))
        return dt.isoformat()
    except Exception:
        return None

# Alias para consistência
def normalizar_data_movidesk(data_iso: str) -> Optional[str]:
    return normalizar_para_iso_brasilia(data_iso)


async def buscar_lista_artigos(
    client: httpx.AsyncClient,
    pagina: int,
    limite: int,
    status: int = 1  # por padrão busca somente artigos publicados
) -> List[Dict]:
    """
    Busca artigos na API Movidesk, filtrando por status (1=publicado, 4=suspenso).
    Retorna lista de dicionários com fields 'id', 'updatedAt', 'title', etc.
    """
    settings = get_settings()
    base_url = obter_parametro("movi_list_url")
    token = settings.MOVI_TOKEN
    if not base_url or not token:
        return []

    # monta os parâmetros, incluindo status=1
    params = {
        "token": token,
        "page": pagina,
        "$top": limite,
        "$select": "id,updatedAt,title",
        "status": status,
    }

    resp = await client.get(
        base_url,
        params=params,
        timeout=30
    )
    resp.raise_for_status()
    data = resp.json()
    items = data if isinstance(data, list) else data.get("items", [])

    # log de ID e título para comparação
    for art in items:
        art_id = art.get("id")
        art_title = art.get("title", "<sem título>")
        logger.info(f"📋 Lista Movidesk - ID {art_id} | Título: {art_title}")

    return items



async def buscar_detalhes_artigo(client: httpx.AsyncClient, artigo_id: int) -> Optional[Dict]:
    settings = get_settings()
    url = obter_parametro("movi_detail_url")
    if not url:
        return None
    resp = await client.get(f"{url}/{artigo_id}", params={"token": settings.MOVI_TOKEN}, timeout=20)
    resp.raise_for_status()
    art = resp.json()
    art["createdDate"] = normalizar_data_movidesk(art.get("createdDate"))
    art["updatedDate"] = normalizar_data_movidesk(art.get("updatedDate"))
    return art


async def gerar_embedding_conteudo(conteudo: str) -> Optional[List[float]]:
    """Gera o embedding vetorial para um texto."""
    if not conteudo or not conteudo.strip(): return None
    try:
        return get_openai_client().embeddings.create(model=obter_parametro("embedding_model"), input=conteudo.replace("\n", " ")).data[0].embedding
    except Exception as e:
        logger.error(f"❌ Erro ao gerar embedding: {e}")
        return None

async def verificar_e_criar_schema(resetar_base: bool = True):
    """Verifica e cria o schema 'Article' no Weaviate com todas as propriedades necessárias."""
    client = get_weaviate_client()
    collection_name = "Article"
    if resetar_base and client.collections.exists(collection_name):
        client.collections.delete(collection_name)
        await asyncio.sleep(2)
    if not client.collections.exists(collection_name):
        client.collections.create(name=collection_name, properties=[
            Property(name="movidesk_id", data_type=DataType.INT),
            Property(name="title", data_type=DataType.TEXT),
            Property(name="content", data_type=DataType.TEXT),
            Property(name="resumo", data_type=DataType.TEXT),
            Property(name="status", data_type=DataType.TEXT),
            Property(name="url", data_type=DataType.TEXT),
            Property(name="createdDate", data_type=DataType.TEXT),
            Property(name="updatedDate", data_type=DataType.TEXT),
            Property(name="categoria", data_type=DataType.TEXT),
        ])

# --- FUNÇÃO PRINCIPAL DE IMPORTAÇÃO ---
async def importar_artigos_movidesk(progresso_callback=None, reset_base: bool = True):
    if import_status["in_progress"]:
        raise RuntimeError("Uma importação já está em andamento.")
    import_status["in_progress"] = True
    import_status["message"] = f"Importação iniciada às {datetime.now().strftime('%H:%M:%S')}"

    contadores = {
        "paginas": 0,
        "enviados": 0,
        "pulados_sem_conteudo": 0,
        "pulados_embedding": 0,
        "falhas_datas": 0
    }
    pagina = 0
    batch_size = int(obter_parametro("rag_search_limit", 30))
    # lista para CSV: armazena tuplas (id, titulo)
    all_artigos_meta: List[Tuple[int, str]] = []

    try:
        await verificar_e_criar_schema(resetar_base=reset_base)
        collection = get_weaviate_client().collections.get("Article")

        async with httpx.AsyncClient() as client:
            while True:
                artigos = await buscar_lista_artigos(client, pagina, batch_size)
                if not artigos:
                    break

                # Acumula metadados para CSV
                for art in artigos:
                    aid = art.get("id")
                    titulo = art.get("title", "")
                    all_artigos_meta.append((aid, titulo))

                contadores["paginas"] += 1
                logger.info(f"Página {pagina}: obtidos {len(artigos)} artigos")
                batch = []

                for item in artigos:
                    aid = item.get("id")
                    if not aid:
                        logger.warning("Artigo sem ID recebido, pulado.")
                        contadores["falhas_datas"] += 1
                        continue

                    uuid = generate_uuid5(str(aid))
                    deve = False
                    motivo = None

                    # Verifica se precisa processar
                    if reset_base or not collection.data.exists(uuid=uuid):
                        deve = True
                        motivo = "novo artigo"
                    else:
                        obj = collection.query.fetch_object_by_id(uuid=uuid)
                        weav_date = obj.properties.get("updatedDate")
                        try:
                            det = await buscar_detalhes_artigo(client, aid)
                            raw_date = det.get("updatedDate") if det else None
                            t1 = converter_iso_para_timestamp_utc3(raw_date)
                            t2 = converter_iso_para_timestamp_utc3(weav_date)
                            if abs(t1 - t2) > 1:
                                deve = True
                                motivo = "timestamps divergem"
                        except Exception:
                            contadores["falhas_datas"] += 1
                            deve = True
                            motivo = "erro ao comparar datas"

                    if not deve:
                        logger.debug(f"Artigo {aid} sem alterações, pulado.")
                        continue

                    det = await buscar_detalhes_artigo(client, aid)
                    raw_date = det.get("updatedDate") if det else None
                    weav_date = weav_date if 'weav_date' in locals() else None
                    logger.info(
                        f"Artigo {aid}: processar devido a {motivo}. MoviData: {raw_date!r}, WeavData: {weav_date!r}"
                    )

                    if not det or not det.get("contentText"):
                        contadores["pulados_sem_conteudo"] += 1
                        logger.warning(f"Artigo {aid} sem conteúdo, mas será importado.")

                    props = {
                        "movidesk_id": aid,
                        "title": det.get("title", "") if det else "",
                        "content": det.get("contentText") or "" if det else "",
                        "resumo": det.get("shortContent", "") if det else "",
                        "status": det.get("statusDescription", "") if det else "",
                        "url": f"{obter_parametro('base_article_url','')}/{aid}/{det.get('slug','')}" if det else "",
                        "createdDate": det.get("createdDate") if det else None,
                        "updatedDate": det.get("updatedDate") if det else None,
                        "categoria": det.get("categoryName", "geral") if det else "geral"
                    }
                    vetor = await gerar_embedding_conteudo(props["content"])
                    if not vetor:
                        contadores["pulados_embedding"] += 1
                        logger.warning(f"Artigo {aid} sem embedding, mas será importado.")

                    batch.append(DataObject(properties=props, vector=vetor, uuid=uuid))

                if batch:
                    try:
                        collection.data.insert_many(objects=batch)
                        contadores["enviados"] += len(batch)
                        logger.info(f"Página {pagina}: {len(batch)} artigos gravados no Weaviate")
                    except WeaviateInsertManyAllFailedError as e:
                        logger.error(f"Erro ao inserir batch página {pagina}: {e}")

                pagina += 1

        # Resumo final
        logger.info(
            f"Importação concluída: {contadores['paginas']} páginas, {contadores['enviados']} gravados, "
            f"{contadores['pulados_sem_conteudo']} sem conteúdo, "
            f"{contadores['pulados_embedding']} sem embedding, {contadores['falhas_datas']} falhas de data"
        )

        # Gera CSV complementar com id e título
        csv_path = 'artigos_movidesk.csv'
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['id', 'titulo'])
            writer.writerows(all_artigos_meta)
        logger.info(f"Arquivo CSV gerado: {csv_path}")

    finally:
        import_status["in_progress"] = False