# Use uma imagem base oficial e leve do Python
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Otimização para que os logs do Python apareçam imediatamente
ENV PYTHONUNBUFFERED 1

# ==================================================
# 👇 CORREÇÃO AQUI 👇
# Como o build agora começa de dentro da pasta "backend",
# os caminhos de cópia não precisam mais do prefixo "backend/".
# ==================================================

# Copia o arquivo de requisitos para dentro do container
COPY requirements.txt .

# Instala as dependências do backend
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da pasta atual (que agora é a 'backend') para o container
COPY . /app

# Expõe a porta em que a aplicação vai rodar
EXPOSE 8080

# Define o comando para iniciar o servidor Uvicorn quando o container iniciar
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]