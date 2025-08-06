#!/bin/bash

# Script de instalacao para Raspberry Pi 5 com Ubuntu 24
# Cadastro Streamlit - Versao Otimizada para ARM64

set -e

echo "🚀 Instalando Cadastro Streamlit no Raspberry Pi 5..."
echo "=================================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funcao para log colorido
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se e Raspberry Pi 5
check_raspberry_pi() {
    log_info "Verificando hardware..."
    
    if [[ -f /proc/device-tree/model ]]; then
        MODEL=$(cat /proc/device-tree/model)
        if [[ $MODEL == *"Raspberry Pi 5"* ]]; then
            log_success "Raspberry Pi 5 detectado!"
        else
            log_warning "Hardware nao e Raspberry Pi 5: $MODEL"
        fi
    else
        log_warning "Nao foi possivel detectar o modelo do hardware"
    fi
    
    # Verificar arquitetura
    ARCH=$(uname -m)
    if [[ $ARCH == "aarch64" ]]; then
        log_success "Arquitetura ARM64 detectada"
    else
        log_error "Arquitetura nao suportada: $ARCH"
        exit 1
    fi
}

# Atualizar sistema
update_system() {
    log_info "Atualizando sistema..."
    sudo apt update && sudo apt upgrade -y
    log_success "Sistema atualizado"
}

# Instalar dependencias do sistema
install_system_dependencies() {
    log_info "Instalando dependencias do sistema..."
    
    sudo apt install -y \
        curl \
        wget \
        git \
        ca-certificates \
        gnupg \
        lsb-release \
        apt-transport-https \
        software-properties-common
    
    log_success "Dependencias do sistema instaladas"
}

# Instalar Docker
install_docker() {
    log_info "Instalando Docker..."
    
    # Remover instalacoes antigas
    sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Adicionar repositorio oficial do Docker
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Instalar Docker
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Adicionar usuario ao grupo docker
    sudo usermod -aG docker $USER
    
    # Habilitar Docker para iniciar com o sistema
    sudo systemctl enable docker
    sudo systemctl start docker
    
    log_success "Docker instalado com sucesso"
}

# Configurar otimizacoes para Raspberry Pi 5
configure_raspberry_pi() {
    log_info "Configurando otimizacoes para Raspberry Pi 5..."
    
    # Aumentar swap se necessario
    if [[ $(free -m | awk 'NR==2{printf "%.0f", $3*100/$2 }') -gt 80 ]]; then
        log_info "Configurando swap..."
        sudo fallocate -l 1G /swapfile
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile
        sudo swapon /swapfile
        echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    fi
    
    # Otimizar configuracoes do sistema
    echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
    echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf
    
    log_success "Otimizacoes configuradas"
}

# Clonar ou atualizar o projeto
setup_project() {
    log_info "Configurando projeto..."
    
    PROJECT_DIR="$HOME/cadastro_streamlit"
    
    if [[ -d "$PROJECT_DIR" ]]; then
        log_info "Projeto ja existe, atualizando..."
        cd "$PROJECT_DIR"
        git pull origin master
    else
        log_info "Clonando projeto..."
        git clone https://github.com/seu-usuario/cadastro_streamlit.git "$PROJECT_DIR"
        cd "$PROJECT_DIR"
    fi
    
    # Criar diretorios necessarios
    mkdir -p data config logs
    
    log_success "Projeto configurado"
}

# Configurar firewall
setup_firewall() {
    log_info "Configurando firewall..."
    
    # Instalar ufw se nao estiver instalado
    sudo apt install -y ufw
    
    # Configurar regras basicas
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    sudo ufw allow 8501  # Streamlit
    sudo ufw allow 5000  # API
    
    # Habilitar firewall
    sudo ufw --force enable
    
    log_success "Firewall configurado"
}

# Criar script de inicializacao
create_startup_script() {
    log_info "Criando script de inicializacao..."
    
    cat > ~/start-cadastro.sh << 'EOF'
#!/bin/bash

# Script de inicializacao do Cadastro Streamlit
# Para Raspberry Pi 5

cd ~/cadastro_streamlit

# Verificar se Docker esta rodando
if ! docker info > /dev/null 2>&1; then
    echo "Docker nao esta rodando. Iniciando..."
    sudo systemctl start docker
    sleep 5
fi

# Usar compose especifico para Raspberry Pi
docker-compose -f docker-compose.raspberry.yml up -d

echo "Cadastro Streamlit iniciado!"
echo "Acesse: http://$(hostname -I | awk '{print $1}'):8501"
echo "API: http://$(hostname -I | awk '{print $1}'):5000"
EOF
    
    chmod +x ~/start-cadastro.sh
    
    log_success "Script de inicializacao criado"
}

# Funcao principal
main() {
    echo "🎯 Iniciando instalacao para Raspberry Pi 5..."
    
    check_raspberry_pi
    update_system
    install_system_dependencies
    install_docker
    configure_raspberry_pi
    setup_project
    setup_firewall
    create_startup_script
    
    echo ""
    echo "✅ Instalacao concluida!"
    echo ""
    echo "📋 Prximos passos:"
    echo "1. Reinicie o sistema: sudo reboot"
    echo "2. Execute: ~/start-cadastro.sh"
    echo "3. Acesse: http://$(hostname -I | awk '{print $1}'):8501"
    echo ""
    echo "🔧 Comandos utiles:"
    echo "- Parar: docker-compose -f docker-compose.raspberry.yml down"
    echo "- Logs: docker-compose -f docker-compose.raspberry.yml logs"
    echo "- Status: docker-compose -f docker-compose.raspberry.yml ps"
    echo ""
}

# Executar instalacao
main "$@" 