# 🏗️ Arquitetura do Backend — AgenteIA

## 📚 Descrição Geral

A arquitetura do backend é baseada em Clean Architecture e Domain-Driven Design (DDD), separando claramente responsabilidades em camadas:

- **Routers** → Definem os endpoints HTTP.
- **Domain** → Motor de regras de negócio (como funciona o chat, com ou sem RAG).
- **Services** → Controle de histórico, classificação, e persistência da conversa.
- **Core** → Configurações globais, conexões com OpenAI, Weaviate e Supabase.

---

## 🗂️ Estrutura de Pastas

app/
├── core/ # Configurações e clientes externos
├── domain/ # Motor da IA (Chat Engine)
├── routers/ # Endpoints HTTP
├── services/ # Controle de histórico, classificação, persistência
main.py # Inicialização do FastAPI



---

## 🔧 Tecnologias Utilizadas

- **FastAPI** — Framework web.
- **OpenAI API** — IA generativa (ChatGPT, embeddings).
- **Weaviate** — Banco de vetores (busca semântica — RAG).
- **Supabase** — Banco de dados relacional e autenticação.
- **Pydantic** — Validação de dados e settings.
- **Uvicorn** — Servidor ASGI.

---

## 🔥 Fluxo Resumido do Chat

- `/api/chat` → **Chat Simples (IA pura, sem RAG)**
- `/api/chat-rag` → **Chat Avançado com RAG (busca + IA)**

Ambos os fluxos usam o mesmo motor central (`domain/chat_engine.py`), que decide se utiliza ou não o RAG com base no parâmetro `usar_rag`.

---
