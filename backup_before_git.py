#!/usr/bin/env python3
"""
Script para fazer backup dos dados antes de subir para o GitHub.
Este script cria um backup dos dados e remove arquivos sensíveis.
"""

import os
import shutil
import sqlite3
import json
from datetime import datetime
import sys

def create_backup():
    """Cria backup dos dados importantes."""
    
    print("🔒 Criando backup antes do Git...")
    
    # Criar diretório de backup
    backup_dir = "backup_before_git"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Backup do banco de dados
    db_path = "data/data.db"
    if os.path.exists(db_path):
        backup_db = f"{backup_dir}/data_backup_{timestamp}.db"
        shutil.copy2(db_path, backup_db)
        print(f"✅ Backup do banco criado: {backup_db}")
        
        # Criar relatório do banco
        create_db_report(db_path, backup_dir, timestamp)
    else:
        print("⚠️ Banco de dados não encontrado")
    
    # Backup das configurações
    config_files = ["users.json", "tables.json", "config.json"]
    for config_file in config_files:
        if os.path.exists(config_file):
            backup_config = f"{backup_dir}/{config_file.replace('.json', '')}_backup_{timestamp}.json"
            shutil.copy2(config_file, backup_config)
            print(f"✅ Backup da configuração criado: {backup_config}")
    
    # Criar arquivo de instruções
    create_instructions(backup_dir, timestamp)
    
    print(f"\n🎯 Backup completo criado em: {backup_dir}/")
    print("📋 Arquivos que serão ignorados pelo Git:")
    print("   - data/data.db")
    print("   - logs/")
    print("   - *.log")
    print("   - config/local_*")

def create_db_report(db_path, backup_dir, timestamp):
    """Cria relatório do banco de dados."""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Listar tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        report = {
            "timestamp": timestamp,
            "database_path": db_path,
            "tables": []
        }
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            # Obter estrutura da tabela
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            table_info = {
                "name": table_name,
                "row_count": count,
                "columns": [{"name": col[1], "type": col[2]} for col in columns]
            }
            
            report["tables"].append(table_info)
        
        conn.close()
        
        # Salvar relatório
        report_file = f"{backup_dir}/database_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Relatório do banco criado: {report_file}")
        
        # Mostrar resumo
        print(f"\n📊 Resumo do banco:")
        for table in report["tables"]:
            print(f"   - {table['name']}: {table['row_count']} registros")
    
    except Exception as e:
        print(f"❌ Erro ao criar relatório: {e}")

def create_instructions(backup_dir, timestamp):
    """Cria arquivo de instruções para restaurar dados."""
    
    instructions = f"""# 🔄 Instruções para Restaurar Dados

## 📅 Backup criado em: {timestamp}

### 📁 Arquivos de Backup
- `data_backup_{timestamp}.db` - Banco de dados completo
- `users_backup_{timestamp}.json` - Configuração de usuários
- `tables_backup_{timestamp}.json` - Configuração de tabelas
- `config_backup_{timestamp}.json` - Configurações gerais
- `database_report_{timestamp}.json` - Relatório do banco

### 🔄 Como Restaurar

#### 1. Restaurar Banco de Dados
```bash
# Parar aplicação
./start-app.sh stop  # Linux
# ou
.\\start-app.ps1 stop  # Windows

# Restaurar banco
cp data_backup_{timestamp}.db data/data.db

# Reiniciar aplicação
./start-app.sh start  # Linux
# ou
.\\start-app.ps1 start  # Windows
```

#### 2. Restaurar Configurações
```bash
# Restaurar arquivos de configuração
cp users_backup_{timestamp}.json users.json
cp tables_backup_{timestamp}.json tables.json
cp config_backup_{timestamp}.json config.json
```

### ⚠️ Importante
- Este backup foi criado automaticamente antes de subir para o Git
- Os dados originais foram preservados
- O arquivo `data/data.db` será ignorado pelo Git
- Para restaurar, use os arquivos de backup acima

### 📊 Dados no Backup
Verifique o arquivo `database_report_{timestamp}.json` para ver:
- Tabelas existentes
- Número de registros por tabela
- Estrutura das colunas

---
**Criado automaticamente pelo script backup_before_git.py**
"""
    
    instructions_file = f"{backup_dir}/RESTAURAR_DADOS_{timestamp}.md"
    with open(instructions_file, 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print(f"✅ Instruções criadas: {instructions_file}")

def clean_for_git():
    """Remove arquivos sensíveis para o Git."""
    
    print("\n🧹 Limpando arquivos sensíveis...")
    
    # Lista de arquivos/diretórios a remover
    sensitive_files = [
        "data/data.db",
        "logs/",
        "*.log",
        "config/local_*",
        ".env"
    ]
    
    for pattern in sensitive_files:
        if os.path.exists(pattern):
            if os.path.isfile(pattern):
                os.remove(pattern)
                print(f"🗑️ Removido arquivo: {pattern}")
            elif os.path.isdir(pattern):
                shutil.rmtree(pattern)
                print(f"🗑️ Removido diretório: {pattern}")
    
    print("✅ Limpeza concluída!")

def main():
    """Função principal."""
    
    if len(sys.argv) > 1 and sys.argv[1] == "--clean-only":
        clean_for_git()
        return
    
    print("🚀 Backup e Preparação para Git")
    print("=" * 40)
    
    # Criar backup
    create_backup()
    
    # Perguntar se quer limpar
    response = input("\n❓ Deseja remover arquivos sensíveis agora? (s/N): ").lower()
    if response in ['s', 'sim', 'y', 'yes']:
        clean_for_git()
        print("\n✅ Pronto para subir para o Git!")
    else:
        print("\n💡 Para limpar depois, execute: python backup_before_git.py --clean-only")
    
    print("\n📋 Próximos passos:")
    print("1. git add .")
    print("2. git commit -m 'Sistema de cadastro completo'")
    print("3. git push origin main")

if __name__ == "__main__":
    main() 