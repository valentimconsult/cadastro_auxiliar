"""
Configuracao de banco de dados PostgreSQL para Cadastro Streamlit
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Classe para gerenciar configuracao do banco PostgreSQL"""
    
    def __init__(self):
        self.host = os.getenv('POSTGRES_HOST', 'localhost')
        self.port = os.getenv('POSTGRES_PORT', '5436')
        self.database = os.getenv('POSTGRES_DB', 'cadastro_db')
        self.user = os.getenv('POSTGRES_USER', 'cadastro_user')
        self.password = os.getenv('POSTGRES_PASSWORD', 'cadastro_password')
        
    def get_connection_string(self):
        """Retorna string de conexao para PostgreSQL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    def get_connection_params(self):
        """Retorna parametros de conexao como dicionario"""
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password
        }

# Instancia global da configuracao
db_config = DatabaseConfig()

@contextmanager
def get_db_connection():
    """
    Context manager para conexao com banco PostgreSQL
    Retorna conexao com cursor RealDictCursor para acesso por nome de coluna
    """
    conn = None
    try:
        conn = psycopg2.connect(**db_config.get_connection_params())
        conn.autocommit = False
        yield conn
    except psycopg2.Error as e:
        logger.error(f"Erro ao conectar com PostgreSQL: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

@contextmanager
def get_db_cursor(connection=None):
    """
    Context manager para cursor do banco PostgreSQL
    Retorna cursor com RealDictCursor para acesso por nome de coluna
    """
    conn = connection
    should_close = False
    
    if not conn:
        conn = psycopg2.connect(**db_config.get_connection_params())
        should_close = True
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro na operacao do banco: {e}")
        raise
    finally:
        cursor.close()
        if should_close and conn:
            conn.close()

def test_connection():
    """Testa conexao com o banco PostgreSQL"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                logger.info(f"Conexao com PostgreSQL estabelecida. Versao: {version[0]}")
                return True
    except Exception as e:
        logger.error(f"Falha na conexao com PostgreSQL: {e}")
        return False

def create_tables_if_not_exist():
    """Cria tabelas basicas se nao existirem"""
    try:
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cursor:
                # Verificar se tabelas ja existem
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('users', 'tables_metadata', 'config')
                """)
                existing_tables = [row['table_name'] for row in cursor.fetchall()]
                
                if len(existing_tables) < 3:
                    logger.info("Criando tabelas basicas...")
                    
                    # Executar script de inicializacao
                    with open('init-db.sql', 'r', encoding='utf-8') as f:
                        init_script = f.read()
                    
                    cursor.execute(init_script)
                    logger.info("Tabelas basicas criadas com sucesso!")
                else:
                    logger.info("Tabelas basicas ja existem")
                    
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        raise

if __name__ == "__main__":
    # Teste da configuracao
    print("Testando configuracao do banco...")
    if test_connection():
        print("Conexao OK!")
        create_tables_if_not_exist()
    else:
        print("Falha na conexao!")
