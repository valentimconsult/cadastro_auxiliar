# Script de inicializacao do Cadastro Streamlit com PostgreSQL
# Execute este script no PowerShell como Administrador

Write-Host "🚀 Iniciando Cadastro Streamlit com PostgreSQL..." -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Cyan

# Verificar se Docker esta rodando
Write-Host "🔍 Verificando Docker..." -ForegroundColor Yellow
try {
    docker version | Out-Null
    Write-Host "✅ Docker esta rodando" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker nao esta rodando. Inicie o Docker Desktop primeiro." -ForegroundColor Red
    exit 1
}

# Parar containers existentes se houver
Write-Host "🛑 Parando containers existentes..." -ForegroundColor Yellow
docker-compose down

# Remover containers e volumes antigos (opcional)
$removeOld = Read-Host "Deseja remover containers e volumes antigos? (s/N)"
if ($removeOld -eq "s" -or $removeOld -eq "S") {
    Write-Host "🗑️  Removendo containers e volumes antigos..." -ForegroundColor Yellow
    docker-compose down -v
    docker system prune -f
}

# Construir e iniciar containers
Write-Host "🏗️  Construindo e iniciando containers..." -ForegroundColor Yellow
docker-compose up --build -d

# Aguardar PostgreSQL estar pronto
Write-Host "⏳ Aguardando PostgreSQL estar pronto..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0

do {
    Start-Sleep -Seconds 2
    $attempt++
    
    try {
        $result = docker exec cadastro-postgres pg_isready -U cadastro_user -d cadastro_db
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ PostgreSQL esta pronto!" -ForegroundColor Green
            break
        }
    } catch {
        # Ignorar erros
    }
    
    Write-Host "⏳ Aguardando... ($attempt/$maxAttempts)" -ForegroundColor Yellow
    
    if ($attempt -ge $maxAttempts) {
        Write-Host "❌ Timeout aguardando PostgreSQL" -ForegroundColor Red
        Write-Host "Verifique os logs com: docker-compose logs postgres" -ForegroundColor Yellow
        exit 1
    }
} while ($true)

# Aguardar aplicacoes estarem prontas
Write-Host "⏳ Aguardando aplicacoes estarem prontas..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Verificar status dos containers
Write-Host "🔍 Verificando status dos containers..." -ForegroundColor Yellow
docker-compose ps

# Mostrar logs dos containers
Write-Host "📋 Logs dos containers:" -ForegroundColor Cyan
Write-Host "Para ver logs em tempo real, use:" -ForegroundColor Yellow
Write-Host "  docker-compose logs -f" -ForegroundColor White
Write-Host "  docker-compose logs -f cadastro-app" -ForegroundColor White
Write-Host "  docker-compose logs -f postgres" -ForegroundColor White

# Mostrar URLs de acesso
Write-Host "🌐 URLs de acesso:" -ForegroundColor Cyan
Write-Host "  Streamlit App: http://localhost:8503" -ForegroundColor Green
Write-Host "  API Server: http://localhost:5000" -ForegroundColor Green
Write-Host "  PostgreSQL: localhost:5436" -ForegroundColor Green

# Informacoes de conexao com banco
Write-Host "🗄️  Informacoes do banco PostgreSQL:" -ForegroundColor Cyan
Write-Host "  Host: localhost" -ForegroundColor White
Write-Host "  Database: cadastro_db" -ForegroundColor White
Write-Host "  Usuario: cadastro_user" -ForegroundColor White
Write-Host "  Senha: cadastro_password" -ForegroundColor White

Write-Host "=" * 50 -ForegroundColor Cyan
Write-Host "🎉 Sistema iniciado com sucesso!" -ForegroundColor Green
Write-Host "💡 Use 'docker-compose down' para parar o sistema" -ForegroundColor Yellow
