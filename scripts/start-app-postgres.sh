#!/bin/bash

# Script de inicializacao do Cadastro Streamlit com PostgreSQL
# Execute este script no terminal

echo "🚀 Iniciando Cadastro Streamlit com PostgreSQL..."
echo "=================================================="

# Verificar se Docker esta rodando
echo "🔍 Verificando Docker..."
if ! docker version > /dev/null 2>&1; then
    echo "❌ Docker nao esta rodando. Inicie o Docker primeiro."
    exit 1
fi
echo "✅ Docker esta rodando"

# Parar containers existentes SEM remover volumes
echo "🛑 Parando containers existentes (preservando dados)..."
docker-compose down --remove-orphans

# Remover containers com nomes conflitantes
echo "🗑️  Removendo containers conflitantes..."
docker rm -f cadastro-postgres cadastro-streamlit cadastro-api 2>/dev/null || true

# Limpar apenas redes orfaos (NAO volumes!)
echo "🧹  Limpando redes orfaos (preservando volumes)..."
docker network prune -f

# Construir e iniciar containers
echo "🏗️  Construindo e iniciando containers..."
docker-compose up --build -d

# Aguardar PostgreSQL estar pronto
echo "⏳ Aguardando PostgreSQL estar pronto..."
maxAttempts=30
attempt=0

while [ $attempt -lt $maxAttempts ]; do
    sleep 2
    attempt=$((attempt + 1))
    
    if docker exec cadastro-postgres pg_isready -U cadastro_user -d cadastro_db > /dev/null 2>&1; then
        echo "✅ PostgreSQL esta pronto!"
        break
    fi
    
    echo "⏳ Aguardando... ($attempt/$maxAttempts)"
    
    if [ $attempt -ge $maxAttempts ]; then
        echo "❌ Timeout aguardando PostgreSQL"
        echo "Verifique os logs com: docker-compose logs postgres"
        exit 1
    fi
done

# Aguardar aplicacoes estarem prontas
echo "⏳ Aguardando aplicacoes estarem prontas..."
sleep 10

# Verificar status dos containers
echo "🔍 Verificando status dos containers..."
docker-compose ps

# Mostrar logs dos containers
echo "📋 Logs dos containers:"
echo "Para ver logs em tempo real, use:"
echo "  docker-compose logs -f"
echo "  docker-compose logs -f cadastro-app"
echo "  docker-compose logs -f postgres"

# Mostrar URLs de acesso
echo "🌐 URLs de acesso:"
echo "  Streamlit App: http://localhost:8503"
echo "  API Server: http://localhost:5000"
echo "  PostgreSQL: localhost:5436"

# Informacoes de conexao com banco
echo "🗄️  Informacoes do banco PostgreSQL:"
echo "  Host: localhost"
echo "  Porta: 5436"
echo "  Database: cadastro_db"
echo "  Usuario: cadastro_user"
echo "  Senha: cadastro_password"

echo "=================================================="
echo "🎉 Sistema iniciado com sucesso!"
echo "💡 Use 'docker-compose down' para parar o sistema"
