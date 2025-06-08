# Use uma imagem base oficial e leve do Python
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Otimização para que os logs do Python apareçam imediatamente
ENV PYTHONUNBUFFERED 1

# Copia APENAS o arquivo de requisitos do backend para dentro do container
# Isso otimiza o cache do Docker. A instalação só será refeita se este arquivo mudar.
COPY backend/requirements.txt .

# Instala as dependências do backend
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do seu backend para o diretório de trabalho no container
COPY ./backend /app

# Expõe a porta em que a aplicação vai rodar
EXPOSE 8080

# Define o comando para iniciar o servidor Uvicorn quando o container iniciar
# O Cloud Run automaticamente fornecerá a variável de ambiente $PORT, mas 8080 é um padrão seguro.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]