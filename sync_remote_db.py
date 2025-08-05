#!/usr/bin/env python3
"""
Script para sincronizar banco de dados remoto com local
Permite usar DBeaver com dados da VM remota
"""

import requests
import sqlite3
import pandas as pd
import os
import json
from datetime import datetime
import argparse

class RemoteDatabaseSync:
    def __init__(self, remote_api_url, local_db_path="data_local.db"):
        self.remote_api_url = remote_api_url.rstrip('/')
        self.local_db_path = local_db_path
        self.session = requests.Session()
        
    def test_connection(self):
        """Testa conexao com a API remota."""
        try:
            response = self.session.get(f"{self.remote_api_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Conexao OK: {data['status']}")
                print(f"📅 Timestamp: {data['timestamp']}")
                print(f"🗄️ Database: {data['database']}")
                return True
            else:
                print(f"❌ Erro na conexao: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro ao conectar: {e}")
            return False
    
    def get_tables_info(self):
        """Obtem informacoes das tabelas remotas."""
        try:
            response = self.session.get(f"{self.remote_api_url}/tables")
            if response.status_code == 200:
                data = response.json()
                return data['tables']
            else:
                print(f"❌ Erro ao obter tabelas: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Erro ao obter tabelas: {e}")
            return []
    
    def sync_table(self, table_name, limit=None):
        """Sincroniza uma tabela especifica."""
        try:
            # Construir URL com parametros
            url = f"{self.remote_api_url}/tables/{table_name}"
            params = {}
            if limit:
                params['limit'] = limit
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                records = data['data']
                pagination = data.get('pagination', {})
                
                print(f"📊 Tabela '{table_name}': {len(records)} registros")
                if pagination:
                    print(f"   Total: {pagination.get('total', 'N/A')} registros")
                    print(f"   Paginas: {pagination.get('pages', 'N/A')}")
                
                return records
            else:
                print(f"❌ Erro ao obter dados da tabela {table_name}: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Erro ao sincronizar tabela {table_name}: {e}")
            return []
    
    def create_local_database(self, tables_data):
        """Cria banco de dados local com os dados sincronizados."""
        try:
            # Criar conexao SQLite
            conn = sqlite3.connect(self.local_db_path)
            
            total_records = 0
            
            for table_info in tables_data:
                table_name = table_info['name']
                print(f"\n🔄 Sincronizando tabela: {table_name}")
                
                # Obter dados da tabela
                records = self.sync_table(table_name)
                
                if records:
                    # Converter para DataFrame
                    df = pd.DataFrame(records)
                    
                    # Salvar no banco local
                    df.to_sql(table_name, conn, if_exists='replace', index=False)
                    
                    total_records += len(records)
                    print(f"✅ Tabela '{table_name}' sincronizada: {len(records)} registros")
                else:
                    print(f"⚠️ Tabela '{table_name}' vazia ou erro")
            
            conn.close()
            print(f"\n🎉 Sincronizacao concluida!")
            print(f"📁 Arquivo local: {self.local_db_path}")
            print(f"📊 Total de registros: {total_records}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar banco local: {e}")
            return False
    
    def export_to_csv(self, table_name, output_dir="exports"):
        """Exporta uma tabela para CSV."""
        try:
            # Criar diretorio se nao existir
            os.makedirs(output_dir, exist_ok=True)
            
            # Obter dados da tabela
            records = self.sync_table(table_name)
            
            if records:
                df = pd.DataFrame(records)
                filename = f"{output_dir}/{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                df.to_csv(filename, index=False, encoding='utf-8')
                print(f"✅ CSV exportado: {filename}")
                return filename
            else:
                print(f"❌ Nenhum dado para exportar da tabela {table_name}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao exportar CSV: {e}")
            return None
    
    def get_database_stats(self):
        """Obtem estatisticas do banco remoto."""
        try:
            response = self.session.get(f"{self.remote_api_url}/stats")
            if response.status_code == 200:
                stats = response.json()['stats']
                print(f"\n📈 Estatisticas do Banco Remoto:")
                print(f"   Total de tabelas: {stats['total_tables']}")
                
                for table in stats['tables']:
                    print(f"   - {table['name']}: {table['row_count']} linhas, {table['column_count']} colunas")
                
                return stats
            else:
                print(f"❌ Erro ao obter estatisticas: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Erro ao obter estatisticas: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description='Sincronizar banco de dados remoto')
    parser.add_argument('--api-url', required=True, help='URL da API remota (ex: http://IP_DA_VM:5000/api)')
    parser.add_argument('--local-db', default='data_local.db', help='Caminho do banco local')
    parser.add_argument('--export-csv', help='Exportar tabela especifica para CSV')
    parser.add_argument('--stats-only', action='store_true', help='Apenas mostrar estatisticas')
    parser.add_argument('--test-connection', action='store_true', help='Apenas testar conexao')
    
    args = parser.parse_args()
    
    # Criar instancia do sincronizador
    sync = RemoteDatabaseSync(args.api_url, args.local_db)
    
    print("🚀 Sincronizador de Banco Remoto")
    print("=" * 50)
    print(f"🌐 API Remota: {args.api_url}")
    print(f"📁 Banco Local: {args.local_db}")
    print()
    
    # Testar conexao
    if not sync.test_connection():
        print("❌ Falha na conexao. Verifique a URL da API.")
        return
    
    if args.test_connection:
        print("✅ Teste de conexao concluido.")
        return
    
    # Obter estatisticas
    stats = sync.get_database_stats()
    
    if args.stats_only:
        return
    
    # Exportar CSV especifico
    if args.export_csv:
        sync.export_to_csv(args.export_csv)
        return
    
    # Sincronizar todas as tabelas
    print("\n🔄 Iniciando sincronizacao...")
    tables_info = sync.get_tables_info()
    
    if tables_info:
        success = sync.create_local_database(tables_info)
        if success:
            print(f"\n📋 Para usar no DBeaver:")
            print(f"1. Abra o DBeaver")
            print(f"2. Nova Conexao > SQLite")
            print(f"3. Database: {os.path.abspath(args.local_db)}")
            print(f"4. Test Connection > Finish")
    else:
        print("❌ Nenhuma tabela encontrada para sincronizar.")

if __name__ == "__main__":
    main() 