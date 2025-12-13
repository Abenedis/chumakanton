# Исправление: externally-managed-environment

## Проблема:
Nix управляет Python окружением, нельзя устанавливать пакеты напрямую через pip

## Решение:
Используем виртуальное окружение Python для установки зависимостей

## Команды для обновления:

```bash
cd /Users/alexbenedis/1

git add nixpacks.toml Procfile

git commit -m "Fix externally-managed-environment - use virtual environment"

git push origin main
```

## Что было исправлено:

- **nixpacks.toml** - создается виртуальное окружение `/opt/venv` и все пакеты устанавливаются туда
- **Procfile** - обновлен для использования gunicorn из виртуального окружения
- Убраны лишние пакеты из nixPkgs (оставлен только python311)

После push Railway должен успешно установить все зависимости в виртуальное окружение.

