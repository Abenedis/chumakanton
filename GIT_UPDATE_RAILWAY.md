# Команды для обновления Railway конфигурации на GitHub

## Выполните эти команды:

```bash
cd /Users/alexbenedis/1

# Добавить все файлы Railway конфигурации
git add app.py requirements.txt Procfile railway.json nixpacks.toml runtime.txt .python-version .gitignore

# Проверить статус
git status

# Создать коммит
git commit -m "Configure for Railway deployment - add nixpacks config, update dependencies, use virtual env"

# Отправить в GitHub
git push origin main
```

## Или выполните скрипт:

```bash
cd /Users/alexbenedis/1
./update_railway_github.sh
```

## Файлы для Railway:

- ✅ `app.py` - поддержка переменных окружения PORT, HOST
- ✅ `requirements.txt` - обновленные версии зависимостей
- ✅ `Procfile` - команда запуска через gunicorn
- ✅ `railway.json` - конфигурация Railway
- ✅ `nixpacks.toml` - конфигурация виртуального окружения
- ✅ `runtime.txt` - версия Python
- ✅ `.python-version` - версия Python для nixpacks
- ✅ `.gitignore` - игнорируемые файлы

После push Railway автоматически пересоберет проект с новой конфигурацией.

