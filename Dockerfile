# Dockerfile otimizado para Raspberry Pi e sistemas ARM64
# Compativel com: Ubuntu, Raspberry Pi 5, Docker Compose v1 e v2

# Usar imagem base Python
FROM python:3.11-slim

# Metadados da imagem
LABEL maintainer="Cadastro Streamlit App"
LABEL description="Aplicacao de cadastro com Streamlit e Flask API"
LABEL version="1.0"

# Configuracoes de ambiente para otimizacao
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias do sistema
RUN apt-get update && apt-get install -y \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Atualizar pip e instalar dependencias Python
RUN pip install --upgrade pip setuptools wheel

# Copiar arquivo de dependencias primeiro para aproveitar cache do Docker
COPY requirements.txt /app/requirements.txt

# Instalar dependencias Python
RUN pip install --no-cache-dir -r /app/requirements.txt

# Criar diretorio da aplicacao
WORKDIR /app

# Copiar arquivos da aplicacao
COPY streamlit_app.py /app/
COPY api_server.py /app/
COPY config.json /app/
COPY database /app/database
COPY data /app/data

# Criar diretorios necessarios
RUN mkdir -p /app/logs /app/config

# Definir permissoes adequadas
RUN chmod -R 755 /app

# Expor porta padrao do Streamlit
EXPOSE 8501

# Comando padrao para executar a aplicacao Streamlit
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.headless=true", "--browser.gatherUsageStats=false"]