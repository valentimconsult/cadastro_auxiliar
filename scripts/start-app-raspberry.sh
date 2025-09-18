#!/bin/bash

# Script para iniciar a aplicacao no Raspberry Pi
# Resolve problemas de compatibilidade com Docker Compose v1.29.2

echo "=== Iniciando Cadastro Auxiliar no Raspberry Pi ==="

# Detectar diretorio do script e navegar para o diretorio do projeto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DOCKER_COMPOSE_FILE="$PROJECT_DIR/docker-compose-raspberry.yml"

echo "Diretorio do projeto: $PROJECT_DIR"
echo "Arquivo docker-compose: $DOCKER_COMPOSE_FILE"

# Verificar se o arquivo docker-compose existe
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo "ERRO: Arquivo docker-compose-raspberry.yml nao encontrado em: $DOCKER_COMPOSE_FILE"
    echo "Certifique-se de que esta executando o script do diretorio correto."
    exit 1
fi

# Navegar para o diretorio do projeto
cd "$PROJECT_DIR"
echo "Trabalhando no diretorio: $(pwd)"

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
docker-compose -f "$DOCKER_COMPOSE_FILE" down 2>/dev/null

# Limpar imagens antigas (opcional)
echo "Limpando imagens antigas..."
docker system prune -f 2>/dev/null

# Construir e iniciar os containers
echo "Construindo e iniciando containers..."
echo "Isso pode levar alguns minutos na primeira execucao..."

# Iniciar todos os containers de uma vez (sem healthcheck dependencies)
echo "Iniciando todos os containers..."
if docker-compose -f "$DOCKER_COMPOSE_FILE" up --build -d; then
    echo "Containers iniciados! Aguardando estabilizacao..."
    
    # Aguardar um pouco para os containers estabilizarem
    sleep 15
    
    # Verificar se todos os containers estao rodando
    echo "Verificando status dos containers:"
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    
    # Aguardar PostgreSQL estar pronto (versao simplificada)
    echo "Aguardando PostgreSQL estar pronto..."
    max_attempts=20
    attempt=0
    postgres_ready=false
    
    while [ $attempt -lt $max_attempts ]; do
        if docker exec cadastro_banco pg_isready -U cadastro_user -d cadastro_db >/dev/null 2>&1; then
            echo "PostgreSQL esta pronto!"
            postgres_ready=true
            break
        fi
        
        echo "Aguardando PostgreSQL... (tentativa $((attempt + 1))/$max_attempts)"
        sleep 3
        attempt=$((attempt + 1))
    done
    
    if [ "$postgres_ready" = true ]; then
        echo "=== Aplicacao iniciada com sucesso! ==="
        echo ""
        echo "Acesse a aplicacao em:"
        echo "  Streamlit: http://localhost:8503"
        echo "  API: http://localhost:5000"
        echo "  PostgreSQL: localhost:5436"
        echo ""
        echo "Para ver os logs:"
        echo "  docker-compose -f $DOCKER_COMPOSE_FILE logs -f"
        echo ""
        echo "Para parar a aplicacao:"
        echo "  docker-compose -f $DOCKER_COMPOSE_FILE down"
    else
        echo "AVISO: PostgreSQL pode nao estar totalmente pronto, mas os containers estao rodando."
        echo "Tente acessar a aplicacao em: http://localhost:8503"
        echo "Se houver problemas, verifique os logs: docker-compose -f $DOCKER_COMPOSE_FILE logs"
    fi
else
    echo "ERRO: Falha ao iniciar a aplicacao."
    echo "Verifique os logs com: docker-compose -f $DOCKER_COMPOSE_FILE logs"
    exit 1
fi
