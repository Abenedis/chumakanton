# Деплой Flask приложения на Railway

## Подготовка к деплою

### 1. Установите Railway CLI (опционально)
```bash
npm i -g @railway/cli
railway login
```

### 2. Создайте проект на Railway

1. Перейдите на [railway.app](https://railway.app)
2. Войдите через GitHub
3. Нажмите "New Project"
4. Выберите "Deploy from GitHub repo"
5. Выберите ваш репозиторий с Python кодом

### 3. Настройка переменных окружения

В настройках проекта Railway добавьте переменные окружения (опционально):

- `FLASK_DEBUG=false` - для production режима
- `PORT` - Railway автоматически установит порт (не нужно менять)

### 4. Деплой

Railway автоматически определит Python проект и установит зависимости из `requirements.txt`.

После деплоя Railway предоставит вам URL вида:
`https://your-app-name.railway.app`

### 5. Обновите Flutter код

В файле `flutter_module_chumak/lib/services/floor_plan_service.dart`:

1. Замените `'https://your-app-name.railway.app'` на ваш Railway URL
2. Установите `useLocalhost = false` для production

## Проверка работы

После деплоя проверьте:

1. Откройте в браузере: `https://your-app-name.railway.app/`
2. Должна открыться страница с загрузкой JSON
3. Проверьте endpoint: `https://your-app-name.railway.app/convert` (должен вернуть ошибку без данных, но не 404)

## Структура файлов для Railway

```
/
├── app.py              # Главный файл приложения
├── requirements.txt    # Зависимости Python
├── Procfile           # Команда запуска для Railway
├── railway.json       # Конфигурация Railway (опционально)
└── .gitignore         # Игнорируемые файлы
```

## Важные замечания

1. **CORS**: Уже настроен в коде для работы с Flutter
2. **Порт**: Railway автоматически устанавливает переменную `PORT`
3. **HTTPS**: Railway предоставляет HTTPS по умолчанию
4. **Таймауты**: Railway имеет лимиты на время выполнения запросов (обычно 60 секунд)

## Локальная разработка

Для локальной разработки установите в `floor_plan_service.dart`:
```dart
static const bool useLocalhost = true;
```

И запустите локальный сервер:
```bash
python3 app.py
```

