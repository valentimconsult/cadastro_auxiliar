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

if docker-compose -f docker-compose-raspberry.yml up --build -d; then
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
