#!/usr/bin/env python3
"""
Exemplo de como conectar ao banco de dados SQLite externamente
Este script demonstra diferentes formas de acessar os dados
"""

import sqlite3
import pandas as pd
import requests
import json
from datetime import datetime

# Configuracao
DB_PATH = "data/data.db"  # Caminho para o arquivo SQLite
API_BASE_URL = "http://localhost:5000/api"  # URL da API

def connect_direct_sqlite():
    """Conecta diretamente ao arquivo SQLite."""
    print("🔗 Conectando diretamente ao SQLite...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Listar todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📊 Tabelas encontradas: {len(tables)}")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   - {table_name}: {count} registros")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False

def connect_via_api():
    """Conecta via API REST."""
    print("\n🌐 Conectando via API REST...")
    
    try:
        # Testar health check
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ API Status: {health['status']}")
            print(f"📅 Timestamp: {health['timestamp']}")
            print(f"🗄️ Database: {health['database']}")
        
        # Listar tabelas
        response = requests.get(f"{API_BASE_URL}/tables")
        if response.status_code == 200:
            data = response.json()
            tables = data['tables']
            print(f"\n📊 Tabelas via API: {len(tables)}")
            for table in tables:
                print(f"   - {table['name']}: {table['row_count']} registros")
        
        # Obter estatisticas
        response = requests.get(f"{API_BASE_URL}/stats")
        if response.status_code == 200:
            stats = response.json()['stats']
            print(f"\n📈 Estatisticas do banco:")
            print(f"   - Total de tabelas: {stats['total_tables']}")
            for table in stats['tables']:
                print(f"   - {table['name']}: {table['row_count']} linhas, {table['column_count']} colunas")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao conectar via API: {e}")
        return False

def export_data_examples():
    """Exemplos de como exportar dados."""
    print("\n📤 Exemplos de exportacao de dados...")
    
    try:
        # Exportar via API
        response = requests.get(f"{API_BASE_URL}/tables")
        if response.status_code == 200:
            tables = response.json()['tables']
            
            if tables:
                table_name = tables[0]['name']
                
                # Exportar CSV
                response = requests.get(f"{API_BASE_URL}/tables/{table_name}/export?format=csv")
                if response.status_code == 200:
                    with open(f"{table_name}_export.csv", "w", encoding="utf-8") as f:
                        f.write(response.text)
                    print(f"✅ CSV exportado: {table_name}_export.csv")
                
                # Exportar JSON
                response = requests.get(f"{API_BASE_URL}/tables/{table_name}/export?format=json")
                if response.status_code == 200:
                    data = response.json()
                    with open(f"{table_name}_export.json", "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"✅ JSON exportado: {table_name}_export.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na exportacao: {e}")
        return False

def custom_query_example():
    """Exemplo de query customizada."""
    print("\n🔍 Exemplo de query customizada...")
    
    try:
        # Query via API
        query_data = {
            "query": "SELECT name FROM sqlite_master WHERE type='table'"
        }
        response = requests.post(f"{API_BASE_URL}/query", json=query_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Query executada: {result['row_count']} resultados")
            for row in result['data']:
                print(f"   - {row['name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na query: {e}")
        return False

def pandas_example():
    """Exemplo usando pandas."""
    print("\n🐼 Exemplo usando pandas...")
    
    try:
        # Conectar diretamente
        conn = sqlite3.connect(DB_PATH)
        
        # Ler dados com pandas
        df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
        print(f"✅ Pandas conectado: {len(df)} tabelas encontradas")
        
        # Se houver tabelas, ler dados da primeira
        if not df.empty:
            table_name = df.iloc[0]['name']
            data_df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5", conn)
            print(f"📊 Primeiros 5 registros de '{table_name}':")
            print(data_df)
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro com pandas: {e}")
        return False

def exemplo_edicao_registro():
    """Exemplo de como editar um registro via API."""
    print("\n=== Exemplo: Editar Registro ===")
    
    # Dados para atualizar
    dados_atualizacao = {
        "nome": "João Silva Atualizado",
        "email": "joao.novo@email.com",
        "idade": 35
    }
    
    # Atualizar registro ID 1 da tabela 'pessoas'
    response = requests.put(
        "http://localhost:5000/api/tables/pessoas/records/1",
        json=dados_atualizacao
    )
    
    if response.status_code == 200:
        print("✅ Registro atualizado com sucesso!")
        print(f"Resposta: {response.json()}")
    else:
        print(f"❌ Erro ao atualizar: {response.json()}")


def exemplo_excluir_registro():
    """Exemplo de como excluir um registro via API."""
    print("\n=== Exemplo: Excluir Registro ===")
    
    # Excluir registro ID 2 da tabela 'pessoas'
    response = requests.delete(
        "http://localhost:5000/api/tables/pessoas/records/2"
    )
    
    if response.status_code == 200:
        print("✅ Registro excluído com sucesso!")
        print(f"Resposta: {response.json()}")
    else:
        print(f"❌ Erro ao excluir: {response.json()}")


def exemplo_obter_registro():
    """Exemplo de como obter um registro específico via API."""
    print("\n=== Exemplo: Obter Registro Específico ===")
    
    # Obter registro ID 1 da tabela 'pessoas'
    response = requests.get(
        "http://localhost:5000/api/tables/pessoas/records/1"
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Registro encontrado!")
        print(f"Dados: {data['record']}")
    else:
        print(f"❌ Erro ao buscar registro: {response.json()}")


def main():
    """Funcao principal."""
    print("🚀 Exemplos de Conexao com Banco de Dados")
    print("=" * 50)
    
    # Testar conexao direta
    connect_direct_sqlite()
    
    # Testar conexao via API
    connect_via_api()
    
    # Exemplos de exportacao
    export_data_examples()
    
    # Exemplo de query customizada
    custom_query_example()
    
    # Exemplo com pandas
    pandas_example()
    
    # Exemplos de edicao e exclusao de registros
    exemplo_edicao_registro()
    exemplo_excluir_registro()
    exemplo_obter_registro()
    
    print("\n" + "=" * 50)
    print("📋 Resumo das formas de acesso:")
    print("1. Direto ao SQLite: sqlite3.connect('data/data.db')")
    print("2. Via API REST: http://localhost:5000/api/")
    print("3. Com pandas: pd.read_sql_query()")
    print("4. DBeaver: Conectar ao arquivo data/data.db")
    print("5. Outros clientes SQLite: SQLite Browser, DB Browser")

if __name__ == "__main__":
    main() 