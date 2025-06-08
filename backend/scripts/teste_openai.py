from openai import OpenAI
from dotenv import load_dotenv

# Apenas carrega as variáveis do seu arquivo .env para o ambiente
load_dotenv()

# Cria o cliente SEM passar a chave diretamente.
# A biblioteca da OpenAI irá procurar automaticamente pela variável de ambiente "OPENAI_API_KEY".
# Se não encontrar, ela dará um erro claro, o que é um comportamento seguro.
client = OpenAI()

# O resto do seu código de teste continua igual
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "Olá, você está funcionando?"}
    ],
)

print(response.choices[0].message.content)