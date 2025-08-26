# Exemplo Pratico: Acesso Remoto ao Banco de Dados

## 🎯 Cenario: Docker rodando em VM AWS/Azure

### Configuracao da VM

1. **Subir a aplicacao na VM:**
```bash
# Na VM
git clone <seu-repositorio>
cd cadastro_streamlit
docker-compose up -d
```

2. **Verificar se esta rodando:**
```bash
# Verificar containers
docker-compose ps

# Testar API
curl http://localhost:5000/api/health
```

3. **Configurar firewall:**
```bash
# Abrir porta 5000
sudo ufw allow 5000
sudo ufw allow 8501
```

## 🔧 Solucao 1: Script de Sincronizacao (Recomendado)

### Passo 1: Instalar dependencias
```bash
# Na sua maquina local
pip install requests pandas sqlite3
```

### Passo 2: Sincronizar banco
```bash
# Sincronizar todas as tabelas
python sync_remote_db.py --api-url http://IP_DA_VM:5000/api

# Apenas testar conexao
python sync_remote_db.py --api-url http://IP_DA_VM:5000/api --test-connection

# Ver estatisticas
python sync_remote_db.py --api-url http://IP_DA_VM:5000/api --stats-only

# Exportar tabela especifica para CSV
python sync_remote_db.py --api-url http://IP_DA_VM:5000/api --export-csv funcionarios
```

### Passo 3: Usar no DBeaver
1. Abra o DBeaver
2. Nova Conexao > SQLite
3. Database: `data_local.db` (arquivo gerado pelo script)
4. Test Connection > Finish

## 🔧 Solucao 2: Acesso Direto via API

### Via Navegador
```
http://IP_DA_VM:5000/api/health
http://IP_DA_VM:5000/api/tables
http://IP_DA_VM:5000/api/tables/funcionarios
```

### Via Python
```python
import requests
import pandas as pd

# Configuracao
API_URL = "http://IP_DA_VM:5000/api"

# Testar conexao
response = requests.get(f"{API_URL}/health")
print(response.json())

# Listar tabelas
response = requests.get(f"{API_URL}/tables")
tables = response.json()['tables']
for table in tables:
    print(f"- {table['name']}: {table['row_count']} registros")

# Obter dados de uma tabela
response = requests.get(f"{API_URL}/tables/funcionarios")
data = response.json()['data']
df = pd.DataFrame(data)
print(df.head())

# Exportar para CSV
response = requests.get(f"{API_URL}/tables/funcionarios/export?format=csv")
with open('funcionarios.csv', 'w') as f:
    f.write(response.text)
```

## 🔧 Solucao 3: Tunel SSH

### Criar tunel SSH
```bash
# Conectar via SSH e criar tunel
ssh -L 5000:localhost:5000 usuario@IP_DA_VM

# Em outro terminal, acessar localmente
curl http://localhost:5000/api/health
```

### Usar com DBeaver
1. Configure conexao SSH no DBeaver
2. Host: IP_DA_VM
3. Port: 22
4. Username: seu_usuario
5. Use SSH tunnel: Sim

## 📊 Exemplos Praticos

### Exemplo 1: VM AWS (Ubuntu)

```bash
# 1. Conectar na VM
ssh -i chave.pem ubuntu@IP_DA_VM

# 2. Verificar Docker
docker-compose ps

# 3. Testar API
curl http://localhost:5000/api/health

# 4. Sincronizar para sua maquina
python sync_remote_db.py --api-url http://IP_DA_VM:5000/api
```

### Exemplo 2: VM Azure (Windows)

```powershell
# 1. Conectar via RDP ou SSH
ssh usuario@IP_DA_VM

# 2. Verificar se aplicacao esta rodando
docker-compose ps

# 3. Testar API
Invoke-WebRequest -Uri "http://localhost:5000/api/health"

# 4. Sincronizar dados
python sync_remote_db.py --api-url http://IP_DA_VM:5000/api
```

### Exemplo 3: VM Google Cloud

```bash
# 1. Conectar via gcloud
gcloud compute ssh minha-vm

# 2. Verificar aplicacao
docker-compose ps

# 3. Configurar firewall
gcloud compute firewall-rules create allow-api \
  --allow tcp:5000 \
  --source-ranges 0.0.0.0/0

# 4. Sincronizar dados
python sync_remote_db.py --api-url http://IP_DA_VM:5000/api
```

## 🛠️ Troubleshooting

### Problema: API nao responde
```bash
# 1. Verificar se Docker esta rodando
docker-compose ps

# 2. Verificar logs
docker-compose logs api-server

# 3. Verificar firewall
sudo ufw status

# 4. Testar localmente na VM
curl http://localhost:5000/api/health
```

### Problema: Nao consegue conectar
```bash
# 1. Verificar IP da VM
ip addr show

# 2. Verificar se porta esta aberta
netstat -tlnp | grep :5000

# 3. Testar conectividade
telnet IP_DA_VM 5000
```

### Problema: DBeaver nao conecta
```bash
# 1. Verificar se arquivo foi criado
ls -la data_local.db

# 2. Verificar permissoes
chmod 644 data_local.db

# 3. Testar SQLite
sqlite3 data_local.db ".tables"
```

## 📋 Checklist Completo

### Na VM:
- [ ] Docker instalado
- [ ] Aplicacao rodando
- [ ] Porta 5000 aberta
- [ ] Firewall configurado
- [ ] API respondendo

### Na sua maquina:
- [ ] Python instalado
- [ ] Script de sincronizacao baixado
- [ ] DBeaver instalado
- [ ] Conexao SSH configurada (se necessario)

### Testes:
- [ ] API responde via navegador
- [ ] Script sincroniza dados
- [ ] DBeaver conecta ao arquivo local
- [ ] Dados aparecem corretamente

## 🎯 Fluxo de Trabalho Recomendado

1. **Desenvolvimento:**
   - Use a API para consultas rapidas
   - Use o script para sincronizacao completa
   - Use DBeaver para analises detalhadas

2. **Producao:**
   - Configure backup automatico
   - Monitore a API
   - Sincronize periodicamente

3. **Manutencao:**
   - Verifique logs regularmente
   - Atualize o script quando necessario
   - Mantenha backup dos dados

## 💡 Dicas Importantes

1. **Seguranca:**
   - Use HTTPS em producao
   - Implemente autenticacao na API
   - Restrinja acesso por IP

2. **Performance:**
   - Sincronize apenas quando necessario
   - Use paginacao para grandes volumes
   - Configure cache se necessario

3. **Backup:**
   - Configure backup automatico do arquivo SQLite
   - Mantenha copias da API
   - Documente procedimentos de recuperacao 