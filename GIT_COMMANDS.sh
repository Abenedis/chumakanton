#!/bin/bash
# Скрипт для загрузки проекта в GitHub

cd /Users/alexbenedis/1

echo "📦 Инициализация Git репозитория..."
if [ ! -d .git ]; then
    git init
    echo "✅ Git инициализирован"
else
    echo "✅ Git уже инициализирован"
fi

echo ""
echo "📝 Добавление файлов..."
git add README.md app.py requirements.txt Procfile railway.json README_RAILWAY.md .gitignore DEPLOY_STEPS.md

echo ""
echo "📋 Статус файлов:"
git status --short

echo ""
echo "💾 Создание коммита..."
git commit -m "Initial commit: Flask API for floor plan generation"

echo ""
echo "🌿 Переименование ветки в main..."
git branch -M main

echo ""
echo "🔗 Добавление remote репозитория..."
git remote remove origin 2>/dev/null
git remote add origin https://github.com/Abenedis/chumakanton.git

echo ""
echo "📡 Проверка remote:"
git remote -v

echo ""
echo "🚀 Отправка в GitHub..."
echo "⚠️  Внимание: Вам может потребоваться авторизация GitHub"
git push -u origin main

echo ""
echo "✅ Готово! Проверьте репозиторий: https://github.com/Abenedis/chumakanton"

