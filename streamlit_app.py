import streamlit as st
import os
import json
import hashlib
import pandas as pd
from datetime import datetime
import io
import base64
from PIL import Image
from database.db_config import get_db_connection, get_db_cursor


# Paths for configuration and data.  The app writes all of its state into
# files next to the application code.  When running inside Docker these
# will live in the container's filesystem; when running locally they'll
# live in the project directory.  Creating the data directory if it
# does not exist ensures the SQLite database has somewhere to live.
DATA_DIR = "data"
USERS_FILE = "users.json"
TABLES_FILE = "tables.json"
CONFIG_FILE = "config.json"

os.makedirs(DATA_DIR, exist_ok=True)

# Create the initial configuration files if they are missing.  A default
# admin user is created with username "admin" and password "admin".
if not os.path.exists(USERS_FILE):
    default_admin_pwd = hashlib.sha256("admin".encode("utf-8")).hexdigest()
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({"admin": {"password": default_admin_pwd, "role": "admin"}}, f, indent=2)

if not os.path.exists(TABLES_FILE):
    with open(TABLES_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"logo": ""}, f)


def hash_password(password: str) -> str:
    """Return a SHA‑256 hash of the provided password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def load_users() -> dict:
    """Load the user database from the JSON file."""
    with open(USERS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_users(users: dict) -> None:
    """Persist the user database back to disk."""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def load_tables_metadata() -> list:
    """Load the table definitions from disk."""
    with open(TABLES_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_tables_metadata(metadata: list) -> None:
    """Write the table definitions back to disk."""
    with open(TABLES_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


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
    """Insert multiple records into the specified table with duplicate checking.
    
    Returns a tuple (inserted_count, duplicate_count, errors)
    """
    inserted_count = 0
    duplicate_count = 0
    errors = []
    
    # Get existing records for duplicate checking
    existing_records = set()
    try:
        with get_db_cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name}")
            for row in cursor.fetchall():
                # Create a tuple of values (excluding id) for comparison
                existing_records.add(tuple(row[1:]))  # Skip id column
    except Exception as e:
        errors.append(f"Erro ao verificar registros existentes: {e}")
        return 0, 0, errors
    
    # Build column names
    column_names = []
    for field in fields:
        fname = field['name']
        sql_name = sanitize_identifier(fname)
        column_names.append(sql_name)
    
    # Prepare SQL statement
    placeholders = ["%s"] * len(column_names)
    sql = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({', '.join(placeholders)})"
    
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
                
                value_list.append(value)
            
            # Check for duplicates
            record_tuple = tuple(value_list)
            if record_tuple in existing_records:
                duplicate_count += 1
                continue
            
            # Insert record
            with get_db_cursor() as cursor:
                cursor.execute(sql, value_list)
            inserted_count += 1
            existing_records.add(record_tuple)
            
        except Exception as e:
            errors.append(f"Erro na linha {i+1}: {e}")
    
    return inserted_count, duplicate_count, errors


def generate_template_csv(table_meta: dict) -> str:
    """Generate a CSV template for the given table."""
    # Create a DataFrame with column headers
    headers = [field['name'] for field in table_meta['fields']]
    df = pd.DataFrame(columns=headers)
    
    # Add example row
    example_row = {}
    for field in table_meta['fields']:
        if field['type'] == 'text':
            example_row[field['name']] = 'Exemplo de texto'
        elif field['type'] == 'int':
            example_row[field['name']] = 123
        elif field['type'] == 'float':
            example_row[field['name']] = 123.45
        elif field['type'] == 'date':
            example_row[field['name']] = '2024-01-01'
        elif field['type'] == 'bool':
            example_row[field['name']] = 'True'
    
    df = pd.DataFrame([example_row])
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
            else:  # text, date
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
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = users[username].get("role", "user")
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos.")


def page_create_table() -> None:
    """Render the page that allows administrators to define new tables."""
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
        metadata.append({
            "name": table_name,
            "display_name": table_display_name,
            "fields": field_defs,
            "created_by": st.session_state.username,
            "created_at": datetime.now().isoformat(),
        })
        save_tables_metadata(metadata)
        st.success("Tabela criada com sucesso!")


def page_manage_tables() -> None:
    """Render the page for managing existing tables: viewing data, adding
    records, altering structure or deleting tables."""
    st.header("Gerenciar tabelas existentes")
    metadata = load_tables_metadata()
    if not metadata:
        st.info("Nenhuma tabela foi criada ainda.")
        return
    table_names = [t['display_name'] for t in metadata]
    choice = st.selectbox("Selecione a tabela", options=table_names)
    selected_meta = next((t for t in metadata if t['display_name'] == choice), None)
    if selected_meta is None:
        st.error("Tabela não encontrada.")
        return
    # Show basic information about the table
    st.subheader(f"Tabela: {selected_meta['display_name']}")
    st.write("Campos:")
    fields_df = pd.DataFrame(selected_meta['fields'])
    st.table(fields_df)
    # Subpage navigation
    subpage = st.radio("O que você deseja fazer?", [
        "Adicionar registro", 
        "Carga em lote", 
        "Visualizar dados", 
        "Editar registro",
        "Excluir registro",
        "Adicionar campo", 
        "Excluir tabela"
    ])
    if subpage == "Adicionar registro":
        add_record_form(selected_meta)
    elif subpage == "Carga em lote":
        batch_upload_form(selected_meta)
    elif subpage == "Visualizar dados":
        view_table_data(selected_meta)
    elif subpage == "Editar registro":
        edit_record_form(selected_meta)
    elif subpage == "Excluir registro":
        delete_record_form(selected_meta)
    elif subpage == "Adicionar campo":
        add_field_to_table(selected_meta)
    elif subpage == "Excluir tabela":
        delete_table(selected_meta)


def batch_upload_form(table_meta: dict) -> None:
    """Display a form for batch upload of records via CSV."""
    st.subheader("Carga em lote via CSV")
    
    # Generate and download template
    st.write("**Passo 1: Baixe o modelo CSV**")
    template_csv = generate_template_csv(table_meta)
    st.download_button(
        label="Baixar modelo CSV",
        data=template_csv,
        file_name=f"modelo_{table_meta['name']}.csv",
        mime="text/csv"
    )
    
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
    st.subheader("Visualizar dados")
    with get_db_connection() as conn:
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_meta['name']}", conn)
            
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
            except Exception as e:
                st.error(f"Erro ao adicionar coluna: {e}")
                return
            # Append to metadata and save
            metadata = load_tables_metadata()
            for t in metadata:
                if t['name'] == table_meta['name']:
                    t['fields'].append({"name": fname, "type": canonical_type})
                    break
            save_tables_metadata(metadata)
            st.success("Campo adicionado com sucesso!")
            st.experimental_rerun()


def delete_table(table_meta: dict) -> None:
    """Allow the administrator to remove a table permanently."""
    st.subheader("Excluir tabela")
    st.warning(
        "Esta ação removerá permanentemente a tabela e todos os dados associados. "
        "Esta operação não pode ser desfeita."
    )
    if st.button("Confirmar exclusão"):
        try:
            drop_table(table_meta['name'])
            # Remove metadata
            metadata = load_tables_metadata()
            metadata = [t for t in metadata if t['name'] != table_meta['name']]
            save_tables_metadata(metadata)
            st.success("Tabela excluída com sucesso!")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Erro ao excluir tabela: {e}")


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
        st.experimental_rerun()


def page_manage_users() -> None:
    """Render the user management page.  Only administrators may use this."""
    st.header("Gerenciamento de usuários")
    if st.session_state.role != "admin":
        st.error("Acesso negado. Apenas administradores podem gerenciar usuários.")
        return
    users = load_users()
    st.subheader("Usuários cadastrados")
    user_list = list(users.keys())
    st.table(pd.DataFrame([
        {"Usuário": u, "Perfil": users[u].get("role", "user")} for u in user_list
    ]))
    st.divider()
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
                st.experimental_rerun()
    st.divider()
    st.subheader("Excluir usuário")
    if len(users) > 1:
        selected_user = st.selectbox("Selecione o usuário a excluir", options=[u for u in users if u != "admin"])
        if st.button("Excluir usuário"):
            if selected_user in users:
                del users[selected_user]
                save_users(users)
                st.success("Usuário excluído com sucesso!")
                st.experimental_rerun()
    else:
        st.info("Nenhum usuário removível.")


def get_record_by_id(table_name: str, record_id: int) -> dict:
    """Busca um registro específico por ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (record_id,))
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
    st.subheader("Editar registro")
    
    # Buscar registros para seleção
    with get_db_connection() as conn:
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_meta['name']}", conn)
            
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
                            submitted = st.form_submit_button("Atualizar registro", key=f"submit_{form_key}")
                        with col2:
                            cancel = st.form_submit_button("Cancelar", key=f"cancel_{form_key}")
                        
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
                                st.experimental_rerun()
                            else:
                                st.error("Erro ao atualizar registro.")
                        
                        if cancel:
                            st.info("Edição cancelada.")
                            st.experimental_rerun()
                
                if not fields_to_edit:
                    st.info("Selecione pelo menos um campo para editar.")
                        
        except Exception as e:
            st.error(f"Erro ao carregar dados para edição: {e}")
            st.info("Tente recarregar a página ou verificar se a tabela existe.")


def delete_record_form(table_meta: dict) -> None:
    """Interface para exclusão de registros."""
    st.subheader("Excluir registro")
    
    with get_db_connection() as conn:
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_meta['name']}", conn)
            
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
                        submitted = st.form_submit_button("Excluir registro", key=f"submit_{form_key}")
                    with col2:
                        cancel = st.form_submit_button("Cancelar", key=f"cancel_{form_key}")
                    
                    if submitted and confirm_delete:
                        # Excluir registro
                        with get_db_cursor() as cursor:
                            cursor.execute(f"DELETE FROM {table_meta['name']} WHERE id = %s", (record_id,))
                            
                            if cursor.rowcount > 0:
                                st.success("Registro excluído com sucesso!")
                                st.experimental_rerun()
                            else:
                                st.error("Erro ao excluir registro.")
                    
                    if cancel:
                        st.info("Exclusão cancelada.")
                        st.experimental_rerun()
                        
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
        st.experimental_rerun()
    # Main menu
    menu_options = ["Página Inicial", "Criar Tabela", "Gerenciar Tabelas", "Configurações"]
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