# Быстрый старт - Развертывание на сервере

## Автоматическая установка

```bash
# Скачайте и запустите скрипт установки
curl -o install.sh https://raw.githubusercontent.com/RubeRoid-creat/skladtver_bot/main/install.sh
chmod +x install.sh
./install.sh
```

Или клонируйте репозиторий и запустите:

```bash
git clone https://github.com/RubeRoid-creat/skladtver_bot.git
cd skladtver_bot
chmod +x install.sh
./install.sh
```

## Ручная установка (пошагово)

### 1. Подключитесь к серверу

```bash
ssh user@your-server.com
```

### 2. Клонируйте репозиторий

```bash
cd ~
git clone https://github.com/RubeRoid-creat/skladtver_bot.git
cd skladtver_bot
```

### 3. Создайте виртуальное окружение

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Установите зависимости

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Настройте токен бота

```bash
nano .env
```

Добавьте:
```
BOT_TOKEN=ваш_токен_бота_здесь
```

Сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`

### 6. Настройте systemd сервис

```bash
# Скопируйте файл сервиса
sudo cp skladtver-bot.service /etc/systemd/system/

# Отредактируйте пути
sudo nano /etc/systemd/system/skladtver-bot.service
```

Измените:
- `User=YOUR_USER` → `User=ваш_пользователь`
- `WorkingDirectory=/path/to/skladtver_bot` → `WorkingDirectory=/home/ваш_пользователь/skladtver_bot`
- `Environment="PATH=/path/to/venv/bin"` → `Environment="PATH=/home/ваш_пользователь/skladtver_bot/venv/bin"`
- `ExecStart=/path/to/venv/bin/python /path/to/skladtver_bot/bot.py` → `ExecStart=/home/ваш_пользователь/skladtver_bot/venv/bin/python /home/ваш_пользователь/skladtver_bot/bot.py`

### 7. Запустите сервис

```bash
# Перезагрузите systemd
sudo systemctl daemon-reload

# Включите автозапуск
sudo systemctl enable skladtver-bot

# Запустите сервис
sudo systemctl start skladtver-bot

# Проверьте статус
sudo systemctl status skladtver-bot
```

### 8. Проверьте логи

```bash
# Просмотр логов в реальном времени
sudo journalctl -u skladtver-bot -f

# Просмотр последних логов
sudo journalctl -u skladtver-bot -n 50
```

## Полезные команды

```bash
# Остановить бота
sudo systemctl stop skladtver-bot

# Запустить бота
sudo systemctl start skladtver-bot

# Перезапустить бота
sudo systemctl restart skladtver-bot

# Проверить статус
sudo systemctl status skladtver-bot

# Просмотр логов
sudo journalctl -u skladtver-bot -f

# Обновление бота
cd ~/skladtver_bot
./deploy.sh
```

## Альтернатива: Запуск без systemd

Если у вас нет прав root или не хотите использовать systemd:

```bash
# Запуск в screen
screen -S skladtver-bot
cd ~/skladtver_bot
source venv/bin/activate
python bot.py
# Нажмите Ctrl+A, затем D для отсоединения

# Или с nohup
cd ~/skladtver_bot
source venv/bin/activate
nohup python bot.py > bot.log 2>&1 &
```

## Решение проблем

### Бот не запускается

1. Проверьте токен в `.env`:
```bash
cat .env
```

2. Проверьте логи:
```bash
sudo journalctl -u skladtver-bot -n 100
```

3. Проверьте права доступа:
```bash
ls -la ~/skladtver_bot
chmod +x bot.py
```

### Ошибка "BOT_TOKEN не найден"

Убедитесь, что файл `.env` существует и содержит токен:
```bash
cat .env
```

### Ошибка подключения к базе данных

Проверьте права на файл базы данных:
```bash
ls -la warehouse.db
chmod 644 warehouse.db
```

## Поддержка

Если возникли проблемы, проверьте:
- Логи сервиса: `sudo journalctl -u skladtver-bot -f`
- Файл `.env` с токеном
- Права доступа к файлам
- Версию Python (должна быть 3.8+)

