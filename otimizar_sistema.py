#!/usr/bin/env python3
"""
Script para otimizar o sistema de cadastro.
Resolve problemas de performance e configuracoes.
"""

import os
import json
import shutil
from PIL import Image
import sqlite3

def limpar_logos_antigas():
    """Remove logos antigas e desnecessarias."""
    logos_dir = os.path.join("data", "logos")
    if os.path.exists(logos_dir):
        for file in os.listdir(logos_dir):
            if file.endswith(('.png', '.jpg', '.jpeg')):
                file_path = os.path.join(logos_dir, file)
                try:
                    # Verificar se e uma imagem valida
                    with Image.open(file_path) as img:
                        # Se a imagem for muito grande, redimensionar
                        if img.width > 300 or img.height > 200:
                            print(f"Redimensionando {file}...")
                            ratio = min(300 / img.width, 200 / img.height)
                            new_width = int(img.width * ratio)
                            new_height = int(img.height * ratio)
                            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                            resized_img.save(file_path, quality=95, optimize=True)
                            print(f"✅ {file} redimensionado com sucesso!")
                except Exception as e:
                    print(f"❌ Erro ao processar {file}: {e}")

def otimizar_banco_dados():
    """Otimiza o banco de dados SQLite."""
    db_path = os.path.join("data", "data.db")
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # VACUUM para otimizar o banco
            cursor.execute("VACUUM")
            print("✅ Banco de dados otimizado!")
            
            # ANALYZE para estatisticas
            cursor.execute("ANALYZE")
            print("✅ Estatisticas do banco atualizadas!")
            
            conn.close()
        except Exception as e:
            print(f"❌ Erro ao otimizar banco: {e}")

def limpar_cache():
    """Remove arquivos temporarios e cache."""
    # Limpar arquivos temporarios
    temp_files = [
        ".streamlit/cache",
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "*.pyd"
    ]
    
    for pattern in temp_files:
        if os.path.exists(pattern):
            try:
                if os.path.isdir(pattern):
                    shutil.rmtree(pattern)
                else:
                    os.remove(pattern)
                print(f"✅ Removido: {pattern}")
            except Exception as e:
                print(f"⚠️ Nao foi possivel remover {pattern}: {e}")

def verificar_configuracoes():
    """Verifica e corrige configuracoes do sistema."""
    config_file = "config.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Verificar se a logo existe
            if config.get("logo"):
                logo_path = config["logo"]
                if not os.path.exists(logo_path):
                    print(f"⚠️ Logo nao encontrada: {logo_path}")
                    # Remover referencia da logo
                    config.pop("logo", None)
                    with open(config_file, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2)
                    print("✅ Referencia da logo removida do config")
            
            print("✅ Configuracoes verificadas!")
        except Exception as e:
            print(f"❌ Erro ao verificar configuracoes: {e}")

def criar_diretorios():
    """Cria diretorios necessarios se nao existirem."""
    diretorios = [
        "data",
        "data/logos",
        "config",
        "logs"
    ]
    
    for diretorio in diretorios:
        os.makedirs(diretorio, exist_ok=True)
        print(f"✅ Diretorio criado/verificado: {diretorio}")

def main():
    """Funcao principal de otimizacao."""
    print("🔧 Iniciando otimizacao do sistema...")
    print("=" * 50)
    
    # Criar diretorios necessarios
    print("\n📁 Criando diretorios...")
    criar_diretorios()
    
    # Limpar logos antigas
    print("\n🖼️ Otimizando logos...")
    limpar_logos_antigas()
    
    # Otimizar banco de dados
    print("\n🗄️ Otimizando banco de dados...")
    otimizar_banco_dados()
    
    # Verificar configuracoes
    print("\n⚙️ Verificando configuracoes...")
    verificar_configuracoes()
    
    # Limpar cache
    print("\n🧹 Limpando cache...")
    limpar_cache()
    
    print("\n" + "=" * 50)
    print("✅ Otimizacao concluida!")
    print("\n💡 Dicas para melhorar a performance:")
    print("   - Use logos com tamanho maximo de 300x200 pixels")
    print("   - Mantenha o banco de dados organizado")
    print("   - Reinicie o sistema periodicamente")
    print("   - Monitore o uso de memoria")

if __name__ == "__main__":
    main() 