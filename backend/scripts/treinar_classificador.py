# treinar_classificador.py

from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
import pandas as pd
import torch
import os

# Configurações
MODELO_BASE = "xlm-roberta-base"
CAMINHO_CSV = "../dados/dataset_classificador.csv"
PASTA_MODELO_SAIDA = "../modelos/classificador_finetune"

# Detecta se há GPU
dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🚀 Usando dispositivo: {dispositivo}")

# Carrega tokenizer e modelo base
tokenizador = AutoTokenizer.from_pretrained(MODELO_BASE)
modelo = AutoModelForSequenceClassification.from_pretrained(MODELO_BASE, num_labels=8)  # ajustar se mudar número de categorias

# Carrega dataset
df = pd.read_csv(CAMINHO_CSV)

# Mapeia categorias para IDs
categorias_unicas = sorted(df["categoria"].unique())
categoria_para_id = {categoria: i for i, categoria in enumerate(categorias_unicas)}
id_para_categoria = {i: categoria for categoria, i in categoria_para_id.items()}

print(f"✅ Categorias: {categoria_para_id}")

# Adiciona coluna de labels
df["labels"] = df["categoria"].map(categoria_para_id)

# Converte para Dataset Hugging Face
dataset_hf = Dataset.from_pandas(df[["pergunta", "labels"]])

# Função para tokenizar as perguntas
def tokenizar_exemplo(exemplos):
    return tokenizador(exemplos["pergunta"], padding="max_length", truncation=True)

# Aplica tokenização
dataset_tokenizado = dataset_hf.map(tokenizar_exemplo, batched=True)

# Parâmetros de treinamento
argumentos_treinamento = TrainingArguments(
    output_dir=PASTA_MODELO_SAIDA,
    evaluation_strategy="no",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    num_train_epochs=5,
    weight_decay=0.01,
    logging_dir="../logs",
    logging_steps=10,
    save_total_limit=2
)

# Configura mapeamento de labels no modelo
modelo.config.id2label = id_para_categoria
modelo.config.label2id = categoria_para_id

# Configura Trainer
treinador = Trainer(
    model=modelo,
    args=argumentos_treinamento,
    train_dataset=dataset_tokenizado,
    tokenizer=tokenizador
)

# Inicia o treinamento
treinador.train()

# Cria pasta de saída se não existir
os.makedirs(PASTA_MODELO_SAIDA, exist_ok=True)

# Salva modelo fine-tuneado
modelo.save_pretrained(PASTA_MODELO_SAIDA)
tokenizador.save_pretrained(PASTA_MODELO_SAIDA)

print("✅ Fine-tune concluído!")
print(f"✅ Modelo salvo em: {PASTA_MODELO_SAIDA}")
print(f"✅ Categorias: {categoria_para_id}")
