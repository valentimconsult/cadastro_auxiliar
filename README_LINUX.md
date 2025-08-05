# 🐧 Deploy no Linux - Sistema de Cadastro

Guia completo para deploy da aplicação no Linux usando o script bash.

## 📋 Pré-requisitos

### 1. **Docker e Docker Compose**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose

# CentOS/RHEL
sudo yum install docker docker-compose

# Verificar instalação
docker --version
docker-compose --version
```

### 2. **Python 3** (para otimizações)
```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip

# CentOS/RHEL
sudo yum install python3 python3-pip

# Verificar instalação
python3 --version
```

### 3. **Permissões Docker**
```bash
# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Reiniciar sessão ou executar
newgrp docker
```

## 🚀 Instalação e Configuração

### 1. **Clonar/Transferir Projeto**
```bash
# Se usando git
git clone <seu-repositorio>
cd cadastro_streamlit

# Ou transferir arquivos via SCP/SFTP
scp -r /caminho/local/cadastro_streamlit usuario@servidor:/home/usuario/
```

### 2. **Tornar Script Executável**
```bash
chmod +x start-app.sh
```

### 3. **Verificar Estrutura**
```bash
ls -la
# Deve mostrar:
# - start-app.sh (executável)
# - docker-compose.yml
# - Dockerfile
# - streamlit_app.py
# - api_server.py
# - requirements.txt
# - etc.
```

## 🎯 Uso do Script

### **Comandos Diretos**
```bash
# Iniciar aplicação
./start-app.sh start

# Parar aplicação
./start-app.sh stop

# Reiniciar aplicação
./start-app.sh restart

# Ver logs
./start-app.sh logs

# Rebuild da imagem
./start-app.sh build

# Limpar Docker
./start-app.sh clean

# Ver status
./start-app.sh status

# Otimizar sistema
./start-app.sh optimize
```

### **Menu Interativo**
```bash
# Executar sem parâmetros para menu interativo
./start-app.sh
```

## 🔧 Configurações Específicas do Linux

### 1. **Configurar Firewall**
```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 8501/tcp  # Streamlit
sudo ufw allow 5000/tcp  # API
sudo ufw enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=8501/tcp
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

### 2. **Configurar Systemd (Opcional)**
```bash
# Criar serviço systemd
sudo tee /etc/systemd/system/cadastro-streamlit.service << EOF
[Unit]
Description=Sistema de Cadastro Streamlit
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/caminho/para/cadastro_streamlit
ExecStart=/caminho/para/cadastro_streamlit/start-app.sh start
ExecStop=/caminho/para/cadastro_streamlit/start-app.sh stop
User=seu-usuario

[Install]
WantedBy=multi-user.target
EOF

# Habilitar e iniciar serviço
sudo systemctl daemon-reload
sudo systemctl enable cadastro-streamlit
sudo systemctl start cadastro-streamlit
```

### 3. **Configurar Nginx (Recomendado)**
```bash
# Instalar Nginx
sudo apt install nginx  # Ubuntu/Debian
sudo yum install nginx  # CentOS/RHEL

# Configurar proxy reverso
sudo tee /etc/nginx/sites-available/cadastro-streamlit << EOF
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Habilitar site
sudo ln -s /etc/nginx/sites-available/cadastro-streamlit /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 📊 Monitoramento

### 1. **Logs do Sistema**
```bash
# Logs da aplicação
./start-app.sh logs

# Logs do Docker
docker-compose logs -f

# Logs do sistema
sudo journalctl -u docker.service -f
```

### 2. **Monitoramento de Recursos**
```bash
# Status dos containers
docker ps

# Uso de recursos
docker stats

# Espaço em disco
df -h

# Memória
free -h
```

## 🔒 Segurança

### 1. **Configurar SSL/HTTPS**
```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d seu-dominio.com

# Renovação automática
sudo crontab -e
# Adicionar: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. **Backup Automático**
```bash
# Criar script de backup
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/cadastro-streamlit"
mkdir -p $BACKUP_DIR

# Backup do banco de dados
cp data/data.db $BACKUP_DIR/data_$DATE.db

# Backup das configurações
tar -czf $BACKUP_DIR/config_$DATE.tar.gz *.json *.py

echo "Backup criado: $BACKUP_DIR/data_$DATE.db"
echo "Backup criado: $BACKUP_DIR/config_$DATE.tar.gz"
EOF

chmod +x backup.sh

# Adicionar ao crontab
crontab -e
# Adicionar: 0 2 * * * /caminho/para/backup.sh
```

## 🚨 Troubleshooting

### **Problemas Comuns**

#### 1. **Permissões Docker**
```bash
# Erro: "permission denied"
sudo usermod -aG docker $USER
newgrp docker
```

#### 2. **Porta em Uso**
```bash
# Verificar portas
sudo netstat -tulpn | grep :8501
sudo netstat -tulpn | grep :5000

# Matar processo
sudo kill -9 <PID>
```

#### 3. **Espaço em Disco**
```bash
# Limpar Docker
./start-app.sh clean

# Verificar espaço
df -h
docker system df
```

#### 4. **Memória Insuficiente**
```bash
# Verificar memória
free -h

# Aumentar swap (se necessário)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## 📈 Performance

### **Otimizações Recomendadas**

1. **Ajustar Limites do Sistema**
```bash
# /etc/security/limits.conf
* soft nofile 65536
* hard nofile 65536
```

2. **Configurar Docker daemon**
```bash
# /etc/docker/daemon.json
{
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

3. **Monitoramento Contínuo**
```bash
# Instalar htop
sudo apt install htop

# Monitorar recursos
htop
```

## 📞 Suporte

### **Comandos Úteis**
```bash
# Status completo
./start-app.sh status

# Logs detalhados
docker-compose logs --tail=100

# Rebuild completo
./start-app.sh clean
./start-app.sh build
./start-app.sh start

# Verificar conectividade
curl http://localhost:8501
curl http://localhost:5000/api/health
```

### **Informações do Sistema**
```bash
# Versões
docker --version
docker-compose --version
python3 --version

# Sistema
uname -a
lsb_release -a
```

---

**🎯 Sistema pronto para produção no Linux!** 