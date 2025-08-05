# Script para gerenciar a aplicacao de cadastro Streamlit
# Autor: Sistema de Cadastro
# Data: $(Get-Date -Format "yyyy-MM-dd")

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "restart", "logs", "build", "clean", "status")]
    [string]$Action = "start"
)

function Write-Header {
    param([string]$Message)
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Yellow
}

# Verificar se Docker esta instalado
function Test-Docker {
    try {
        docker --version | Out-Null
        return $true
    }
    catch {
        Write-Error "Docker nao esta instalado ou nao esta no PATH"
        return $false
    }
}

# Verificar se Docker Compose esta disponivel
function Test-DockerCompose {
    try {
        docker-compose --version | Out-Null
        return $true
    }
    catch {
        Write-Error "Docker Compose nao esta disponivel"
        return $false
    }
}

# Criar diretorios necessarios
function Initialize-Directories {
    $directories = @("data", "config", "logs")
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir | Out-Null
            Write-Success "Diretorio '$dir' criado"
        }
    }
}

# Iniciar aplicacao
function Start-Application {
    Write-Header "Iniciando aplicacao de cadastro"
    
    if (-not (Test-Docker) -or -not (Test-DockerCompose)) {
        return
    }
    
    Initialize-Directories
    
    Write-Info "Executando docker-compose up -d"
    docker-compose up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Aplicacao iniciada com sucesso!"
        Write-Info "Acesse: http://localhost:8501"
        Write-Info "Credenciais: admin/admin"
    }
    else {
        Write-Error "Erro ao iniciar aplicacao"
    }
}

# Parar aplicacao
function Stop-Application {
    Write-Header "Parando aplicacao"
    
    if (-not (Test-DockerCompose)) {
        return
    }
    
    Write-Info "Executando docker-compose down"
    docker-compose down
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Aplicacao parada com sucesso!"
    }
    else {
        Write-Error "Erro ao parar aplicacao"
    }
}

# Reiniciar aplicacao
function Restart-Application {
    Write-Header "Reiniciando aplicacao"
    
    Stop-Application
    Start-Sleep -Seconds 2
    Start-Application
}

# Mostrar logs
function Show-Logs {
    Write-Header "Mostrando logs da aplicacao"
    
    if (-not (Test-DockerCompose)) {
        return
    }
    
    Write-Info "Executando docker-compose logs -f"
    docker-compose logs -f
}

# Rebuild da imagem
function Build-Application {
    Write-Header "Rebuild da imagem Docker"
    
    if (-not (Test-Docker) -or -not (Test-DockerCompose)) {
        return
    }
    
    Write-Info "Executando docker-compose build --no-cache"
    docker-compose build --no-cache
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Imagem rebuildada com sucesso!"
    }
    else {
        Write-Error "Erro ao rebuildar imagem"
    }
}

# Limpar recursos Docker
function Clean-Docker {
    Write-Header "Limpando recursos Docker"
    
    if (-not (Test-Docker)) {
        return
    }
    
    Write-Info "Parando containers..."
    docker-compose down
    
    Write-Info "Removendo imagens nao utilizadas..."
    docker image prune -f
    
    Write-Info "Removendo containers parados..."
    docker container prune -f
    
    Write-Success "Limpeza concluida!"
}

# Mostrar status
function Show-Status {
    Write-Header "Status da aplicacao"
    
    if (-not (Test-DockerCompose)) {
        return
    }
    
    Write-Info "Status dos containers:"
    docker-compose ps
    
    Write-Info "`nRecursos Docker:"
    docker system df
}

# Otimizar sistema
function Optimize-System {
    Write-Header "Otimizando sistema"
    
    Write-Info "Executando script de otimizacao..."
    
    # Verificar se Python esta disponivel
    try {
        python --version | Out-Null
    }
    catch {
        Write-Error "Python nao esta disponivel para otimizacao"
        return
    }
    
    # Executar script de otimizacao
    if (Test-Path "otimizar_sistema.py") {
        python otimizar_sistema.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Sistema otimizado com sucesso!"
        }
        else {
            Write-Error "Erro durante a otimizacao"
        }
    }
    else {
        Write-Error "Script de otimizacao nao encontrado"
    }
}

# Menu principal
function Show-Menu {
    Write-Host "`n=== Sistema de Cadastro - Gerenciador ===" -ForegroundColor Magenta
    Write-Host "1. Iniciar aplicacao" -ForegroundColor White
    Write-Host "2. Parar aplicacao" -ForegroundColor White
    Write-Host "3. Reiniciar aplicacao" -ForegroundColor White
    Write-Host "4. Ver logs" -ForegroundColor White
    Write-Host "5. Rebuild imagem" -ForegroundColor White
    Write-Host "6. Limpar Docker" -ForegroundColor White
    Write-Host "7. Ver status" -ForegroundColor White
    Write-Host "8. Otimizar Sistema" -ForegroundColor Cyan
    Write-Host "9. Sair" -ForegroundColor White
    Write-Host "`nEscolha uma opcao (1-9): " -NoNewline -ForegroundColor Cyan
}

# Executar acao baseada no parametro
switch ($Action) {
    "start" { Start-Application }
    "stop" { Stop-Application }
    "restart" { Restart-Application }
    "logs" { Show-Logs }
    "build" { Build-Application }
    "clean" { Clean-Docker }
    "status" { Show-Status }
    "optimize" { Optimize-System }
    default {
        # Menu interativo se nenhum parametro for fornecido
        do {
            Show-Menu
            $choice = Read-Host
            
            switch ($choice) {
                "1" { Start-Application }
                "2" { Stop-Application }
                "3" { Restart-Application }
                "4" { Show-Logs }
                "5" { Build-Application }
                "6" { Clean-Docker }
                "7" { Show-Status }
                "8" { Optimize-System }
                "9" { 
                    Write-Success "Saindo..."
                    exit 0
                }
                default { Write-Error "Opcao invalida!" }
            }
            
            if ($choice -ne "9") {
                Write-Host "`nPressione qualquer tecla para continuar..." -NoNewline
                $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            }
        } while ($choice -ne "9")
    }
} 