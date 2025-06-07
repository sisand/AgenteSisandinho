"""
Gestão de artigos da base de conhecimento.
Responsável por operações CRUD nos artigos utilizados pelo RAG.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from app.utils.logger import get_logger
from app.core.clients import get_weaviate_client, gerar_embedding_openai
from app.utils.time_utils import get_brazil_time

logger = get_logger(__name__)

async def buscar_artigos(
    query: Optional[str] = None,
    categoria: Optional[str] = None,
    limite: int = 50
) -> List[Dict[str, Any]]:
    """
    Busca artigos na base de conhecimento.
    
    Args:
        query: Texto para busca (opcional)
        categoria: Filtrar por categoria (opcional)
        limite: Número máximo de resultados
        
    Returns:
        Lista de artigos encontrados
    """
    try:
        client = get_weaviate_client()
        
        if not client:
            raise Exception("Cliente Weaviate não disponível")
            
        collection = client.collections.get("Article")
        
        # Definir filtros
        filters = None
        if categoria:
            filters = {
                "path": ["category"],
                "operator": "Equal",
                "valueString": categoria
            }
            
        # Executar consulta
        if query:
            # Busca semântica
            results = collection.query.near_text(
                query=query,
                limit=limite,
                filters=filters
            )
        else:
            # Busca por filtros ou todos os artigos
            results = collection.query.fetch_objects(
                limit=limite,
                filters=filters
            )
            
        # Processar resultados
        artigos = []
        for obj in results.objects:
            artigos.append({
                "id": obj.uuid,
                "titulo": obj.properties.get("title", "Sem título"),
                "categoria": obj.properties.get("category", "Geral"),
                "resumo": obj.properties.get("summary", ""),
                "conteudo": obj.properties.get("content", ""),
                "url": obj.properties.get("url", ""),
                "data_criacao": obj.properties.get("creation_date", "")
            })
            
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
    resumo: str = "",
    id_externo: str = ""
) -> Dict[str, Any]:
    """
    Cria um novo artigo na base de conhecimento.
    
    Args:
        titulo: Título do artigo
        conteudo: Conteúdo do artigo
        categoria: Categoria do artigo
        url: URL de origem (opcional)
        resumo: Resumo do artigo (opcional)
        id_externo: ID externo para rastreamento (opcional)
        
    Returns:
        Artigo criado ou detalhes do erro
    """
    try:
        client = get_weaviate_client()
        
        if not client:
            raise Exception("Cliente Weaviate não disponível")
            
        collection = client.collections.get("Article")
        
        # Gerar embedding do conteúdo
        embedding = await gerar_embedding_openai(conteudo)
        
        if not embedding:
            raise Exception("Falha ao gerar embedding para o artigo")
            
        # Montar dados do artigo
        artigo_data = {
            "title": titulo,
            "content": conteudo,
            "category": categoria,
            "url": url or "",
            "summary": resumo or "",
            "external_id": id_externo or "",
            "creation_date": get_brazil_time().isoformat(),
            "vector": embedding
        }
        
        # Inserir no Weaviate
        result = collection.data.insert(artigo_data)
        
        logger.info(f"Artigo '{titulo}' criado com sucesso (ID: {result})")
        
        return {
            "id": result,
            "titulo": titulo,
            "categoria": categoria,
            "status": "success"
        }
        
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
    Atualiza um artigo existente.
    
    Args:
        artigo_id: ID do artigo
        titulo: Novo título (opcional)
        conteudo: Novo conteúdo (opcional)
        categoria: Nova categoria (opcional)
        url: Nova URL (opcional)
        resumo: Novo resumo (opcional)
        
    Returns:
        Status da operação
    """
    try:
        client = get_weaviate_client()
        
        if not client:
            raise Exception("Cliente Weaviate não disponível")
            
        collection = client.collections.get("Article")
        
        # Montar dados para atualização
        update_data = {}
        
        if titulo:
            update_data["title"] = titulo
            
        if categoria:
            update_data["category"] = categoria
            
        if url:
            update_data["url"] = url
            
        if resumo:
            update_data["summary"] = resumo
            
        if conteudo:
            update_data["content"] = conteudo
            # Atualizar embedding se o conteúdo mudou
            embedding = await gerar_embedding_openai(conteudo)
            if embedding:
                update_data["vector"] = embedding
        
        # Aplicar atualização
        if update_data:
            collection.data.update(
                uuid=artigo_id,
                properties=update_data
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
    
    Args:
        artigo_id: ID do artigo
        
    Returns:
        Status da operação
    """
    try:
        client = get_weaviate_client()
        
        if not client:
            raise Exception("Cliente Weaviate não disponível")
            
        collection = client.collections.get("Article")
        
        # Excluir do Weaviate
        collection.data.delete(uuid=artigo_id)
        
        logger.info(f"Artigo {artigo_id} excluído com sucesso")
        return {"status": "success", "id": artigo_id}
        
    except Exception as e:
        logger.error(f"Erro ao excluir artigo {artigo_id}: {str(e)}")
        return {"error": str(e), "status": "error"}
