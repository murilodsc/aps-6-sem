#!/bin/bash

# Script para limpar todos os arquivos de cache Python

echo "🧹 Limpando cache Python..."

# Remover diretórios __pycache__
find . -type d -name "__pycache__" -not -path "./.venv/*" -not -path "./venv/*" -exec rm -rf {} + 2>/dev/null

# Remover arquivos .pyc
find . -name "*.pyc" -not -path "./.venv/*" -not -path "./venv/*" -delete 2>/dev/null

# Remover arquivos .pyo
find . -name "*.pyo" -not -path "./.venv/*" -not -path "./venv/*" -delete 2>/dev/null

# Remover arquivos .pyd
find . -name "*.pyd" -not -path "./.venv/*" -not -path "./venv/*" -delete 2>/dev/null

# Limpar cache do pytest
rm -rf .pytest_cache 2>/dev/null

# Limpar cache do mypy
rm -rf .mypy_cache 2>/dev/null

# Limpar .DS_Store (macOS)
find . -name ".DS_Store" -delete 2>/dev/null

echo "✅ Cache limpo com sucesso!"
echo ""
echo "📊 Arquivos restantes (deve estar vazio):"
find . -name "*.pyc" -o -name "__pycache__" -type d | grep -v ".venv" | wc -l
echo " arquivos/diretórios de cache encontrados"
