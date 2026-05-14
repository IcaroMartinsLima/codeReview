#!/bin/bash
# build.sh — gera o executável com PyInstaller

echo "📦 Instalando dependências..."
pip install customtkinter groq pyinstaller --break-system-packages -q

echo "🔨 Gerando executável..."
pyinstaller \
  --onefile \
  --windowed \
  --name "CodeReviewer" \
  --add-data "$(python -c 'import customtkinter; import os; print(os.path.dirname(customtkinter.__file__))'):customtkinter" \
  code_reviewer/main.py

echo ""
echo "✅ Executável gerado em: dist/CodeReviewer"
