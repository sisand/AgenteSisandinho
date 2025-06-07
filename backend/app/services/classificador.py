import logging
import re
from transformers import pipeline
import torch

logger = logging.getLogger(__name__)

# Detecta se há GPU disponível
device = 0 if torch.cuda.is_available() else -1

# Caminho para o modelo fine-tuneado
CAMINHO_MODELO_FINE_TUNE = "modelos/classificador_finetune"

# Carrega o pipeline de classificação com o modelo treinado
logger.info("🔍 Carregando modelo fine-tuneado...")
classificador_pipeline = pipeline(
    "text-classification",
    model=CAMINHO_MODELO_FINE_TUNE,
    device=device,
    top_k=3
)
logger.info("✅ Modelo fine-tuneado carregado com sucesso.")

# Função para normalizar texto
def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = text.strip()
    return text

# Função principal de classificação
async def classificar_pergunta(pergunta: str) -> str:
    pergunta_normalizada = normalize_text(pergunta)

    try:
        # Classificação com o modelo fine-tuneado
        logger.info(f"🧠 Classificando pergunta com modelo fine-tuneado: {pergunta}")
        resultado = classificador_pipeline(pergunta, truncation=True)

        logger.info(f"🎯 Resultado classificação: {resultado}")

        # Se vier como lista de listas (por causa do top_k)
        melhor_resultado = resultado[0][0]

        best_label = melhor_resultado['label']
        best_score = melhor_resultado['score']

        logger.info(f"✅ Classificação final: {best_label} (confiança: {best_score:.2f})")

        # Fallback opcional: se confiança for muito baixa, retorna "geral"
        LIMIAR_CONFIANCA = 0.30
        if best_score < LIMIAR_CONFIANCA:
            logger.warning(f"⚠️ Confiança baixa ({best_score:.2f}), retornando 'geral'")
            return "geral"

        return best_label.lower()
    except Exception as e:
        logger.error(f"❌ Erro na classificação: {e}")
        return "geral"
