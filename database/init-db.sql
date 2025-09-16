-- Script de inicializacao do banco PostgreSQL para Cadastro Streamlit
-- Este arquivo e executado automaticamente quando o container PostgreSQL e criado

-- Criar extensao para UUID (se necessario)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabela de usuarios
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de metadados das tabelas
CREATE TABLE IF NOT EXISTS tables_metadata (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    display_name VARCHAR(200),
    description TEXT,
    columns JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'ativo' CHECK (status IN ('ativo', 'inativo')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de configuracao
CREATE TABLE IF NOT EXISTS config (
    id SERIAL PRIMARY KEY,
    key_name VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de permissoes de usuarios por tabela
CREATE TABLE IF NOT EXISTS user_table_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    table_name VARCHAR(100) NOT NULL,
    can_view BOOLEAN DEFAULT FALSE,
    can_insert BOOLEAN DEFAULT FALSE,
    can_update BOOLEAN DEFAULT FALSE,
    can_delete BOOLEAN DEFAULT FALSE,
    granted_by INTEGER REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, table_name)
);

-- Tabela de permissoes gerais dos usuarios
CREATE TABLE IF NOT EXISTS user_general_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    can_create_tables BOOLEAN DEFAULT FALSE,
    granted_by INTEGER REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Inserir usuario admin padrao
INSERT INTO users (username, password, role) 
VALUES ('admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'admin')
ON CONFLICT (username) DO NOTHING;

-- Criar usuario admin no PostgreSQL com privilégios de superusuário
-- (Este comando será executado pelo grants_manager)
-- CREATE USER admin WITH PASSWORD 'admin_password' SUPERUSER;

-- Inserir configuracao padrao
INSERT INTO config (key_name, value) 
VALUES ('logo', '')
ON CONFLICT (key_name) DO NOTHING;

-- Criar indices para melhor performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_tables_metadata_name ON tables_metadata(table_name);
CREATE INDEX IF NOT EXISTS idx_config_key ON config(key_name);
CREATE INDEX IF NOT EXISTS idx_user_permissions_user ON user_table_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_permissions_table ON user_table_permissions(table_name);
CREATE INDEX IF NOT EXISTS idx_user_general_permissions_user ON user_general_permissions(user_id);

-- Funcao para atualizar timestamp automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para atualizar timestamp automaticamente
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tables_metadata_updated_at BEFORE UPDATE ON tables_metadata
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_config_updated_at BEFORE UPDATE ON config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
