#!/usr/bin/env python3
"""
Script para configurar o sistema de grants PostgreSQL.
Este script deve ser executado após a criação do banco de dados.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.grants_manager import grants_manager
from database.db_config import test_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_admin_user():
    """Configura o usuário admin no PostgreSQL."""
    try:
        # Criar usuário admin no PostgreSQL
        admin_password = "admin_password_123"  # Senha segura para o admin
        
        if grants_manager.create_database_user(
            username="admin",
            password=admin_password,
            role="admin"
        ):
            logger.info("✅ Usuário admin criado no PostgreSQL")
            
            # Aplicar permissões de admin
            grants_manager.grant_general_permissions("admin", True)
            logger.info("✅ Permissões de admin aplicadas")
            
            return True
        else:
            logger.error("❌ Falha ao criar usuário admin")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao configurar admin: {e}")
        return False

def test_grants_system():
    """Testa o sistema de grants."""
    try:
        # Testar conexão do admin
        if grants_manager.test_user_connection("admin", "admin_password_123"):
            logger.info("✅ Teste de conexão do admin passou")
        else:
            logger.error("❌ Teste de conexão do admin falhou")
            return False
        
        # Listar permissões do admin
        permissions = grants_manager.get_user_permissions("admin")
        if permissions:
            logger.info("✅ Permissões do admin listadas com sucesso")
            logger.info(f"   Tabelas: {len(permissions['table_permissions'])}")
            logger.info(f"   Schemas: {len(permissions['schema_permissions'])}")
        else:
            logger.warning("⚠️ Não foi possível listar permissões do admin")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de grants: {e}")
        return False

def main():
    """Executa a configuração completa."""
    logger.info("🚀 Iniciando configuração do sistema de grants PostgreSQL...")
    
    # Verificar conexão com banco
    if not test_connection():
        logger.error("❌ Falha na conexão com banco de dados")
        return False
    
    logger.info("✅ Conexão com banco OK")
    
    # Configurar usuário admin
    if not setup_admin_user():
        logger.error("❌ Falha na configuração do admin")
        return False
    
    # Testar sistema
    if not test_grants_system():
        logger.error("❌ Falha no teste do sistema")
        return False
    
    logger.info("🎉 Sistema de grants PostgreSQL configurado com sucesso!")
    logger.info("📋 Próximos passos:")
    logger.info("   1. Reinicie o Docker Compose")
    logger.info("   2. Acesse a aplicação como admin")
    logger.info("   3. Vá em 'Usuários' > 'PostgreSQL Grants' para gerenciar usuários")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
