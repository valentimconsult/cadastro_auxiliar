"""
Script de migracao de dados do SQLite para PostgreSQL
Este script migra todos os dados existentes para o novo banco PostgreSQL
"""

import sqlite3
import json
import os
import sys
from datetime import datetime
from db_config import get_db_cursor, test_connection

def load_sqlite_data():
    """Carrega dados existentes do SQLite"""
    sqlite_path = os.path.join("data", "data.db")
    
    if not os.path.exists(sqlite_path):
        print("❌ Arquivo SQLite nao encontrado em data/data.db")
        return None, None, None
    
    try:
        conn = sqlite3.connect(sqlite_path)
        conn.row_factory = sqlite3.Row
        
        # Carregar usuarios
        users = {}
        try:
            cursor = conn.execute("SELECT username, password, role FROM users")
            for row in cursor.fetchall():
                users[row['username']] = {
                    'password': row['password'],
                    'role': row['role']
                }
        except sqlite3.OperationalError:
            print("⚠️  Tabela users nao encontrada no SQLite")
        
        # Carregar metadados das tabelas
        tables_metadata = []
        try:
            with open("tables.json", "r", encoding="utf-8") as f:
                tables_metadata = json.load(f)
        except FileNotFoundError:
            print("⚠️  Arquivo tables.json nao encontrado")
        
        # Carregar configuracao
        config = {}
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
        except FileNotFoundError:
            print("⚠️  Arquivo config.json nao encontrado")
        
        # Carregar dados das tabelas dinamicas
        tables_data = {}
        for table_meta in tables_metadata:
            table_name = table_meta['name']
            try:
                cursor = conn.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                tables_data[table_name] = [dict(row) for row in rows]
                print(f"📊 Tabela {table_name}: {len(rows)} registros")
            except sqlite3.OperationalError as e:
                print(f"⚠️  Erro ao carregar tabela {table_name}: {e}")
        
        conn.close()
        return users, tables_metadata, tables_data, config
        
    except Exception as e:
        print(f"❌ Erro ao carregar dados do SQLite: {e}")
        return None, None, None, None

def migrate_users(users):
    """Migra usuarios para PostgreSQL"""
    if not users:
        return
    
    print(f"👥 Migrando {len(users)} usuarios...")
    
    with get_db_cursor() as cursor:
        for username, user_data in users.items():
            try:
                cursor.execute("""
                    INSERT INTO users (username, password, role) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT (username) DO UPDATE SET
                        password = EXCLUDED.password,
                        role = EXCLUDED.role
                """, (username, user_data['password'], user_data['role']))
                print(f"  ✅ Usuario {username} migrado")
            except Exception as e:
                print(f"  ❌ Erro ao migrar usuario {username}: {e}")

def migrate_tables_metadata(tables_metadata):
    """Migra metadados das tabelas para PostgreSQL"""
    if not tables_metadata:
        return
    
    print(f"📋 Migrando metadados de {len(tables_metadata)} tabelas...")
    
    with get_db_cursor() as cursor:
        for table_meta in tables_metadata:
            try:
                cursor.execute("""
                    INSERT INTO tables_metadata (table_name, display_name, description, columns) 
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (table_name) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        description = EXCLUDED.description,
                        columns = EXCLUDED.columns
                """, (
                    table_meta['name'],
                    table_meta.get('display_name', table_meta['name']),
                    table_meta.get('description', ''),
                    json.dumps(table_meta['fields'])
                ))
                print(f"  ✅ Metadados da tabela {table_meta['name']} migrados")
            except Exception as e:
                print(f"  ❌ Erro ao migrar metadados da tabela {table_meta['name']}: {e}")

def migrate_config(config):
    """Migra configuracao para PostgreSQL"""
    if not config:
        return
    
    print(f"⚙️  Migrando configuracao...")
    
    with get_db_cursor() as cursor:
        for key, value in config.items():
            try:
                cursor.execute("""
                    INSERT INTO config (key_name, value) 
                    VALUES (%s, %s)
                    ON CONFLICT (key_name) DO UPDATE SET
                        value = EXCLUDED.value
                """, (key, value))
                print(f"  ✅ Configuracao {key} migrada")
            except Exception as e:
                print(f"  ❌ Erro ao migrar configuracao {key}: {e}")

def create_dynamic_tables(tables_metadata):
    """Cria tabelas dinamicas no PostgreSQL"""
    if not tables_metadata:
        return
    
    print(f"🏗️  Criando {len(tables_metadata)} tabelas dinamicas...")
    
    for table_meta in tables_metadata:
        table_name = table_meta['name']
        fields = table_meta['fields']
        
        try:
            with get_db_cursor() as cursor:
                # Criar tabela
                columns = ["id SERIAL PRIMARY KEY"]
                type_map = {
                    "text": "TEXT",
                    "int": "INTEGER",
                    "float": "REAL",
                    "date": "DATE",
                    "bool": "BOOLEAN",
                }
                
                for field in fields:
                    col_name = field['name'].strip().lower().replace(" ", "_")
                    sql_type = type_map.get(field['type'], "TEXT")
                    columns.append(f"{col_name} {sql_type}")
                
                sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)});"
                cursor.execute(sql)
                print(f"  ✅ Tabela {table_name} criada")
                
        except Exception as e:
            print(f"  ❌ Erro ao criar tabela {table_name}: {e}")

def migrate_table_data(table_name, data, fields):
    """Migra dados de uma tabela especifica"""
    if not data:
        return
    
    print(f"📊 Migrando {len(data)} registros da tabela {table_name}...")
    
    # Preparar colunas e placeholders
    column_names = []
    for field in fields:
        col_name = field['name'].strip().lower().replace(" ", "_")
        column_names.append(col_name)
    
    placeholders = ["%s"] * len(column_names)
    sql = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({', '.join(placeholders)})"
    
    inserted_count = 0
    error_count = 0
    
    with get_db_cursor() as cursor:
        for record in data:
            try:
                # Preparar valores
                values = []
                for field in fields:
                    value = record.get(field['name'])
                    
                    # Converter tipos de dados
                    if field['type'] == 'int':
                        value = int(value) if value else None
                    elif field['type'] == 'float':
                        value = float(value) if value else None
                    elif field['type'] == 'bool':
                        value = True if value in ['True', 'true', '1', 1] else False
                    elif field['type'] == 'date' and value:
                        # Converter formato de data se necessario
                        if isinstance(value, str):
                            try:
                                datetime.strptime(value, '%Y-%m-%d')
                            except ValueError:
                                value = None
                    
                    values.append(value)
                
                cursor.execute(sql, values)
                inserted_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"    ❌ Erro ao migrar registro: {e}")
    
    print(f"  ✅ {inserted_count} registros migrados, {error_count} erros")

def main():
    """Funcao principal de migracao"""
    print("🚀 Iniciando migracao do SQLite para PostgreSQL...")
    print("=" * 50)
    
    # Testar conexao com PostgreSQL
    if not test_connection():
        print("❌ Nao foi possivel conectar ao PostgreSQL")
        print("   Verifique se o container esta rodando e as configuracoes estao corretas")
        sys.exit(1)
    
    print("✅ Conexao com PostgreSQL estabelecida")
    
    # Carregar dados do SQLite
    print("\n📥 Carregando dados do SQLite...")
    users, tables_metadata, tables_data, config = load_sqlite_data()
    
    if not any([users, tables_metadata, tables_data, config]):
        print("❌ Nenhum dado encontrado para migrar")
        sys.exit(1)
    
    # Migrar dados
    print("\n🔄 Iniciando migracao...")
    
    # Migrar usuarios
    migrate_users(users)
    
    # Migrar metadados das tabelas
    migrate_tables_metadata(tables_metadata)
    
    # Migrar configuracao
    migrate_config(config)
    
    # Criar tabelas dinamicas
    create_dynamic_tables(tables_metadata)
    
    # Migrar dados das tabelas
    for table_name, data in tables_data.items():
        # Encontrar metadados da tabela
        table_meta = next((t for t in tables_metadata if t['name'] == table_name), None)
        if table_meta:
            migrate_table_data(table_name, data, table_meta['fields'])
    
    print("\n🎉 Migracao concluida com sucesso!")
    print("=" * 50)
    print("📝 Resumo da migracao:")
    print(f"   👥 Usuarios: {len(users) if users else 0}")
    print(f"   📋 Tabelas: {len(tables_metadata) if tables_metadata else 0}")
    print(f"   📊 Total de registros: {sum(len(data) for data in tables_data.values()) if tables_data else 0}")
    print(f"   ⚙️  Configuracoes: {len(config) if config else 0}")
    print("\n💡 Agora voce pode remover os arquivos SQLite antigos se desejar")

if __name__ == "__main__":
    main()
