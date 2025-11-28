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

# Настройка systemd сервиса
echo ""
echo "🔧 Настройка systemd сервиса..."

# Определение текущего пользователя
CURRENT_USER=$(whoami)
CURRENT_HOME=$(eval echo ~$CURRENT_USER)
FULL_PATH="$INSTALL_DIR"
VENV_PATH="$INSTALL_DIR/venv"

echo "   Пользователь: $CURRENT_USER"
echo "   Путь к проекту: $FULL_PATH"
echo "   Путь к venv: $VENV_PATH"

# Создание файла сервиса с правильными путями
SERVICE_FILE="/tmp/skladtver-bot.service"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Telegram Bot Sklad Tver
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$FULL_PATH
Environment="PATH=$VENV_PATH/bin"
ExecStart=$VENV_PATH/bin/python $FULL_PATH/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "✅ Файл сервиса создан: $SERVICE_FILE"
echo ""
echo "📋 Следующие шаги:"
echo "1. Отредактируйте файл .env и добавьте токен бота:"
echo "   nano $INSTALL_DIR/.env"
echo ""
echo "2. Скопируйте файл сервиса в systemd:"
echo "   sudo cp $SERVICE_FILE /etc/systemd/system/skladtver-bot.service"
echo ""
echo "3. Запустите сервис:"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable skladtver-bot"
echo "   sudo systemctl start skladtver-bot"
echo ""
echo "4. Проверьте статус:"
echo "   sudo systemctl status skladtver-bot"
echo ""
echo "5. Просмотр логов:"
echo "   sudo journalctl -u skladtver-bot -f"
echo ""

