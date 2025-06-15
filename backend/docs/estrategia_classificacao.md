
# 🧠 Estratégia de Classificação de Perguntas — Sisandinho

## ✅ Objetivo

Classificar automaticamente toda pergunta que entra no sistema para definir:
1. **Categoria de domínio** (ex: fiscal, financeiro, oficina, etc.).
2. **Tipo de resposta** (ex: precisa de RAG ou pode ser respondida direto com Fine-Tune).

---

## 🔹 Etapa atual (em produção)

Utilizando classificador **zero-shot** com `facebook/bart-large-mnli` para:

- Detectar a **categoria** da pergunta com as seguintes labels:
  ```
  fiscal, financeiro, oficina, estoque, contabil, integracoes, comercial
  ```
- Essa categoria é usada no pipeline para:
  - Filtrar artigos no RAG (quando necessário).
  - Selecionar o modelo Fine-Tune correto no futuro.

---

## 🔸 Etapas futuras (planejadas no roadmap)

### 1. Substituir o zero-shot por modelo fine-tuned

- Criar dataset com perguntas reais da Sisand.
- Treinar na OpenAI com `classification_finetune.jsonl`.
- Reduzir custo, latência e melhorar precisão.

### 2. Adicionar classificador "Precisa de RAG?"

- Nova etapa no pipeline:
  ```python
  precisa_rag = classificar_precisa_rag(pergunta)
  ```
- Se `sim` → ativa busca no Weaviate.
- Se `não` → responde direto com Fine-Tune.

---

## 🧩 Pipeline de Classificação

```plaintext
Pergunta do usuário
    ↓
[Classificador de Categoria]
    ↓
[Classificador Precisa de RAG?]
    ↓
[Decisão: RAG ou Fine-Tune]
```

---

## ✅ Vantagens da Abordagem

| Item                        | Resultado Esperado                              |
|----------------------------|--------------------------------------------------|
| Latência menor             | Fine-Tune responde rápido e direto               |
| Custo mais baixo           | Menos chamadas OpenAI com RAG                    |
| Precisão adaptada          | IA responde no estilo e contexto da Sisand       |
| Atualização simples        | Basta reclassificar perguntas e reentreinar      |
| Modularidade               | Fácil testar, monitorar e evoluir por partes     |
