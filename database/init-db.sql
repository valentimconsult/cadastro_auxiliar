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

-- Inserir usuario admin padrao
INSERT INTO users (username, password, role) 
VALUES ('admin', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 'admin')
ON CONFLICT (username) DO NOTHING;

-- Inserir configuracao padrao
INSERT INTO config (key_name, value) 
VALUES ('logo', '')
ON CONFLICT (key_name) DO NOTHING;

-- Criar indices para melhor performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_tables_metadata_name ON tables_metadata(table_name);
CREATE INDEX IF NOT EXISTS idx_config_key ON config(key_name);

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
