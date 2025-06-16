# Use uma imagem base oficial e leve do Python
FROM python:3.10-slim

# Defina o diretório de trabalho dentro do contentor
WORKDIR /app

# Otimização: Copie apenas o ficheiro de requisitos primeiro
COPY requirements.txt ./

# Instale as dependências
# A atualização do pip é uma boa prática
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Agora, copie o resto do código da sua aplicação
COPY . .

# Expõe a porta que o Cloud Run irá usar para comunicar com o contentor
# Embora o comando CMD defina a porta, isto é uma boa prática para documentação.
EXPOSE 8080

# Comando para executar a aplicação Streamlit
# --- CORREÇÃO AQUI: A porta foi alterada para 8080 ---
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
