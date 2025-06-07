from transformers import AutoModelForSequenceClassification

modelo = AutoModelForSequenceClassification.from_pretrained("modelos/classificador_finetune")

print(modelo.config.id2label)
print(modelo.config.label2id)
