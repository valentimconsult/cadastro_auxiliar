#!/bin/bash

# Script para gerenciar a aplicacao de cadastro Streamlit
# Autor: Sistema de Cadastro
# Data: $(date +%Y-%m-%d)

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Funcoes de output
write_header() {
    echo -e "\n${CYAN}=== $1 ===${NC}"
}

write_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

write_error() {
    echo -e "${RED}✗ $1${NC}"
}

write_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Verificar se Docker esta instalado
test_docker() {
    if command -v docker &> /dev/null; then
        return 0
    else
        write_error "Docker nao esta instalado ou nao esta no PATH"
        return 1
    fi
}

# Verificar se Docker Compose esta disponivel
test_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        return 0
    else
        write_error "Docker Compose nao esta disponivel"
        return 1
    fi
}

# Criar diretorios necessarios
initialize_directories() {
    local directories=("data" "config" "logs")
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            write_success "Diretorio '$dir' criado"
        fi
    done
}

# Iniciar aplicacao
start_application() {
    write_header "Iniciando aplicacao de cadastro"
    
    if ! test_docker || ! test_docker_compose; then
        return 1
    fi
    
    initialize_directories
    
    write_info "Executando docker-compose up -d"
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        write_success "Aplicacao iniciada com sucesso!"
        write_info "Acesse: http://localhost:8501"
        write_info "Credenciais: admin/admin"
    else
        write_error "Erro ao iniciar aplicacao"
        return 1
    fi
}

# Parar aplicacao
stop_application() {
    write_header "Parando aplicacao"
    
    if ! test_docker_compose; then
        return 1
    fi
    
    write_info "Executando docker-compose down"
    docker-compose down
    
    if [ $? -eq 0 ]; then
        write_success "Aplicacao parada com sucesso!"
    else
        write_error "Erro ao parar aplicacao"
        return 1
    fi
}

# Reiniciar aplicacao
restart_application() {
    write_header "Reiniciando aplicacao"
    
    stop_application
    sleep 2
    start_application
}

# Mostrar logs
show_logs() {
    write_header "Mostrando logs da aplicacao"
    
    if ! test_docker_compose; then
        return 1
    fi
    
    write_info "Executando docker-compose logs -f"
    docker-compose logs -f
}

# Rebuild da imagem
build_application() {
    write_header "Rebuild da imagem Docker"
    
    if ! test_docker || ! test_docker_compose; then
        return 1
    fi
    
    write_info "Executando docker-compose build --no-cache"
    docker-compose build --no-cache
    
    if [ $? -eq 0 ]; then
        write_success "Imagem rebuildada com sucesso!"
    else
        write_error "Erro ao rebuildar imagem"
        return 1
    fi
}

# Limpar recursos Docker
clean_docker() {
    write_header "Limpando recursos Docker"
    
    if ! test_docker; then
        return 1
    fi
    
    write_info "Parando containers..."
    docker-compose down
    
    write_info "Removendo imagens nao utilizadas..."
    docker image prune -f
    
    write_info "Removendo containers parados..."
    docker container prune -f
    
    write_success "Limpeza concluida!"
}

# Mostrar status
show_status() {
    write_header "Status da aplicacao"
    
    if ! test_docker_compose; then
        return 1
    fi
    
    write_info "Status dos containers:"
    docker-compose ps
    
    write_info "\nRecursos Docker:"
    docker system df
}

# Otimizar sistema
optimize_system() {
    write_header "Otimizando sistema"
    
    write_info "Executando script de otimizacao..."
    
    # Verificar se Python esta disponivel
    if ! command -v python3 &> /dev/null; then
        write_error "Python3 nao esta disponivel para otimizacao"
        return 1
    fi
    
    # Executar script de otimizacao
    if [ -f "otimizar_sistema.py" ]; then
        python3 otimizar_sistema.py
        
        if [ $? -eq 0 ]; then
            write_success "Sistema otimizado com sucesso!"
        else
            write_error "Erro durante a otimizacao"
            return 1
        fi
    else
        write_error "Script de otimizacao nao encontrado"
        return 1
    fi
}

# Menu principal
show_menu() {
    echo -e "\n${MAGENTA}=== Sistema de Cadastro - Gerenciador ===${NC}"
    echo -e "${WHITE}1. Iniciar aplicacao${NC}"
    echo -e "${WHITE}2. Parar aplicacao${NC}"
    echo -e "${WHITE}3. Reiniciar aplicacao${NC}"
    echo -e "${WHITE}4. Ver logs${NC}"
    echo -e "${WHITE}5. Rebuild imagem${NC}"
    echo -e "${WHITE}6. Limpar Docker${NC}"
    echo -e "${WHITE}7. Ver status${NC}"
    echo -e "${CYAN}8. Otimizar Sistema${NC}"
    echo -e "${WHITE}9. Sair${NC}"
    echo -e "\n${CYAN}Escolha uma opcao (1-9): ${NC}"
}

# Funcao principal
main() {
    local action="${1:-}"
    
    case "$action" in
        "start")
            start_application
            ;;
        "stop")
            stop_application
            ;;
        "restart")
            restart_application
            ;;
        "logs")
            show_logs
            ;;
        "build")
            build_application
            ;;
        "clean")
            clean_docker
            ;;
        "status")
            show_status
            ;;
        "optimize")
            optimize_system
            ;;
        "")
            # Menu interativo se nenhum parametro for fornecido
            while true; do
                show_menu
                read -r choice
                
                case "$choice" in
                    "1")
                        start_application
                        ;;
                    "2")
                        stop_application
                        ;;
                    "3")
                        restart_application
                        ;;
                    "4")
                        show_logs
                        ;;
                    "5")
                        build_application
                        ;;
                    "6")
                        clean_docker
                        ;;
                    "7")
                        show_status
                        ;;
                    "8")
                        optimize_system
                        ;;
                    "9")
                        write_success "Saindo..."
                        exit 0
                        ;;
                    *)
                        write_error "Opcao invalida!"
                        ;;
                esac
                
                if [ "$choice" != "9" ]; then
                    echo -e "\nPressione Enter para continuar..."
                    read -r
                fi
            done
            ;;
        *)
            write_error "Acao invalida: $action"
            echo "Uso: $0 [start|stop|restart|logs|build|clean|status|optimize]"
            exit 1
            ;;
    esac
}

# Executar funcao principal
main "$@" 