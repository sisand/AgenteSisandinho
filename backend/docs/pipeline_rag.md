# 🚀 Pipeline RAG — Sisandinho IA (Versão PRO) — Junho 2025

---

## 🎯 Visão geral

Este documento descreve o pipeline de **RAG (Retrieval Augmented Generation)** que será utilizado no Sisandinho IA.

Objetivo:

✅ Permitir que o Sisandinho responda perguntas **com base nos artigos do Movidesk**, garantindo:

- Respostas sempre atualizadas (conforme a base do Weaviate).
- Consistência com o conhecimento oficial da Sisand.
- Escalabilidade e controle (não precisa re-treinar para cada nova informação).

---

## 🧩 Componentes do pipeline

| Componente         | Descrição                               |
|--------------------|----------------------------------------|
| Weaviate            | Banco vetorizado com os artigos (Movidesk) |
| Embeddings          | Gerados com OpenAI (ou modelo compatível) |
| FastAPI (fluxo_chat.py) | Orquestrador do fluxo de decisão         |
| Gerador_resposta.py | Responsável por montar o prompt e gerar a resposta final (via GPT) |

---

## 🚀 Fluxo geral RAG

```plaintext
Pergunta do usuário
    ↓
Classificador Categoria (Fine-Tune)
    ↓
Motor de decisão (Precisa de RAG?)
    ↓
Se RAG = SIM:
    ↓
[Função buscar_artigos_weaviate()]
    ↓
Top N artigos relevantes
    ↓
Montar prompt estruturado com artigos
    ↓
Enviar para GPT (via OpenAI API)
    ↓
Resposta contextualizada
    ↓
Resposta final → Supabase + Frontend (Streamlit/Workspace)
