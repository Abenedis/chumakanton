# Команды для отправки изменений в GitHub

Выполните эти команды в терминале:

```bash
cd /Users/alexbenedis/1

# Добавить измененные файлы
git add requirements.txt runtime.txt nixpacks.toml railway.json

# Проверить статус
git status

# Создать коммит
git commit -m "Fix Python 3.12 compatibility - update dependencies to compatible versions"

# Отправить в GitHub
git push origin main
```

Или выполните скрипт:
```bash
cd /Users/alexbenedis/1
./update_github.sh
```

После успешного push Railway автоматически начнет новый деплой с исправленными зависимостями.

