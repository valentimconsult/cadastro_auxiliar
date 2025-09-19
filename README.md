# Sistema de Cadastros Auxiliares

Sistema completo de gerenciamento de cadastros auxiliares desenvolvido em Streamlit com PostgreSQL, oferecendo interface web intuitiva, API REST e sistema robusto de permissões.

## 🚀 **Características Principais**

### **Interface e Usabilidade**
- ✅ **Interface web moderna** com Streamlit
- ✅ **Sistema de autenticação** com controle de usuários
- ✅ **Criação dinâmica de tabelas** por administradores
- ✅ **Gerenciamento completo de dados** (CRUD)
- ✅ **Carga em lote via CSV** com controle de duplicidade
- ✅ **Exportação de dados** em múltiplos formatos

### **Sistema de Permissões Avançado**
- 🔐 **Controle granular de permissões** por tabela e usuário
- 🔐 **Permissões automáticas** para criadores de tabelas
- 🔐 **Sistema de ativação/inativação** de tabelas
- 🔐 **Gerenciamento de usuários** com diferentes níveis de acesso
- 🔐 **Integração completa com PostgreSQL** via grants

### **Arquitetura Robusta**
- 🏗️ **PostgreSQL** como banco de dados principal
- 🏗️ **API REST** para integração externa
- 🏗️ **Containerização Docker** para fácil deploy
- 🏗️ **Sistema de metadados** para controle de estrutura
- 🏗️ **Backup automático** e persistência de dados

## 🏗️ **Arquitetura do Sistema**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   API Server    │    │   PostgreSQL    │
│   (Porta 8503)  │◄──►│   (Porta 5000)  │◄──►│   (Porta 5436)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Metadados     │
                    │   & Permissões  │
                    └─────────────────┘
```

## 📋 **Pré-requisitos**

- **Docker Desktop** instalado e rodando
- **PowerShell** (Windows) ou **Terminal** (Linux/Mac)
- **Portas disponíveis**: 8503, 5000, 5436

## 🚀 **Instalação e Uso**

### **Windows (PowerShell)**
```powershell
# Executar como Administrador
cd "caminho\para\seu\projeto\cadastro_auxiliar"
docker-compose up --build -d
```

### **Linux/Mac (Terminal) - Unificado**
```bash
# Navegar para o diretório do projeto
cd caminho/para/seu/projeto/cadastro_auxiliar

# Dar permissão de execução
chmod +x scripts/start-app-linux.sh

# Executar (detecta automaticamente Desktop ou Raspberry Pi)
./scripts/start-app-linux.sh
```

> **📌 Nota**: O script detecta automaticamente se está rodando em Raspberry Pi e aplica otimizações específicas. Funciona tanto em desktop quanto em Raspberry Pi com 16GB de RAM.

### **Troubleshooting**

**Problemas comuns:**
```bash
# Verificar logs
docker-compose logs

# Verificar status dos containers
docker-compose ps

# Reiniciar aplicação
docker-compose restart

# Limpar tudo e recomeçar
docker-compose down -v
docker system prune -f
./scripts/start-app-linux.sh
```

**Problemas de memória (Raspberry Pi):**
```bash
# Aumentar swap se necessário
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Altere CONF_SWAPSIZE=100 para CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### **Execução Manual**
```bash
# Construir e iniciar containers
docker-compose up --build -d

# Verificar status
docker-compose ps
```

## 🌐 **Acessos**

- **Aplicação Principal**: http://localhost:8503
- **API REST**: http://localhost:5000
- **PostgreSQL**: localhost:5436

## 🔐 **Credenciais Padrão**

### **Sistema**
- **Usuário Admin**: `admin`
- **Senha Admin**: `admin`

### **Banco PostgreSQL**
- **Host**: localhost
- **Porta**: 5436
- **Database**: cadastro_db
- **Usuário**: cadastro_user
- **Senha**: cadastro_password

## 🎯 **Funcionalidades Detalhadas**

### **Para Administradores**
- 👥 **Gerenciamento de usuários** (criar, editar, ativar/inativar)
- 🔐 **Configuração de permissões** gerais e por tabela
- 📊 **Criação de tabelas** dinâmicas
- ⚙️ **Ativação/inativação** de tabelas
- 📈 **Monitoramento** do sistema

### **Para Usuários**
- 📋 **Visualização de dados** (conforme permissões)
- ➕ **Inserção de registros** (conforme permissões)
- ✏️ **Edição de dados** (conforme permissões)
- 📤 **Exportação de dados** em CSV, JSON, Excel
- 📥 **Carga em lote** via CSV

### **Sistema de Permissões**
- **Permissões Gerais**: Criar tabelas, gerenciar usuários
- **Permissões por Tabela**: Visualizar, Inserir, Editar, Excluir
- **Permissões Automáticas**: Criadores recebem permissões básicas automaticamente
- **Controle de Status**: Tabelas podem ser ativadas/inativadas

## 🗄️ **Estrutura do Banco de Dados**

### **Tabelas Principais**
- **`users`**: Usuários do sistema
- **`tables_metadata`**: Metadados das tabelas criadas
- **`user_table_permissions`**: Permissões por tabela
- **`user_general_permissions`**: Permissões gerais
- **`config`**: Configurações do sistema

### **Tabelas Dinâmicas**
- Criadas automaticamente conforme necessidade
- Estrutura definida pelos administradores
- Controle de acesso via sistema de permissões

## 🔧 **Comandos Úteis**

### **Docker**
```bash
# Ver status dos containers
docker-compose ps

# Ver logs em tempo real
docker-compose logs -f

# Parar sistema
docker-compose down

# Reconstruir containers
docker-compose up --build -d
```

### **Banco de Dados**
```bash
# Conectar ao PostgreSQL
docker exec -it cadastro_banco psql -U cadastro_user -d cadastro_db

# Ver tabelas
\dt

# Ver estrutura de uma tabela
\d nome_da_tabela
```

## 🛠️ **Desenvolvimento**

### **Estrutura de Arquivos**
```
cadastro_auxiliar/
├── 📁 scripts/                    # Scripts de inicialização
│   └── start-app-linux.sh         # Linux/Mac (unificado)
├── 📁 database/                   # Configurações do banco
│   ├── db_config.py               # Conexão PostgreSQL
│   ├── grants_manager.py          # Gerenciamento de permissões
│   └── init-db.sql                # Inicialização do banco
├── 📁 docs/                       # Documentação técnica
│   └── ARQUITETURA_POSTGRESQL_GRANTS.md
├── 📁 data/                       # Dados da aplicação
│   └── logos/                     # Logos da empresa
├── 🐳 docker-compose.yml          # Orquestração Docker
├── 🐳 Dockerfile                  # Imagem Docker
├── 📋 requirements.txt            # Dependências Python
├── 🌐 streamlit_app.py            # Aplicação principal
├── 🔌 api_server.py               # API REST
├── ⚙️ config.json                 # Configurações
└── 📖 README.md                   # Esta documentação
```

### **Modificando o Sistema**
1. **Interface**: Modifique `streamlit_app.py`
2. **API**: Modifique `api_server.py`
3. **Banco**: Modifique `database/db_config.py`
4. **Docker**: Modifique `docker-compose.yml`

## 🔍 **Troubleshooting**

### **Problemas Comuns**

#### **Containers não iniciam**
```bash
# Verificar logs
docker-compose logs

# Verificar portas em uso
netstat -an | grep -E "(8503|5000|5436)"
```

#### **Erro de conexão com banco**
```bash
# Verificar se PostgreSQL está rodando
docker exec cadastro_banco pg_isready -U cadastro_user -d cadastro_db

# Verificar logs do PostgreSQL
docker-compose logs cadastro_banco
```

#### **Problemas de permissão**
```bash
# Windows: Executar PowerShell como Administrador
# Linux/Mac: Verificar permissões dos scripts
chmod +x scripts/*.sh
```

#### **Erro de Login - Coluna "status" não existe**
Se você receber o erro `column "status" does not exist` ao tentar fazer login:

**Solução Rápida:**
```bash
# Linux/Mac
docker exec -i cadastro_banco psql -U cadastro_user -d cadastro_db -c "ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ativo' CHECK (status IN ('ativo', 'inativo')); UPDATE users SET status = 'ativo' WHERE status IS NULL;"

# Windows (PowerShell)
docker exec -i cadastro_banco psql -U cadastro_user -d cadastro_db -c "ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ativo' CHECK (status IN ('ativo', 'inativo')); UPDATE users SET status = 'ativo' WHERE status IS NULL;"
```

**Solução Manual:**
```bash
# Conectar ao PostgreSQL
docker exec -it cadastro_banco psql -U cadastro_user -d cadastro_db

# Executar migração
ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'ativo' CHECK (status IN ('ativo', 'inativo'));
UPDATE users SET status = 'ativo' WHERE status IS NULL;
\q
```

> **📌 Nota**: Este erro só ocorre em instalações antigas. Novas instalações já incluem a coluna `status` automaticamente.

## 📈 **Monitoramento**

### **Health Checks**
- **Streamlit**: http://localhost:8503/_stcore/health
- **API**: http://localhost:5000/api/health
- **PostgreSQL**: Verificado automaticamente pelo Docker

### **Logs**
```bash
# Logs consolidados
docker-compose logs

# Logs específicos
docker-compose logs cadastro-app
docker-compose logs api-server
docker-compose logs cadastro_banco
```

## 🔒 **Segurança**

- **Porta PostgreSQL**: 5436 (não conflita com instalações locais)
- **Usuários**: Gerenciados pelo sistema com hash SHA-256
- **Permissões**: Controle granular via PostgreSQL grants
- **CORS**: Configurado para desenvolvimento
- **Dados**: Persistidos em volumes Docker

## 🔄 **Versões e Melhorias**

### **v2.0 - Sistema de Permissões Avançado**
- ✅ Sistema robusto de permissões com PostgreSQL
- ✅ Ativação/inativação de tabelas
- ✅ Permissões automáticas para criadores
- ✅ Interface de gerenciamento aprimorada
- ✅ Integração completa com grants PostgreSQL

### **v1.0 - Versão Inicial**
- ✅ Sistema básico de cadastros
- ✅ Interface Streamlit
- ✅ API REST
- ✅ Banco PostgreSQL
- ✅ Containerização Docker

## 📝 **Notas Importantes**

1. **Primeira execução**: Pode demorar para baixar imagens Docker
2. **Dados**: Persistidos em volumes Docker (não são perdidos ao parar)
3. **Backup**: Sempre faça backup antes de atualizações importantes
4. **Portas**: Verifique se não estão em uso por outros serviços
5. **Permissões**: Sistema de permissões é robusto e granular

## 🤝 **Suporte**

Para problemas ou dúvidas:

1. **Verifique os logs** dos containers
2. **Teste a conexão** com o banco
3. **Verifique se todas as portas** estão disponíveis
4. **Consulte a documentação** do Docker e PostgreSQL

## 📚 **Recursos Adicionais**

- [Documentação Docker](https://docs.docker.com/)
- [Documentação PostgreSQL](https://www.postgresql.org/docs/)
- [Documentação Streamlit](https://docs.streamlit.io/)
- [Documentação Flask](https://flask.palletsprojects.com/)

---

**Desenvolvido por Valentim Consult** - Sistema de Cadastros Auxiliares v2.0