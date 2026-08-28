#!/bin/bash

set -e

# Переходим в директорию скрипта
cd "$(dirname "$0")"

echo "================================"
echo "       CASE CLUB BOT"
echo "================================"
echo

# Проверяем Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден."
    echo
    echo "Установите Python 3 и запустите этот файл ещё раз."
    echo
    exit 1
fi

echo "✓ Python найден:"
python3 --version
echo

# Проверяем requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo "❌ Файл requirements.txt не найден!"
    echo
    echo "Создайте его командой:"
    echo "  pip freeze > requirements.txt"
    echo
    exit 1
fi

# Создаём виртуальное окружение
if [ ! -d ".venv" ]; then
    echo "📦 Создаём виртуальное окружение..."
    python3 -m venv .venv
    echo "✓ Виртуальное окружение создано"
    echo
fi

# Обновляем pip
echo "📦 Проверяем зависимости..."
.venv/bin/python -m pip install --upgrade pip --quiet

# Устанавливаем зависимости
.venv/bin/python -m pip install -r requirements.txt --quiet

echo "✓ Все зависимости установлены"
echo

# Проверяем .env файл
if [ ! -f ".env" ]; then
    echo "⚠️  Файл .env не найден!"
    echo
    echo "Создайте .env файл с BOT_TOKEN:"
    echo "  echo 'BOT_TOKEN=ваш_токен' > .env"
    echo
    exit 1
fi

# Функция для остановки
stop_bot() {
    echo
    echo "👋 Бот остановлен"
    exit 0
}

trap stop_bot SIGINT SIGTERM

echo "🤖 Запускаем бота..."
echo
echo "================================"
echo

# Запускаем бота (без exec)
.venv/bin/python src/app.py

# Если бот упал
echo
echo "❌ Бот завершил работу с ошибкой"
exit 1