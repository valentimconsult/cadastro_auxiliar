# 🚀 Guia para Subir no GitHub

## ⚠️ Importante: Segurança dos Dados

**NUNCA suba dados sensíveis para o GitHub!** O arquivo `.gitignore` já está configurado para proteger seus dados.

## 📋 Passo a Passo

### 1. **Fazer Backup dos Dados**
```bash
# Executar script de backup
python backup_before_git.py
```

Este script vai:
- ✅ Criar backup do banco de dados
- ✅ Criar backup das configurações
- ✅ Gerar relatório dos dados
- ✅ Criar instruções de restauração
- ✅ Remover arquivos sensíveis (opcional)

### 2. **Verificar o que será enviado**
```bash
# Ver arquivos que serão enviados
git status

# Ver arquivos ignorados
git status --ignored
```

### 3. **Subir para o GitHub**
```bash
# Inicializar repositório (se for a primeira vez)
git init

# Adicionar arquivos
git add .

# Fazer commit
git commit -m "Sistema de cadastro completo com API REST"

# Adicionar repositório remoto (substitua pela sua URL)
git remote add origin https://github.com/seu-usuario/seu-repositorio.git

# Enviar para o GitHub
git push -u origin main
```

## 🔒 Arquivos Protegidos

O `.gitignore` protege automaticamente:

### **Banco de Dados**
- `data/data.db` - Seu banco SQLite
- `data/*.db` - Qualquer arquivo .db
- `*.db` - Arquivos de banco em qualquer lugar

### **Logs e Temporários**
- `logs/` - Diretório de logs
- `*.log` - Arquivos de log
- `*.tmp`, `*.temp` - Arquivos temporários

### **Configurações Locais**
- `config/local_*` - Configurações específicas
- `.env` - Variáveis de ambiente

### **Uploads e Backups**
- `uploads/` - Arquivos enviados pelos usuários
- `backup/` - Diretório de backups
- `*_resized.*` - Imagens redimensionadas

## 📁 Estrutura que será enviada

```
cadastro_streamlit/
├── streamlit_app.py          ✅ Código principal
├── api_server.py             ✅ API REST
├── docker-compose.yml        ✅ Configuração Docker
├── Dockerfile               ✅ Imagem Docker
├── requirements.txt         ✅ Dependências
├── start-app.ps1           ✅ Script Windows
├── start-app.sh            ✅ Script Linux
├── .gitignore              ✅ Proteção de dados
├── README.md              ✅ Documentação
├── README_LINUX.md        ✅ Guia Linux
├── backup_before_git.py   ✅ Script de backup
├── GUIA_GITHUB.md         ✅ Este guia
├── data/                  ✅ Diretório (sem .db)
├── config/                ✅ Diretório (sem dados locais)
└── [outros arquivos]      ✅ Documentação e scripts
```

## 🔄 Como Restaurar Dados

### **Após clonar o repositório:**

1. **Verificar backup criado:**
   ```bash
   ls backup_before_git/
   ```

2. **Restaurar banco de dados:**
   ```bash
   # Parar aplicação (se estiver rodando)
   ./start-app.sh stop  # Linux
   # ou
   .\start-app.ps1 stop  # Windows
   
   # Restaurar banco
   cp backup_before_git/data_backup_*.db data/data.db
   
   # Reiniciar aplicação
   ./start-app.sh start  # Linux
   # ou
   .\start-app.ps1 start  # Windows
   ```

3. **Restaurar configurações:**
   ```bash
   cp backup_before_git/users_backup_*.json users.json
   cp backup_before_git/tables_backup_*.json tables.json
   cp backup_before_git/config_backup_*.json config.json
   ```

## ⚡ Comandos Rápidos

### **Backup e Preparação:**
```bash
python backup_before_git.py
```

### **Verificar o que será enviado:**
```bash
git status
```

### **Subir para GitHub:**
```bash
git add .
git commit -m "Sistema de cadastro completo"
git push origin main
```

### **Limpar arquivos sensíveis (se necessário):**
```bash
python backup_before_git.py --clean-only
```

## 🛡️ Segurança

### **O que NÃO será enviado:**
- ❌ Dados do banco SQLite
- ❌ Logs da aplicação
- ❌ Configurações locais
- ❌ Arquivos temporários
- ❌ Uploads de usuários
- ❌ Backups automáticos

### **O que SERÁ enviado:**
- ✅ Código fonte completo
- ✅ Configurações Docker
- ✅ Scripts de gerenciamento
- ✅ Documentação
- ✅ Scripts de backup
- ✅ Estrutura de diretórios

## 🎯 Checklist Antes de Subir

- [ ] Backup criado com `python backup_before_git.py`
- [ ] Verificado `git status` - sem dados sensíveis
- [ ] Testado aplicação localmente
- [ ] Documentação atualizada
- [ ] README.md completo
- [ ] .gitignore configurado

## 📞 Se Algo Der Errado

### **Dados perdidos?**
```bash
# Verificar backups
ls backup_before_git/

# Restaurar do backup mais recente
cp backup_before_git/data_backup_*.db data/data.db
```

### **Arquivo sensível enviado?**
```bash
# Remover do histórico do Git
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch ARQUIVO_SENSIVEL" \
  --prune-empty --tag-name-filter cat -- --all

# Forçar push
git push origin --force
```

---

**🔒 Seus dados estão seguros! O .gitignore protege automaticamente.** 