# Команды для обновления на GitHub

## Выполните эти команды в терминале:

```bash
# Перейдите в папку проекта
cd /Users/alexbenedis/1

# Добавьте все измененные файлы
git add requirements.txt runtime.txt nixpacks.toml railway.json

# Проверьте статус (опционально)
git status

# Создайте коммит
git commit -m "Fix Python 3.12 compatibility - update dependencies to compatible versions"

# Отправьте в GitHub
git push origin main
```

## Или выполните все одной командой:

```bash
cd /Users/alexbenedis/1 && \
git add requirements.txt runtime.txt nixpacks.toml railway.json && \
git commit -m "Fix Python 3.12 compatibility - update dependencies to compatible versions" && \
git push origin main
```

## Или используйте готовый скрипт:

```bash
cd /Users/alexbenedis/1
./update_github.sh
```

## После успешного push:

1. Railway автоматически обнаружит изменения
2. Начнется новый деплой
3. Проверьте логи в Railway dashboard
4. Дождитесь завершения деплоя (2-5 минут)

## Проверка:

После push откройте:
https://github.com/Abenedis/chumakanton

Вы должны увидеть обновленные файлы:
- ✅ requirements.txt (обновленные версии)
- ✅ runtime.txt (Python 3.11)
- ✅ nixpacks.toml (конфигурация Railway)
- ✅ railway.json (обновленная команда запуска)

