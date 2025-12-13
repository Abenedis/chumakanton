#!/bin/bash
# Скрипт для обновления Railway конфигурации на GitHub

cd /Users/alexbenedis/1

echo "📦 Добавление файлов Railway конфигурации..."
git add app.py requirements.txt Procfile railway.json nixpacks.toml runtime.txt .python-version .gitignore

echo ""
echo "📋 Статус изменений:"
git status --short

echo ""
echo "💾 Создание коммита..."
git commit -m "Configure for Railway deployment - add nixpacks config, update dependencies, use virtual env"

echo ""
echo "🚀 Отправка в GitHub..."
git push origin main

echo ""
echo "✅ Готово! Railway конфигурация обновлена на GitHub"
echo "🔍 Проверьте репозиторий: https://github.com/Abenedis/chumakanton"

