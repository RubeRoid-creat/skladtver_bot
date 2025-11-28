#!/bin/bash
# Скрипт для настройки systemd сервиса

set -e

echo "🔧 Настройка systemd сервиса для skladtver-bot..."

# Определение текущего пользователя и путей
CURRENT_USER=$(whoami)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
FULL_PATH="$SCRIPT_DIR"
VENV_PATH="$SCRIPT_DIR/venv"

echo "   Пользователь: $CURRENT_USER"
echo "   Путь к проекту: $FULL_PATH"
echo "   Путь к venv: $VENV_PATH"

# Проверка существования venv
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Виртуальное окружение не найдено в $VENV_PATH"
    echo "   Создайте его: python3 -m venv venv"
    exit 1
fi

# Проверка существования bot.py
if [ ! -f "$FULL_PATH/bot.py" ]; then
    echo "❌ Файл bot.py не найден в $FULL_PATH"
    exit 1
fi

# Создание файла сервиса
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
echo "1. Скопируйте файл сервиса в systemd:"
echo "   sudo cp $SERVICE_FILE /etc/systemd/system/skladtver-bot.service"
echo ""
echo "2. Перезагрузите systemd:"
echo "   sudo systemctl daemon-reload"
echo ""
echo "3. Включите автозапуск:"
echo "   sudo systemctl enable skladtver-bot"
echo ""
echo "4. Запустите сервис:"
echo "   sudo systemctl start skladtver-bot"
echo ""
echo "5. Проверьте статус:"
echo "   sudo systemctl status skladtver-bot"
echo ""
echo "6. Просмотр логов:"
echo "   sudo journalctl -u skladtver-bot -f"
echo ""

