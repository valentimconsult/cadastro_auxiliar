#!/bin/bash

# Script unificado para iniciar a aplicacao no Linux (Desktop e Raspberry Pi)
# Detecta automaticamente o ambiente e otimiza conforme necessario
# Inclui configuracao automatica de acesso externo via Cloudflare Tunnel

echo "=== Iniciando Cadastro Auxiliar no Linux ==="
echo "🚀 Sistema completo com acesso externo configurado automaticamente"

# Verificar se foi passado parametro para apenas configurar acesso externo
if [ "$1" = "--configure-external" ] || [ "$1" = "-c" ]; then
    echo "🔧 Modo: Apenas configurar acesso externo (Docker ja rodando)"
    CONFIGURE_ONLY=true
else
    echo "🚀 Modo: Iniciar aplicacao completa"
    CONFIGURE_ONLY=false
fi

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

# Se for apenas configuracao externa, verificar se Docker esta rodando
if [ "$CONFIGURE_ONLY" = true ]; then
    echo "🔍 Verificando se Docker esta rodando..."
    if ! docker ps | grep -q "cadastro_banco"; then
        echo "❌ ERRO: Container cadastro_banco nao esta rodando!"
        echo "   Execute primeiro: ./scripts/start-app-linux.sh"
        echo "   Ou inicie manualmente: docker-compose up -d"
        exit 1
    fi
    echo "✅ Container PostgreSQL encontrado!"
    
    # Executar configuracao externa
    echo "🔧 Configurando acesso externo ao PostgreSQL..."
    docker exec cadastro_banco /bin/bash -c "
        # Aguardar PostgreSQL estar totalmente pronto
        sleep 2
        
        # Configurar pg_hba.conf para acesso externo
        echo 'Configurando autenticacao para acesso externo...'
        cp /var/lib/postgresql/data/pg_hba.conf /var/lib/postgresql/data/pg_hba.conf.backup
        
        cat > /var/lib/postgresql/data/pg_hba.conf << 'EOF'
# Configuracao de autenticacao PostgreSQL para acesso externo
local   all             all                                     trust
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
host    all             all             0.0.0.0/0               md5
host    all             all             ::/0                    md5
host    all             all             172.16.0.0/12           md5
host    all             all             192.168.0.0/16          md5
host    all             all             10.0.0.0/8              md5
host    cadastro_db     cadastro_user   0.0.0.0/0               md5
EOF
        
        # Configurar postgresql.conf para escutar em todas as interfaces
        echo 'Configurando PostgreSQL para escutar em todas as interfaces...'
        cp /var/lib/postgresql/data/postgresql.conf /var/lib/postgresql/data/postgresql.conf.backup
        
        # Aplicar configuracao de rede
        sed -i \"s/#listen_addresses = 'localhost'/listen_addresses = '*'/\" /var/lib/postgresql/data/postgresql.conf
        sed -i \"s/listen_addresses = 'localhost'/listen_addresses = '*'/\" /var/lib/postgresql/data/postgresql.conf
        
        # Adicionar configuracoes de logging
        cat >> /var/lib/postgresql/data/postgresql.conf << 'EOF'

# Configuracoes de logging para debug
log_connections = on
log_disconnections = on
log_statement = 'all'
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_min_duration_statement = 1000
log_checkpoints = on
log_lock_waits = on
EOF
        
        # Recarregar configuracoes
        echo 'Recarregando configuracoes do PostgreSQL...'
        psql -U cadastro_user -d cadastro_db -c \"SELECT pg_reload_conf();\" || true
        
        echo 'Configuracao de acesso externo concluida!'
    " 2>/dev/null || echo "⚠️  Aviso: Nao foi possivel configurar acesso externo automaticamente"

    # Verificar se todos os servicos estao rodando
    echo "🔍 Verificando servicos..."
    sleep 3

    # Verificar PostgreSQL
    if docker exec cadastro_banco pg_isready -U cadastro_user -d cadastro_db -h localhost >/dev/null 2>&1; then
        echo "✅ PostgreSQL: OK"
    else
        echo "❌ PostgreSQL: ERRO"
    fi

    # Verificar Streamlit
    if curl -s http://localhost:8503 >/dev/null 2>&1; then
        echo "✅ Streamlit: OK"
    else
        echo "❌ Streamlit: ERRO"
    fi

    # Verificar API
    if curl -s http://localhost:5000 >/dev/null 2>&1; then
        echo "✅ API Flask: OK"
    else
        echo "❌ API Flask: ERRO"
    fi

    echo ""
    echo "🎉 Configuracao de acesso externo concluida!"
    echo "=================================================="
    echo ""
    echo "🌐 URLs de acesso local:"
    echo "   Streamlit: http://localhost:8503"
    echo "   API: http://localhost:5000"
    echo "   PostgreSQL: localhost:5436"
    echo ""
    echo "🔗 URLs externas (via Cloudflare Tunnel):"
    echo "   App: https://app-cadastro.valentimconsult.com"
    echo "   API: https://api-cadastro.valentimconsult.com"
    echo "   PostgreSQL: postgres-cadastro.valentimconsult.com:5432"
    echo ""
    echo "📊 Configuracao para Metabase/Superset:"
    echo "   Host: postgres-cadastro.valentimconsult.com"
    echo "   Porta: 5432"
    echo "   Database: cadastro_db"
    echo "   User: cadastro_user"
    echo "   Password: cadastro_password"
    echo ""
    echo "✅ PostgreSQL agora aceita conexoes externas via Cloudflare Tunnel"
    exit 0
fi

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

# Remover volume do PostgreSQL para aplicar configuracoes de acesso externo
echo "🗑️  Removendo volume do PostgreSQL para aplicar configuracoes de acesso externo..."
docker volume rm cadastro_auxiliar_postgres_data 2>/dev/null || true

# Criar diretorios necessarios
echo "📁 Criando diretorios necessarios..."
mkdir -p data logs config database/backups

# Scripts executaveis ja configurados

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
        # Configurar acesso externo ao PostgreSQL
        echo "🔧 Configurando acesso externo ao PostgreSQL..."
        docker exec cadastro_banco /bin/bash -c "
            # Aguardar PostgreSQL estar totalmente pronto
            sleep 5
            
            # Configurar pg_hba.conf para acesso externo
            echo 'Configurando autenticacao para acesso externo...'
            cp /var/lib/postgresql/data/pg_hba.conf /var/lib/postgresql/data/pg_hba.conf.backup
            
            cat > /var/lib/postgresql/data/pg_hba.conf << 'EOF'
# Configuracao de autenticacao PostgreSQL para acesso externo
local   all             all                                     trust
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
host    all             all             0.0.0.0/0               md5
host    all             all             ::/0                    md5
host    all             all             172.16.0.0/12           md5
host    all             all             192.168.0.0/16          md5
host    all             all             10.0.0.0/8              md5
host    cadastro_db     cadastro_user   0.0.0.0/0               md5
EOF
            
            # Configurar postgresql.conf para escutar em todas as interfaces
            echo 'Configurando PostgreSQL para escutar em todas as interfaces...'
            cp /var/lib/postgresql/data/postgresql.conf /var/lib/postgresql/data/postgresql.conf.backup
            
            # Aplicar configuracao de rede
            sed -i \"s/#listen_addresses = 'localhost'/listen_addresses = '*'/\" /var/lib/postgresql/data/postgresql.conf
            sed -i \"s/listen_addresses = 'localhost'/listen_addresses = '*'/\" /var/lib/postgresql/data/postgresql.conf
            
            # Adicionar configuracoes de logging
            cat >> /var/lib/postgresql/data/postgresql.conf << 'EOF'

# Configuracoes de logging para debug
log_connections = on
log_disconnections = on
log_statement = 'all'
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_min_duration_statement = 1000
log_checkpoints = on
log_lock_waits = on
EOF
            
            # Recarregar configuracoes
            echo 'Recarregando configuracoes do PostgreSQL...'
            psql -U cadastro_user -d cadastro_db -c \"SELECT pg_reload_conf();\" || true
            
            echo 'Configuracao de acesso externo concluida!'
        " 2>/dev/null || echo "⚠️  Aviso: Nao foi possivel configurar acesso externo automaticamente"

        # Verificar se todos os servicos estao rodando
        echo "🔍 Verificando servicos..."
        sleep 5

        # Verificar PostgreSQL
        if docker exec cadastro_banco pg_isready -U cadastro_user -d cadastro_db -h localhost >/dev/null 2>&1; then
            echo "✅ PostgreSQL: OK"
        else
            echo "❌ PostgreSQL: ERRO"
        fi

        # Verificar Streamlit
        if curl -s http://localhost:8503 >/dev/null 2>&1; then
            echo "✅ Streamlit: OK"
        else
            echo "❌ Streamlit: ERRO"
        fi

        # Verificar API
        if curl -s http://localhost:5000 >/dev/null 2>&1; then
            echo "✅ API Flask: OK"
        else
            echo "❌ API Flask: ERRO"
        fi

        echo ""
        echo "🎉 Aplicacao iniciada com sucesso!"
        echo "=================================================="
        echo ""
        echo "🌐 URLs de acesso local:"
        echo "   Streamlit: http://localhost:8503"
        echo "   API: http://localhost:5000"
        echo "   PostgreSQL: localhost:5436"
        echo ""
        echo "🔗 URLs externas (via Cloudflare Tunnel):"
        echo "   App: https://app-cadastro.valentimconsult.com"
        echo "   API: https://api-cadastro.valentimconsult.com"
        echo "   PostgreSQL: postgres-cadastro.valentimconsult.com:5432"
        echo ""
        echo "📊 Configuracao para Metabase/Superset:"
        echo "   Host: postgres-cadastro.valentimconsult.com"
        echo "   Porta: 5432"
        echo "   Database: cadastro_db"
        echo "   User: cadastro_user"
        echo "   Password: cadastro_password"
        echo ""
        echo "📝 Para ver os logs:"
        echo "   docker-compose logs -f"
        echo ""
        echo "🛑 Para parar a aplicacao:"
        echo "   docker-compose down"
        echo ""

        if [ "$IS_RASPBERRY_PI" = true ]; then
            echo "🍓 Configuracao otimizada para Raspberry Pi ativa!"
        fi

        echo "✅ Configuracao de acesso externo concluida!"
        echo "🌐 PostgreSQL agora aceita conexoes externas via Cloudflare Tunnel"
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
