# 🚀 AgenteIA — API do Assistente Virtual Sisandinho

Sistema backend para suporte inteligente utilizando IA generativa (OpenAI) combinada com busca semântica (RAG) através do Weaviate e banco de dados no Supabase.

---

## 🏗️ Arquitetura

A arquitetura segue princípios de **Clean Architecture** e **Domain-Driven Design (DDD)**, separando responsabilidades claramente:

app/
├── core/ # Configurações e conexões (OpenAI, Weaviate, Supabase)
├── domain/ # Motor central da IA (Chat Engine)
├── routers/ # Endpoints HTTP (chat, chat_rag, sessoes, usuarios...)
├── services/ # Controle de histórico, classificação e persistência
├── main.py # Inicialização da aplicação FastAPI
├── docs/ # Documentação técnica



---

## ⚙️ Tecnologias

- **FastAPI** — API moderna e de alta performance
- **OpenAI API** — IA generativa (ChatGPT e embeddings)
- **Weaviate** — Banco de vetores para busca semântica (RAG)
- **Supabase** — Banco de dados e autenticação
- **Pydantic + Pydantic-Settings** — Validação e gestão de configuração
- **Uvicorn** — ASGI Server
- **Hugging Face Transformers** — Classificação e NLP
- **Torch** — Machine Learning

---

## 🔥 Fluxos Disponíveis

### 🧠 Chat Simples (`/api/chat/ask`)
- IA responde diretamente com base no prompt e, opcionalmente, no histórico.
- Não faz busca semântica (não usa RAG).

### 🔍 Chat com RAG (`/api/chat-rag/ask`)
- IA utiliza contexto externo.
- Faz embedding da pergunta → busca artigos relevantes no Weaviate → monta prompt → gera resposta.

---

## 🌐 Documentação dos Endpoints

| Método | Endpoint              | Descrição                                 |
|--------|------------------------|--------------------------------------------|
| POST   | `/api/chat/ask`        | Chat simples (IA pura)                    |
| POST   | `/api/chat-rag/ask`    | Chat com RAG (busca + IA)                 |
| GET    | `/api/health`          | Verificar status e serviços externos      |
| GET    | `/api/debug/routes`    | Lista todas as rotas da API               |

Documentação Swagger disponível automaticamente em:  
👉 **`/docs`**

---

## 📄 Documentação Técnica

- 🏗️ [Arquitetura do Projeto](./docs/arquitetura.md)
- 🔥 [Fluxo do Chat Engine (com e sem RAG)](./docs/fluxo_chat_engine.md)
- 🌐 [Documentação dos Endpoints](./docs/apis.md)
- ⚙️ [Configurações e Variáveis de Ambiente](./docs/configuracoes.md)

---

## 🚀 Executando Localmente

### ✔️ Pré-requisitos
- Python 3.10+
- Ambiente virtual configurado (`venv`)
- Dependências instaladas

### ✔️ Instalação

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente (Windows)
venv\Scripts\activate

# Ativar ambiente (Mac/Linux)
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

✔️ Executar o servidor
uvicorn app.main:app --reload

Acesse:
👉 http://127.0.0.1:8000/docs → Swagger UI

🧠 Variáveis de Ambiente (.env)
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=xxxx
OPENAI_API_KEY=sk-xxxx
WEAVIATE_URL=https://weaviate.xxxx
WEAVIATE_API_KEY=xxxx
EMBEDDING_MODEL=text-embedding-ada-002
DEFAULT_MODEL=gpt-3.5-turbo
ENVIRONMENT=development


🏥 Health Check
GET /api/health
Retorna status do backend e de serviços externos (Supabase e OpenAI).

🚀 Roadmap
✅ Organização dos routers e domain

✅ Documentação completa no /docs

🔜 Testes automatizados (Pytest + HTTPX)

🔜 Deploy com Docker + CI/CD

🔜 Painel de administração

🔜 Logs estruturados e monitoramento

🔜 Classificação de intenção otimizada com Hugging Face

🤝 Contribuindo
Clone este repositório.

Crie uma branch:
git checkout -b feature/sua-feature


Commit suas alterações:
git commit -m 'feat: Sua alteração'

Push para sua branch:
git push origin feature/sua-feature

Crie um Pull Request.

🏢 Sobre a Sisand
Este projeto é parte da transformação digital da Sisand, levando IA, automação e eficiência para os nossos clientes e para o mercado de gestão de concessionárias e centros automotivos.
