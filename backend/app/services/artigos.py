# app/services/artigos.py
"""
Gestão de artigos da base de conhecimento.
Responsável por operações CRUD (Criar, Ler, Atualizar, Excluir) 
nos artigos utilizados pelo RAG.
"""

import logging
from typing import List, Dict, Any, Optional

# Importa as funções de cliente necessárias
from datetime import datetime, timezone # <-- CORREÇÃO: Importa datetime e timezone
# Importa as funções de cliente necessárias
from app.core.clients import get_weaviate_client, gerar_embedding_openai
# A importação de time_utils foi removida, pois não é mais necessária aqui.


logger = logging.getLogger(__name__)

async def buscar_artigos(
    query: Optional[str] = None,
    categoria: Optional[str] = None,
    limite: int = 50
) -> List[Dict[str, Any]]:
    """
    Busca artigos na base de conhecimento do Weaviate.
    - Se uma 'query' é fornecida, faz uma busca semântica (near_text).
    - Se não, faz uma busca geral com filtros (fetch_objects).
    """
    try:
        client = get_weaviate_client()
        collection = client.collections.get("Article")
        
        # Define filtros para a busca, se uma categoria for fornecida
        filters = None
        if categoria:
            from weaviate.classes.query import Filter # Importação local para clareza
            filters = Filter.by_property("category").equal(categoria)
            
        # Executa a consulta com a lógica correta
        if query:
            # Busca semântica (vetorial) se uma query for fornecida
            results = collection.query.near_text(
                query=query,
                limit=limite,
                filters=filters
            )
        else:
            # Busca geral com filtros ou simplesmente lista todos os artigos
            results = collection.query.fetch_objects(
                limit=limite,
                filters=filters
            )
            
        # Processa os resultados para um formato limpo
        artigos = [obj.properties for obj in results.objects]
            
        logger.info(f"Encontrados {len(artigos)} artigos")
        return artigos
        
    except Exception as e:
        logger.error(f"Erro ao buscar artigos: {str(e)}")
        return []
        
async def criar_artigo(
    titulo: str,
    conteudo: str,
    categoria: str = "Geral",
    url: str = "",
    resumo: str = ""
) -> Dict[str, Any]:
    """
    Cria um novo artigo de forma assíncrona.
    """
    try:
        client = get_weaviate_client()
        collection = client.collections.get("Article")
        
        embedding = await gerar_embedding_openai(conteudo)
        if not embedding:
            raise Exception("Falha ao gerar embedding para o artigo")
            
        artigo_data = {
            "title": titulo,
            "content": conteudo,
            "category": categoria,
            "url": url,
            "summary": resumo,
            # --- CORREÇÃO: Usa o padrão de data UTC ---
            "creation_date": datetime.now(timezone.utc).isoformat(),
        }
        
        uuid_gerado = collection.data.insert(
            properties=artigo_data,
            vector=embedding
        )
        
        logger.info(f"Artigo '{titulo}' criado com sucesso (UUID: {uuid_gerado})")
        return {"id": str(uuid_gerado), "titulo": titulo, "status": "success"}
        
    except Exception as e:
        logger.error(f"Erro ao criar artigo: {str(e)}")
        return {"error": str(e), "status": "error"}

async def atualizar_artigo(
    artigo_id: str,
    titulo: Optional[str] = None,
    conteudo: Optional[str] = None,
    categoria: Optional[str] = None,
    url: Optional[str] = None,
    resumo: Optional[str] = None
) -> Dict[str, Any]:
    """
    Atualiza um artigo existente. Se o conteúdo for alterado, o vetor é recalculado.
    """
    try:
        client = get_weaviate_client()
        collection = client.collections.get("Article")
        
        update_data = {}
        if titulo is not None: update_data["title"] = titulo
        if categoria is not None: update_data["category"] = categoria
        if url is not None: update_data["url"] = url
        if resumo is not None: update_data["summary"] = resumo
        
        vetor_para_atualizar = None
        if conteudo is not None:
            update_data["content"] = conteudo
            vetor_para_atualizar = await gerar_embedding_openai(conteudo)
        
        if update_data:
            collection.data.update(
                uuid=artigo_id,
                properties=update_data,
                vector=vetor_para_atualizar
            )
            logger.info(f"Artigo {artigo_id} atualizado com sucesso")
            return {"status": "success", "id": artigo_id}
        else:
            return {"status": "no_change", "message": "Nenhum dado fornecido para atualização"}
            
    except Exception as e:
        logger.error(f"Erro ao atualizar artigo {artigo_id}: {str(e)}")
        return {"error": str(e), "status": "error"}
        
async def excluir_artigo(artigo_id: str) -> Dict[str, Any]:
    """
    Exclui um artigo da base de conhecimento.
    """
    try:
        client = get_weaviate_client()
        collection = client.collections.get("Article")
        
        collection.data.delete(uuid=artigo_id)
        
        logger.info(f"Artigo {artigo_id} excluído com sucesso")
        return {"status": "success", "id": artigo_id}
        
    except Exception as e:
        logger.error(f"Erro ao excluir artigo {artigo_id}: {str(e)}")
        return {"error": str(e), "status": "error"}