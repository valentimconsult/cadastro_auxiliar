# Sistema de Cadastro - Streamlit

Aplicacao web completa para cadastro de dados desenvolvida com Streamlit, Docker e API REST.

## 🚀 Caracteristicas

### **Funcionalidades Principais**
- ✅ Interface web amigavel para cadastro de dados
- ✅ Sistema de autenticacao de usuarios
- ✅ Criacao dinamica de tabelas
- ✅ **Gerenciamento completo de registros** (adicionar, visualizar, editar, excluir)
- ✅ **Carga em lote via CSV** com controle de duplicidade
- ✅ **Validacao automatica de dados**
- ✅ **API REST para acesso externo** ao banco de dados
- ✅ **Acesso via DBeaver e outros clientes SQLite**
- ✅ Persistencia de dados em SQLite
- ✅ Deploy via Docker Compose
- ✅ **Script PowerShell para gerenciamento** (Windows)

### **Funcionalidades Avancadas**
- 🔄 **Sincronizacao remota** de banco de dados
- 📊 **Exportacao de dados** em CSV, JSON, Excel
- 🔍 **Queries SQL customizadas** via API
- 📈 **Estatisticas e relatorios** do banco
- 🛡️ **Controle de duplicidade** automatico
- 📋 **Templates CSV** para carga em lote
- 🌐 **Acesso multiplo** (web, API, clientes SQLite)

## 📋 Pre-requisitos

- Docker
- Docker Compose
- Python 3.8+ (para scripts locais)

## 🚀 Instalacao e Uso

### 1. Clonar o repositorio
```bash
git clone <url-do-repositorio>
cd cadastro_streamlit
```

### 2. Executar com Docker Compose

#### **Opcao A: Comando direto**
```powershell
# Primeira execucao (build da imagem)
docker-compose up --build

# Execucoes subsequentes
docker-compose up

# Executar em background
docker-compose up -d
```

#### **Opcao B: Script PowerShell (Windows)**
```powershell
# Menu interativo
.\start-app.ps1

# Comandos diretos
.\start-app.ps1 start     # Iniciar
.\start-app.ps1 stop      # Parar
.\start-app.ps1 restart   # Reiniciar
.\start-app.ps1 logs      # Ver logs
.\start-app.ps1 status    # Ver status
.\start-app.ps1 optimize  # Otimizar sistema
```

#### **Opcao C: Script Bash (Linux)**
```bash
# Tornar executável
chmod +x start-app.sh

# Menu interativo
./start-app.sh

# Comandos diretos
./start-app.sh start     # Iniciar
./start-app.sh stop      # Parar
./start-app.sh restart   # Reiniciar
./start-app.sh logs      # Ver logs
./start-app.sh status    # Ver status
./start-app.sh optimize  # Otimizar sistema
```

### 3. Acessar a aplicacao

- **Interface Web**: http://localhost:8501
- **API REST**: http://localhost:5000/api
- **Credenciais**: admin/admin

## 🔧 API REST

### **Endpoints Principais**

```bash
# Health Check
GET http://localhost:5000/api/health

# Listar tabelas
GET http://localhost:5000/api/tables

# Dados de uma tabela
GET http://localhost:5000/api/tables/{nome}

# Exportar dados
GET http://localhost:5000/api/tables/{nome}/export?format=csv
GET http://localhost:5000/api/tables/{nome}/export?format=json
GET http://localhost:5000/api/tables/{nome}/export?format=excel

# Gerenciar registros
GET http://localhost:5000/api/tables/{nome}/records/{id} - Obter registro
PUT http://localhost:5000/api/tables/{nome}/records/{id} - Atualizar registro
DELETE http://localhost:5000/api/tables/{nome}/records/{id} - Excluir registro

# Schema da tabela
GET http://localhost:5000/api/tables/{nome}/schema

# Estatisticas do banco
GET http://localhost:5000/api/stats

# Query SQL customizada (apenas SELECT)
POST http://localhost:5000/api/query
Content-Type: application/json
{
  "query": "SELECT * FROM tabela WHERE campo = 'valor'"
}
```

### **Exemplo de Uso**
```python
import requests

# Testar conexao
response = requests.get("http://localhost:5000/api/health")
print(response.json())

# Listar tabelas
response = requests.get("http://localhost:5000/api/tables")
tables = response.json()['tables']
for table in tables:
    print(f"- {table['name']}: {table['row_count']} registros")
```

## 📊 Carga em Lote

### **Como Usar**

1. **Criar tabela** na interface web
2. **Acessar "Carga em lote"** na pagina de gerenciamento
3. **Baixar template CSV** com as colunas da tabela
4. **Preencher dados** no arquivo CSV
5. **Fazer upload** e configurar opcoes
6. **Importar dados** com controle de duplicidade

### **Caracteristicas**
- ✅ **Template automatico** baseado na estrutura da tabela
- ✅ **Validacao de tipos** de dados
- ✅ **Controle de duplicidade** automatico
- ✅ **Modo preview** antes da importacao
- ✅ **Relatorio detalhado** da importacao
- ✅ **Suporte a CSV** com encoding UTF-8

## 🌐 Acesso Remoto ao Banco

### **Para VM Remota**

Quando o Docker esta rodando em uma VM (AWS, Azure, etc.):

#### **Solucao 1: Script de Sincronizacao**
```bash
# Instalar dependencias
pip install requests pandas

# Sincronizar banco remoto
python sync_remote_db.py --api-url http://IP_DA_VM:5000/api

# Testar conexao
python sync_remote_db.py --api-url http://IP_DA_VM:5000/api --test-connection

# Ver estatisticas
python sync_remote_db.py --api-url http://IP_DA_VM:5000/api --stats-only
```

#### **Solucao 2: DBeaver com arquivo local**
1. Execute o script de sincronizacao
2. Abra DBeaver
3. Nova Conexao > SQLite
4. Database: `data_local.db`
5. Test Connection > Finish

#### **Solucao 3: Tunel SSH**
```bash
# Criar tunel SSH
ssh -L 5000:localhost:5000 usuario@IP_DA_VM

# Acessar localmente
curl http://localhost:5000/api/health
```

## 🛠️ Comandos Utilitarios

### **Docker Compose**
```powershell
# Parar aplicacao
docker-compose down

# Parar e remover volumes
docker-compose down -v

# Ver logs
docker-compose logs -f

# Rebuild da imagem
docker-compose build --no-cache

# Executar apenas um servico
docker-compose up cadastro-app
```

### **Script PowerShell**
```powershell
# Menu completo
.\start-app.ps1

# Comandos diretos
.\start-app.ps1 start    # Iniciar
.\start-app.ps1 stop     # Parar
.\start-app.ps1 restart  # Reiniciar
.\start-app.ps1 logs     # Ver logs
.\start-app.ps1 build    # Rebuild
.\start-app.ps1 clean    # Limpar Docker
.\start-app.ps1 status   # Ver status
```

## 📁 Estrutura do Projeto

```
cadastro_streamlit/
├── streamlit_app.py          # Aplicacao principal
├── api_server.py             # API REST
├── docker-compose.yml        # Configuracao Docker
├── Dockerfile               # Imagem Docker
├── requirements.txt         # Dependencias Python
├── start-app.ps1           # Script PowerShell
├── sync_remote_db.py       # Sincronizacao remota
├── db_connection_example.py # Exemplos de conexao
├── data/                   # Dados SQLite
├── config/                 # Configuracoes
├── logs/                   # Logs da aplicacao
├── README.md              # Documentacao principal
├── CARGA_EM_LOTE.md       # Guia carga em lote
├── ACESSO_EXTERNO_BANCO.md # Guia acesso externo
├── ACESSO_REMOTO_DBEAVER.md # Guia acesso remoto
└── exemplo_uso_remoto.md   # Exemplos praticos
```

## 🔧 Configuracao de Ambiente

### **Variaveis de Ambiente**
```yaml
# docker-compose.yml
environment:
  - STREAMLIT_SERVER_PORT=8501
  - STREAMLIT_SERVER_HEADLESS=true
  - STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
  - FLASK_APP=api_server.py
  - FLASK_ENV=production
```

### **Volumes**
```yaml
volumes:
  - ./data:/app/data          # Dados SQLite
  - ./config:/app/config      # Configuracoes
  - ./logs:/app/logs          # Logs
```

## 🛠️ Troubleshooting

### **Problema: Porta 8501 ja esta em uso**
```powershell
# Verificar processos na porta
netstat -ano | findstr :8501

# Alterar porta no docker-compose.yml
ports:
  - "8502:8501"  # Muda para porta 8502
```

### **Problema: API nao responde**
```bash
# Verificar logs
docker-compose logs api-server

# Testar localmente
curl http://localhost:5000/api/health

# Verificar firewall
sudo ufw allow 5000
```

### **Problema: DBeaver nao conecta**
```bash
# Verificar arquivo sincronizado
ls -la data_local.db

# Testar SQLite
sqlite3 data_local.db ".tables"
```

## 📚 Documentacao Adicional

### **Guias Detalhados**
- 📋 `CARGA_EM_LOTE.md` - Funcionalidade de carga em lote
- 📝 `EDICAO_REGISTROS.md` - Edição e exclusão de registros
- 🌐 `ACESSO_EXTERNO_BANCO.md` - Acesso externo ao banco
- 🔗 `ACESSO_REMOTO_DBEAVER.md` - Acesso remoto via DBeaver
- 📖 `exemplo_uso_remoto.md` - Exemplos praticos
- 🐧 `README_LINUX.md` - Deploy completo no Linux

### **Scripts de Exemplo**
- `sync_remote_db.py` - Sincronizacao de banco remoto
- `db_connection_example.py` - Exemplos de conexao
- `start-app.ps1` - Gerenciador PowerShell (Windows)
- `start-app.sh` - Gerenciador Bash (Linux)

## 🎯 Casos de Uso

### **Desenvolvimento Local**
1. Execute `docker-compose up --build`
2. Acesse http://localhost:8501
3. Use a interface web para cadastros
4. Use a API para integracoes

### **Deploy em VM**
1. Configure Docker na VM
2. Execute `docker-compose up -d`
3. Abra porta 5000 no firewall
4. Use scripts de sincronizacao

### **Integracao com Outros Sistemas**
1. Use a API REST para consultas
2. Sincronize dados com scripts
3. Conecte DBeaver ao arquivo local
4. Exporte dados em diferentes formatos

## 🔄 Producao

### **Recomendacoes**
1. ✅ Use HTTPS em producao
2. ✅ Implemente autenticacao na API
3. ✅ Configure backup automatico
4. ✅ Monitore logs e performance
5. ✅ Use secrets para senhas

### **Exemplo com Nginx**
```yaml
# Descomente no docker-compose.yml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
  depends_on:
    - cadastro-app
```

## 🤝 Contribuicao

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudancas
4. Push para a branch
5. Abra um Pull Request

## 📄 Licenca

Este projeto esta sob a licenca MIT. Veja o arquivo LICENSE para mais detalhes.

## 📞 Suporte

Para duvidas ou problemas:
1. Verifique a documentacao
2. Consulte os guias detalhados
3. Verifique os logs da aplicacao
4. Teste com os scripts de exemplo

---

**🎉 Sistema de Cadastro - Versao Completa com API REST, Carga em Lote e Acesso Remoto!** 