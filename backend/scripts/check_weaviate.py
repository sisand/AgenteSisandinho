import weaviate
import json
from app.core.config import settings  # Importa suas configurações

print("Conectando ao Weaviate para inspecionar o esquema...")

# Use as mesmas configurações do seu app para conectar
client = weaviate.connect_to_wcs(
    cluster_url=settings.WEAVIATE_URL,
    auth_credentials=weaviate.auth.AuthApiKey(settings.WEAVIATE_API_KEY),
    headers={"X-OpenAI-Api-Key": settings.OPENAI_API_KEY}
)

try:
    # Obtém a coleção 'Article'
    collection = client.collections.get("Article")
    
    # Pega a configuração da coleção
    config = collection.config.get()
    
    print("\n✅ Esquema da coleção 'Article':")
    # Imprime a configuração de forma legível
    print(json.dumps(config.to_dict(), indent=2))

    # Bônus: Pega um objeto para vermos as propriedades na prática
    response = collection.query.fetch_objects(limit=1)
    if response.objects:
        print("\n✅ Exemplo de um objeto na coleção:")
        print(response.objects[0].properties)

finally:
    print("\nFechando conexão.")
    client.close()