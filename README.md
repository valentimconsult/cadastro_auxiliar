# Sistema de Cadastro Streamlit com PostgreSQL

Sistema completo de cadastros auxiliares desenvolvido em Streamlit, utilizando PostgreSQL como banco de dados principal, com API REST e containerizacao Docker.

## 🚀 Caracteristicas

### **Funcionalidades Principais**
- ✅ Interface web amigavel para cadastro de dados
- ✅ Sistema de autenticacao de usuarios
- ✅ Criacao dinamica de tabelas
- ✅ Gerenciamento completo de registros (CRUD)
- ✅ Carga em lote via CSV com controle de duplicidade
- ✅ Validacao automatica de dados
- ✅ API REST para acesso externo
- ✅ Banco PostgreSQL robusto e escalavel
- ✅ Deploy via Docker Compose
- ✅ Scripts de inicializacao para Windows e Linux

### **Funcionalidades Avancadas**
- 🔄 Migracao automatica de dados
- 📊 Exportacao de dados em CSV, JSON, Excel
- 🔍 Queries SQL customizadas via API
- 📈 Estatisticas e relatorios do banco
- 🛡️ Controle de duplicidade automatico
- 📋 Templates CSV para carga em lote
- 🌐 Acesso multiplo (web, API, clientes PostgreSQL)

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   API Server    │    │   PostgreSQL    │
│   (Porta 8503)  │◄──►│   (Porta 5000)  │◄──►│   (Porta 5436)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Pre-requisitos

- Docker Desktop instalado e rodando
- PowerShell (Windows) ou Terminal (Linux/Mac)
- Portas 8503, 5000 e 5436 disponiveis

## 🚀 Instalacao e Uso

### **Windows (PowerShell)**

```powershell
# Executar como Administrador
cd "C:\valentim_consult\projetos_sistemas\cadastros_auxiliares\cadastro_streamlit"
.\scripts\start-app-postgres.ps1
```

### **Linux/Mac (Terminal)**

```bash
# Dar permissao de execucao
chmod +x scripts/start-app-postgres.sh

# Executar
./scripts/start-app-postgres.sh
```

### **Raspberry Pi (ARM64)**

```bash
# Navegar para o diretorio
cd ~/infra/docker/cadastro_auxiliar/cadastro_auxiliar

# Dar permissao de execucao
chmod +x scripts/start-app-postgres.sh

# Executar
./scripts/start-app-postgres.sh

# Ou executar manualmente
docker-compose up --build -d
```

### **Manual**

```bash
# Construir e iniciar containers
docker-compose up --build -d

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f
```

## 🌐 Acessos

- **Streamlit App**: http://localhost:8503
- **API Server**: http://localhost:5000
- **PostgreSQL**: localhost:5436

## 🗄️ Configuracao do Banco

### **Credenciais Padrao**

- **Host**: localhost
- **Porta**: 5436
- **Database**: cadastro_db
- **Usuario**: cadastro_user
- **Senha**: cadastro_password

### **Usuario Admin Padrao**

- **Usuario**: admin
- **Senha**: admin

## 📊 Migracao de Dados

Se voce tem dados existentes no SQLite, use o script de migracao:

```bash
# Executar migracao
python migrate_to_postgres.py
```

O script ira:
1. Conectar ao PostgreSQL
2. Carregar dados do SQLite
3. Criar tabelas no PostgreSQL
4. Migrar todos os dados
5. Manter usuarios e configuracoes

## 🔧 Comandos Uteis

### **Docker**

```bash
# Ver status dos containers
docker-compose ps

# Ver logs em tempo real
docker-compose logs -f

# Parar sistema
docker-compose down

# Parar e remover volumes
docker-compose down -v

# Reconstruir containers
docker-compose up --build -d
```

### **Banco de Dados**

```bash
# Conectar ao PostgreSQL
docker exec -it cadastro-postgres psql -U cadastro_user -d cadastro_db

# Ver tabelas
\dt

# Ver estrutura de uma tabela
\d nome_da_tabela

# Sair
\q
```

### **Logs**

```bash
# Logs do Streamlit
docker-compose logs -f cadastro-app

# Logs da API
docker-compose logs -f api-server

# Logs do PostgreSQL
docker-compose logs -f postgres
```

## 🛠️ Desenvolvimento

### **Estrutura de Arquivos**

```
cadastro_streamlit/
├── 📁 scripts/                    # Scripts de inicializacao e utilitarios
│   ├── start-app-postgres.ps1     # Script de inicializacao (Windows)
│   ├── start-app-postgres.sh      # Script de inicializacao (Linux/Mac)
│   └── migrate_to_postgres.py     # Script de migracao de dados
├── 📁 database/                   # Configuracoes e scripts do banco
│   ├── db_config.py               # Configuracao de conexao PostgreSQL
│   └── init-db.sql                # Script de inicializacao do banco
├── 📁 docs/                       # Documentacao adicional
│   ├── exemplo_uso_remoto.md      # Exemplos de uso remoto
│   └── ACESSO_EXTERNO_BANCO.md    # Guia de acesso externo
├── 📁 data/                       # Dados da aplicacao
├── 🐳 docker-compose.yml          # Configuracao Docker
├── 🐳 Dockerfile                  # Imagem Docker
├── 📋 requirements.txt            # Dependencias Python
├── 🌐 streamlit_app.py            # App principal Streamlit
├── 🔌 api_server.py               # API REST Flask
├── ⚙️ config.json                 # Configuracoes da aplicacao
├── 📖 README.md                   # Documentacao principal
└── 🚫 .gitignore                  # Arquivos ignorados pelo Git
```

### **Modificando o Sistema**

1. **Alterar banco**: Modifique `db_config.py`
2. **Alterar API**: Modifique `api_server.py`
3. **Alterar interface**: Modifique `streamlit_app.py`
4. **Alterar Docker**: Modifique `docker-compose.yml`

### **Adicionando Novas Dependencias**

```bash
# Editar requirements.txt
echo "nova_dependencia==1.0.0" >> requirements.txt

# Reconstruir container
docker-compose up --build -d
```

## 🔍 Troubleshooting

### **Erro de Importacao CSV - "unhashable type: 'slice'"**

**Problema**: Erro ao importar dados CSV com a mensagem "unhashable type: 'slice'"

**Causa**: Incompatibilidade entre objetos Row do psycopg2 e operacoes de slice

**Solucao**: Corrigido na versao atual - o sistema agora converte corretamente os objetos Row para listas antes de fazer operacoes de slice

**Verificacao**: 
- A importacao de CSV agora funciona corretamente
- Controle de duplicidade funcional
- Validacao de dados mantida

### **Raspberry Pi - Docker Compose**

Se voce receber erro sobre opcoes nao suportadas:

```bash
# Verificar versao do Docker Compose
docker-compose --version

# Se for versao antiga, o arquivo ja foi simplificado
# Caso contrario, execute:
docker-compose up --build -d
```

### **PostgreSQL nao inicia**

```bash
# Ver logs
docker-compose logs postgres

# Verificar se porta esta em uso
netstat -an | grep 5436

# Parar e reiniciar
docker-compose down
docker-compose up -d
```

### **Erro de conexao**

```bash
# Verificar se containers estao rodando
docker-compose ps

# Testar conexao com banco
docker exec cadastro-postgres pg_isready -U cadastro_user -d cadastro_db

# Verificar variaveis de ambiente
docker-compose config
```

### **Problemas de permissao**

```bash
# Windows: Executar PowerShell como Administrador
# Linux/Mac: Verificar permissoes dos arquivos
chmod +x *.sh
```

## 📈 Monitoramento

### **Health Checks**

- **Streamlit**: http://localhost:8503/_stcore/health
- **API**: http://localhost:5000/api/health
- **PostgreSQL**: Verificado automaticamente pelo Docker

### **Logs**

```bash
# Logs consolidados
docker-compose logs

# Logs de um servico especifico
docker-compose logs cadastro-app
docker-compose logs api-server
docker-compose logs postgres
```

## 🔒 Seguranca

- **Porta PostgreSQL**: 5436 (nao conflita com instalacoes locais)
- **Usuarios**: Gerenciados pelo sistema
- **Senhas**: Hash SHA-256
- **CORS**: Configurado para desenvolvimento

## 🔄 Melhorias Recentes

### **v1.1 - Correcao de Importacao CSV**
- ✅ Corrigido erro "unhashable type: 'slice'" na importacao de CSV
- ✅ Melhorada compatibilidade com PostgreSQL e psycopg2
- ✅ Controle de duplicidade mais robusto
- ✅ Validacao de dados aprimorada

### **v1.0 - Versao Inicial**
- ✅ Sistema completo de cadastros
- ✅ Interface Streamlit responsiva
- ✅ API REST funcional
- ✅ Banco PostgreSQL integrado
- ✅ Containerizacao Docker

## 📝 Notas Importantes

1. **Primeira execucao**: Pode demorar para baixar imagens Docker
2. **Dados**: Sao persistidos em volume Docker
3. **Backup**: Sempre faca backup antes de atualizacoes
4. **Portas**: Verifique se nao estao em uso por outros servicos
5. **Importacao CSV**: Agora totalmente funcional com controle de duplicidade

## 🤝 Suporte

Para problemas ou duvidas:

1. Verifique os logs dos containers
2. Teste a conexao com o banco
3. Verifique se todas as portas estao disponiveis
4. Consulte a documentacao do Docker e PostgreSQL

## 📚 Recursos Adicionais

- [Documentacao Docker](https://docs.docker.com/)
- [Documentacao PostgreSQL](https://www.postgresql.org/docs/)
- [Documentacao Streamlit](https://docs.streamlit.io/)
- [Documentacao Flask](https://flask.palletsprojects.com/) 