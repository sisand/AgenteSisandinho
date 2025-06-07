# 🧠 Roadmap Atualizado do Sisandinho IA — Junho 2025 (pós-importação Weaviate + sugestões Gemini)

---

## 🎯 Visão de Futuro

Um agente inteligente capaz de:

✅ Classificar qualquer pergunta (`social`, `fiscal`, `financeiro`, `comercial`, etc.).  
✅ Decidir de forma **automática e eficiente**: Fine-Tune direto ou RAG.  
✅ Responder com o **tom da Sisand**, com contexto de processos e conhecimento atualizado.  
✅ Aprender continuamente por **curadoria** e feedback real.  
✅ Evoluir com métricas claras e versionamento.  
✅ Permitir conversas multi-turno e integração com funções operacionais (visão futura). 🆕

---

# 🟠 Fase 0 — Validação e Alinhamento Estratégico (🆕 Adição sugerida por Gemini)

🎯 **Objetivo:** Revisar se estamos otimizando para as métricas certas e se a base e classificações estão preparadas.

### Etapas:

✅ Revisar cobertura dos 470 artigos:
- Cobrem os top tickets?
- Existe priorização de gaps?

✅ Revisar granularidade da classificação:
- "Fiscal" precisa subcategorias?
- Alguma categoria nova emergindo?

✅ Definir claramente:
- O que é um "ticket evitado"?
- O que é um "usuário com autonomia"?

✅ Revisar fluxo de perguntas fora de escopo:
- Estratégia de fallback e de escalonamento para humano.

✅ Definir e registrar:
- Métricas de sucesso: resolução pelo agente, redução de tickets, feedback, taxa de uso.

---

# 🟩 Fase 1 — Classificação Profissional com Fine-Tune (status: CONCLUÍDA v1)

🎯 **Objetivo:** Trocar regras manuais por classificador robusto.

### Status:

✅ Fine-tune Hugging Face com `xlm-roberta-base`.  
✅ Pipeline rodando no `fluxo_chat.py`.  
✅ Labels personalizadas.  
✅ Fallback implementado.  
✅ Logs no backend + Supabase.

### Próximas melhorias:

- Expandir dataset com uso real.  
- Refinar Fine-Tune.  
- Testar modelos mais leves (DistilRoberta).  

---

# 🟨 Fase 2 — Roteamento Inteligente com Classificador "Precisa de RAG?" (em andamento)

🎯 **Objetivo:** IA decidir se busca no RAG ou responde direto.

### Avanços recentes:

✅ Importação 100% dos artigos no Weaviate.  
✅ Base RAG operacional.  
✅ Busca semântica validada.

### Novas prioridades:

1️⃣ Implementar `classificar_precisa_rag()`.  
2️⃣ 🆕 **Filtrar busca no RAG com base na classificação** (ex: fiscal → só artigos fiscais).  
3️⃣ Aprimorar prompts RAG.  
4️⃣ 🆕 Logar **quais chunks foram usados** na resposta (para curadoria futura).  
5️⃣ Iniciar Dashboard de Curadoria com:
- Feedback (👍 / 👎).  
- Fluxo utilizado (RAG_Fiscal, ForaDeEscopo, etc.).  
- Logs de chunks usados.

---

# 🟧 Fase 3 — Modelos Especialistas por Domínio + Curadoria Avançada

🎯 **Objetivo:** Refino contínuo da IA com aprendizado supervisionado.

### Etapas:

✅ Criar datasets especialistas (fiscal, oficina, financeiro).  
✅ Treinar modelos por domínio.  
✅ Atualizar curadoria para alimentar esses domínios.  
✅ Aprimorar decisão Fine-Tune vs RAG.

### 🆕 Curadoria avançada:
- Análise de erros de classificação.  
- Análise de falhas de chunking.  
- Análise de falha de síntese do LLM.  
- Correção de classificações para re-treino.  
- Correção de base RAG e chunking.  
- Construção de dataset curado para fine-tune do LLM.  

---

# 🟥 Fase 4 — IA Autônoma e Aprendizado Contínuo

🎯 **Objetivo:** Pipeline de melhoria contínua + expansão das capacidades.

### Etapas:

✅ Coleta de feedback (👍 / 👎).  
✅ Dashboard de curadoria.  
✅ Geração automatizada de dataset incremental.  
✅ Pipeline de retrain dos modelos (HF + LLM).  
✅ Deploy contínuo com versionamento (`ft-sisand-vYYYYMMDD`).  
✅ Monitoramento avançado:
- Taxa de acerto.  
- Uso de RAG vs Fine-Tune.  
- Satisfação do usuário.  
- Detecção de drift de dados. 🆕

### 🆕 Fine-tuning do LLM:
- Dataset: pergunta + chunks corretos + resposta ideal.  
- Fine-tune do LLM (ex: GPT-4 FT, OpenChat, Claude FT).  
- Deploy da versão fine-tunada no backend.  

### 🆕 Expansão:
- Conversas multi-turno.  
- Function calling: integração com APIs do Vision (consultas e pequenas automações).  
- Sugestões proativas do agente.  
- Monitoramento de custo / performance.  

---

# 🚀 Pipeline Atual (visual)

```plaintext
Pergunta do usuário
    ↓
[Classificador Categoria Fine-Tune]
    ↓
[classificar_precisa_rag()]
    ↓
→ Se SIM → Busca no Weaviate (RAG com filtro de categoria)
→ Se NÃO → Resposta Fine-Tune direto
    ↓
Resposta final
    ↓
Feedback (👍 / 👎) → Logs → Curadoria → Dataset incremental


## 🏆 Vantagens da arquitetura atual

| Item           | Resultado Atual                           | Próxima evolução                       |
| -------------- | ----------------------------------------- | -------------------------------------- |
| Classificação  | Fine-Tune Hugging Face funcionando        | Refinar + dataset real                 |
| Latência       | Melhor que zero-shot na OpenAI            | DistilRoberta + filtros por categoria  |
| Modularidade   | Backend FastAPI com métricas              | Logging de chunks + curadoria avançada |
| Custo          | Baixo custo para classificação            | Otimização RAG + LLM FT                |
| Escalabilidade | Arquitetura preparada para IA operacional | Function calling + multi-turn          |
| Curadoria      | Supabase + backend prontos                | Dashboard avançado                     |
| RAG            | Base 100% populada + busca validada       | Filtro por categoria + fine-tune LLM   |



## 🚀 Roadmap das fases (atualizado — junho 2025)

| Fase      | Objetivo                                                | Status                 |
| --------- | ------------------------------------------------------- | ---------------------- |
| 🟠 Fase 0 | Validação estratégica e métricas                        | 🚀 Iniciar em paralelo |
| 🟩 Fase 1 | Classificador Fine-Tune                                 | ✅ Concluído v1         |
| 🟨 Fase 2 | Roteamento inteligente + logging RAG + curadoria básica | 🔄 Em andamento        |
| 🟧 Fase 3 | Curadoria avançada + modelos especialistas              | 🟡 Planejamento        |
| 🟥 Fase 4 | IA autônoma + fine-tune LLM + multi-turn + FC           | 🟡 Planejamento        |
