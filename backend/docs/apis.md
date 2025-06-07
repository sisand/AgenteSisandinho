# 🌐 Documentação dos Endpoints — AgenteIA

## 🧠 Chat Simples

- **POST** `/api/chat/ask`
- ✅ IA responde sem buscar artigos externos.
- 🔥 Parâmetros:
  - `pergunta`: string (obrigatório)
  - `usuario_id`: string (opcional)
  - `contexto_anterior`: list (opcional)
  - `sistema_prompt`: string (opcional)
  - `temperatura`: float (opcional)

## 🔍 Chat com RAG

- **POST** `/api/chat-rag/ask`
- 🔥 Funciona igual ao chat, porém utilizando busca vetorial (RAG).

## 🏥 Health Check

- **GET** `/api/health`
- ✅ Verifica status do servidor, Supabase e OpenAI.

## 🔧 Debug

- **GET** `/api/debug/routes`
- ✅ Lista todas as rotas da API.

---
