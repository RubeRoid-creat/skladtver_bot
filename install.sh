#!/bin/bash
# Скрипт автоматической установки бота на сервере

set -e  # Остановка при ошибке

echo "🚀 Начало установки Telegram бота Sklad Tver..."

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.8 или выше."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Найден Python $PYTHON_VERSION"

# Проверка Git
if ! command -v git &> /dev/null; then
    echo "❌ Git не найден. Установите Git."
    exit 1
fi

echo "✅ Git найден"

# Определение директории установки
INSTALL_DIR="${1:-$HOME/skladtver_bot}"
echo "📁 Директория установки: $INSTALL_DIR"

# Клонирование репозитория
if [ -d "$INSTALL_DIR" ]; then
    echo "⚠️  Директория уже существует. Обновление..."
    cd "$INSTALL_DIR"
    git pull origin main || git pull origin master
else
    echo "📥 Клонирование репозитория..."
    git clone https://github.com/RubeRoid-creat/skladtver_bot.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo "🔧 Создание виртуального окружения..."
    python3 -m venv venv
else
    echo "✅ Виртуальное окружение уже существует"
fi

# Активация виртуального окружения
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Установка зависимостей
echo "📦 Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# Создание файла .env если его нет
if [ ! -f ".env" ]; then
    echo "📝 Создание файла .env..."
    echo "BOT_TOKEN=your_telegram_bot_token_here" > .env
    echo "⚠️  ВАЖНО: Отредактируйте файл .env и добавьте токен бота!"
    echo "   nano $INSTALL_DIR/.env"
else
    echo "✅ Файл .env уже существует"
fi

echo ""
echo "✅ Установка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Отредактируйте файл .env и добавьте токен бота:"
echo "   nano $INSTALL_DIR/.env"
echo ""
echo "2. Настройте systemd сервис:"
echo "   sudo nano /etc/systemd/system/skladtver-bot.service"
echo "   (Измените пути в файле skladtver-bot.service)"
echo ""
echo "3. Запустите сервис:"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable skladtver-bot"
echo "   sudo systemctl start skladtver-bot"
echo ""
echo "4. Проверьте статус:"
echo "   sudo systemctl status skladtver-bot"
echo ""

