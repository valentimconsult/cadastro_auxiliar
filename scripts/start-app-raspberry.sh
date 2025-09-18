#!/bin/bash

# Script para iniciar a aplicacao no Raspberry Pi
# Resolve problemas de compatibilidade com Docker Compose v1.29.2

echo "=== Iniciando Cadastro Auxiliar no Raspberry Pi ==="

# Verificar se o Docker esta rodando
echo "Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo "ERRO: Docker nao encontrado. Instale o Docker primeiro."
    exit 1
fi
echo "Docker encontrado!"

# Verificar se o Docker Compose esta disponivel
echo "Verificando Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "ERRO: Docker Compose nao encontrado. Instale o Docker Compose primeiro."
    exit 1
fi
echo "Docker Compose encontrado!"

# Parar containers existentes
echo "Parando containers existentes..."
docker-compose -f docker-compose-raspberry.yml down 2>/dev/null

# Limpar imagens antigas (opcional)
echo "Limpando imagens antigas..."
docker system prune -f 2>/dev/null

# Construir e iniciar os containers
echo "Construindo e iniciando containers..."
echo "Isso pode levar alguns minutos na primeira execucao..."

# Iniciar PostgreSQL primeiro
echo "Iniciando PostgreSQL..."
if ! docker-compose -f docker-compose-raspberry.yml up -d postgres; then
    echo "ERRO: Falha ao iniciar PostgreSQL."
    exit 1
fi

# Aguardar PostgreSQL estar pronto
echo "Aguardando PostgreSQL estar pronto..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker exec cadastro_banco pg_isready -U cadastro_user -d cadastro_db >/dev/null 2>&1; then
        echo "PostgreSQL esta pronto!"
        break
    fi
    echo "Aguardando PostgreSQL... (tentativa $((attempt + 1))/$max_attempts)"
    sleep 5
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "ERRO: PostgreSQL nao ficou pronto a tempo."
    echo "Verifique os logs: docker-compose -f docker-compose-raspberry.yml logs postgres"
    exit 1
fi

# Iniciar os outros containers
echo "Iniciando aplicacao e API..."
if docker-compose -f docker-compose-raspberry.yml up --build -d cadastro-app api-server; then
    echo "=== Aplicacao iniciada com sucesso! ==="
    echo ""
    echo "Acesse a aplicacao em:"
    echo "  Streamlit: http://localhost:8503"
    echo "  API: http://localhost:5000"
    echo "  PostgreSQL: localhost:5436"
    echo ""
    echo "Para ver os logs:"
    echo "  docker-compose -f docker-compose-raspberry.yml logs -f"
    echo ""
    echo "Para parar a aplicacao:"
    echo "  docker-compose -f docker-compose-raspberry.yml down"
else
    echo "ERRO: Falha ao iniciar a aplicacao."
    echo "Verifique os logs com: docker-compose -f docker-compose-raspberry.yml logs"
    exit 1
fi
