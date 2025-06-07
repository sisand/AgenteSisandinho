# app/routers/base_conhecimento.py

import logging
from fastapi import APIRouter, HTTPException
from app.core.clients import get_weaviate_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/artigos", summary="Listar Artigos Base Conhecimento")
async def listar_artigos_base_conhecimento():

    try:
        client = get_weaviate_client()
        collection = client.collections.get("Article")
        
        # Correto: fetch_objects NÃO recebe "properties" mais
        results = collection.query.fetch_objects(limit=100)
        
        artigos = []
        for obj in results.objects:
            artigo = {
                "title": obj.properties.get("title", ""),
                "url": obj.properties.get("url", ""),
                "summary": obj.properties.get("summary", "")
            }
            artigos.append(artigo)
        
        return artigos

    except Exception as e:
        print(f"❌ Erro ao listar artigos da base de conhecimento: {e}")
        raise e