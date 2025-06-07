# ⚙️ Configurações e Variáveis de Ambiente

## 🌍 Variáveis obrigatórias

| Variável             | Descrição                              |
|----------------------|----------------------------------------|
| `SUPABASE_URL`       | URL do Supabase                       |
| `SUPABASE_KEY`       | API Key do Supabase                   |
| `OPENAI_API_KEY`     | API Key do OpenAI                     |
| `WEAVIATE_URL`       | URL do Weaviate                       |
| `WEAVIATE_API_KEY`   | API Key do Weaviate (se necessário)   |
| `EMBEDDING_MODEL`    | Modelo de embedding (ex: text-embedding-ada-002) |
| `DEFAULT_MODEL`      | Modelo de IA (ex: gpt-3.5-turbo)      |
| `ENVIRONMENT`        | dev, staging, production              |

---

## 📜 Exemplo `.env`

SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=xxxx
OPENAI_API_KEY=sk-xxxx
WEAVIATE_URL=https://weaviate.xxxx
WEAVIATE_API_KEY=xxxx
EMBEDDING_MODEL=text-embedding-ada-002
DEFAULT_MODEL=gpt-3.5-turbo
ENVIRONMENT=development