#!/bin/bash
# Скрипт для обновления изменений на GitHub

cd /Users/alexbenedis/1

echo "📦 Добавление измененных файлов..."
git add requirements.txt runtime.txt nixpacks.toml railway.json

echo ""
echo "📋 Статус изменений:"
git status --short

echo ""
echo "💾 Создание коммита..."
git commit -m "Fix Python 3.12 compatibility - update dependencies to compatible versions"

echo ""
echo "🚀 Отправка в GitHub..."
git push origin main

echo ""
echo "✅ Готово! Изменения отправлены в GitHub"
echo "🔍 Проверьте репозиторий: https://github.com/Abenedis/chumakanton"

