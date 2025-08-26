from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
import os
import pandas as pd
from datetime import datetime
import io
import base64
from database.db_config import get_db_cursor

app = Flask(__name__)
CORS(app)  # Permitir CORS para acesso externo

# Configuracao
DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, "data.db")
USERS_FILE = "users.json"
TABLES_FILE = "tables.json"

def get_db_connection():
    """Retorna conexao com o banco PostgreSQL."""
    from database.db_config import get_db_connection as pg_get_connection
    return pg_get_connection()

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
            with get_db_cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table['name']}")
                row_count = cursor.fetchone()['count']
            
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
            with get_db_cursor() as cursor:
                cursor.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND data_type IN ('character varying', 'text', 'character')
                """, (table_name,))
                columns = cursor.fetchall()
                text_columns = [col['column_name'] for col in columns]
                
                if text_columns:
                    search_conditions = [f"{col} ILIKE %s" for col in text_columns]
                    where_clause = f"WHERE {' OR '.join(search_conditions)}"
                    params = [f"%{search}%" for _ in text_columns]
        
        # Query para contar total de registros
        count_query = f"SELECT COUNT(*) as total FROM {table_name} {where_clause}"
        with get_db_cursor() as cursor:
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()['total']
        
        # Query para dados paginados
        data_query = f"""
            SELECT * FROM {table_name} 
            {where_clause}
            ORDER BY {sort_by} {sort_order}
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        with get_db_cursor() as cursor:
            cursor.execute(data_query, params)
            rows = cursor.fetchall()
        
        # Converter para dicionarios
        data = []
        for row in rows:
            data.append(dict(row))
        
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
        
        with get_db_cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            df = pd.DataFrame(rows)
        
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
        with get_db_cursor() as cursor:
            cursor.execute(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            columns = cursor.fetchall()
        
        schema = []
        for col in columns:
            schema.append({
                "name": col['column_name'],
                "type": col['data_type'],
                "not_null": col['is_nullable'] == 'NO',
                "primary_key": False,  # PostgreSQL nao fornece isso diretamente
                "default_value": col['column_default']
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
        # Listar todas as tabelas
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row['table_name'] for row in cursor.fetchall()]
        
        stats = {
            "total_tables": len(tables),
            "tables": []
        }
        
        for table in tables:
            with get_db_cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                row_count = cursor.fetchone()['count']
                
                cursor.execute(f"""
                    SELECT COUNT(*) as column_count
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public'
                """, (table,))
                column_count = cursor.fetchone()['column_count']
                
                stats["tables"].append({
                    "name": table,
                    "row_count": row_count,
                    "column_count": column_count
                })
        
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
        
        # Construir query de UPDATE
        set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE id = %s"
        
        # Preparar valores
        update_values = list(data.values())
        update_values.append(record_id)
        
        with get_db_cursor() as cursor:
            cursor.execute(query, update_values)
            
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
        with get_db_cursor() as cursor:
            cursor.execute(f"DELETE FROM {table_name} WHERE id = %s", (record_id,))
            
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


@app.route('/api/tables/<table_name>/records/<int:record_id>', methods=['GET'])
def get_record(table_name, record_id):
    """Obtem um registro especifico por ID."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s", (record_id,))
            row = cursor.fetchone()
        
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
        
        with get_db_cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
        
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
    print("📊 Banco de dados: PostgreSQL")
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