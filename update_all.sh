#!/bin/bash
# Обновление всех изменений Python на GitHub

set -e  # Остановить при ошибке

cd /Users/alexbenedis/1

echo "📦 Добавление всех изменений..."
git add app.py requirements.txt Procfile railway.json nixpacks.toml runtime.txt .gitignore

echo ""
echo "📋 Статус:"
git status --short

echo ""
read -p "Продолжить коммит? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "💾 Создание коммита..."
    git commit -m "Update Python Flask app - Railway deployment, native iOS WebView integration"
    
    echo ""
    echo "🚀 Отправка в GitHub..."
    git push origin main
    
    echo ""
    echo "✅ Готово! Изменения отправлены на GitHub"
else
    echo "❌ Отменено"
fi

