from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import sqlite3
import json
import os
import pandas as pd
from datetime import datetime
import io
import base64

app = Flask(__name__)
CORS(app)  # Permitir CORS para acesso externo

# Configuracao
DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, "data.db")
USERS_FILE = "users.json"
TABLES_FILE = "tables.json"

def get_db_connection():
    """Retorna conexao com o banco SQLite."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Permite acesso por nome de coluna
    return conn

def load_tables_metadata():
    """Carrega metadados das tabelas."""
    try:
        with open(TABLES_FILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def load_users():
    """Carrega usuarios do sistema."""
    try:
        with open(USERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de health check."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": os.path.exists(DB_PATH)
    })

@app.route('/api/tables', methods=['GET'])
def get_tables():
    """Lista todas as tabelas disponiveis."""
    try:
        metadata = load_tables_metadata()
        tables_info = []
        
        for table in metadata:
            conn = get_db_connection()
            cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table['name']}")
            row_count = cursor.fetchone()['count']
            conn.close()
            
            tables_info.append({
                "name": table['name'],
                "display_name": table.get('display_name', table['name']),
                "fields": table['fields'],
                "row_count": row_count
            })
        
        return jsonify({
            "success": True,
            "tables": tables_info
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/tables/<table_name>', methods=['GET'])
def get_table_data(table_name):
    """Obtem dados de uma tabela especifica."""
    try:
        # Parametros de paginacao
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 100, type=int)
        offset = (page - 1) * limit
        
        # Parametros de filtro
        search = request.args.get('search', '')
        sort_by = request.args.get('sort_by', 'id')
        sort_order = request.args.get('sort_order', 'ASC')
        
        conn = get_db_connection()
        
        # Construir query com filtros
        where_clause = ""
        params = []
        
        if search:
            # Busca em todas as colunas de texto
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            text_columns = [col['name'] for col in columns if col['type'].upper() == 'TEXT']
            
            if text_columns:
                search_conditions = [f"{col} LIKE ?" for col in text_columns]
                where_clause = f"WHERE {' OR '.join(search_conditions)}"
                params = [f"%{search}%" for _ in text_columns]
        
        # Query para contar total de registros
        count_query = f"SELECT COUNT(*) as total FROM {table_name} {where_clause}"
        cursor = conn.execute(count_query, params)
        total_count = cursor.fetchone()['total']
        
        # Query para dados paginados
        data_query = f"""
            SELECT * FROM {table_name} 
            {where_clause}
            ORDER BY {sort_by} {sort_order}
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        cursor = conn.execute(data_query, params)
        rows = cursor.fetchall()
        
        # Converter para dicionarios
        data = []
        for row in rows:
            data.append(dict(row))
        
        conn.close()
        
        return jsonify({
            "success": True,
            "data": data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/tables/<table_name>/export', methods=['GET'])
def export_table(table_name):
    """Exporta dados de uma tabela em diferentes formatos."""
    try:
        format_type = request.args.get('format', 'csv').lower()
        
        conn = get_db_connection()
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        
        if format_type == 'csv':
            output = io.StringIO()
            df.to_csv(output, index=False)
            return output.getvalue(), 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename={table_name}.csv'
            }
        
        elif format_type == 'json':
            return jsonify({
                "success": True,
                "data": df.to_dict('records')
            })
        
        elif format_type == 'excel':
            output = io.BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)
            return output.getvalue(), 200, {
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'Content-Disposition': f'attachment; filename={table_name}.xlsx'
            }
        
        else:
            return jsonify({
                "success": False,
                "error": "Formato nao suportado. Use: csv, json, excel"
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/tables/<table_name>/schema', methods=['GET'])
def get_table_schema(table_name):
    """Obtem o schema de uma tabela."""
    try:
        conn = get_db_connection()
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        conn.close()
        
        schema = []
        for col in columns:
            schema.append({
                "name": col['name'],
                "type": col['type'],
                "not_null": bool(col['notnull']),
                "primary_key": bool(col['pk']),
                "default_value": col['dflt_value']
            })
        
        return jsonify({
            "success": True,
            "table_name": table_name,
            "schema": schema
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_database_stats():
    """Obtem estatisticas do banco de dados."""
    try:
        conn = get_db_connection()
        
        # Listar todas as tabelas
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in cursor.fetchall()]
        
        stats = {
            "total_tables": len(tables),
            "tables": []
        }
        
        for table in tables:
            cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
            row_count = cursor.fetchone()['count']
            
            cursor = conn.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            column_count = len(columns)
            
            stats["tables"].append({
                "name": table,
                "row_count": row_count,
                "column_count": column_count
            })
        
        conn.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/tables/<table_name>/records/<int:record_id>', methods=['PUT'])
def update_record(table_name, record_id):
    """Atualiza um registro especifico."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "Dados nao fornecidos"
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Construir query de UPDATE
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE id = ?"
        
        # Preparar valores
        update_values = list(data.values())
        update_values.append(record_id)
        
        cursor.execute(query, update_values)
        conn.commit()
        
        if cursor.rowcount > 0:
            return jsonify({
                "success": True,
                "message": "Registro atualizado com sucesso",
                "affected_rows": cursor.rowcount
            })
        else:
            return jsonify({
                "success": False,
                "error": "Registro nao encontrado"
            }), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    finally:
        conn.close()


@app.route('/api/tables/<table_name>/records/<int:record_id>', methods=['DELETE'])
def delete_record(table_name, record_id):
    """Exclui um registro especifico."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se o registro existe
        cursor.execute(f"SELECT id FROM {table_name} WHERE id = ?", (record_id,))
        if not cursor.fetchone():
            return jsonify({
                "success": False,
                "error": "Registro nao encontrado"
            }), 404
        
        # Excluir registro
        cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "Registro excluido com sucesso",
            "affected_rows": cursor.rowcount
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    finally:
        conn.close()


@app.route('/api/tables/<table_name>/records/<int:record_id>', methods=['GET'])
def get_record(table_name, record_id):
    """Obtem um registro especifico por ID."""
    try:
        conn = get_db_connection()
        cursor = conn.execute(f"SELECT * FROM {table_name} WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return jsonify({
                "success": True,
                "record": dict(row)
            })
        else:
            return jsonify({
                "success": False,
                "error": "Registro nao encontrado"
            }), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/query', methods=['POST'])
def execute_custom_query():
    """Executa uma query SQL customizada (apenas SELECT)."""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        # Validar se e uma query SELECT
        if not query.upper().startswith('SELECT'):
            return jsonify({
                "success": False,
                "error": "Apenas queries SELECT sao permitidas por seguranca"
            }), 400
        
        conn = get_db_connection()
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        # Converter para dicionarios
        data = []
        for row in rows:
            data.append(dict(row))
        
        return jsonify({
            "success": True,
            "data": data,
            "row_count": len(data)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    # Criar diretorio de dados se nao existir
    os.makedirs(DATA_DIR, exist_ok=True)
    
    print("🚀 API Server iniciando...")
    print(f"📊 Banco de dados: {DB_PATH}")
    print("🌐 Endpoints disponiveis:")
    print("   GET  /api/health - Status do servidor")
    print("   GET  /api/tables - Lista todas as tabelas")
    print("   GET  /api/tables/<nome> - Dados de uma tabela")
    print("   GET  /api/tables/<nome>/records/<id> - Registro especifico")
    print("   PUT  /api/tables/<nome>/records/<id> - Atualizar registro")
    print("   DELETE /api/tables/<nome>/records/<id> - Excluir registro")
    print("   GET  /api/tables/<nome>/export - Exporta dados")
    print("   GET  /api/tables/<nome>/schema - Schema da tabela")
    print("   GET  /api/stats - Estatisticas do banco")
    print("   POST /api/query - Query SQL customizada")
    
    app.run(host='0.0.0.0', port=5000, debug=False) 