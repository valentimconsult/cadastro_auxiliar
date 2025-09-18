# Script para iniciar a aplicacao no Raspberry Pi
# Resolve problemas de compatibilidade com Docker Compose v1.29.2

Write-Host "=== Iniciando Cadastro Auxiliar no Raspberry Pi ===" -ForegroundColor Green

# Verificar se o Docker esta rodando
Write-Host "Verificando Docker..." -ForegroundColor Yellow
try {
    docker --version | Out-Null
    Write-Host "Docker encontrado!" -ForegroundColor Green
} catch {
    Write-Host "ERRO: Docker nao encontrado. Instale o Docker primeiro." -ForegroundColor Red
    exit 1
}

# Verificar se o Docker Compose esta disponivel
Write-Host "Verificando Docker Compose..." -ForegroundColor Yellow
try {
    docker-compose --version | Out-Null
    Write-Host "Docker Compose encontrado!" -ForegroundColor Green
} catch {
    Write-Host "ERRO: Docker Compose nao encontrado. Instale o Docker Compose primeiro." -ForegroundColor Red
    exit 1
}

# Parar containers existentes
Write-Host "Parando containers existentes..." -ForegroundColor Yellow
docker-compose -f docker-compose-raspberry.yml down 2>$null

# Limpar imagens antigas (opcional)
Write-Host "Limpando imagens antigas..." -ForegroundColor Yellow
docker system prune -f 2>$null

# Construir e iniciar os containers
Write-Host "Construindo e iniciando containers..." -ForegroundColor Yellow
Write-Host "Isso pode levar alguns minutos na primeira execucao..." -ForegroundColor Cyan

try {
    # Iniciar PostgreSQL primeiro
    Write-Host "Iniciando PostgreSQL..." -ForegroundColor Yellow
    docker-compose -f docker-compose-raspberry.yml up -d postgres
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERRO: Falha ao iniciar PostgreSQL." -ForegroundColor Red
        exit 1
    }
    
    # Aguardar PostgreSQL estar pronto
    Write-Host "Aguardando PostgreSQL estar pronto..." -ForegroundColor Yellow
    $maxAttempts = 30
    $attempt = 0
    $postgresReady = $false
    
    while ($attempt -lt $maxAttempts) {
        $result = docker exec cadastro_banco pg_isready -U cadastro_user -d cadastro_db 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "PostgreSQL esta pronto!" -ForegroundColor Green
            $postgresReady = $true
            break
        }
        Write-Host "Aguardando PostgreSQL... (tentativa $($attempt + 1)/$maxAttempts)" -ForegroundColor Cyan
        Start-Sleep -Seconds 5
        $attempt++
    }
    
    if (-not $postgresReady) {
        Write-Host "ERRO: PostgreSQL nao ficou pronto a tempo." -ForegroundColor Red
        Write-Host "Verifique os logs: docker-compose -f docker-compose-raspberry.yml logs postgres" -ForegroundColor Yellow
        exit 1
    }
    
    # Iniciar os outros containers
    Write-Host "Iniciando aplicacao e API..." -ForegroundColor Yellow
    docker-compose -f docker-compose-raspberry.yml up --build -d cadastro-app api-server
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "=== Aplicacao iniciada com sucesso! ===" -ForegroundColor Green
        Write-Host ""
        Write-Host "Acesse a aplicacao em:" -ForegroundColor Cyan
        Write-Host "  Streamlit: http://localhost:8503" -ForegroundColor White
        Write-Host "  API: http://localhost:5000" -ForegroundColor White
        Write-Host "  PostgreSQL: localhost:5436" -ForegroundColor White
        Write-Host ""
        Write-Host "Para ver os logs:" -ForegroundColor Cyan
        Write-Host "  docker-compose -f docker-compose-raspberry.yml logs -f" -ForegroundColor White
        Write-Host ""
        Write-Host "Para parar a aplicacao:" -ForegroundColor Cyan
        Write-Host "  docker-compose -f docker-compose-raspberry.yml down" -ForegroundColor White
    } else {
        Write-Host "ERRO: Falha ao iniciar a aplicacao." -ForegroundColor Red
        Write-Host "Verifique os logs com: docker-compose -f docker-compose-raspberry.yml logs" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "ERRO: Erro inesperado ao iniciar a aplicacao." -ForegroundColor Red
    Write-Host "Detalhes: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
