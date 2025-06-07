# 🔥 Fluxo do Chat Engine — AgenteIA

## 🚀 Funcionamento Geral

O Chat Engine funciona para dois fluxos:

- ✅ **Chat simples:** IA responde diretamente com base no prompt.
- ✅ **Chat com RAG:** A IA utiliza contexto externo (artigos buscados no Weaviate) + prompt.

---

## 🏗️ Fluxo com RAG (`/api/chat-rag/ask`)

1. Usuário envia uma pergunta.
2. Sistema gera embedding da pergunta.
3. Faz busca vetorial no Weaviate para encontrar artigos relacionados.
4. Monta um prompt contendo:
   - Histórico da conversa (se houver).
   - Artigos encontrados (contexto externo).
5. Envia esse prompt para o OpenAI.
6. Recebe a resposta e salva no histórico.

---

## 🔸 Fluxo sem RAG (`/api/chat/ask`)

1. Usuário envia uma pergunta.
2. Monta o prompt apenas com:
   - Histórico da conversa (se houver).
3. OpenAI responde diretamente (sem buscar artigos).
4. Salva no histórico.

---

## 📦 Controle de Histórico

Feito por `/services/chat_flow.py`:

- `add_message_to_history()`
- `get_user_history()`
- `classify_message()`
- `save_interaction()`

---

## ⚙️ Componentes Chave

- **`domain/chat_engine.py`** → Motor central.
- **`services/chat_flow.py`** → Histórico e classificação.
- **`routers/chat.py`** → Endpoint IA pura.
- **`routers/chat_rag.py`** → Endpoint IA + RAG.

---
