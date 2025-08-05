# Acesso Externo ao Banco de Dados

## Visao Geral

O sistema agora oferece multiplas formas de acessar o banco de dados SQLite externamente, permitindo integracao com ferramentas como DBeaver, APIs, scripts Python e outros clientes SQLite.

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   DBeaver       │    │   API REST      │    │   Scripts       │
│   SQLite Browser│    │   (Porta 5000)  │    │   Python        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   SQLite DB     │
                    │  data/data.db   │
                    └─────────────────┘
```

## 🔧 Formas de Acesso

### 1. Acesso Direto ao SQLite

**Caminho do arquivo**: `data/data.db`

#### Com DBeaver:
1. Abra o DBeaver
2. Clique em "Nova Conexao"
3. Selecione "SQLite"
4. Configure:
   - **Database**: `data/data.db`
   - **Path**: Caminho completo para o arquivo
5. Clique em "Test Connection"
6. Clique em "Finish"

#### Com SQLite Browser:
1. Abra o DB Browser for SQLite
2. Clique em "Open Database"
3. Navegue ate `data/data.db`
4. Clique em "Open"

#### Com linha de comando:
```bash
# No diretorio do projeto
sqlite3 data/data.db

# Comandos uteis
.tables                    # Listar tabelas
.schema nome_tabela        # Ver schema
SELECT * FROM nome_tabela; # Consultar dados
.quit                      # Sair
```

### 2. Acesso via API REST

**URL Base**: `http://localhost:5000/api`

#### Endpoints Disponiveis:

**Health Check:**
```bash
GET http://localhost:5000/api/health
```

**Listar Tabelas:**
```bash
GET http://localhost:5000/api/tables
```

**Dados de uma Tabela:**
```bash
GET http://localhost:5000/api/tables/nome_tabela
GET http://localhost:5000/api/tables/nome_tabela?page=1&limit=100
GET http://localhost:5000/api/tables/nome_tabela?search=termo
```

**Exportar Dados:**
```bash
GET http://localhost:5000/api/tables/nome_tabela/export?format=csv
GET http://localhost:5000/api/tables/nome_tabela/export?format=json
GET http://localhost:5000/api/tables/nome_tabela/export?format=excel
```

**Schema da Tabela:**
```bash
GET http://localhost:5000/api/tables/nome_tabela/schema
```

**Estatisticas do Banco:**
```bash
GET http://localhost:5000/api/stats
```

**Query Customizada:**
```bash
POST http://localhost:5000/api/query
Content-Type: application/json

{
  "query": "SELECT * FROM nome_tabela WHERE campo = 'valor'"
}
```

### 3. Acesso via Python

#### Conectar Diretamente:
```python
import sqlite3
import pandas as pd

# Conexao direta
conn = sqlite3.connect('data/data.db')

# Listar tabelas
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

# Ler dados com pandas
df = pd.read_sql_query("SELECT * FROM nome_tabela", conn)
print(df)

conn.close()
```

#### Conectar via API:
```python
import requests
import json

# Health check
response = requests.get('http://localhost:5000/api/health')
print(response.json())

# Listar tabelas
response = requests.get('http://localhost:5000/api/tables')
tables = response.json()['tables']

# Exportar dados
response = requests.get('http://localhost:5000/api/tables/nome_tabela/export?format=csv')
with open('dados.csv', 'w') as f:
    f.write(response.text)
```

## 🚀 Deploy em Servidor

### Configuracao para Producao

1. **Expor portas necessarias:**
```yaml
# docker-compose.yml
services:
  cadastro-app:
    ports:
      - "8501:8501"  # Interface web
  api-server:
    ports:
      - "5000:5000"  # API REST
```

2. **Configurar firewall:**
```bash
# Permitir acesso as portas
sudo ufw allow 8501
sudo ufw allow 5000
```

3. **Acesso externo:**
```
Interface Web: http://IP_DO_SERVIDOR:8501
API REST: http://IP_DO_SERVIDOR:5000/api
```

### Seguranca

1. **Autenticacao da API** (implementar se necessario):
```python
# Adicionar autenticacao basica
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    # Implementar verificacao de credenciais
    return username == 'admin' and password == 'senha'
```

2. **HTTPS** (recomendado para producao):
```yaml
# Usar nginx com SSL
nginx:
  image: nginx:alpine
  ports:
    - "443:443"
  volumes:
    - ./ssl:/etc/nginx/ssl
```

## 📊 Exemplos de Uso

### 1. DBeaver

**Configuracao:**
- **Driver**: SQLite
- **Database**: `data/data.db`
- **Path**: `/caminho/completo/para/data/data.db`

**Comandos uteis:**
```sql
-- Listar todas as tabelas
SELECT name FROM sqlite_master WHERE type='table';

-- Ver schema de uma tabela
PRAGMA table_info(nome_tabela);

-- Consultar dados
SELECT * FROM nome_tabela LIMIT 100;

-- Estatisticas
SELECT COUNT(*) as total FROM nome_tabela;
```

### 2. Script Python

**Exemplo completo:**
```python
import sqlite3
import pandas as pd
import requests

# Opcao 1: Acesso direto
conn = sqlite3.connect('data/data.db')
df = pd.read_sql_query("SELECT * FROM funcionarios", conn)
print(df.head())

# Opcao 2: Via API
response = requests.get('http://localhost:5000/api/tables/funcionarios')
data = response.json()
print(f"Total de registros: {len(data['data'])}")

conn.close()
```

### 3. Integracao com Outros Sistemas

**Power BI:**
```python
# Script para Power BI
import requests
import pandas as pd

def get_data_from_api():
    response = requests.get('http://localhost:5000/api/tables/funcionarios')
    data = response.json()
    return pd.DataFrame(data['data'])

# Usar no Power BI
df = get_data_from_api()
```

**Excel:**
```python
# Exportar para Excel
import requests

response = requests.get('http://localhost:5000/api/tables/funcionarios/export?format=excel')
with open('dados.xlsx', 'wb') as f:
    f.write(response.content)
```

## 🔄 Sincronizacao com Nuvem

### 1. Backup Automatico

```python
# Script de backup
import shutil
import datetime

def backup_database():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup/data_{timestamp}.db"
    shutil.copy2("data/data.db", backup_file)
    print(f"Backup criado: {backup_file}")
```

### 2. Sincronizacao com Google Drive

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_to_drive(file_path):
    # Configurar credenciais do Google Drive
    service = build('drive', 'v3', credentials=creds)
    
    file_metadata = {'name': 'database_backup.db'}
    media = MediaFileUpload(file_path, resumable=True)
    
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    print(f"Arquivo enviado: {file.get('id')}")
```

### 3. Sincronizacao com AWS S3

```python
import boto3

def upload_to_s3(file_path, bucket_name):
    s3 = boto3.client('s3')
    
    s3.upload_file(
        file_path,
        bucket_name,
        'database_backup.db'
    )
    
    print(f"Arquivo enviado para S3: s3://{bucket_name}/database_backup.db")
```

## 🛠️ Troubleshooting

### Problemas Comuns

1. **Arquivo nao encontrado:**
   - Verifique se o caminho esta correto
   - Confirme se o Docker esta rodando
   - Verifique permissoes do arquivo

2. **API nao responde:**
   - Verifique se a porta 5000 esta aberta
   - Confirme se o container da API esta rodando
   - Verifique logs: `docker-compose logs api-server`

3. **DBeaver nao conecta:**
   - Verifique se o arquivo existe
   - Confirme permissoes de leitura
   - Teste com SQLite Browser primeiro

### Comandos de Diagnostico

```bash
# Verificar se containers estao rodando
docker-compose ps

# Ver logs da API
docker-compose logs api-server

# Testar conectividade
curl http://localhost:5000/api/health

# Verificar arquivo do banco
ls -la data/data.db
```

## 📋 Checklist de Configuracao

- [ ] Docker Compose configurado com API
- [ ] Portas 8501 e 5000 expostas
- [ ] Arquivo data.db acessivel
- [ ] API respondendo em /api/health
- [ ] DBeaver conectando ao banco
- [ ] Scripts Python funcionando
- [ ] Backup configurado
- [ ] Seguranca implementada (se necessario)

## 🎯 Prximos Passos

1. **Implementar autenticacao** na API
2. **Configurar HTTPS** para producao
3. **Implementar backup automatico**
4. **Criar dashboard** de monitoramento
5. **Configurar alertas** de performance 