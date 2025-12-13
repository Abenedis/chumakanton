# Команды для обновления Python изменений на GitHub

## Выполните эти команды в терминале:

```bash
cd /Users/alexbenedis/1

# Добавить все измененные файлы
git add -A

# Или добавить конкретные файлы:
git add app.py requirements.txt Procfile railway.json nixpacks.toml runtime.txt .gitignore

# Проверить статус
git status

# Создать коммит
git commit -m "Update Python Flask app - Railway deployment, native iOS WebView integration"

# Отправить в GitHub
git push origin main
```

## Или выполните скрипт:

```bash
cd /Users/alexbenedis/1
./update_python_github.sh
```

## Основные изменения Python:

- ✅ `app.py` - Flask приложение с CORS для Railway
- ✅ `requirements.txt` - зависимости для Python 3.11/3.12
- ✅ `Procfile` - команда запуска через gunicorn
- ✅ `railway.json` - конфигурация Railway
- ✅ `nixpacks.toml` - конфигурация виртуального окружения
- ✅ `runtime.txt` - версия Python 3.11.0
- ✅ `.gitignore` - игнорируемые файлы

После push Railway автоматически пересоберет проект с новой конфигурацией.

