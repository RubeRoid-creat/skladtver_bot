"""
Телеграм-бот для управления складом
"""
import os
import logging
from typing import List
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from database import Database

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация базы данных
db = Database()


# === Команды бота ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = [
        [InlineKeyboardButton("📦 Товары", callback_data="menu_products")],
        [InlineKeyboardButton("💰 Касса", callback_data="menu_cashbox")],
        [InlineKeyboardButton("📊 Список товаров", callback_data="list_products")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🏪 Добро пожаловать в систему управления складом!\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📋 Доступные команды:

/start - Главное меню
/help - Справка
/products - Список всех товаров
/cashbox - Баланс кассы

🔧 Функции бота:
• Добавление товаров
• Управление количеством
• Управление ценой
• Продажа товаров
• Управление кассой
    """
    await update.message.reply_text(help_text)


async def products_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /products"""
    products = db.get_all_products()
    
    if not products:
        await update.message.reply_text("📦 Товары не найдены")
        return
    
    text = "📦 Список товаров:\n\n"
    for product in products:
        text += (
            f"• {product['name']}\n"
            f"  Количество: {product['quantity']}\n"
            f"  Цена: {product['price']:.2f} руб.\n\n"
        )
    
    await update.message.reply_text(text)


async def cashbox_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /cashbox"""
    balance = db.get_cashbox_balance()
    await update.message.reply_text(f"💰 Баланс кассы: {balance:.2f} руб.")


# === Обработчики callback-запросов ===

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "menu_products":
        await show_products_menu(query)
    elif data == "menu_cashbox":
        await show_cashbox_menu(query)
    elif data == "list_products":
        await show_products_list(query)
    elif data.startswith("product_"):
        await handle_product_action(query, data)
    elif data.startswith("cashbox_"):
        await handle_cashbox_action(query, data)
    elif data == "back_main":
        await show_main_menu(query)


async def show_main_menu(query):
    """Показать главное меню"""
    keyboard = [
        [InlineKeyboardButton("📦 Товары", callback_data="menu_products")],
        [InlineKeyboardButton("💰 Касса", callback_data="menu_cashbox")],
        [InlineKeyboardButton("📊 Список товаров", callback_data="list_products")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🏪 Главное меню\n\nВыберите действие:",
        reply_markup=reply_markup
    )


async def show_products_menu(query):
    """Показать меню управления товарами"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить товар", callback_data="product_add")],
        [InlineKeyboardButton("📝 Изменить количество", callback_data="product_quantity")],
        [InlineKeyboardButton("💵 Изменить цену", callback_data="product_price")],
        [InlineKeyboardButton("🛒 Продать товар", callback_data="product_sell")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📦 Управление товарами\n\nВыберите действие:",
        reply_markup=reply_markup
    )


async def show_cashbox_menu(query):
    """Показать меню управления кассой"""
    balance = db.get_cashbox_balance()
    
    keyboard = [
        [InlineKeyboardButton("➕ Пополнить", callback_data="cashbox_add")],
        [InlineKeyboardButton("➖ Снять", callback_data="cashbox_withdraw")],
        [InlineKeyboardButton("📜 История", callback_data="cashbox_history")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"💰 Управление кассой\n\nТекущий баланс: {balance:.2f} руб.\n\nВыберите действие:",
        reply_markup=reply_markup
    )


async def show_products_list(query):
    """Показать список товаров"""
    products = db.get_all_products()
    
    if not products:
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "📦 Товары не найдены",
            reply_markup=reply_markup
        )
        return
    
    text = "📦 Список товаров:\n\n"
    for product in products:
        text += (
            f"• {product['name']}\n"
            f"  Количество: {product['quantity']}\n"
            f"  Цена: {product['price']:.2f} руб.\n\n"
        )
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)


async def handle_product_action(query, data: str):
    """Обработка действий с товарами"""
    user_id = query.from_user.id
    
    if data == "product_add":
        user_states[user_id] = "add_product"
        await query.edit_message_text(
            "➕ Добавление товара\n\n"
            "Введите данные в формате:\n"
            "название | количество | цена\n\n"
            "Пример: Молоко | 10 | 50.00"
        )
        return
    
    elif data == "product_quantity":
        user_states[user_id] = "update_quantity"
        await query.edit_message_text(
            "📝 Изменение количества\n\n"
            "Введите данные в формате:\n"
            "название | новое_количество\n\n"
            "Пример: Молоко | 15"
        )
        return
    
    elif data == "product_price":
        user_states[user_id] = "update_price"
        await query.edit_message_text(
            "💵 Изменение цены\n\n"
            "Введите данные в формате:\n"
            "название | новая_цена\n\n"
            "Пример: Молоко | 55.00"
        )
        return
    
    elif data == "product_sell":
        user_states[user_id] = "sell_product"
        await query.edit_message_text(
            "🛒 Продажа товара\n\n"
            "Введите данные в формате:\n"
            "название | количество\n\n"
            "Пример: Молоко | 5"
        )
        return


async def handle_cashbox_action(query, data: str):
    """Обработка действий с кассой"""
    user_id = query.from_user.id
    
    if data == "cashbox_add":
        user_states[user_id] = "cashbox_add"
        await query.edit_message_text(
            "➕ Пополнение кассы\n\n"
            "Введите сумму для пополнения:\n\n"
            "Пример: 1000.00"
        )
        return
    
    elif data == "cashbox_withdraw":
        user_states[user_id] = "cashbox_withdraw"
        await query.edit_message_text(
            "➖ Снятие из кассы\n\n"
            "Введите сумму для снятия:\n\n"
            "Пример: 500.00"
        )
        return
    
    elif data == "cashbox_history":
        history = db.get_cashbox_history(10)
        
        if not history:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="menu_cashbox")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "📜 История операций пуста",
                reply_markup=reply_markup
            )
            return
        
        text = "📜 История операций:\n\n"
        for record in history:
            amount = record['amount']
            sign = "+" if amount > 0 else ""
            text += (
                f"{sign}{amount:.2f} руб. - {record['description']}\n"
                f"  {record['created_at']}\n\n"
            )
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="menu_cashbox")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)


# === Обработчики текстовых сообщений ===

# Хранилище состояний пользователей (в продакшене использовать Redis или БД)
user_states = {}


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений для ввода данных"""
    text = update.message.text.strip()
    user_id = update.message.from_user.id
    
    # Получаем текущее состояние пользователя
    state = user_states.get(user_id, None)
    
    # Обработка в зависимости от состояния
    if state == "add_product":
        # Добавление товара: название | количество | цена
        if "|" in text and text.count("|") == 2:
            parts = [p.strip() for p in text.split("|")]
            if len(parts) == 3:
                try:
                    name, quantity, price = parts
                    quantity = int(quantity)
                    price = float(price)
                    
                    if db.add_product(name, quantity, price):
                        await update.message.reply_text(
                            f"✅ Товар добавлен:\n"
                            f"Название: {name}\n"
                            f"Количество: {quantity}\n"
                            f"Цена: {price:.2f} руб."
                        )
                    else:
                        await update.message.reply_text(
                            f"❌ Товар '{name}' уже существует"
                        )
                    user_states.pop(user_id, None)
                    return
                except ValueError:
                    await update.message.reply_text("❌ Неверный формат. Используйте: название | количество | цена")
                    return
    
    elif state == "update_quantity":
        # Изменение количества: название | количество
        if "|" in text:
            parts = [p.strip() for p in text.split("|")]
            if len(parts) == 2:
                try:
                    name, quantity = parts
                    quantity = int(quantity)
                    
                    if db.update_product_quantity(name, quantity):
                        await update.message.reply_text(
                            f"✅ Количество обновлено:\n"
                            f"Товар: {name}\n"
                            f"Новое количество: {quantity}"
                        )
                    else:
                        await update.message.reply_text(
                            f"❌ Товар '{name}' не найден"
                        )
                    user_states.pop(user_id, None)
                    return
                except ValueError:
                    await update.message.reply_text("❌ Неверный формат. Используйте: название | количество")
                    return
    
    elif state == "update_price":
        # Изменение цены: название | цена
        if "|" in text:
            parts = [p.strip() for p in text.split("|")]
            if len(parts) == 2:
                try:
                    name, price_str = parts
                    price = float(price_str)
                    
                    if db.update_product_price(name, price):
                        await update.message.reply_text(
                            f"✅ Цена обновлена:\n"
                            f"Товар: {name}\n"
                            f"Новая цена: {price:.2f} руб."
                        )
                    else:
                        await update.message.reply_text(
                            f"❌ Товар '{name}' не найден"
                        )
                    user_states.pop(user_id, None)
                    return
                except ValueError:
                    await update.message.reply_text("❌ Неверный формат. Используйте: название | цена")
                    return
    
    elif state == "sell_product":
        # Продажа товара: название | количество
        if "|" in text:
            parts = [p.strip() for p in text.split("|")]
            if len(parts) == 2:
                try:
                    name, quantity = parts
                    quantity = int(quantity)
                    
                    success, total_price = db.sell_product(name, quantity)
                    if success:
                        balance = db.get_cashbox_balance()
                        await update.message.reply_text(
                            f"✅ Товар продан:\n"
                            f"Товар: {name}\n"
                            f"Количество: {quantity}\n"
                            f"Сумма: {total_price:.2f} руб.\n"
                            f"Баланс кассы: {balance:.2f} руб."
                        )
                    else:
                        product = db.get_product(name)
                        if not product:
                            await update.message.reply_text(
                                f"❌ Товар '{name}' не найден"
                            )
                        else:
                            await update.message.reply_text(
                                f"❌ Недостаточно товара на складе.\n"
                                f"Доступно: {product['quantity']}"
                            )
                    user_states.pop(user_id, None)
                    return
                except ValueError:
                    await update.message.reply_text("❌ Неверный формат. Используйте: название | количество")
                    return
    
    elif state == "cashbox_add":
        # Пополнение кассы: просто число
        try:
            amount = float(text)
            if amount > 0:
                if db.add_cash(amount, "Пополнение через бота"):
                    balance = db.get_cashbox_balance()
                    await update.message.reply_text(
                        f"✅ Касса пополнена на {amount:.2f} руб.\n"
                        f"Новый баланс: {balance:.2f} руб."
                    )
                    user_states.pop(user_id, None)
                    return
        except ValueError:
            await update.message.reply_text("❌ Введите положительное число")
            return
    
    elif state == "cashbox_withdraw":
        # Снятие из кассы: просто число
        try:
            amount = float(text)
            if amount > 0:
                if db.withdraw_cash(amount, "Снятие через бота"):
                    balance = db.get_cashbox_balance()
                    await update.message.reply_text(
                        f"✅ Из кассы снято {amount:.2f} руб.\n"
                        f"Новый баланс: {balance:.2f} руб."
                    )
                else:
                    balance = db.get_cashbox_balance()
                    await update.message.reply_text(
                        f"❌ Недостаточно средств в кассе.\n"
                        f"Текущий баланс: {balance:.2f} руб."
                    )
                user_states.pop(user_id, None)
                return
        except ValueError:
            await update.message.reply_text("❌ Введите положительное число")
            return
    
    # Если состояние не установлено, пробуем определить по формату
    # Добавление товара: название | количество | цена
    if "|" in text and text.count("|") == 2:
        parts = [p.strip() for p in text.split("|")]
        if len(parts) == 3:
            try:
                name, quantity, price = parts
                quantity = int(quantity)
                price = float(price)
                
                if db.add_product(name, quantity, price):
                    await update.message.reply_text(
                        f"✅ Товар добавлен:\n"
                        f"Название: {name}\n"
                        f"Количество: {quantity}\n"
                        f"Цена: {price:.2f} руб."
                    )
                else:
                    await update.message.reply_text(
                        f"❌ Товар '{name}' уже существует"
                    )
                return
            except ValueError:
                pass
    
    # Если ничего не подошло
    await update.message.reply_text(
        "❌ Неверный формат данных.\n\n"
        "Используйте команды из меню или формат:\n"
        "• Добавление: название | количество | цена\n"
        "• Изменение количества: название | количество\n"
        "• Изменение цены: название | цена\n"
        "• Продажа: название | количество"
    )


def main():
    """Главная функция запуска бота"""
    token = os.getenv("BOT_TOKEN")
    
    if not token:
        logger.error("BOT_TOKEN не найден в переменных окружения!")
        return
    
    # Создание приложения
    application = Application.builder().token(token).build()
    
    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("products", products_command))
    application.add_handler(CommandHandler("cashbox", cashbox_command))
    
    # Регистрация обработчика кнопок
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Регистрация обработчика текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запуск бота
    logger.info("Бот запущен")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

