# Инструкция по развертыванию бота на сервере

## Требования

- Python 3.8 или выше
- Git
- systemd (для Linux)

## Шаги развертывания

### 1. Клонирование репозитория

```bash
git clone https://github.com/RubeRoid-creat/skladtver_bot.git
cd skladtver_bot
```

### 2. Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate  # Для Linux/Mac
# или
venv\Scripts\activate  # Для Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```bash
nano .env
```

Добавьте токен бота:

```
BOT_TOKEN=ваш_токен_бота
```

### 5. Настройка systemd сервиса (для Linux)

1. Скопируйте файл `skladtver-bot.service` в `/etc/systemd/system/`:

```bash
sudo cp skladtver-bot.service /etc/systemd/system/
```

2. Отредактируйте файл сервиса:

```bash
sudo nano /etc/systemd/system/skladtver-bot.service
```

Измените следующие параметры:
- `User=YOUR_USER` - замените на ваше имя пользователя
- `WorkingDirectory=/path/to/skladtver_bot` - путь к проекту
- `Environment="PATH=/path/to/venv/bin"` - путь к виртуальному окружению
- `ExecStart=/path/to/venv/bin/python /path/to/skladtver_bot/bot.py` - полный путь к Python и скрипту

3. Перезагрузите systemd:

```bash
sudo systemctl daemon-reload
```

4. Включите автозапуск:

```bash
sudo systemctl enable skladtver-bot
```

5. Запустите сервис:

```bash
sudo systemctl start skladtver-bot
```

6. Проверьте статус:

```bash
sudo systemctl status skladtver-bot
```

### 6. Просмотр логов

```bash
sudo journalctl -u skladtver-bot -f
```

### 7. Обновление бота

Используйте скрипт `deploy.sh`:

```bash
chmod +x deploy.sh
./deploy.sh
```

Или вручную:

```bash
git pull origin master
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart skladtver-bot
```

## Альтернативный способ запуска (без systemd)

Запуск в фоновом режиме с помощью screen:

```bash
screen -S skladtver-bot
source venv/bin/activate
python bot.py
# Нажмите Ctrl+A, затем D для отсоединения
```

Для повторного подключения:

```bash
screen -r skladtver-bot
```

## Запуск с помощью nohup

```bash
nohup python bot.py > bot.log 2>&1 &
```

## Проверка работы

После запуска проверьте логи на наличие ошибок. Бот должен вывести сообщение о успешном запуске.

## Безопасность

- Не коммитьте файл `.env` в репозиторий
- Используйте отдельного пользователя для запуска бота
- Ограничьте права доступа к файлам проекта
- Регулярно обновляйте зависимости

