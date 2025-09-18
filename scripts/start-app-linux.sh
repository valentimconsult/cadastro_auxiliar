#!/bin/bash

# Script unificado para iniciar a aplicacao no Linux (Desktop e Raspberry Pi)
# Detecta automaticamente o ambiente e otimiza conforme necessario

echo "=== Iniciando Cadastro Auxiliar no Linux ==="

# Detectar diretorio do script e navegar para o diretorio do projeto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DOCKER_COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"

echo "Diretorio do projeto: $PROJECT_DIR"
echo "Arquivo docker-compose: $DOCKER_COMPOSE_FILE"

# Verificar se o arquivo docker-compose existe
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo "ERRO: Arquivo docker-compose.yml nao encontrado em: $DOCKER_COMPOSE_FILE"
    echo "Certifique-se de que esta executando o script do diretorio correto."
    exit 1
fi

# Navegar para o diretorio do projeto
cd "$PROJECT_DIR"
echo "Trabalhando no diretorio: $(pwd)"

# Detectar se e Raspberry Pi
if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "Raspberry Pi detectado! Aplicando otimizacoes..."
    IS_RASPBERRY_PI=true
else
    echo "Desktop Linux detectado."
    IS_RASPBERRY_PI=false
fi

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

# Verificar memoria disponivel
echo "Verificando recursos do sistema..."
TOTAL_MEM=$(free -m | awk 'NR==2{printf "%.0f", $2}')
TOTAL_CPU=$(nproc)
echo "Memoria total: ${TOTAL_MEM}MB"
echo "CPUs disponiveis: ${TOTAL_CPU}"

if [ "$IS_RASPBERRY_PI" = true ]; then
    echo "Configuracao otimizada para Raspberry Pi aplicada."
    if [ $TOTAL_MEM -lt 4000 ]; then
        echo "AVISO: Memoria baixa detectada. Considerando otimizacoes adicionais..."
    fi
fi

# Parar containers existentes
echo "Parando containers existentes..."
docker-compose -f "$DOCKER_COMPOSE_FILE" down 2>/dev/null

# Limpar imagens antigas (opcional)
echo "Limpando imagens antigas..."
docker system prune -f 2>/dev/null

# Construir e iniciar os containers
echo "Construindo e iniciando containers..."
echo "Isso pode levar alguns minutos na primeira execucao..."

# Iniciar todos os containers de uma vez
if docker-compose -f "$DOCKER_COMPOSE_FILE" up --build -d; then
    echo "Containers iniciados! Aguardando estabilizacao..."
    
    # Aguardar estabilizacao
    if [ "$IS_RASPBERRY_PI" = true ]; then
        echo "Aguardando estabilizacao no Raspberry Pi (30 segundos)..."
        sleep 30
    else
        echo "Aguardando estabilizacao no desktop (15 segundos)..."
        sleep 15
    fi
    
    # Verificar se todos os containers estao rodando
    echo "Verificando status dos containers:"
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    
    # Aguardar PostgreSQL estar pronto
    echo "Aguardando PostgreSQL estar pronto..."
    max_attempts=30
    attempt=0
    postgres_ready=false
    
    while [ $attempt -lt $max_attempts ]; do
        # Verificar se o container está rodando
        if ! docker ps | grep -q "cadastro_banco"; then
            echo "ERRO: Container cadastro_banco nao esta rodando!"
            echo "Verificando logs do PostgreSQL:"
            docker-compose -f "$DOCKER_COMPOSE_FILE" logs postgres
            exit 1
        fi
        
        # Verificar status do container
        CONTAINER_STATUS=$(docker ps --filter "name=cadastro_banco" --format "{{.Status}}")
        echo "Status do PostgreSQL: $CONTAINER_STATUS"
        
        # Tentar conectar com PostgreSQL
        if docker exec cadastro_banco pg_isready -U cadastro_user -d cadastro_db >/dev/null 2>&1; then
            echo "PostgreSQL esta pronto!"
            postgres_ready=true
            break
        fi
        
        echo "Aguardando PostgreSQL... (tentativa $((attempt + 1))/$max_attempts)"
        
        # Verificar logs se estiver demorando muito
        if [ $attempt -eq 5 ] || [ $attempt -eq 15 ]; then
            echo "Logs do PostgreSQL (ultimas 5 linhas):"
            docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=5 postgres
        fi
        
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
        echo "  docker-compose logs -f"
        echo ""
        echo "Para parar a aplicacao:"
        echo "  docker-compose down"
        echo ""
        if [ "$IS_RASPBERRY_PI" = true ]; then
            echo "Configuracao otimizada para Raspberry Pi ativa!"
        fi
    else
        echo "ERRO: PostgreSQL nao ficou pronto a tempo."
        echo "Verifique os logs: docker-compose logs postgres"
        echo ""
        echo "Troubleshooting:"
        echo "1. Verifique se ha memoria suficiente: free -h"
        echo "2. Verifique se ha espaco em disco: df -h"
        echo "3. Verifique logs detalhados: docker-compose logs postgres"
        exit 1
    fi
else
    echo "ERRO: Falha ao iniciar a aplicacao."
    echo "Verifique os logs com: docker-compose logs"
    exit 1
fi
