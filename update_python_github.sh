#!/bin/bash
# Скрипт для обновления всех изменений Python на GitHub

cd /Users/alexbenedis/1

echo "📦 Добавление всех изменений Python..."
git add -A

echo ""
echo "📋 Статус изменений:"
git status --short

echo ""
echo "💾 Создание коммита..."
git commit -m "Update Python Flask app - Railway deployment, native iOS WebView integration"

echo ""
echo "🚀 Отправка в GitHub..."
git push origin main

echo ""
echo "✅ Готово! Все изменения Python обновлены на GitHub"

