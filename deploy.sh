#!/bin/bash
# Скрипт для деплоя бота на сервере

set -e  # Остановка при ошибке

echo "🚀 Начало деплоя бота..."

# Определение текущей директории
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Обновление кода
echo "📥 Обновление кода из репозитория..."
git fetch origin
BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
git pull origin "$BRANCH" || git pull origin master

# Активация виртуального окружения (если используется)
if [ -d "venv" ]; then
    echo "🔧 Активация виртуального окружения..."
    source venv/bin/activate
else
    echo "⚠️  Виртуальное окружение не найдено. Создание..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Установка/обновление зависимостей
echo "📦 Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# Перезапуск сервиса (если systemd установлен)
if systemctl is-active --quiet skladtver-bot 2>/dev/null; then
    echo "🔄 Перезапуск сервиса..."
    sudo systemctl restart skladtver-bot
    echo "✅ Сервис перезапущен"
elif systemctl list-units --type=service | grep -q skladtver-bot; then
    echo "⚠️  Сервис найден, но не активен. Попытка запуска..."
    sudo systemctl start skladtver-bot || echo "⚠️  Не удалось запустить сервис"
else
    echo "ℹ️  Systemd сервис не настроен. Бот не будет перезапущен автоматически."
    echo "   Для запуска вручную: source venv/bin/activate && python bot.py"
fi

echo "✅ Деплой завершен!"

