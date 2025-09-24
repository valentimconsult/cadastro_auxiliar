import streamlit as st
import os
import json
import hashlib
import pandas as pd
from datetime import datetime
import io
import base64
from PIL import Image
import psycopg2
from database.db_config import get_db_connection, get_db_cursor, db_config
from database.grants_manager import grants_manager


# Paths for configuration and data.  The app writes all of its state into
# PostgreSQL database.  Configuration files are minimal and only for UI elements.
DATA_DIR = "data"
CONFIG_FILE = "config.json"

os.makedirs(DATA_DIR, exist_ok=True)

# Create the initial configuration file if it is missing.
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"logo": ""}, f)


def hash_password(password: str) -> str:
    """Return a SHA‑256 hash of the provided password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def load_users() -> dict:
    """Load the user database from the PostgreSQL database."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT username, password, role, status FROM users ORDER BY username")
            users = {}
            for row in cursor.fetchall():
                users[row['username']] = {
                    'password': row['password'],
                    'role': row['role'],
                    'status': row['status']
                }
            return users
    except Exception as e:
        st.error(f"Erro ao carregar usuários do banco: {e}")
        return {}


def toggle_user_status(username: str, new_status: str) -> dict:
    """Ativar ou inativar usuário no banco de dados."""
    if new_status not in ['ativo', 'inativo']:
        raise ValueError("Status deve ser 'ativo' ou 'inativo'")
    
    results = {
        'user_id': None,
        'username': username,
        'old_status': None,
        'new_status': new_status,
        'success': False,
        'errors': []
    }
    
    try:
        with get_db_cursor() as cursor:
            # 1. Verificar se usuário existe e obter status atual
            cursor.execute("SELECT id, status FROM users WHERE username = %s", (username,))
            user_row = cursor.fetchone()
            if not user_row:
                raise ValueError(f"Usuário '{username}' não encontrado na tabela users")
            
            user_id = user_row['id']
            old_status = user_row['status']
            results['user_id'] = user_id
            results['old_status'] = old_status
            
            print(f"✅ Usuário '{username}' encontrado com ID: {user_id}, status atual: {old_status}")
            
            # 2. Atualizar status do usuário
            cursor.execute("UPDATE users SET status = %s, updated_at = NOW() WHERE username = %s", (new_status, username))
            updated_rows = cursor.rowcount
            
            if updated_rows > 0:
                results['success'] = True
                print(f"✅ Usuário '{username}' {new_status} com sucesso!")
            else:
                raise Exception(f"Falha ao atualizar status do usuário '{username}'")
            
            # 3. Verificar se realmente foi atualizado
            cursor.execute("SELECT status FROM users WHERE username = %s", (username,))
            updated_user = cursor.fetchone()
            if updated_user and updated_user['status'] != new_status:
                raise Exception(f"Falha: Status do usuário '{username}' não foi atualizado corretamente")
                
    except Exception as e:
        error_msg = f"Erro ao alterar status do usuário {username}: {e}"
        results['errors'].append(error_msg)
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        raise
    
    return results


def save_users(users: dict) -> None:
    """Persist the user database to PostgreSQL database and create PostgreSQL users."""
    try:
        with get_db_cursor() as cursor:
            for username, user_data in users.items():
                # Salvar no banco de dados da aplicação
                cursor.execute("""
                    INSERT INTO users (username, password, role)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (username) 
                    DO UPDATE SET 
                        password = EXCLUDED.password,
                        role = EXCLUDED.role,
                        updated_at = CURRENT_TIMESTAMP
                """, (username, user_data['password'], user_data['role']))
                
                # Criar usuário no PostgreSQL com grants
                try:
                    # Gerar senha para o usuário PostgreSQL (usar hash da senha da aplicação)
                    pg_password = user_data['password'][:20]  # Usar parte do hash como senha
                    
                    # Criar usuário no PostgreSQL
                    grants_manager.create_database_user(
                        username=username,
                        password=pg_password,
                        role=user_data['role']
                    )
                    
                    # Aplicar permissões gerais
                    grants_manager.grant_general_permissions(
                        username=username,
                        can_create_tables=(user_data['role'] == 'admin')
                    )
                    
                except Exception as e:
                    print(f"Aviso: Não foi possível criar usuário PostgreSQL para {username}: {e}")
                    
    except Exception as e:
        st.error(f"Erro ao salvar usuários no banco: {e}")
        raise


def apply_auto_permissions_for_existing_tables(username: str) -> None:
    """Aplica permissões automáticas para um usuário em todas as tabelas existentes."""
    try:
        # Obter ID do usuário
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user_row = cursor.fetchone()
            if not user_row:
                return
            
            user_id = user_row['id']
            
            # Obter todas as tabelas ativas
            cursor.execute("SELECT table_name FROM tables_metadata WHERE status = 'ativo'")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table['table_name']
                
                # Aplicar permissões automáticas: visualizar, inserir, editar
                cursor.execute("""
                    INSERT INTO user_table_permissions (user_id, table_name, can_view, can_insert, can_update, can_delete)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, table_name)
                    DO UPDATE SET
                        can_view = EXCLUDED.can_view,
                        can_insert = EXCLUDED.can_insert,
                        can_update = EXCLUDED.can_update,
                        can_delete = EXCLUDED.can_delete,
                        granted_at = CURRENT_TIMESTAMP
                """, (user_id, table_name, True, True, True, False))  # can_delete = False por padrão
            
            print(f"✅ Permissões automáticas aplicadas para {username} em {len(tables)} tabelas existentes")
            
    except Exception as e:
        print(f"❌ Erro ao aplicar permissões automáticas para {username} nas tabelas existentes: {e}")


def apply_auto_permissions_for_table_creator(username: str, table_name: str) -> None:
    """Aplica permissões automáticas para o criador da tabela se ele tem permissão geral de criar tabelas."""
    try:
        # Verificar se o usuário tem permissão geral de criar tabelas
        if not check_user_general_permission(username, "create_tables"):
            return
        
        # Obter ID do usuário
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user_row = cursor.fetchone()
            if not user_row:
                return
            
            user_id = user_row['id']
            
            # Aplicar permissões automáticas: visualizar, inserir, editar
            cursor.execute("""
                INSERT INTO user_table_permissions (user_id, table_name, can_view, can_insert, can_update, can_delete)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, table_name)
                DO UPDATE SET
                    can_view = EXCLUDED.can_view,
                    can_insert = EXCLUDED.can_insert,
                    can_update = EXCLUDED.can_update,
                    can_delete = EXCLUDED.can_delete,
                    granted_at = CURRENT_TIMESTAMP
            """, (user_id, table_name, True, True, True, False))  # can_delete = False por padrão
            
            print(f"✅ Permissões automáticas aplicadas para {username} na tabela {table_name}")
            
    except Exception as e:
        print(f"❌ Erro ao aplicar permissões automáticas para {username}: {e}")


def toggle_table_status(table_name: str, new_status: str) -> dict:
    """Ativar ou inativar tabela no banco de dados."""
    if new_status not in ['ativo', 'inativo']:
        raise ValueError("Status deve ser 'ativo' ou 'inativo'")
    
    results = {
        'table_id': None,
        'table_name': table_name,
        'old_status': None,
        'new_status': new_status,
        'success': False,
        'errors': []
    }
    
    try:
        with get_db_cursor() as cursor:
            # 1. Verificar se tabela existe e obter status atual
            cursor.execute("SELECT id, status FROM tables_metadata WHERE table_name = %s", (table_name,))
            table_row = cursor.fetchone()
            if not table_row:
                raise ValueError(f"Tabela '{table_name}' não encontrada na tabela tables_metadata")
            
            table_id = table_row['id']
            old_status = table_row['status']
            results['table_id'] = table_id
            results['old_status'] = old_status
            
            print(f"✅ Tabela '{table_name}' encontrada com ID: {table_id}, status atual: {old_status}")
            
            # 2. Atualizar status da tabela
            cursor.execute("UPDATE tables_metadata SET status = %s, updated_at = NOW() WHERE table_name = %s", (new_status, table_name))
            updated_rows = cursor.rowcount
            
            if updated_rows > 0:
                results['success'] = True
                print(f"✅ Tabela '{table_name}' {new_status} com sucesso!")
            else:
                raise Exception(f"Falha ao atualizar status da tabela '{table_name}'")
            
            # 3. Verificar se realmente foi atualizado
            cursor.execute("SELECT status FROM tables_metadata WHERE table_name = %s", (table_name,))
            updated_table = cursor.fetchone()
            if updated_table and updated_table['status'] != new_status:
                raise Exception(f"Falha: Status da tabela '{table_name}' não foi atualizado corretamente")
                
    except Exception as e:
        error_msg = f"Erro ao alterar status da tabela {table_name}: {e}"
        results['errors'].append(error_msg)
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
    
    return results


def load_tables_metadata(include_inactive: bool = False) -> list:
    """Load the table definitions from the database."""
    try:
        with get_db_cursor() as cursor:
            if include_inactive:
                # Carregar todas as tabelas (ativas e inativas) - para administradores
                cursor.execute("""
                    SELECT id, table_name, display_name, description, columns, status, created_at, updated_at
                    FROM tables_metadata
                    ORDER BY created_at
                """)
            else:
                # Carregar apenas tabelas ativas - para usuarios normais
                cursor.execute("""
                    SELECT id, table_name, display_name, description, columns, status, created_at, updated_at
                    FROM tables_metadata
                    WHERE status = 'ativo'
                    ORDER BY created_at
                """)
            
            metadata = []
            for row in cursor.fetchall():
                table_id = row['id']
                table_name = row['table_name']
                display_name = row['display_name']
                description = row['description']
                columns = row['columns']
                status = row['status']
                created_at = row['created_at']
                updated_at = row['updated_at']
                
                # Converter JSONB para lista de campos
                fields = []
                if columns:
                    # PostgreSQL JSONB já vem como dict/list, não precisa fazer parse
                    if isinstance(columns, list):
                        # Processar lista de campos
                        for field in columns:
                            if isinstance(field, dict):
                                fields.append({
                                    'name': field.get('name', ''),
                                    'type': field.get('type', 'text')
                                })
                            else:
                                print(f"Campo invalido na tabela {table_name}: {field} (tipo: {type(field)})")
                    elif isinstance(columns, dict):
                        # Se for dict único, converter para lista
                        fields.append({
                            'name': columns.get('name', ''),
                            'type': columns.get('type', 'text')
                        })
                    elif isinstance(columns, str):
                        # Se for string, tentar fazer parse do JSON
                        try:
                            columns_parsed = json.loads(columns)
                            if isinstance(columns_parsed, list):
                                for field in columns_parsed:
                                    if isinstance(field, dict):
                                        fields.append({
                                            'name': field.get('name', ''),
                                            'type': field.get('type', 'text')
                                        })
                            elif isinstance(columns_parsed, dict):
                                fields.append({
                                    'name': columns_parsed.get('name', ''),
                                    'type': columns_parsed.get('type', 'text')
                                })
                        except json.JSONDecodeError as e:
                            print(f"Erro ao fazer parse JSON da tabela {table_name}: {e}")
                            # Se falhar no parse, pular esta tabela mas continuar
                            continue
                    else:
                        print(f"Formato invalido de campos na tabela {table_name}. Esperado: list/dict, Recebido: {type(columns)}")
                else:
                    print(f"Tabela {table_name} nao tem campos definidos")
                
                metadata.append({
                    'id': table_id,
                    'name': table_name,
                    'display_name': display_name or table_name,
                    'description': description,
                    'fields': fields,
                    'status': status,
                    'created_at': created_at.isoformat() if created_at else None,
                    'updated_at': updated_at.isoformat() if updated_at else None
                })
            
            return metadata
            
    except Exception as e:
        print(f"Erro ao carregar metadados do banco: {e}")
        import traceback
        traceback.print_exc()
        return []


def refresh_table_metadata(table_name: str) -> dict:
    """Recarrega os metadados de uma tabela específica do banco."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT id, table_name, display_name, description, columns, created_at, updated_at
                FROM tables_metadata
                WHERE table_name = %s
            """, (table_name,))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            # Converter JSONB para lista de campos
            fields = []
            columns = row['columns']
            if columns and isinstance(columns, list):
                for field in columns:
                    if isinstance(field, dict):
                        fields.append({
                            'name': field.get('name', ''),
                            'type': field.get('type', 'text')
                        })
            
            return {
                'id': row['id'],
                'name': row['table_name'],
                'display_name': row['display_name'] or row['table_name'],
                'description': row['description'],
                'fields': fields,
                'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None
            }
            
    except Exception as e:
        print(f"Erro ao recarregar metadados da tabela {table_name}: {e}")
        return None


def sync_table_structure_with_metadata(table_name: str) -> bool:
    """Sincroniza a estrutura real da tabela com os metadados automaticamente."""
    try:
        with get_db_cursor() as cursor:
            # Buscar colunas reais da tabela
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = %s AND column_name != 'id'
                ORDER BY ordinal_position
            """, (table_name,))
            
            real_columns = cursor.fetchall()
            
            # Buscar metadados atuais
            cursor.execute("SELECT columns FROM tables_metadata WHERE table_name = %s", (table_name,))
            result = cursor.fetchone()
            
            if not result:
                return False
                
            current_fields = result['columns'] or []
            current_field_names = [f['name'] for f in current_fields]
            
            # Mapear tipos de dados
            type_mapping = {
                'text': 'text',
                'character varying': 'text',
                'varchar': 'text',
                'integer': 'int',
                'bigint': 'int',
                'real': 'float',
                'double precision': 'float',
                'numeric': 'float',
                'date': 'date',
                'timestamp': 'date',
                'boolean': 'bool'
            }
            
            # Verificar se há colunas novas na tabela que não estão nos metadados
            updated = False
            for col in real_columns:
                col_name = col['column_name']
                col_type = type_mapping.get(col['data_type'], 'text')
                
                if col_name not in current_field_names:
                    # Adicionar nova coluna aos metadados
                    current_fields.append({
                        'name': col_name,
                        'type': col_type
                    })
                    updated = True
                    print(f"Coluna {col_name} adicionada aos metadados automaticamente")
            
            # Atualizar metadados se houve mudanças
            if updated:
                cursor.execute("""
                    UPDATE tables_metadata 
                    SET columns = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE table_name = %s
                """, (json.dumps(current_fields), table_name))
                print(f"Metadados da tabela {table_name} sincronizados com sucesso")
                return True
                
            return False
            
    except Exception as e:
        print(f"Erro ao sincronizar estrutura da tabela {table_name}: {e}")
        return False


def save_tables_metadata(metadata: list) -> None:
    """Save the table definitions to the database."""
    try:
        with get_db_cursor() as cursor:
            for table_meta in metadata:
                # Converter campos para JSONB
                columns_json = json.dumps(table_meta['fields'])
                
                # Inserir ou atualizar metadados
                cursor.execute("""
                    INSERT INTO tables_metadata (table_name, display_name, description, columns, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (table_name) 
                    DO UPDATE SET 
                        display_name = EXCLUDED.display_name,
                        description = EXCLUDED.description,
                        columns = EXCLUDED.columns,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    table_meta['name'],
                    table_meta.get('display_name', table_meta['name']),
                    table_meta.get('description', ''),
                    columns_json,
                    table_meta.get('created_at'),
                    table_meta.get('updated_at')
                ))
            
            st.success("Metadados salvos no banco com sucesso!")
            
    except Exception as e:
        st.error(f"Erro ao salvar metadados no banco: {e}")
        raise


def load_config() -> dict:
    """Load configuration such as the logo path."""
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg: dict) -> None:
    """Persist configuration to disk."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def resize_logo_if_needed(logo_path: str, max_width: int = 300, max_height: int = 200) -> str:
    """Redimensiona a logo se ela for muito grande."""
    try:
        with Image.open(logo_path) as img:
            # Verificar se precisa redimensionar
            if img.width <= max_width and img.height <= max_height:
                return logo_path
            
            # Calcular novas dimensões mantendo proporção
            ratio = min(max_width / img.width, max_height / img.height)
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)
            
            # Redimensionar
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Salvar versão redimensionada
            resized_path = logo_path.replace('.', '_resized.')
            resized_img.save(resized_path, quality=95, optimize=True)
            
            return resized_path
    except Exception as e:
        st.warning(f"Erro ao redimensionar logo: {e}")
        return logo_path


def get_db_connection():
    """Return a connection to the PostgreSQL database."""
    from database.db_config import get_db_connection as pg_get_connection
    return pg_get_connection()


def sanitize_identifier(name: str) -> str:
    """
    Convert a human‑supplied table or column name into a safe SQL identifier.
    This replaces spaces with underscores, converts to lower case and removes
    characters that are not alphanumeric or underscores.  The resulting
    identifier should always be safe to use directly in SQL statements.
    """
    name = name.strip().lower().replace(" ", "_")
    allowed = []
    for c in name:
        if c.isalnum() or c == "_":
            allowed.append(c)
        else:
            allowed.append("_")
    # Ensure the identifier does not start with a number
    sanitized = "".join(allowed)
    if sanitized and sanitized[0].isdigit():
        sanitized = f"_{sanitized}"
    return sanitized


def create_sql_table(table_name: str, fields: list) -> None:
    """Create a new table in the PostgreSQL database with the given fields.

    Each field in the list should be a dict with keys 'name' and 'type'
    where 'type' is one of 'text', 'int', 'float', 'date' or 'bool'.  A
    primary key column named "id" with auto incrementing integers is always
    added automatically.
    """
    with get_db_cursor() as cursor:
        columns = ["id SERIAL PRIMARY KEY"]
        type_map = {
            "text": "TEXT",
            "int": "INTEGER",
            "float": "REAL",
            "date": "DATE",
            "bool": "BOOLEAN",
        }
        for field in fields:
            col_name = sanitize_identifier(field['name'])
            sql_type = type_map.get(field['type'], "TEXT")
            columns.append(f"{col_name} {sql_type}")
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)});"
        cursor.execute(sql)


def insert_record(table_name: str, fields: list, values: dict) -> None:
    """Insert a new record into the specified table.

    `fields` is the list of field definitions from the metadata; `values` is
    a dictionary mapping the field names (not SQL names) to values entered
    by the user.
    """
    with get_db_cursor() as cursor:
        # Build column and placeholder lists skipping the id column.
        column_names = []
        placeholders = []
        value_list = []
        for field in fields:
            fname = field['name']
            sql_name = sanitize_identifier(fname)
            column_names.append(sql_name)
            placeholders.append("%s")
            value_list.append(values.get(fname))
        sql = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({', '.join(placeholders)})"
        cursor.execute(sql, value_list)


def insert_batch_records(table_name: str, fields: list, records: list) -> tuple:
    """Insert multiple records into the specified table with duplicate checking using PostgreSQL.
    
    Returns a tuple (inserted_count, duplicate_count, errors)
    """
    inserted_count = 0
    duplicate_count = 0
    errors = []
    
    if not records:
        return 0, 0, errors
    
    # Build column names
    column_names = []
    for field in fields:
        fname = field['name']
        sql_name = sanitize_identifier(fname)
        column_names.append(sql_name)
    
    try:
        with get_db_cursor() as cursor:
            # Usar UPSERT do PostgreSQL para verificar duplicatas de forma eficiente
            # Criar uma tabela temporária para os novos dados
            temp_table = f"temp_import_{table_name}_{hash(str(records)) % 10000}"
            
            # Criar tabela temporária com a mesma estrutura
            create_temp_sql = f"""
                CREATE TEMP TABLE {temp_table} (
                    {', '.join([f"{col} TEXT" for col in column_names])}
                )
            """
            cursor.execute(create_temp_sql)
            
            # Inserir dados na tabela temporária
            placeholders = ["%s"] * len(column_names)
            insert_temp_sql = f"INSERT INTO {temp_table} ({', '.join(column_names)}) VALUES ({', '.join(placeholders)})"
            
            for i, record in enumerate(records):
                try:
                    # Prepare values for this record
                    value_list = []
                    for field in fields:
                        fname = field['name']
                        value = record.get(fname)
                        
                        # Convert data types
                        if field['type'] == 'int':
                            value = int(value) if value else None
                        elif field['type'] == 'float':
                            value = float(value) if value else None
                        elif field['type'] == 'bool':
                            value = True if value in ['True', 'true', '1', 1] else False
                        
                        # Converter para string para a tabela temporária
                        value_list.append(str(value) if value is not None else None)
                    
                    cursor.execute(insert_temp_sql, value_list)
                    
                except Exception as e:
                    errors.append(f"Erro na linha {i+1}: {e}")
            
            # Verificar duplicatas usando JOIN
            # Construir condição de JOIN baseada nas colunas (excluindo ID)
            # Com conversao de tipos para evitar erro real = text
            join_conditions = []
            for i, col in enumerate(column_names):
                field = fields[i]
                if field['type'] in ['int', 'float']:
                    # Para campos numericos, converter temp para o tipo correto
                    join_conditions.append(f"t.{col} = temp.{col}::{field['type']}")
                elif field['type'] == 'date':
                    # Para campos de data, converter temp para DATE
                    join_conditions.append(f"t.{col} = temp.{col}::DATE")
                else:
                    # Para campos de texto, comparacao direta
                    join_conditions.append(f"t.{col} = temp.{col}")
            
            # Contar duplicatas
            count_duplicates_sql = f"""
                SELECT COUNT(*) as duplicate_count
                FROM {temp_table} temp
                INNER JOIN {table_name} t ON {' AND '.join(join_conditions)}
            """
            cursor.execute(count_duplicates_sql)
            duplicate_count = cursor.fetchone()['duplicate_count']
            
            # Inserir apenas registros não duplicados
            # Construir SELECT com conversao de tipos para campos numericos e datas
            select_columns = []
            for i, col in enumerate(column_names):
                field = fields[i]
                if field['type'] in ['int', 'float']:
                    # Converter campos numericos da tabela temporaria
                    select_columns.append(f"temp.{col}::{field['type']} as {col}")
                elif field['type'] == 'date':
                    # Converter campos de data da tabela temporaria
                    select_columns.append(f"temp.{col}::DATE as {col}")
                else:
                    # Campos de texto sem conversao
                    select_columns.append(f"temp.{col}")
            
            insert_new_sql = f"""
                INSERT INTO {table_name} ({', '.join(column_names)})
                SELECT {', '.join(select_columns)}
                FROM {temp_table} temp
                WHERE NOT EXISTS (
                    SELECT 1 FROM {table_name} t 
                    WHERE {' AND '.join(join_conditions)}
                )
            """
            cursor.execute(insert_new_sql)
            inserted_count = cursor.rowcount
            
            # Limpar tabela temporária
            cursor.execute(f"DROP TABLE {temp_table}")
            
    except Exception as e:
        errors.append(f"Erro ao processar importação: {e}")
        return 0, 0, errors
    
    return inserted_count, duplicate_count, errors


def generate_template_csv(table_meta: dict) -> str:
    """Generate a CSV template for the given table."""
    # Create a DataFrame with column headers
    headers = [field['name'] for field in table_meta['fields']]
    df = pd.DataFrame(columns=headers)
    
    # Add example row with better examples
    example_row = {}
    for field in table_meta['fields']:
        if field['type'] == 'text':
            example_row[field['name']] = 'Exemplo de texto'
        elif field['type'] == 'int':
            example_row[field['name']] = 123
        elif field['type'] == 'float':
            example_row[field['name']] = 123.45
        elif field['type'] == 'date':
            example_row[field['name']] = '2024-01-15'  # Formato recomendado
        elif field['type'] == 'bool':
            example_row[field['name']] = 'True'
    
    # Add second row with alternative examples for dates
    alternative_row = {}
    for field in table_meta['fields']:
        if field['type'] == 'text':
            alternative_row[field['name']] = 'Segundo exemplo'
        elif field['type'] == 'int':
            alternative_row[field['name']] = 456
        elif field['type'] == 'float':
            alternative_row[field['name']] = 99.99
        elif field['type'] == 'date':
            alternative_row[field['name']] = '15/01/2024'  # Formato alternativo brasileiro
        elif field['type'] == 'bool':
            alternative_row[field['name']] = 'False'
    
    df = pd.DataFrame([example_row, alternative_row])
    return df.to_csv(index=False, encoding='utf-8')


def validate_csv_data(df: pd.DataFrame, table_meta: dict) -> tuple:
    """Validate CSV data against table schema.
    
    Returns (is_valid, errors, validated_records)
    """
    errors = []
    validated_records = []
    
    # Check if all required columns are present
    required_columns = {field['name'] for field in table_meta['fields']}
    csv_columns = set(df.columns)
    
    missing_columns = required_columns - csv_columns
    extra_columns = csv_columns - required_columns
    
    if missing_columns:
        errors.append(f"Colunas faltando: {', '.join(missing_columns)}")
    
    if extra_columns:
        errors.append(f"Colunas extras (serao ignoradas): {', '.join(extra_columns)}")
    
    # Validate data types for each row
    for index, row in df.iterrows():
        row_errors = []
        validated_record = {}
        
        for field in table_meta['fields']:
            field_name = field['name']
            value = row.get(field_name)
            
            # Validate data type
            if field['type'] == 'int':
                try:
                    if pd.isna(value) or value == '':
                        validated_record[field_name] = None
                    else:
                        validated_record[field_name] = int(value)
                except (ValueError, TypeError):
                    row_errors.append(f"Campo '{field_name}' deve ser um numero inteiro")
            elif field['type'] == 'float':
                try:
                    if pd.isna(value) or value == '':
                        validated_record[field_name] = None
                    else:
                        validated_record[field_name] = float(value)
                except (ValueError, TypeError):
                    row_errors.append(f"Campo '{field_name}' deve ser um numero decimal")
            elif field['type'] == 'bool':
                if pd.isna(value) or value == '':
                    validated_record[field_name] = None
                else:
                    validated_record[field_name] = str(value).lower() in ['true', '1', 'sim', 'yes']
            elif field['type'] == 'date':
                if pd.isna(value) or value == '':
                    validated_record[field_name] = None
                else:
                    try:
                        # Tentar converter diferentes formatos de data
                        date_str = str(value).strip()
                        
                        # Formatos aceitos: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY
                        if '/' in date_str:
                            # Formato DD/MM/YYYY ou MM/DD/YYYY
                            parts = date_str.split('/')
                            if len(parts) == 3:
                                day, month, year = parts
                                # Assumir formato DD/MM/YYYY (brasileiro)
                                if len(day) <= 2 and len(month) <= 2 and len(year) == 4:
                                    validated_record[field_name] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                else:
                                    validated_record[field_name] = date_str
                            else:
                                validated_record[field_name] = date_str
                        elif '-' in date_str and len(date_str.split('-')) == 3:
                            # Formato YYYY-MM-DD ou DD-MM-YYYY
                            parts = date_str.split('-')
                            if len(parts[0]) == 4:  # YYYY-MM-DD
                                validated_record[field_name] = date_str
                            else:  # DD-MM-YYYY
                                day, month, year = parts
                                validated_record[field_name] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        else:
                            # Tentar parse automático com pandas
                            parsed_date = pd.to_datetime(date_str)
                            validated_record[field_name] = parsed_date.strftime('%Y-%m-%d')
                    except:
                        row_errors.append(f"Campo '{field_name}' deve ser uma data válida (formato: YYYY-MM-DD, DD/MM/YYYY)")
            else:  # text
                validated_record[field_name] = str(value) if not pd.isna(value) else None
        
        if row_errors:
            errors.append(f"Linha {index + 1}: {'; '.join(row_errors)}")
        else:
            validated_records.append(validated_record)
    
    return len(errors) == 0, errors, validated_records


def update_record(table_name: str, record_id: int, values: dict) -> bool:
    """Atualiza um registro existente."""
    try:
        with get_db_cursor() as cursor:
            # Construir query de UPDATE
            set_clause = ", ".join([f"{key} = %s" for key in values.keys()])
            query = f"UPDATE {table_name} SET {set_clause} WHERE id = %s"
            
            # Preparar valores (excluir ID dos valores a atualizar)
            update_values = list(values.values())
            update_values.append(record_id)
            
            # Executar update
            cursor.execute(query, update_values)
            
            if cursor.rowcount > 0:
                return True
            else:
                st.warning("Nenhum registro foi atualizado. Verifique se o ID existe.")
                return False
                
    except Exception as e:
        st.error(f"Erro ao atualizar registro: {e}")
        return False


def drop_table(table_name: str) -> None:
    """Drop the specified table from the database."""
    with get_db_cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")


def alter_table_add_column(table_name: str, field_def: dict) -> None:
    """Adiciona uma nova coluna a uma tabela existente."""
    try:
        with get_db_cursor() as cursor:
            # Mapear tipos de dados
            type_map = {
                "text": "TEXT",
                "int": "INTEGER",
                "float": "REAL",
                "date": "DATE",
                "bool": "BOOLEAN",
            }
            
            # Obter nome da coluna sanitizado
            col_name = sanitize_identifier(field_def['name'])
            sql_type = type_map.get(field_def['type'], "TEXT")
            
            # Executar ALTER TABLE
            sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {sql_type}"
            cursor.execute(sql)
            
            st.success(f"Coluna '{field_def['name']}' adicionada com sucesso!")
            
    except Exception as e:
        st.error(f"Erro ao adicionar coluna: {e}")
        raise


def login_screen() -> None:
    """Render the login form.  If authentication succeeds the user state is
    updated and the page is reloaded.
    """
    st.title("Sistema de Cadastros Auxiliares")
    st.subheader("Autenticação")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        users = load_users()
        if username in users and users[username]["password"] == hash_password(password):
            # Verificar se o usuário está ativo
            user_status = users[username].get("status", "ativo")
            if user_status == "ativo":
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = users[username].get("role", "user")
                st.rerun()
            else:
                st.error("❌ Usuário inativo. Entre em contato com o administrador.")
        else:
            st.error("❌ Usuário ou senha incorretos.")


def page_create_table() -> None:
    """Render the page that allows administrators to define new tables."""
    # Verificar permissão de criação de tabelas
    username = st.session_state.get("username", "")
    if not check_user_general_permission(username, "create_tables"):
        st.error("Você não tem permissão para criar tabelas. Entre em contato com o administrador.")
        return
    
    st.header("Criar nova tabela")
    st.info(
        "Informe o nome da tabela e a quantidade de campos. Em seguida, defina o nome "
        "e o tipo de cada campo. Um campo 'id' será criado automaticamente como chave primária."
    )
    table_display_name = st.text_input("Nome descritivo da tabela", key="table_display_name")
    if table_display_name:
        # Suggest a sanitized name preview for the user
        st.write(f"Identificador interno sugerido: `{sanitize_identifier(table_display_name)}`")
    num_fields = st.number_input(
        "Quantidade de campos", min_value=1, value=1, step=1, format="%d", key="num_fields"
    )
    field_defs = []
    # Loop through the number of fields and build the UI components for each
    for i in range(int(num_fields)):
        col1, col2 = st.columns(2)
        fname = col1.text_input(f"Nome do campo {i+1}", key=f"field_name_{i}")
        ftype = col2.selectbox(
            f"Tipo do campo {i+1}",
            options=["Texto", "Número Inteiro", "Número Decimal", "Data", "Booleano"],
            key=f"field_type_{i}"
        )
        if fname:
            canonical_type = {
                "Texto": "text",
                "Número Inteiro": "int",
                "Número Decimal": "float",
                "Data": "date",
                "Booleano": "bool",
            }[ftype]
            field_defs.append({"name": fname, "type": canonical_type})
    if st.button("Criar tabela"):
        if not table_display_name:
            st.error("O nome da tabela é obrigatório.")
            return
        # Ensure all field names are provided
        missing = [f for f in field_defs if not f["name"]]
        if missing:
            st.error("Todos os campos devem ter um nome.")
            return
        # Prepare names
        table_name = sanitize_identifier(table_display_name)
        # Load metadata and check uniqueness
        metadata = load_tables_metadata()
        existing_names = [t['name'] for t in metadata]
        if table_name in existing_names:
            st.error("Já existe uma tabela com esse nome interno. Escolha outro nome.")
            return
        # Save to database and metadata
        try:
            create_sql_table(table_name, field_defs)
        except Exception as e:
            st.error(f"Erro ao criar a tabela: {e}")
            return
        # Salvar metadados no banco
        table_metadata = {
            "name": table_name,
            "display_name": table_display_name,
            "fields": field_defs,
            "created_at": datetime.now().isoformat(),
        }
        
        # Inserir metadados diretamente no banco
        try:
            with get_db_cursor() as cursor:
                columns_json = json.dumps(field_defs)
                cursor.execute("""
                    INSERT INTO tables_metadata (table_name, display_name, columns, status, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (table_name, table_display_name, columns_json, 'ativo', datetime.now()))
                
                # Aplicar permissões automáticas para o criador da tabela
                apply_auto_permissions_for_table_creator(username, table_name)
                
                st.success("Tabela criada com sucesso!")
                st.info("Permissões automáticas aplicadas: Visualizar, Inserir e Editar")
        except Exception as e:
            st.error(f"Erro ao salvar metadados: {e}")
            return


def page_manage_tables() -> None:
    """Render the page for managing existing tables: viewing data, adding
    records, altering structure or deleting tables."""
    st.header("Gerenciar tabelas existentes")
    
    # Filtrar tabelas baseado nas permissões do usuário
    username = st.session_state.get("username", "")
    role = st.session_state.get("role", "")
    
    # Administradores podem ver todas as tabelas (ativas e inativas)
    if role == "admin":
        metadata = load_tables_metadata(include_inactive=True)
    else:
        metadata = load_tables_metadata(include_inactive=False)
    
    filtered_metadata = filter_tables_by_permission(metadata, username)
    
    if not filtered_metadata:
        st.info("Nenhuma tabela disponível para você ou nenhuma tabela foi criada ainda.")
        return
    
    # Seleção de tabela
    if role == "admin":
        # Para administradores, mostrar status das tabelas
        table_options = []
        for t in filtered_metadata:
            status_icon = "✅" if t.get('status', 'ativo') == 'ativo' else "❌"
            table_options.append(f"{status_icon} {t['display_name']}")
        
        choice_with_status = st.selectbox("Selecione a tabela", options=table_options, key="table_selector")
        # Extrair o nome da tabela removendo o ícone de status
        choice = choice_with_status.split(" ", 1)[1] if " " in choice_with_status else choice_with_status
    else:
        # Para usuários normais, mostrar apenas tabelas ativas
        table_names = [t['display_name'] for t in filtered_metadata]
        choice = st.selectbox("Selecione a tabela", options=table_names, key="table_selector")
    
    # Encontrar metadados da tabela selecionada
    selected_meta = None
    for t in filtered_metadata:
        if t['display_name'] == choice:
            selected_meta = t
            break
    
    if selected_meta is None:
        st.error("Tabela não encontrada.")
        return
    
    # Sincronizar estrutura da tabela com metadados
    sync_table_structure_with_metadata(selected_meta['name'])
    
    # Verificar se a tabela está ativa (usuários normais não podem acessar tabelas inativas)
    if role != "admin" and selected_meta.get('status', 'ativo') != 'ativo':
        st.error("❌ Esta tabela está inativa e não pode ser acessada.")
        st.info("Entre em contato com o administrador para reativar esta tabela.")
        return
    
    # Verificar permissões para esta tabela específica
    table_name = selected_meta['name']
    can_view = check_user_permission(username, table_name, "view")
    can_insert = check_user_permission(username, table_name, "insert")
    can_update = check_user_permission(username, table_name, "update")
    can_delete = check_user_permission(username, table_name, "delete")
    
    # Show basic information about the table
    status_icon = "✅" if selected_meta.get('status', 'ativo') == 'ativo' else "❌"
    status_text = "Ativa" if selected_meta.get('status', 'ativo') == 'ativo' else "Inativa"
    
    st.subheader(f"Tabela: {selected_meta['display_name']} {status_icon} ({status_text})")
    st.write("Campos:")
    fields_df = pd.DataFrame(selected_meta['fields'])
    st.table(fields_df)
    
    # Mostrar permissões do usuário
    if st.session_state.get("role") != "admin":
        st.info(f"**Suas permissões para esta tabela:** Visualizar: {'✅' if can_view else '❌'}, Inserir: {'✅' if can_insert else '❌'}, Editar: {'✅' if can_update else '❌'}, Excluir: {'✅' if can_delete else '❌'}")
    
    # Subpage navigation baseada em permissões
    available_options = []
    
    if can_insert:
        available_options.append("Adicionar registro")
        available_options.append("Carga em lote")
    
    if can_view:
        available_options.append("Visualizar dados")
    
    if can_update:
        available_options.append("Editar registro")
        available_options.append("Adicionar campo")
    
    if can_delete:
        available_options.append("Excluir registro")
    
    # Apenas admin pode gerenciar tabelas (excluir/ativar/inativar)
    if st.session_state.get("role") == "admin":
        available_options.append("Gerenciar tabela")
    
    if not available_options:
        st.warning("Você não tem permissões para realizar nenhuma operação nesta tabela.")
        return
    
    # Usar chave única para manter estado do modo selecionado
    subpage_key = f"subpage_{table_name}"
    subpage = st.radio("O que você deseja fazer?", available_options, key=subpage_key)
    
    if subpage == "Adicionar registro" and can_insert:
        add_record_form(selected_meta)
    elif subpage == "Carga em lote" and can_insert:
        batch_upload_form(selected_meta)
    elif subpage == "Visualizar dados" and can_view:
        view_table_data(selected_meta)
    elif subpage == "Editar registro" and can_update:
        edit_record_form(selected_meta)
    elif subpage == "Excluir registro" and can_delete:
        delete_record_form(selected_meta)
    elif subpage == "Adicionar campo" and can_update:
        add_field_to_table(selected_meta)
    elif subpage == "Gerenciar tabela" and st.session_state.get("role") == "admin":
        manage_table_admin(selected_meta)


def batch_upload_form(table_meta: dict) -> None:
    """Display a form for batch upload of records via CSV."""
    st.subheader("Carga em lote via CSV")
    
    # Mostrar guia de formatos de dados
    with st.expander("📋 Guia de Formatos de Dados", expanded=False):
        st.markdown("""
        **Formatos aceitos para cada tipo de campo:**
        
        **📝 Texto (text):**
        - Qualquer texto: `"João Silva"`, `"Produto ABC"`, `"Descrição qualquer"`
        
        **🔢 Número Inteiro (int):**
        - Apenas números inteiros: `123`, `456`, `0`, `-10`
        - ❌ Não use: `123.45`, `"123"`, `abc`
        
        **💰 Número Decimal (float):**
        - Números com ou sem decimais: `123.45`, `100`, `0.99`, `-5.5`
        - Use ponto (.) como separador decimal: `123.45` ✅
        - ❌ Não use: `123,45` (vírgula), `"123.45"` (aspas)
        
        **📅 Data (date):**
        - Formato recomendado: `2024-01-15` (YYYY-MM-DD)
        - Formatos aceitos: `17/06/2025`, `2025-06-17`, `15/01/2024`
        - ❌ Evite: `17-06-2025`, `06/17/2025` (formato americano)
        
        **✅ Verdadeiro/Falso (bool):**
        - Valores aceitos: `True`, `False`, `1`, `0`, `sim`, `não`
        - Case-insensitive: `true`, `TRUE`, `Sim`, `SIM`
        """)
    
    # Generate and download template
    st.write("**Passo 1: Baixe o modelo CSV**")
    template_csv = generate_template_csv(table_meta)
    st.download_button(
        label="Baixar modelo CSV",
        data=template_csv,
        file_name=f"modelo_{table_meta['name']}.csv",
        mime="text/csv"
    )
    
    st.info("💡 **Dica:** O modelo CSV contém duas linhas de exemplo mostrando formatos aceitos para cada tipo de campo. Use como referência!")
    
    st.write("**Passo 2: Preencha o arquivo CSV e faça o upload**")
    uploaded_file = st.file_uploader(
        "Selecione o arquivo CSV para upload",
        type=['csv'],
        help="O arquivo deve ter as mesmas colunas do modelo"
    )
    
    if uploaded_file is not None:
        try:
            # Read CSV file
            df = pd.read_csv(uploaded_file, encoding='utf-8')
            
            # Show preview
            st.write("**Preview dos dados:**")
            st.dataframe(df.head(10))
            
            # Validate data
            is_valid, errors, validated_records = validate_csv_data(df, table_meta)
            
            if not is_valid:
                st.error("**Erros encontrados:**")
                for error in errors:
                    st.error(error)
                return
            
            st.success(f"✅ Dados validados com sucesso! {len(validated_records)} registros prontos para importar.")
            
            # Show import options
            st.write("**Passo 3: Configurar importação**")
            col1, col2 = st.columns(2)
            
            with col1:
                skip_duplicates = st.checkbox(
                    "Pular registros duplicados",
                    value=True,
                    help="Se marcado, registros duplicados serão ignorados"
                )
            
            with col2:
                preview_mode = st.checkbox(
                    "Modo preview (não salvar)",
                    value=False,
                    help="Teste a importação sem salvar os dados"
                )
            
            # Import button
            if st.button("Importar dados", type="primary"):
                if preview_mode:
                    st.info("Modo preview ativado - dados não foram salvos")
                    st.write("**Registros que seriam importados:**")
                    preview_df = pd.DataFrame(validated_records)
                    st.dataframe(preview_df)
                else:
                    # Perform actual import
                    inserted_count, duplicate_count, errors = insert_batch_records(
                        table_meta['name'], 
                        table_meta['fields'], 
                        validated_records
                    )
                    
                    # Show results
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Registros importados", inserted_count)
                    with col2:
                        st.metric("Duplicados ignorados", duplicate_count)
                    with col3:
                        st.metric("Total processados", len(validated_records))
                    
                    if errors:
                        st.error("**Erros durante a importação:**")
                        for error in errors:
                            st.error(error)
                    
                    if inserted_count > 0:
                        st.success(f"✅ Importação concluída! {inserted_count} registros adicionados.")
                    
                    if duplicate_count > 0:
                        st.warning(f"⚠️ {duplicate_count} registros duplicados foram ignorados.")
        
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")


def add_record_form(table_meta: dict) -> None:
    """Display a form to insert a new record into a table."""
    # Verificar permissão de inserção
    username = st.session_state.get("username", "")
    if not check_user_permission(username, table_meta['name'], "insert"):
        st.error("Você não tem permissão para inserir registros nesta tabela.")
        return
    
    # Recarregar metadados para garantir dados atualizados
    refreshed_meta = refresh_table_metadata(table_meta['name'])
    if refreshed_meta:
        table_meta = refreshed_meta
    
    st.subheader("Adicionar novo registro")
    with st.form(key=f"add_record_{table_meta['name']}"):
        input_values = {}
        for field in table_meta['fields']:
            fname = field['name']
            ftype = field['type']
            if ftype == 'text':
                val = st.text_input(fname)
            elif ftype == 'int':
                val = st.number_input(fname, step=1, format="%d")
                # Ensure integer type conversion later
            elif ftype == 'float':
                val = st.number_input(fname, step=1.0, format="%.2f")
            elif ftype == 'date':
                date_val = st.date_input(fname)
                val = date_val.isoformat() if date_val else None
            elif ftype == 'bool':
                bool_val = st.checkbox(fname)
                val = int(bool_val)
            else:
                val = st.text_input(fname)
            input_values[fname] = val
        submitted = st.form_submit_button("Salvar")
        if submitted:
            # Convert numeric values appropriately
            for f in table_meta['fields']:
                name = f['name']
                if f['type'] == 'int':
                    try:
                        input_values[name] = int(input_values[name]) if input_values[name] != '' else None
                    except ValueError:
                        st.error(f"O valor de {name} deve ser inteiro.")
                        return
                elif f['type'] == 'float':
                    try:
                        input_values[name] = float(input_values[name]) if input_values[name] != '' else None
                    except ValueError:
                        st.error(f"O valor de {name} deve ser numérico.")
                        return
            try:
                insert_record(table_meta['name'], table_meta['fields'], input_values)
                st.success("Registro adicionado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao inserir registro: {e}")


def view_table_data(table_meta: dict) -> None:
    """Show the contents of a table in a data frame."""
    # Verificar permissão de visualização
    username = st.session_state.get("username", "")
    if not check_user_permission(username, table_meta['name'], "view"):
        st.error("Você não tem permissão para visualizar dados desta tabela.")
        return
    
    # Recarregar metadados para garantir dados atualizados
    refreshed_meta = refresh_table_metadata(table_meta['name'])
    if refreshed_meta:
        table_meta = refreshed_meta
    
    st.subheader("Visualizar dados")
    try:
        # Usar cursor para evitar problemas de compatibilidade com pandas
        with get_db_cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_meta['name']}")
            rows = cursor.fetchall()
            
            # Converter para DataFrame manualmente
            if rows:
                # Converter Row objects para dicionários
                data = []
                for row in rows:
                    data.append(dict(row))
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame()
        
        # Show statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de registros", len(df))
        with col2:
            st.metric("Colunas", len(df.columns))
        with col3:
            if len(df) > 0:
                # Check for potential duplicates (excluding ID)
                data_cols = [col for col in df.columns if col != 'id']
                if data_cols:
                    duplicates = df.duplicated(subset=data_cols).sum()
                    st.metric("Possíveis duplicados", duplicates)
                else:
                    st.metric("Possíveis duplicados", 0)
            else:
                st.metric("Possíveis duplicados", 0)
        
        # Show data
        st.write("**Dados da tabela:**")
        st.dataframe(df)
        
        # Provide option to download as CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Baixar CSV",
            data=csv,
            file_name=f"{table_meta['name']}.csv",
            mime="text/csv"
        )
        
        # Show data quality info
        if len(df) > 0:
            st.write("**Qualidade dos dados:**")
            quality_df = pd.DataFrame({
                'Coluna': df.columns,
                'Tipo': df.dtypes,
                'Valores únicos': [df[col].nunique() for col in df.columns],
                'Valores nulos': df.isnull().sum().values
            })
            st.dataframe(quality_df)
            
    except Exception as e:
        st.error(f"Erro ao ler dados: {e}")


def add_field_to_table(table_meta: dict) -> None:
    """Render a form to add a new column to an existing table."""
    # Verificar permissão de edição
    username = st.session_state.get("username", "")
    if not check_user_permission(username, table_meta['name'], "update"):
        st.error("Você não tem permissão para modificar esta tabela.")
        return
    
    st.subheader("Adicionar novo campo à tabela")
    with st.form(key=f"add_field_{table_meta['name']}"):
        fname = st.text_input("Nome do novo campo")
        ftype_label = st.selectbox(
            "Tipo do novo campo",
            options=["Texto", "Número Inteiro", "Número Decimal", "Data", "Booleano"],
        )
        submitted = st.form_submit_button("Adicionar campo")
        if submitted:
            if not fname:
                st.error("O nome do campo é obrigatório.")
                return
            canonical_type = {
                "Texto": "text",
                "Número Inteiro": "int",
                "Número Decimal": "float",
                "Data": "date",
                "Booleano": "bool",
            }[ftype_label]
            # Update database and metadata
            try:
                alter_table_add_column(table_meta['name'], {"name": fname, "type": canonical_type})
                
                # Sincronizar automaticamente os metadados com a estrutura da tabela
                if sync_table_structure_with_metadata(table_meta['name']):
                    st.success("Campo adicionado e metadados sincronizados com sucesso!")
                else:
                    st.success("Campo adicionado com sucesso!")
                
                st.info("🔄 Atualizando interface...")
                
                # Limpar cache do Streamlit para forçar refresh
                if hasattr(st, 'cache_data'):
                    st.cache_data.clear()
                
                # Forçar refresh da página mantendo o modo selecionado
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao adicionar coluna: {e}")
                return


def manage_table_admin(table_meta: dict) -> None:
    """Permite ao administrador gerenciar o status da tabela (ativar/inativar)."""
    st.subheader("Gerenciar tabela")
    
    # Mostrar informações da tabela
    st.info(f"📋 **Tabela:** {table_meta['display_name']}")
    st.info(f"🔧 **Nome interno:** {table_meta['name']}")
    st.info(f"🆔 **ID do metadado:** {table_meta.get('id', 'N/A')}")
    st.info(f"📊 **Status atual:** {table_meta.get('status', 'ativo')}")
    
    # Mostrar opções baseadas no status atual
    current_status = table_meta.get('status', 'ativo')
    
    if current_status == 'ativo':
        st.warning("Esta tabela está ativa e aparece no seletor para usuários com permissão.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚫 Inativar tabela", type="secondary"):
                try:
                    result = toggle_table_status(table_meta['name'], 'inativo')
                    if result['success']:
                        st.success("✅ Tabela inativada com sucesso!")
                        st.info("A tabela foi removida do seletor de tabelas.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ Erro ao inativar tabela: {', '.join(result['errors'])}")
                except Exception as e:
                    st.error(f"❌ Erro ao inativar tabela: {e}")
        
        with col2:
            st.info("ℹ️ Tabela ativa - disponível para usuários")
    
    else:  # status == 'inativo'
        st.info("Esta tabela está inativa e não aparece no seletor para usuários.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Ativar tabela", type="primary"):
                try:
                    result = toggle_table_status(table_meta['name'], 'ativo')
                    if result['success']:
                        st.success("✅ Tabela ativada com sucesso!")
                        st.info("A tabela agora aparece no seletor para usuários com permissão.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ Erro ao ativar tabela: {', '.join(result['errors'])}")
                except Exception as e:
                    st.error(f"❌ Erro ao ativar tabela: {e}")
        
        with col2:
            st.info("ℹ️ Tabela inativa - oculta dos usuários")
    
    # Mostrar informações sobre o impacto
    st.markdown("---")
    st.markdown("### 📋 Informações sobre o status da tabela")
    
    if current_status == 'ativo':
        st.markdown("""
        **Tabela Ativa:**
        - ✅ Aparece no seletor de tabelas para usuários com permissão
        - ✅ Usuários podem visualizar, inserir, editar e excluir dados
        - ✅ Todas as funcionalidades estão disponíveis
        """)
    else:
        st.markdown("""
        **Tabela Inativa:**
        - ❌ Não aparece no seletor de tabelas para nenhum usuário
        - ❌ Usuários não podem acessar os dados
        - ✅ Dados são preservados no banco de dados
        - ✅ Pode ser reativada a qualquer momento
        """)


def delete_table(table_meta: dict) -> None:
    """Allow the administrator to inactivate a table (soft delete)."""
    st.subheader("Inativar tabela")
    
    # Mostrar informações da tabela que será inativada
    st.info(f"📋 **Tabela selecionada:** {table_meta['display_name']}")
    st.info(f"🔧 **Nome interno:** {table_meta['name']}")
    st.info(f"🆔 **ID do metadado:** {table_meta.get('id', 'N/A')}")
    st.info(f"📊 **Status atual:** {table_meta.get('status', 'ativo')}")
    
    st.warning(
        "Esta ação irá inativar a tabela, removendo-a do seletor de tabelas para todos os usuários. "
        "Os dados serão preservados e a tabela poderá ser reativada posteriormente."
    )
    
    # Checkbox de confirmação obrigatório
    confirm_inactivate = st.checkbox(
        "✅ Confirmo que desejo inativar esta tabela",
        key="confirm_inactivate_table"
    )
    
    # Botão de inativação só aparece se o checkbox estiver marcado
    if confirm_inactivate:
        if st.button("🚫 Confirmar inativação", type="primary"):
            try:
                table_name = table_meta['name']
                table_id = table_meta.get('id')
                
                st.info(f"🚫 Iniciando inativação da tabela '{table_name}' (ID: {table_id})...")
                
                # Usar a função toggle_table_status para inativar
                result = toggle_table_status(table_name, 'inativo')
                
                if result['success']:
                    st.success("✅ Tabela inativada com sucesso!")
                    st.info(f"📊 Status alterado de '{result['old_status']}' para '{result['new_status']}'")
                    st.info("🔄 Atualizando lista de tabelas...")
                    
                    # Limpar cache e forçar atualização
                    st.cache_data.clear()
                    
                    # Aguardar um momento para garantir que a transação foi commitada
                    import time
                    time.sleep(0.5)
                    
                    # Forçar rerun
                    st.rerun()
                else:
                    st.error(f"❌ Erro ao inativar tabela: {', '.join(result['errors'])}")
                    st.info("🔍 Verifique os logs da aplicação para mais detalhes.")
                
            except Exception as e:
                st.error(f"❌ Erro ao inativar tabela: {e}")
                st.info("🔍 Verifique os logs da aplicação para mais detalhes.")
                import traceback
                st.error(f"Detalhes do erro: {traceback.format_exc()}")
    else:
        st.info("ℹ️ Marque a caixa de confirmação para habilitar a inativação")


def page_config() -> None:
    """Render the configuration page allowing administrators to upload a logo."""
    st.header("Configurações do sistema")
    cfg = load_config()
    if cfg.get("logo"):
        try:
            # Mostrar logo atual com tamanho controlado
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(cfg["logo"], width=200)
                st.write("**Logo atual da empresa**")
        except Exception:
            st.write("Não foi possível carregar a imagem atual.")
    uploaded = st.file_uploader("Carregar logo da empresa (PNG ou JPG)", type=["png", "jpg", "jpeg"])
    if uploaded:
        # Ensure the logos directory exists
        logo_dir = os.path.join(DATA_DIR, "logos")
        os.makedirs(logo_dir, exist_ok=True)
        # Save the uploaded file to disk
        logo_path = os.path.join(logo_dir, uploaded.name)
        with open(logo_path, "wb") as f:
            f.write(uploaded.getbuffer())
        
        # Redimensionar logo se necessário
        resized_logo_path = resize_logo_if_needed(logo_path)
        
        # Update config
        cfg["logo"] = resized_logo_path
        save_config(cfg)
        st.success("Logo atualizada com sucesso!")
        st.rerun()


def page_manage_users() -> None:
    """Render the user management page.  Only administrators may use this."""
    st.header("Gerenciamento de usuários")
    if st.session_state.role != "admin":
        st.error("Acesso negado. Apenas administradores podem gerenciar usuários.")
        return
    
    # Tabs para diferentes funcionalidades
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Usuários", "Permissões", "Permissões Gerais", "Adicionar Usuário", "Alterar Senhas", "PostgreSQL Grants"])
    
    with tab1:
        st.subheader("Usuários cadastrados")
        users = load_users()
        user_list = list(users.keys())
        user_df = pd.DataFrame([
            {
                "Usuário": u, 
                "Perfil": users[u].get("role", "user"),
                "Status": users[u].get("status", "ativo")
            } for u in user_list
        ])
        st.table(user_df)
        
        # Gerenciar status do usuário
        st.divider()
        st.subheader("Gerenciar Status do Usuário")
        if len(users) > 1:
            selected_user = st.selectbox("Selecione o usuário para alterar status", options=[u for u in users if u != "admin"])
            
            # Mostrar informações do usuário selecionado
            if selected_user:
                current_status = users[selected_user].get('status', 'ativo')
                status_icon = "🟢" if current_status == 'ativo' else "🔴"
                
                st.info(f"👤 **Usuário selecionado:** {selected_user}")
                st.info(f"🔧 **Perfil:** {users[selected_user].get('role', 'user')}")
                st.info(f"{status_icon} **Status atual:** {current_status.upper()}")
                
                # Opções de status
                st.markdown("---")
                st.markdown("**🔄 Alterar status do usuário:**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🟢 Ativar Usuário", type="primary", disabled=(current_status == 'ativo')):
                        try:
                            st.info(f"🔄 Ativando usuário '{selected_user}'...")
                            
                            results = toggle_user_status(selected_user, 'ativo')
                            
                            if results['success']:
                                st.success(f"✅ Usuário '{selected_user}' ativado com sucesso!")
                                
                                # Mostrar detalhes
                                with st.expander("📊 Detalhes da ativação", expanded=True):
                                    st.write(f"**ID do usuário:** {results['user_id']}")
                                    st.write(f"**Status anterior:** {results['old_status']}")
                                    st.write(f"**Novo status:** {results['new_status']}")
                                
                                st.info("🔄 Atualizando lista de usuários...")
                                
                                # Limpar cache e forçar atualização
                                st.cache_data.clear()
                                import time
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("❌ Falha ao ativar usuário!")
                                
                        except Exception as e:
                            st.error(f"❌ Erro ao ativar usuário '{selected_user}': {e}")
                            import traceback
                            st.error(f"Detalhes do erro: {traceback.format_exc()}")
                
                with col2:
                    if st.button("🔴 Inativar Usuário", type="secondary", disabled=(current_status == 'inativo')):
                        try:
                            st.info(f"🔄 Inativando usuário '{selected_user}'...")
                            
                            results = toggle_user_status(selected_user, 'inativo')
                            
                            if results['success']:
                                st.success(f"✅ Usuário '{selected_user}' inativado com sucesso!")
                                
                                # Mostrar detalhes
                                with st.expander("📊 Detalhes da inativação", expanded=True):
                                    st.write(f"**ID do usuário:** {results['user_id']}")
                                    st.write(f"**Status anterior:** {results['old_status']}")
                                    st.write(f"**Novo status:** {results['new_status']}")
                                
                                st.info("🔄 Atualizando lista de usuários...")
                                
                                # Limpar cache e forçar atualização
                                st.cache_data.clear()
                                import time
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("❌ Falha ao inativar usuário!")
                                
                        except Exception as e:
                            st.error(f"❌ Erro ao inativar usuário '{selected_user}': {e}")
                            import traceback
                            st.error(f"Detalhes do erro: {traceback.format_exc()}")
                
                # Informações sobre o status
                st.markdown("---")
                st.markdown("**ℹ️ Informações sobre o status:**")
                st.info("""
                - **🟢 ATIVO**: Usuário pode acessar a aplicação normalmente
                - **🔴 INATIVO**: Usuário não pode acessar a aplicação (acesso bloqueado)
                - **Admin**: Sempre permanece ativo e não pode ser inativado
                - **Dados preservados**: Usuários inativos mantêm todos os dados e permissões
                """)
        else:
            st.info("ℹ️ Nenhum usuário gerenciável (apenas admin existe).")
    
    with tab2:
        manage_user_permissions()
    
    with tab3:
        manage_user_general_permissions()
    
    with tab4:
        st.subheader("Adicionar novo usuário")
        with st.form(key="add_user"):
            new_username = st.text_input("Nome de usuário")
            new_password = st.text_input("Senha", type="password")
            confirm_password = st.text_input("Confirmar senha", type="password")
            role = st.selectbox("Perfil", options=["user", "admin"])
            submitted = st.form_submit_button("Adicionar usuário")
            if submitted:
                if not new_username or not new_password:
                    st.error("Usuário e senha são obrigatórios.")
                elif new_password != confirm_password:
                    st.error("As senhas não conferem.")
                elif new_username in users:
                    st.error("Usuário já existe.")
                else:
                    users[new_username] = {
                        "password": hash_password(new_password),
                        "role": role,
                    }
                    save_users(users)
                    st.success("Usuário adicionado com sucesso!")
                    st.rerun()
    
    with tab5:
        st.subheader("Alterar Senhas")
        users = load_users()
        
        if len(users) > 0:
            # Selecionar usuário
            selected_user = st.selectbox(
                "Selecionar usuário para alterar senha:",
                options=list(users.keys()),
                key="change_password_user"
            )
            
            if selected_user:
                st.info(f"Alterando senha para: **{selected_user}**")
                
                with st.form(key="change_password_form"):
                    current_password = st.text_input("Senha atual", type="password", help="Digite a senha atual para confirmar")
                    new_password = st.text_input("Nova senha", type="password", help="Digite a nova senha")
                    confirm_password = st.text_input("Confirmar nova senha", type="password", help="Digite novamente a nova senha")
                    
                    submitted = st.form_submit_button("Alterar Senha")
                    
                    if submitted:
                        if not current_password or not new_password or not confirm_password:
                            st.error("Todos os campos são obrigatórios.")
                        elif new_password != confirm_password:
                            st.error("As novas senhas não conferem.")
                        elif len(new_password) < 4:
                            st.error("A nova senha deve ter pelo menos 4 caracteres.")
                        else:
                            # Verificar senha atual
                            if users[selected_user]["password"] == hash_password(current_password):
                                # Atualizar senha
                                users[selected_user]["password"] = hash_password(new_password)
                                save_users(users)
                                st.success(f"Senha alterada com sucesso para {selected_user}!")
                                st.rerun()
                            else:
                                st.error("Senha atual incorreta.")
        else:
            st.info("Nenhum usuário encontrado.")
    
    with tab6:
        st.subheader("Gerenciamento de Usuários PostgreSQL")
        manage_postgresql_grants()


def get_record_by_id(table_name: str, record_id: int) -> dict:
    """Busca um registro específico por ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s", (record_id,))
        row = cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        st.error(f"Erro ao buscar registro: {e}")
        return None
    finally:
        conn.close()


def check_user_permission(username: str, table_name: str, permission: str) -> bool:
    """Verifica se um usuário tem permissão específica para uma tabela."""
    try:
        with get_db_cursor() as cursor:
            # Admin tem acesso total
            if st.session_state.get("role") == "admin":
                return True
            
            # Verificar permissão específica
            cursor.execute("""
                SELECT can_view, can_insert, can_update, can_delete 
                FROM user_table_permissions utp
                JOIN users u ON utp.user_id = u.id
                WHERE u.username = %s AND utp.table_name = %s
            """, (username, table_name))
            
            result = cursor.fetchone()
            if result:
                if permission == "view":
                    return result['can_view']
                elif permission == "insert":
                    return result['can_insert']
                elif permission == "update":
                    return result['can_update']
                elif permission == "delete":
                    return result['can_delete']
            
            return False
            
    except Exception as e:
        st.error(f"Erro ao verificar permissão: {e}")
        return False


def check_user_general_permission(username: str, permission: str) -> bool:
    """Verifica se um usuário tem permissão geral específica."""
    try:
        with get_db_cursor() as cursor:
            # Admin tem acesso total
            if st.session_state.get("role") == "admin":
                return True
            
            # Verificar permissão geral
            cursor.execute("""
                SELECT can_create_tables
                FROM user_general_permissions ugp
                JOIN users u ON ugp.user_id = u.id
                WHERE u.username = %s
            """, (username,))
            
            result = cursor.fetchone()
            if result:
                if permission == "create_tables":
                    return result['can_create_tables']
            
            return False
            
    except Exception as e:
        st.error(f"Erro ao verificar permissão geral: {e}")
        return False


def get_user_accessible_tables(username: str) -> list:
    """Retorna lista de tabelas que o usuário pode acessar."""
    try:
        with get_db_cursor() as cursor:
            # Admin vê todas as tabelas
            if st.session_state.get("role") == "admin":
                cursor.execute("SELECT table_name FROM tables_metadata")
                return [row['table_name'] for row in cursor.fetchall()]
            
            # Usuário vê apenas tabelas com permissão
            cursor.execute("""
                SELECT DISTINCT utp.table_name 
                FROM user_table_permissions utp
                JOIN users u ON utp.user_id = u.id
                WHERE u.username = %s AND utp.can_view = TRUE
            """, (username,))
            
            return [row['table_name'] for row in cursor.fetchall()]
            
    except Exception as e:
        st.error(f"Erro ao buscar tabelas acessíveis: {e}")
        return []


def get_user_existing_permissions(username: str) -> dict:
    """Retorna as permissões existentes de um usuário."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT table_name, can_view, can_insert, can_update, can_delete
                FROM user_table_permissions utp
                JOIN users u ON utp.user_id = u.id
                WHERE u.username = %s
            """, (username,))
            
            permissions = {}
            for row in cursor.fetchall():
                permissions[row['table_name']] = {
                    'can_view': row['can_view'],
                    'can_insert': row['can_insert'],
                    'can_update': row['can_update'],
                    'can_delete': row['can_delete']
                }
            
            return permissions
            
    except Exception as e:
        st.error(f"Erro ao buscar permissões existentes: {e}")
        return {}


def manage_user_permissions() -> None:
    """Interface para gerenciar permissões de usuários."""
    #st.subheader("Gerenciar permissões de usuários")
    
    # Selecionar usuário
    users = load_users()
    user_options = [u for u in users.keys() if users[u].get("role") != "admin"]
    
    if not user_options:
        st.info("Nenhum usuário não-admin encontrado para gerenciar permissões.")
        return
    
    selected_user = st.selectbox("Selecione o usuário", options=user_options)
    
    if selected_user:
        # Carregar tabelas disponíveis
        metadata = load_tables_metadata()
        if not metadata:
            st.info("Nenhuma tabela encontrada.")
            return
        
        st.write(f"**Configurando permissões para: {selected_user}**")
        
        # Carregar permissões existentes do usuário
        existing_permissions = get_user_existing_permissions(selected_user)
        
        # Formulário de permissões
        with st.form(key=f"permissions_{selected_user}"):
            st.write("**Permissões por tabela:**")
            
            permissions_data = []
            for table_meta in metadata:
                table_name = table_meta['name']
                display_name = table_meta['display_name']
                
                # Obter permissões existentes para esta tabela
                existing_perm = existing_permissions.get(table_name, {
                    'can_view': False,
                    'can_insert': False,
                    'can_update': False,
                    'can_delete': False
                })
                
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                
                with col1:
                    st.write(f"**{display_name}**")
                
                with col2:
                    can_view = st.checkbox("Visualizar", 
                                        value=existing_perm['can_view'],
                                        key=f"view_{table_name}_{selected_user}")
                
                with col3:
                    can_insert = st.checkbox("Inserir", 
                                           value=existing_perm['can_insert'],
                                           key=f"insert_{table_name}_{selected_user}")
                
                with col4:
                    can_update = st.checkbox("Editar", 
                                           value=existing_perm['can_update'],
                                           key=f"update_{table_name}_{selected_user}")
                
                with col5:
                    can_delete = st.checkbox("Excluir", 
                                           value=existing_perm['can_delete'],
                                           key=f"delete_{table_name}_{selected_user}")
                
                permissions_data.append({
                    'table_name': table_name,
                    'can_view': can_view,
                    'can_insert': can_insert,
                    'can_update': can_update,
                    'can_delete': can_delete
                })
            
            submitted = st.form_submit_button("Salvar permissões")
            
            if submitted:
                save_user_permissions(selected_user, permissions_data)
                st.success("Permissões salvas com sucesso!")
                st.rerun()


def save_user_permissions(username: str, permissions: list) -> None:
    """Salva as permissões de um usuário no banco e aplica grants no PostgreSQL."""
    try:
        with get_db_cursor() as cursor:
            # Obter ID do usuário
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user_result = cursor.fetchone()
            user_id = user_result['id'] if user_result else None
            
            if not user_id:
                st.error(f"Usuário {username} não encontrado!")
                return
            
            # Obter ID do admin que está concedendo as permissões
            cursor.execute("SELECT id FROM users WHERE username = %s", (st.session_state.get("username", "admin"),))
            admin_result = cursor.fetchone()
            admin_id = admin_result['id'] if admin_result else 1
            
            # Limpar permissões existentes
            cursor.execute("DELETE FROM user_table_permissions WHERE user_id = %s", (user_id,))
            
            # Inserir novas permissões e aplicar grants
            for perm in permissions:
                if any([perm['can_view'], perm['can_insert'], perm['can_update'], perm['can_delete']]):
                    # Salvar na tabela de permissões da aplicação
                    cursor.execute("""
                        INSERT INTO user_table_permissions 
                        (user_id, table_name, can_view, can_insert, can_update, can_delete, granted_by)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        user_id, perm['table_name'], 
                        perm['can_view'], perm['can_insert'], 
                        perm['can_update'], perm['can_delete'], 
                        admin_id
                    ))
                    
                    # Aplicar grants no PostgreSQL
                    try:
                        grants_manager.grant_table_permissions(
                            username=username,
                            table_name=perm['table_name'],
                            permissions={
                                'can_view': perm['can_view'],
                                'can_insert': perm['can_insert'],
                                'can_update': perm['can_update'],
                                'can_delete': perm['can_delete']
                            }
                        )
                    except Exception as e:
                        print(f"Aviso: Não foi possível aplicar grants para {username} na tabela {perm['table_name']}: {e}")
            
            st.success(f"Permissões para {username} salvas com sucesso!")
            
    except Exception as e:
        st.error(f"Erro ao salvar permissões: {e}")


def save_user_general_permissions(username: str, can_create_tables: bool) -> None:
    """Salva as permissões gerais de um usuário no banco e aplica grants no PostgreSQL."""
    try:
        with get_db_cursor() as cursor:
            # Obter ID do usuário
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user_result = cursor.fetchone()
            user_id = user_result['id'] if user_result else None
            
            if not user_id:
                st.error(f"Usuário {username} não encontrado!")
                return
            
            # Obter ID do admin que está concedendo as permissões
            cursor.execute("SELECT id FROM users WHERE username = %s", (st.session_state.get("username", "admin"),))
            admin_result = cursor.fetchone()
            admin_id = admin_result['id'] if admin_result else 1
            
            # Inserir ou atualizar permissões gerais
            cursor.execute("""
                INSERT INTO user_general_permissions (user_id, can_create_tables, granted_by)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    can_create_tables = EXCLUDED.can_create_tables,
                    granted_by = EXCLUDED.granted_by,
                    granted_at = CURRENT_TIMESTAMP
            """, (user_id, can_create_tables, admin_id))
            
            # Aplicar grants no PostgreSQL
            try:
                grants_manager.grant_general_permissions(
                    username=username,
                    can_create_tables=can_create_tables
                )
            except Exception as e:
                print(f"Aviso: Não foi possível aplicar grants gerais para {username}: {e}")
            
            # Se o usuário recebeu permissão de criar tabelas, aplicar permissões automáticas nas tabelas existentes
            if can_create_tables:
                apply_auto_permissions_for_existing_tables(username)
            
            st.success(f"Permissões gerais para {username} salvas com sucesso!")
            if can_create_tables:
                st.info("Permissões automáticas aplicadas nas tabelas existentes: Visualizar, Inserir e Editar")
            
    except Exception as e:
        st.error(f"Erro ao salvar permissões gerais: {e}")


def manage_user_general_permissions() -> None:
    """Interface para gerenciar permissões gerais dos usuários."""
    
    # Selecionar usuário
    users = load_users()
    user_options = [u for u in users.keys() if users[u].get("role") != "admin"]
    
    if not user_options:
        st.info("Nenhum usuário não-admin encontrado para gerenciar permissões.")
        return
    
    selected_user = st.selectbox("Selecione o usuário", options=user_options, key="general_permissions_user")
    
    if selected_user:
        # Carregar permissões atuais
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    SELECT ugp.can_create_tables
                    FROM user_general_permissions ugp
                    JOIN users u ON ugp.user_id = u.id
                    WHERE u.username = %s
                """, (selected_user,))
                
                result = cursor.fetchone()
                current_can_create_tables = result['can_create_tables'] if result else False
        except:
            current_can_create_tables = False
        
        st.write(f"**Configurando permissões gerais para: {selected_user}**")
        
        # Formulário de permissões gerais
        with st.form(key=f"general_permissions_{selected_user}"):
            st.write("**Permissões gerais:**")
            
            can_create_tables = st.checkbox(
                "Pode criar tabelas", 
                value=current_can_create_tables,
                key=f"can_create_tables_{selected_user}"
            )
            
            submitted = st.form_submit_button("Salvar permissões gerais")
            
            if submitted:
                save_user_general_permissions(selected_user, can_create_tables)
                st.rerun()


def filter_tables_by_permission(metadata: list, username: str) -> list:
    """Filtra tabelas baseado nas permissões do usuário."""
    if st.session_state.get("role") == "admin":
        return metadata
    
    accessible_tables = get_user_accessible_tables(username)
    return [table for table in metadata if table['name'] in accessible_tables]


def manage_postgresql_grants() -> None:
    """Interface para gerenciar usuários e grants do PostgreSQL."""
    st.write("**Gerenciamento de usuários e permissões no PostgreSQL**")
    
    # Selecionar usuário
    users = load_users()
    user_options = list(users.keys())
    
    if not user_options:
        st.info("Nenhum usuário encontrado.")
        return
    
    selected_user = st.selectbox("Selecione o usuário", options=user_options)
    
    if selected_user:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Usuário selecionado: {selected_user}**")
            
            # Testar conexão do usuário
            if st.button("Testar Conexão PostgreSQL"):
                try:
                    user_data = users[selected_user]
                    pg_password = user_data['password'][:20]
                    
                    if grants_manager.test_user_connection(selected_user, pg_password):
                        st.success("✅ Conexão PostgreSQL funcionando!")
                    else:
                        st.error("❌ Falha na conexão PostgreSQL")
                except Exception as e:
                    st.error(f"Erro ao testar conexão: {e}")
            
            # Recriar usuário no PostgreSQL
            if st.button("Recriar Usuário PostgreSQL"):
                try:
                    user_data = users[selected_user]
                    pg_password = user_data['password'][:20]
                    
                    # Remover usuário existente primeiro
                    grants_manager.drop_user(selected_user)
                    
                    # Criar novo usuário
                    if grants_manager.create_database_user(
                        username=selected_user,
                        password=pg_password,
                        role=user_data['role']
                    ):
                        st.success("✅ Usuário PostgreSQL recriado com sucesso!")
                    else:
                        st.error("❌ Falha ao recriar usuário PostgreSQL")
                except Exception as e:
                    st.error(f"Erro ao recriar usuário: {e}")
        
        with col2:
            st.write("**Ações de Grants**")
            
            # Aplicar todas as permissões salvas
            if st.button("Aplicar Todas as Permissões"):
                try:
                    # Aplicar permissões gerais
                    with get_db_cursor() as cursor:
                        cursor.execute("""
                            SELECT can_create_tables
                            FROM user_general_permissions ugp
                            JOIN users u ON ugp.user_id = u.id
                            WHERE u.username = %s
                        """, (selected_user,))
                        result = cursor.fetchone()
                        can_create = result['can_create_tables'] if result else False
                    
                    grants_manager.grant_general_permissions(selected_user, can_create)
                    
                    # Aplicar permissões de tabelas
                    with get_db_cursor() as cursor:
                        cursor.execute("""
                            SELECT table_name, can_view, can_insert, can_update, can_delete
                            FROM user_table_permissions utp
                            JOIN users u ON utp.user_id = u.id
                            WHERE u.username = %s
                        """, (selected_user,))
                        permissions = cursor.fetchall()
                    
                    for perm in permissions:
                        grants_manager.grant_table_permissions(
                            username=selected_user,
                            table_name=perm['table_name'],
                            permissions={
                                'can_view': perm['can_view'],
                                'can_insert': perm['can_insert'],
                                'can_update': perm['can_update'],
                                'can_delete': perm['can_delete']
                            }
                        )
                    
                    st.success("✅ Todas as permissões aplicadas com sucesso!")
                    
                except Exception as e:
                    st.error(f"Erro ao aplicar permissões: {e}")
            
            # Revogar todas as permissões
            if st.button("Revogar Todas as Permissões"):
                try:
                    grants_manager.revoke_all_permissions(selected_user)
                    st.success("✅ Todas as permissões revogadas!")
                except Exception as e:
                    st.error(f"Erro ao revogar permissões: {e}")
        
        # Mostrar permissões atuais
        st.write("**Permissões Atuais no PostgreSQL:**")
        try:
            permissions = grants_manager.get_user_permissions(selected_user)
            if permissions:
                st.write("**Permissões de Tabelas:**")
                for perm in permissions['table_permissions']:
                    st.write(f"- {perm[1]}.{perm[2]}: {perm[3]}")
                
                st.write("**Permissões de Schema:**")
                for perm in permissions['schema_permissions']:
                    st.write(f"- {perm[0]}: {perm[1]}")
            else:
                st.info("Nenhuma permissão encontrada ou erro ao buscar.")
        except Exception as e:
            st.error(f"Erro ao buscar permissões: {e}")


def update_record(table_name: str, record_id: int, values: dict) -> bool:
    """Atualiza um registro existente."""
    try:
        with get_db_cursor() as cursor:
            # Construir query de UPDATE
            set_clause = ", ".join([f"{key} = %s" for key in values.keys()])
            query = f"UPDATE {table_name} SET {set_clause} WHERE id = %s"
            
            # Preparar valores (excluir ID dos valores a atualizar)
            update_values = list(values.values())
            update_values.append(record_id)
            
            # Executar update
            cursor.execute(query, update_values)
            
            if cursor.rowcount > 0:
                return True
            else:
                st.warning("Nenhum registro foi atualizado. Verifique se o ID existe.")
                return False
                
    except Exception as e:
        st.error(f"Erro ao atualizar registro: {e}")
        return False


def edit_record_form(table_meta: dict) -> None:
    """Interface para edição de registros."""
    # Verificar permissão de edição
    username = st.session_state.get("username", "")
    if not check_user_permission(username, table_meta['name'], "update"):
        st.error("Você não tem permissão para editar registros desta tabela.")
        return
    
    # Recarregar metadados para garantir dados atualizados
    refreshed_meta = refresh_table_metadata(table_meta['name'])
    if refreshed_meta:
        table_meta = refreshed_meta
    
    st.subheader("Editar registro")
    
    # Buscar registros para seleção
    try:
        with get_db_cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_meta['name']}")
            rows = cursor.fetchall()
            
            # Converter para DataFrame manualmente
            if rows:
                data = []
                for row in rows:
                    data.append(dict(row))
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame()
            
            if len(df) == 0:
                st.warning("Nenhum registro encontrado para editar.")
                return
            
            # Selecionar registro para editar
            st.write("**Selecione o registro para editar:**")
            
            # Mostrar dados em formato de tabela com seleção
            selected_index = st.selectbox(
                "Escolha o registro:",
                options=df.index,
                format_func=lambda x: f"ID: {df.iloc[x]['id']} - {' | '.join([f'{col}: {df.iloc[x][col]}' for col in df.columns[:3] if col != 'id'])}",
                key=f"select_record_{table_meta['name']}"
            )
            
            if selected_index is not None:
                record = df.iloc[selected_index].to_dict()
                record_id = record['id']
                
                st.write(f"**Editando registro ID: {record_id}**")
                
                # Mostrar dados atuais do registro
                st.write("**Dados atuais do registro:**")
                for field in table_meta['fields']:
                    field_name = field['name']
                    current_value = record.get(field_name, "")
                    st.write(f"**{field_name}:** {current_value}")
                
                st.write("---")
                
                # Seleção de campos para editar
                st.write("**Selecione os campos que deseja editar:**")
                fields_to_edit = st.multiselect(
                    "Campos para editar:",
                    options=[field['name'] for field in table_meta['fields']],
                    default=[],
                    key=f"fields_to_edit_{table_meta['name']}_{record_id}"
                )
                
                if fields_to_edit:
                    st.write("**Formulário de edição:**")
                    
                    # Formulário de edição com chave única
                    form_key = f"edit_record_{table_meta['name']}_{record_id}_{len(fields_to_edit)}"
                    with st.form(key=form_key):
                        updated_values = {}
                        
                        for field in table_meta['fields']:
                            field_name = field['name']
                            
                            # Só mostrar campos selecionados para edição
                            if field_name in fields_to_edit:
                                field_type = field['type']
                                current_value = record.get(field_name, "")
                                
                                if field_type == "text":
                                    updated_values[field_name] = st.text_input(
                                        f"{field_name} (Texto)",
                                        value=str(current_value) if current_value is not None else "",
                                        key=f"edit_{table_meta['name']}_{field_name}_{record_id}"
                                    )
                                elif field_type == "int":
                                    # Tratar conversão de valores vazios ou nulos
                                    try:
                                        int_value = int(current_value) if current_value is not None and str(current_value).strip() != "" else 0
                                    except (ValueError, TypeError):
                                        int_value = 0
                                    
                                    updated_values[field_name] = st.number_input(
                                        f"{field_name} (Inteiro)",
                                        value=int_value,
                                        step=1,
                                        key=f"edit_{table_meta['name']}_{field_name}_{record_id}"
                                    )
                                elif field_type == "float":
                                    # Tratar conversão de valores vazios ou nulos
                                    try:
                                        float_value = float(current_value) if current_value is not None and str(current_value).strip() != "" else 0.0
                                    except (ValueError, TypeError):
                                        float_value = 0.0
                                    
                                    updated_values[field_name] = st.number_input(
                                        f"{field_name} (Decimal)",
                                        value=float_value,
                                        step=0.01,
                                        key=f"edit_{table_meta['name']}_{field_name}_{record_id}"
                                    )
                                elif field_type == "date":
                                    if current_value:
                                        try:
                                            current_date = pd.to_datetime(current_value).date()
                                        except:
                                            current_date = datetime.now().date()
                                    else:
                                        current_date = datetime.now().date()
                                    
                                    updated_values[field_name] = st.date_input(
                                        f"{field_name} (Data)",
                                        value=current_date,
                                        key=f"edit_{table_meta['name']}_{field_name}_{record_id}"
                                    )
                                elif field_type == "bool":
                                    updated_values[field_name] = st.checkbox(
                                        f"{field_name} (Sim/Não)",
                                        value=bool(current_value) if current_value is not None else False,
                                        key=f"edit_{table_meta['name']}_{field_name}_{record_id}"
                                    )
                        
                        # Botões de submit DENTRO do form
                        col1, col2 = st.columns(2)
                        with col1:
                            submitted = st.form_submit_button("Atualizar registro")
                        with col2:
                            cancel = st.form_submit_button("Cancelar")
                        
                        # Lógica de processamento FORA do form
                        if submitted:
                            # Remover ID dos valores a atualizar
                            if 'id' in updated_values:
                                del updated_values['id']
                            
                            # Validar se há dados para atualizar
                            if not updated_values:
                                st.warning("Nenhum dado foi modificado.")
                                return
                            
                            # Filtrar valores vazios para campos de texto
                            filtered_values = {}
                            for key, value in updated_values.items():
                                if isinstance(value, str) and value.strip() == "":
                                    filtered_values[key] = None  # Permitir valores NULL
                                else:
                                    filtered_values[key] = value
                            
                            # Atualizar registro
                            if update_record(table_meta['name'], record_id, filtered_values):
                                st.success("Registro atualizado com sucesso!")
                                st.rerun()
                            else:
                                st.error("Erro ao atualizar registro.")
                        
                        if cancel:
                            st.info("Edição cancelada.")
                            st.rerun()
                
                if not fields_to_edit:
                    st.info("Selecione pelo menos um campo para editar.")
                        
    except Exception as e:
        st.error(f"Erro ao carregar dados para edição: {e}")
        st.info("Tente recarregar a página ou verificar se a tabela existe.")


def delete_record_form(table_meta: dict) -> None:
    """Interface para exclusão de registros."""
    # Verificar permissão de exclusão
    username = st.session_state.get("username", "")
    if not check_user_permission(username, table_meta['name'], "delete"):
        st.error("Você não tem permissão para excluir registros desta tabela.")
        return
    
    st.subheader("Excluir registro")
    
    try:
        with get_db_cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_meta['name']}")
            rows = cursor.fetchall()
            
            # Converter para DataFrame manualmente
            if rows:
                data = []
                for row in rows:
                    data.append(dict(row))
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame()
            
            if len(df) == 0:
                st.warning("Nenhum registro encontrado para excluir.")
                return
            
            # Selecionar registro para excluir
            st.write("**Selecione o registro para excluir:**")
            
            selected_index = st.selectbox(
                "Escolha o registro:",
                options=df.index,
                format_func=lambda x: f"ID: {df.iloc[x]['id']} - {' | '.join([f'{col}: {df.iloc[x][col]}' for col in df.columns[:3] if col != 'id'])}",
                key=f"delete_record_select_{table_meta['name']}"
            )
            
            if selected_index is not None:
                record = df.iloc[selected_index].to_dict()
                record_id = record['id']
                
                st.write(f"**Registro selecionado para exclusão:**")
                st.write(f"**ID:** {record_id}")
                
                # Mostrar dados do registro
                for field in table_meta['fields']:
                    field_name = field['name']
                    if field_name in record:
                        st.write(f"**{field_name}:** {record[field_name]}")
                
                # Confirmação de exclusão com chave única
                form_key = f"delete_record_{table_meta['name']}_{record_id}"
                with st.form(key=form_key):
                    st.warning("⚠️ Esta ação não pode ser desfeita!")
                    confirm_delete = st.checkbox("Confirmo que desejo excluir este registro", key=f"confirm_{form_key}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submitted = st.form_submit_button("Excluir registro")
                    with col2:
                        cancel = st.form_submit_button("Cancelar")
                    
                    if submitted and confirm_delete:
                        # Excluir registro
                        try:
                            st.info(f"🔍 Iniciando exclusão do registro ID {record_id}")
                            
                            # Usar conexao direta para debug
                            conn = psycopg2.connect(**db_config.get_connection_params())
                            cursor = conn.cursor()
                            
                            st.info(f"📝 Executando: DELETE FROM {table_meta['name']} WHERE id = {record_id}")
                            
                            # Executar DELETE
                            cursor.execute(f"DELETE FROM {table_meta['name']} WHERE id = %s", (record_id,))
                            
                            # Verificar resultado
                            affected_rows = cursor.rowcount
                            st.info(f"✅ Registros afetados: {affected_rows}")
                            
                            # Commit da transacao
                            conn.commit()
                            
                            if affected_rows > 0:
                                st.success(f"🎉 Registro ID {record_id} excluído com sucesso!")
                                cursor.close()
                                conn.close()
                                st.rerun()
                            else:
                                st.warning(f"⚠️ Nenhum registro foi excluído. ID {record_id} pode não existir.")
                                cursor.close()
                                conn.close()
                                
                        except Exception as e:
                            st.error(f"❌ Erro ao excluir registro: {e}")
                            st.info("🔍 Verifique os logs da aplicação para mais detalhes.")
                            try:
                                if 'cursor' in locals():
                                    cursor.close()
                                if 'conn' in locals():
                                    conn.close()
                            except:
                                pass
                    
                    if cancel:
                        st.info("Exclusão cancelada.")
                        st.rerun()
                        
    except Exception as e:
        st.error(f"Erro ao carregar dados para exclusão: {e}")


def main() -> None:
    """Main entry point for the Streamlit app."""
    # Set page configuration
    st.set_page_config(page_title="Sistema de Cadastros Auxiliares", layout="wide")
    if not st.session_state.get("logged_in"):
        login_screen()
        return
    # Display logo in sidebar if configured
    cfg = load_config()
    if cfg.get("logo"):
        try:
            # Limitar tamanho da logo para nao ocupar muito espaço
            st.sidebar.image(cfg["logo"], width=150, use_column_width=False)
        except Exception:
            pass
    # Show user info and logout button
    st.sidebar.write(f"Usuário: {st.session_state.username}")
    if st.sidebar.button("Sair"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()
    # Main menu
    menu_options = ["Página Inicial", "Gerenciar Tabelas", "Configurações"]
    
    # Verificar permissão de criação de tabelas
    username = st.session_state.get("username", "")
    if check_user_general_permission(username, "create_tables"):
        menu_options.insert(1, "Criar Tabela")
    
    # Only show user management to admin
    if st.session_state.role == "admin":
        menu_options.append("Usuários")
    
    selection = st.sidebar.selectbox("Menu", options=menu_options)
    if selection == "Página Inicial":
        st.title("Sistema de Cadastros Auxiliares")
        st.markdown(
            """\
            Este sistema permite a criação de cadastros flexíveis que servem como
            tabelas auxiliares para o seu ERP ou outro sistema corporativo.  Use
            o menu ao lado para criar novas tabelas, gerenciar registros,
            configurar o sistema ou gerenciar usuários (apenas administradores).
            """
        )
    elif selection == "Criar Tabela":
        page_create_table()
    elif selection == "Gerenciar Tabelas":
        page_manage_tables()
    elif selection == "Configurações":
        page_config()
    elif selection == "Usuários":
        page_manage_users()


if __name__ == "__main__":
    main()