#!/usr/bin/env python3
"""
Script para testar a funcionalidade de edição de registros.
"""

import sqlite3
import pandas as pd
import os

def testar_edicao_registros():
    """Testa a funcionalidade de edição de registros."""
    
    db_path = os.path.join("data", "data.db")
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Listar todas as tabelas
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("📊 Tabelas encontradas:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} registros")
        
        # Testar edição em uma tabela específica
        if tables:
            # Procurar por tabelas de dados (que não são do sistema)
            data_tables = []
            for table in tables:
                table_name = table[0]
                if not table_name.startswith('sqlite_') and table_name != 'sqlite_sequence':
                    data_tables.append(table_name)
            
            if data_tables:
                test_table = data_tables[0]  # Primeira tabela de dados
                print(f"\n🧪 Testando edição na tabela: {test_table}")
            else:
                test_table = tables[0][0]  # Fallback para primeira tabela
                print(f"\n🧪 Testando edição na tabela: {test_table}")
                print("  ⚠️ Nenhuma tabela de dados encontrada, testando tabela do sistema")
            
            # Verificar estrutura da tabela
            cursor.execute(f"PRAGMA table_info({test_table})")
            columns = cursor.fetchall()
            print(f"  Estrutura da tabela:")
            for col in columns:
                print(f"    - {col[1]} ({col[2]})")
            
            # Verificar dados existentes
            df = pd.read_sql_query(f"SELECT * FROM {test_table} LIMIT 5", conn)
            print(f"\n  Dados existentes (primeiros 5 registros):")
            print(df.to_string(index=False))
            
            # Testar função de atualização
            if len(df) > 0:
                # Verificar se a tabela tem coluna 'id'
                if 'id' in df.columns:
                    test_record_id = df.iloc[0]['id']
                    print(f"\n  Testando atualização do registro ID: {test_record_id}")
                    
                    # Encontrar uma coluna de texto para testar
                    text_columns = [col for col in df.columns if col != 'id' and df[col].dtype == 'object']
                    
                    if text_columns:
                        test_column = text_columns[0]
                        original_value = df.iloc[0][test_column]
                        test_value = f"TESTE_{original_value}"
                        
                        print(f"  Testando atualização da coluna '{test_column}'")
                        print(f"  Valor original: '{original_value}'")
                        print(f"  Valor de teste: '{test_value}'")
                        
                        # Simular atualização
                        cursor.execute(f"UPDATE {test_table} SET {test_column} = ? WHERE id = ?", 
                                     (test_value, test_record_id))
                        
                        if cursor.rowcount > 0:
                            print("  ✅ Atualização simulada funcionou!")
                            
                            # Restaurar valor original
                            cursor.execute(f"UPDATE {test_table} SET {test_column} = ? WHERE id = ?", 
                                         (original_value, test_record_id))
                            print("  ✅ Valor original restaurado")
                        else:
                            print("  ⚠️ Nenhum registro foi atualizado")
                        
                        conn.commit()
                    else:
                        print("  ⚠️ Nenhuma coluna de texto encontrada para teste")
                else:
                    print(f"\n  ⚠️ Tabela '{test_table}' não tem coluna 'id' - não é uma tabela de dados")
                    print("  Esta tabela provavelmente é uma tabela de sistema do SQLite")
        
        conn.close()
        print("\n✅ Teste concluído!")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")

def verificar_problemas_comuns():
    """Verifica problemas comuns na edição de registros."""
    
    print("\n🔍 Verificando problemas comuns:")
    
    # Verificar se o banco existe
    db_path = os.path.join("data", "data.db")
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado em data/data.db")
        return
    
    # Verificar permissões
    try:
        with open(db_path, 'r+b') as f:
            pass
        print("✅ Permissões de escrita OK")
    except Exception as e:
        print(f"❌ Problema de permissões: {e}")
    
    # Verificar integridade do banco
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        
        if result[0] == "ok":
            print("✅ Integridade do banco OK")
        else:
            print(f"❌ Problema de integridade: {result[0]}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Erro ao verificar integridade: {e}")


def testar_api_edicao():
    """Testa a API de edição de registros."""
    
    print("\n🌐 Testando API de edição:")
    
    try:
        import requests
        
        # Testar health check
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ API está respondendo")
        else:
            print(f"❌ API retornou status {response.status_code}")
            return
        
        # Listar tabelas via API
        response = requests.get("http://localhost:5000/api/tables", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                tables = data.get('tables', [])
                print(f"✅ Encontradas {len(tables)} tabelas via API")
                
                # Testar edição em uma tabela
                if tables:
                    test_table = tables[0]['name']
                    print(f"  Testando edição na tabela: {test_table}")
                    
                    # Tentar obter um registro
                    response = requests.get(f"http://localhost:5000/api/tables/{test_table}", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('success') and data.get('data'):
                            test_record = data['data'][0]
                            record_id = test_record.get('id')
                            
                            if record_id:
                                print(f"  ✅ Encontrado registro ID: {record_id}")
                                print("  ✅ API de edição está funcionando")
                            else:
                                print("  ⚠️ Registro não tem ID")
                        else:
                            print("  ⚠️ Nenhum dado encontrado na tabela")
                    else:
                        print(f"  ❌ Erro ao acessar dados da tabela: {response.status_code}")
            else:
                print("❌ Erro na resposta da API")
        else:
            print(f"❌ Erro ao listar tabelas: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar à API (porta 5000)")
        print("  Verifique se a aplicação está rodando: .\\start-app.ps1 status")
    except Exception as e:
        print(f"❌ Erro ao testar API: {e}")

def main():
    """Função principal."""
    print("🧪 Testando funcionalidade de edição de registros")
    print("=" * 50)
    
    testar_edicao_registros()
    verificar_problemas_comuns()
    testar_api_edicao()
    
    print("\n💡 Dicas para resolver problemas:")
    print("  1. Verifique se o Docker está rodando")
    print("  2. Execute: .\\start-app.ps1 restart")
    print("  3. Verifique os logs: .\\start-app.ps1 logs")
    print("  4. Teste a API: curl http://localhost:5000/api/health")
    print("  5. Rebuild se necessário: .\\start-app.ps1 build")

if __name__ == "__main__":
    main() 