# 🍓 Guia Raspberry Pi 5 - Cadastro Streamlit

## 📋 Visão Geral

Este guia fornece instruções completas para instalar e executar o Cadastro Streamlit no **Raspberry Pi 5** com **Ubuntu 24**.

## 🎯 Características Específicas para Raspberry Pi 5

### ✅ Compatibilidade
- **Arquitetura**: ARM64 (aarch64)
- **Sistema**: Ubuntu 24.04 LTS
- **Docker**: Versão mais recente
- **Recursos**: Otimizado para hardware limitado

### 🚀 Otimizações Implementadas
- **Memória**: Limite de 512MB para Streamlit, 256MB para API
- **CPU**: Limite de 0.5 cores para Streamlit, 0.25 para API
- **Logs**: Rotação automática (5MB máximo, 2 arquivos)
- **Upload**: Limite de 200MB para uploads
- **Swap**: Configuração automática se necessário

## 📦 Pré-requisitos

### Hardware Mínimo
- **Raspberry Pi 5** (4GB RAM recomendado)
- **SD Card**: 32GB classe 10 ou superior
- **Rede**: Conexão Ethernet ou Wi-Fi
- **Energia**: Fonte oficial 5V/3A

### Software
- **Ubuntu 24.04 LTS** (ou superior)
- **Acesso SSH** configurado
- **Git** instalado

## 🛠️ Instalação Automática

### Opção 1: Script Automático (Recomendado)

```bash
# Baixar e executar script de instalação
curl -fsSL https://raw.githubusercontent.com/seu-usuario/cadastro_streamlit/main/install-raspberry-pi.sh | bash
```

### Opção 2: Instalação Manual

```bash
# 1. Atualizar sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar dependências
sudo apt install -y curl wget git ca-certificates

# 3. Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 4. Clonar projeto
git clone https://github.com/seu-usuario/cadastro_streamlit.git
cd cadastro_streamlit

# 5. Criar diretórios
mkdir -p data config logs
```

## 🚀 Execução

### Usando Compose Específico para Raspberry Pi

```bash
# Iniciar aplicação
docker-compose -f docker-compose.raspberry.yml up -d

# Verificar status
docker-compose -f docker-compose.raspberry.yml ps

# Ver logs
docker-compose -f docker-compose.raspberry.yml logs -f

# Parar aplicação
docker-compose -f docker-compose.raspberry.yml down
```

### Script de Inicialização

```bash
# Executar script de inicialização
~/start-cadastro.sh
```

## 🌐 Acesso

### URLs de Acesso
- **Streamlit**: `http://[IP_RASPBERRY_PI]:8501`
- **API**: `http://[IP_RASPBERRY_PI]:5000`

### Descobrir IP
```bash
# Ver IP do Raspberry Pi
hostname -I
# ou
ip addr show | grep "inet " | grep -v 127.0.0.1
```

## 🔧 Configurações Específicas

### Otimizações de Sistema

```bash
# Configurar swap (se necessário)
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Adicionar ao fstab
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Otimizar memória
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf
```

### Firewall

```bash
# Configurar firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 8501  # Streamlit
sudo ufw allow 5000  # API
sudo ufw --force enable
```

## 📊 Monitoramento

### Verificar Recursos

```bash
# Uso de CPU e memória
htop

# Uso de disco
df -h

# Temperatura (se disponível)
vcgencmd measure_temp

# Status dos containers
docker stats
```

### Logs do Sistema

```bash
# Logs do Docker
docker-compose -f docker-compose.raspberry.yml logs

# Logs do sistema
journalctl -u docker.service

# Logs de aplicação
tail -f logs/streamlit.log
```

## 🔄 Manutenção

### Atualizações

```bash
# Atualizar projeto
cd ~/cadastro_streamlit
git pull origin master

# Rebuild containers
docker-compose -f docker-compose.raspberry.yml up -d --build
```

### Backup

```bash
# Backup dos dados
tar -czf backup_$(date +%Y%m%d).tar.gz data/ config/

# Restaurar backup
tar -xzf backup_YYYYMMDD.tar.gz
```

### Limpeza

```bash
# Limpar imagens não utilizadas
docker image prune -f

# Limpar volumes não utilizados
docker volume prune -f

# Limpar sistema completo
docker system prune -f
```

## 🚨 Troubleshooting

### Problemas Comuns

#### 1. Docker não inicia
```bash
# Verificar status
sudo systemctl status docker

# Reiniciar Docker
sudo systemctl restart docker
```

#### 2. Memória insuficiente
```bash
# Verificar uso de memória
free -h

# Aumentar swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 3. Container não inicia
```bash
# Ver logs detalhados
docker-compose -f docker-compose.raspberry.yml logs --tail=100

# Verificar recursos
docker stats
```

#### 4. Acesso externo não funciona
```bash
# Verificar firewall
sudo ufw status

# Verificar portas
sudo netstat -tlnp | grep :8501
sudo netstat -tlnp | grep :5000
```

### Comandos de Diagnóstico

```bash
# Verificar arquitetura
uname -m

# Verificar versão do Docker
docker --version
docker-compose --version

# Verificar recursos do sistema
cat /proc/cpuinfo | grep "Model name"
cat /proc/meminfo | grep MemTotal
```

## 📈 Performance

### Otimizações Recomendadas

1. **SD Card de Alta Velocidade**: Use SD card classe 10 ou superior
2. **Ventilação Adequada**: Mantenha temperatura baixa
3. **Fonte de Energia**: Use fonte oficial 5V/3A
4. **Rede**: Use conexão Ethernet quando possível
5. **Swap**: Configure swap adequado se necessário

### Métricas Esperadas

- **Inicialização**: 2-3 minutos
- **Uso de Memória**: 300-500MB
- **Uso de CPU**: 10-30% em uso normal
- **Temperatura**: 40-60°C

## 🔐 Segurança

### Configurações Recomendadas

```bash
# Atualizar senhas padrão
sudo passwd

# Configurar SSH apenas com chaves
sudo nano /etc/ssh/sshd_config
# PasswordAuthentication no
# PubkeyAuthentication yes

# Reiniciar SSH
sudo systemctl restart ssh
```

### Firewall Avançado

```bash
# Configurar regras específicas
sudo ufw allow from 192.168.1.0/24 to any port 8501
sudo ufw allow from 192.168.1.0/24 to any port 5000
```

## 📞 Suporte

### Informações Úteis

- **Versão do Sistema**: `lsb_release -a`
- **Versão do Kernel**: `uname -r`
- **Arquitetura**: `uname -m`
- **Modelo do Hardware**: `cat /proc/device-tree/model`

### Logs Importantes

- **Docker**: `/var/log/docker.log`
- **Sistema**: `journalctl -xe`
- **Aplicação**: `logs/` no diretório do projeto

---

## ✅ Checklist de Instalação

- [ ] Raspberry Pi 5 com Ubuntu 24
- [ ] Docker instalado e funcionando
- [ ] Projeto clonado
- [ ] Containers iniciados
- [ ] Acesso via navegador funcionando
- [ ] Firewall configurado
- [ ] Backup configurado
- [ ] Monitoramento ativo

**🎉 Parabéns! Seu Cadastro Streamlit está rodando no Raspberry Pi 5!** 