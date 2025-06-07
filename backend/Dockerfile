FROM python:3.10-slim

WORKDIR /app

# Copiar requisitos e instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Variável de ambiente para porta
ENV PORT=8000

# Expor a porta
EXPOSE 8000

# Comando para iniciar 
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
