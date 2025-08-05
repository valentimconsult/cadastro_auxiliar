# Acesso Remoto ao Banco de Dados via DBeaver

## 🚨 Problema: Docker em VM Remota

Quando o Docker esta rodando em uma VM, voce nao tem acesso direto ao arquivo `data.db` dentro do container. Aqui estao as solucoes:

## 🔧 Solucao 1: API REST (Recomendado)

### Configuracao da API

1. **Expor a API na VM:**
```yaml
# docker-compose.yml
services:
  api-server:
    ports:
      - "5000:5000"  # Expor API externamente
```

2. **Acesso via navegador:**
```
http://IP_DA_VM:5000/api/health
http://IP_DA_VM:5000/api/tables
```

### Usar com DBeaver

**Opcao A: Conectar via HTTP/JSON**
1. Instale o driver **JSON** no DBeaver
2. Configure conexao HTTP:
   - **URL**: `http://IP_DA_VM:5000/api/tables`
   - **Method**: GET

**Opcao B: Script Python para DBeaver**
```python
# Script para DBeaver - Python
import requests
import pandas as pd

def get_data_from_remote_api():
    base_url = "http://IP_DA_VM:5000/api"
    
    # Listar tabelas
    response = requests.get(f"{base_url}/tables")
    tables = response.json()['tables']
    
    # Para cada tabela, obter dados
    for table in tables:
        table_name = table['name']
        response = requests.get(f"{base_url}/tables/{table_name}")
        data = response.json()['data']
        
        # Converter para DataFrame
        df = pd.DataFrame(data)
        print(f"Tabela: {table_name}")
        print(df.head())
    
    return tables

# Executar no DBeaver
result = get_data_from_remote_api()
```

## 🔧 Solucao 2: Expor Volume do SQLite

### Configuracao do Docker

```yaml
# docker-compose.yml
services:
  cadastro-app:
    volumes:
      - ./data:/app/data:ro  # Read-only para seguranca
      - ./data:/shared/db:ro  # Volume compartilhado
    ports:
      - "8501:8501"
      - "5000:5000"
```

### Acesso via SSH + SCP

```bash
# 1. Conectar via SSH na VM
ssh usuario@IP_DA_VM

# 2. Copiar arquivo do banco para sua maquina
scp usuario@IP_DA_VM:/caminho/para/data/data.db ./data_remoto.db

# 3. Ou montar diretorio via SSHFS
sshfs usuario@IP_DA_VM:/caminho/para/data ./dados_remotos
```

### Configurar DBeaver

1. **Conexao SSH Tunnel:**
   - **Host**: IP_DA_VM
   - **Port**: 22
   - **Username**: seu_usuario
   - **Password**: sua_senha

2. **Conexao SQLite:**
   - **Database**: `/caminho/remoto/data.db`
   - **Use SSH tunnel**: Sim

## 🔧 Solucao 3: Port Forwarding

### Configuracao SSH

```bash
# Criar tunel SSH para acessar arquivo remoto
ssh -L 5000:localhost:5000 usuario@IP_DA_VM

# Ou para acessar diretorio completo
ssh -L 8501:localhost:8501 usuario@IP_DA_VM
```

### Acesso Local

Apos o tunel SSH:
- **API**: `http://localhost:5000/api`
- **Interface**: `http://localhost:8501`

## 🔧 Solucao 4: Script de Sincronizacao

### Script Python para Sincronizar

```python
# sync_database.py
import requests
import sqlite3
import os
from datetime import datetime

def sync_remote_database():
    """Sincroniza banco remoto para local."""
    
    # Configuracao
    REMOTE_API = "http://IP_DA_VM:5000/api"
    LOCAL_DB = "data_local.db"
    
    # 1. Obter lista de tabelas
    response = requests.get(f"{REMOTE_API}/tables")
    tables = response.json()['tables']
    
    # 2. Criar banco local
    conn = sqlite3.connect(LOCAL_DB)
    
    for table in tables:
        table_name = table['name']
        
        # 3. Obter dados da tabela
        response = requests.get(f"{REMOTE_API}/tables/{table_name}")
        data = response.json()['data']
        
        if data:
            # 4. Criar tabela local
            df = pd.DataFrame(data)
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            print(f"Tabela {table_name} sincronizada: {len(data)} registros")
    
    conn.close()
    print(f"Banco sincronizado: {LOCAL_DB}")

if __name__ == "__main__":
    sync_remote_database()
```

### Usar com DBeaver

1. Execute o script de sincronizacao
2. Conecte DBeaver ao arquivo local `data_local.db`
3. Configure sincronizacao automatica

## 🔧 Solucao 5: Docker Volume Compartilhado

### Configuracao Avancada

```yaml
# docker-compose.yml
services:
  cadastro-app:
    volumes:
      - db_data:/app/data
      - ./shared:/shared:ro  # Volume compartilhado
    ports:
      - "8501:8501"
      - "5000:5000"

volumes:
  db_data:
    driver: local
```

### Acesso via NFS/SMB

```bash
# Na VM, compartilhar diretorio
sudo apt install nfs-kernel-server
echo "/caminho/para/data *(ro)" >> /etc/exports
sudo exportfs -a

# Na sua maquina, montar
sudo mount IP_DA_VM:/caminho/para/data /mnt/remote_db
```

## 📊 Exemplos Praticos

### Exemplo 1: VM no AWS

```bash
# 1. Conectar na VM
ssh -i chave.pem ubuntu@IP_DA_VM

# 2. Verificar se Docker esta rodando
docker-compose ps

# 3. Testar API
curl http://localhost:5000/api/health

# 4. Copiar arquivo do banco
docker cp cadastro-streamlit:/app/data/data.db ./data_remoto.db
scp ubuntu@IP_DA_VM:./data_remoto.db ./
```

### Exemplo 2: VM no Azure

```bash
# 1. Conectar via Azure CLI
az vm connect --name minha-vm --resource-group meu-rg

# 2. Verificar portas abertas
netstat -tlnp | grep :5000

# 3. Configurar firewall
az network nsg rule create \
  --resource-group meu-rg \
  --nsg-name minha-nsg \
  --name allow-api \
  --protocol tcp \
  --priority 1001 \
  --destination-port-range 5000
```

## 🛠️ Troubleshooting

### Problemas Comuns

1. **API nao responde:**
```bash
# Verificar se porta esta aberta
telnet IP_DA_VM 5000

# Verificar firewall
sudo ufw status
sudo ufw allow 5000
```

2. **Arquivo nao encontrado:**
```bash
# Verificar volume no Docker
docker exec cadastro-streamlit ls -la /app/data

# Copiar arquivo do container
docker cp cadastro-streamlit:/app/data/data.db ./
```

3. **Permissoes SSH:**
```bash
# Configurar chave SSH
ssh-keygen -t rsa -b 4096
ssh-copy-id usuario@IP_DA_VM
```

## 📋 Checklist de Configuracao

### Para VM Remota:

- [ ] Docker Compose configurado
- [ ] Porta 5000 exposta
- [ ] Firewall configurado
- [ ] API respondendo
- [ ] SSH configurado
- [ ] Volume compartilhado (opcional)

### Para Acesso Local:

- [ ] Script de sincronizacao criado
- [ ] DBeaver configurado
- [ ] Tunel SSH funcionando
- [ ] Arquivo local sincronizado

## 🎯 Recomendacao Final

**Para uso em producao, recomendo:**

1. **API REST** para consultas e exportacoes
2. **Backup automatico** do arquivo SQLite
3. **Script de sincronizacao** para DBeaver
4. **Monitoramento** da API

**Exemplo de uso:**
```python
# Script para DBeaver
import requests
import pandas as pd

def get_remote_data(table_name):
    api_url = "http://IP_DA_VM:5000/api"
    response = requests.get(f"{api_url}/tables/{table_name}")
    return pd.DataFrame(response.json()['data'])

# Usar no DBeaver
df = get_remote_data('funcionarios')
``` 