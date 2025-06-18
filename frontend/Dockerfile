# Dockerfile para Frontend (Streamlit)

# Use uma imagem base oficial e leve do Python
FROM python:3.10-slim

# Defina o diretório de trabalho dentro do contentor
WORKDIR /app

# --- OTIMIZAÇÃO E CORREÇÃO ---
# 1. Copia apenas o arquivo de requisitos primeiro para otimizar o cache do Docker
COPY requirements.txt ./

# 2. Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# 4. Agora, copia o resto do código da sua aplicação
COPY . .

# Expõe a porta que o Cloud Run irá usar
EXPOSE 8080

# Comando para executar a aplicação Streamlit na porta correta
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]