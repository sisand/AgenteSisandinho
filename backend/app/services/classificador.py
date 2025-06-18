# app/services/classificador.py

import logging
import re
from transformers import pipeline, Pipeline
import torch
from typing import Optional

logger = logging.getLogger(__name__)

# Detecta se há GPU disponível, caso contrário usa a CPU
device = 0 if torch.cuda.is_available() else -1

# O "endereço" do modelo agora aponta para o seu repositório no Hugging Face Hub
MODEL_ID = "sisand/classificador-sisandinho"

# Carrega o pipeline de classificação com o modelo da nuvem
logger.info(f"🔍 A carregar o modelo '{MODEL_ID}' do Hugging Face Hub...")
classificador_pipeline: Optional[Pipeline] = None # Inicializa como None para segurança
try:
    # A biblioteca transformers usará o MODEL_ID para descarregar e carregar o modelo.
    # Se o seu repositório for privado, é necessário configurar um token de acesso.
    classificador_pipeline = pipeline(
        "text-classification",
        model=MODEL_ID,
        device=device,
        top_k=3 # Retorna as 3 categorias mais prováveis
    )
    logger.info("✅ Modelo do Hub carregado com sucesso.")
except Exception as e:
    logger.error(f"❌ FALHA CRÍTICA AO CARREGAR O MODELO DO HUB: {e}")
    # Se o modelo não puder ser carregado, a aplicação ainda pode subir,
    # mas a função de classificação retornará um valor padrão.


def normalizar_texto(texto: str) -> str:
    """Normaliza o texto para a classificação."""
    texto = texto.lower()
    texto = re.sub(r'[^\w\s]', '', texto)
    texto = texto.strip()
    return texto


async def classificar_pergunta(pergunta: str) -> str:
    """
    Classifica a pergunta do usuário usando o modelo do Hugging Face.
    Retorna a categoria com maior pontuação ou 'geral' se a confiança for baixa.
    """
    # Verificação de segurança para garantir que o pipeline foi carregado
    if not classificador_pipeline:
        logger.error("O pipeline de classificação não está disponível. A retornar 'geral'.")
        return "geral"

    texto_normalizado = normalizar_texto(pergunta)

    try:
        logger.info(f"🧠 A classificar pergunta com o modelo fine-tuneado: {pergunta}")
        resultado = classificador_pipeline(texto_normalizado, truncation=True)
        logger.info(f"🎯 Resultado da classificação: {resultado}")

        melhor_resultado = resultado[0][0]
        melhor_categoria = melhor_resultado['label']
        melhor_pontuacao = melhor_resultado['score']

        logger.info(f"✅ Classificação final: {melhor_categoria} (confiança: {melhor_pontuacao:.2f})")

        LIMIAR_CONFIANCA = 0.01
        if melhor_pontuacao < LIMIAR_CONFIANCA:
            logger.warning(f"⚠️ Confiança baixa ({melhor_pontuacao:.2f}), a retornar 'geral'")
            return "geral"

        return melhor_categoria.lower()
    except Exception as e:
        logger.error(f"❌ Erro durante a classificação: {e}")
        return "geral"