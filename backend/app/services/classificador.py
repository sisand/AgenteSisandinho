import logging
import re
from transformers import pipeline
import torch

logger = logging.getLogger(__name__)

# Detecta se há GPU disponível
device = 0 if torch.cuda.is_available() else -1

# ===================================================================
# 👇 INÍCIO DA MUDANÇA 👇
# ===================================================================

# O "endereço" do modelo agora aponta para o seu repositório no Hugging Face Hub
MODEL_ID = "sisand/classificador-sisandinho"

# Carrega o pipeline de classificação com o modelo da nuvem
logger.info(f"🔍 Carregando modelo '{MODEL_ID}' do Hugging Face Hub...")
classificador_pipeline = None # Inicializa como None
try:
    # A biblioteca transformers usará o MODEL_ID para baixar e carregar o modelo.
    # Se o token HUGGING_FACE_HUB_TOKEN estiver configurado no Render, ele o usará
    # para acessar seu repositório privado.
    classificador_pipeline = pipeline(
        "text-classification",
        model=MODEL_ID,
        device=device,
        top_k=3
    )
    logger.info("✅ Modelo do Hub carregado com sucesso.")
except Exception as e:
    logger.error(f"❌ FALHA CRÍTICA AO CARREGAR MODELO DO HUB: {e}")
    # Se o modelo não puder ser carregado, a aplicação ainda pode subir,
    # mas a função de classificação retornará um valor padrão.

# ===================================================================
# 👆 FIM DA MUDANÇA 👆
# ===================================================================


# Função para normalizar texto (nenhuma mudança aqui)
def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = text.strip()
    return text

# Função principal de classificação (pequeno ajuste de segurança)
async def classificar_pergunta(pergunta: str) -> str:
    # Adicionamos uma verificação para garantir que o pipeline foi carregado
    if not classificador_pipeline:
        logger.error("Pipeline de classificação não está disponível. Retornando 'geral'.")
        return "geral"

    pergunta_normalizada = normalize_text(pergunta)

    try:
        logger.info(f"🧠 Classificando pergunta com modelo fine-tuneado: {pergunta}")
        resultado = classificador_pipeline(pergunta, truncation=True)
        logger.info(f"🎯 Resultado classificação: {resultado}")

        melhor_resultado = resultado[0][0]
        best_label = melhor_resultado['label']
        best_score = melhor_resultado['score']

        logger.info(f"✅ Classificação final: {best_label} (confiança: {best_score:.2f})")

        LIMIAR_CONFIANCA = 0.30
        if best_score < LIMIAR_CONFIANCA:
            logger.warning(f"⚠️ Confiança baixa ({best_score:.2f}), retornando 'geral'")
            return "geral"

        return best_label.lower()
    except Exception as e:
        logger.error(f"❌ Erro na classificação: {e}")
        return "geral"