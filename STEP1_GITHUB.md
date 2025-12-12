# Шаг 1: Загрузка в GitHub

## Выполните эти команды в терминале:

```bash
# Перейдите в папку с Python проектом
cd /Users/alexbenedis/1

# Инициализация Git (если еще не сделано)
git init

# Добавление файлов
git add README.md app.py requirements.txt Procfile railway.json README_RAILWAY.md .gitignore DEPLOY_STEPS.md

# Проверка статуса
git status

# Настройка Git (если еще не настроено)
git config user.name "Abenedis"
git config user.email "your-email@example.com"

# Создание коммита
git commit -m "Initial commit: Flask API for floor plan generation"

# Переименование ветки в main
git branch -M main

# Добавление remote репозитория
git remote add origin https://github.com/Abenedis/chumakanton.git

# Если remote уже существует, используйте:
# git remote set-url origin https://github.com/Abenedis/chumakanton.git

# Отправка в GitHub
git push -u origin main
```

## ⚠️ Если потребуется авторизация:

GitHub может запросить авторизацию. Используйте:
- Personal Access Token (рекомендуется)
- Или GitHub CLI: `gh auth login`

## ✅ Проверка:

После успешного push откройте:
https://github.com/Abenedis/chumakanton

Вы должны увидеть все файлы проекта.

---

## 🚀 Следующий шаг:

После успешной загрузки в GitHub переходите к **Шагу 2: Деплой на Railway**
(см. файл `DEPLOY_STEPS.md`)

