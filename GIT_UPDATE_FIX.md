# Обновление для исправления ошибки pip

## Проблема:
Railway не может найти команду `pip`

## Решение:
Обновлены файлы конфигурации для правильной установки зависимостей

## Команды для обновления:

```bash
cd /Users/alexbenedis/1

git add nixpacks.toml railway.json .python-version

git commit -m "Fix pip command not found - use python3 -m pip"

git push origin main
```

## Что было исправлено:

1. **nixpacks.toml** - теперь использует `python3 -m pip` вместо `pip`
2. **railway.json** - упрощена конфигурация (Railway автоматически использует nixpacks.toml)
3. **.python-version** - добавлен файл для указания версии Python

После push Railway должен успешно установить зависимости.

