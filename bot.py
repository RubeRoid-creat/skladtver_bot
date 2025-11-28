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

# Настройка логирования (должна быть до load_dotenv для корректной обработки ошибок)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
try:
    # Явно указываем путь к .env файлу
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger.info(f"Файл .env загружен из: {env_path}")
    else:
        load_dotenv()  # Пробуем загрузить из текущей директории
        logger.info("Попытка загрузить .env из текущей директории")
except Exception as e:
    logger.warning(f"Не удалось загрузить .env файл: {e}")
    logger.info("Продолжаю работу с переменными окружения системы")

# Инициализация базы данных
db = Database()

# Функция проверки прав администратора
def is_admin(user_id: int) -> bool:
    """Проверить, является ли пользователь администратором"""
    return db.is_admin(user_id)


# === Команды бота ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.message.from_user.id
    admin = is_admin(user_id)
    
    keyboard = [
        [InlineKeyboardButton("📦 Товары", callback_data="menu_products")],
        [InlineKeyboardButton("💰 Касса", callback_data="menu_cashbox")],
        [InlineKeyboardButton("📊 Список товаров", callback_data="list_products")]
    ]
    
    if admin:
        keyboard.append([InlineKeyboardButton("⚙️ Админ-панель", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    role_text = "👑 Администратор" if admin else "👤 Пользователь"
    await update.message.reply_text(
        f"🏪 Добро пожаловать в систему управления складом!\n\n"
        f"Ваша роль: {role_text}\n\n"
        f"Выберите действие:",
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
/admin - Добавить первого администратора

🔧 Функции бота:
• Добавление товаров (только админы)
• Управление количеством (только админы)
• Управление ценой (только админы)
• Продажа товаров (все пользователи)
• Управление кассой
    """
    await update.message.reply_text(help_text)


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /admin - добавление первого администратора"""
    user_id = update.message.from_user.id
    
    # Проверяем, есть ли уже админы
    admins = db.get_all_admins()
    
    if len(admins) == 0:
        # Первый пользователь становится админом
        username = update.message.from_user.username or "Неизвестно"
        if db.add_admin(user_id, username):
            await update.message.reply_text(
                f"✅ Вы стали первым администратором!\n"
                f"Ваш ID: {user_id}\n\n"
                f"Теперь вы можете управлять товарами и добавлять других администраторов."
            )
        else:
            await update.message.reply_text("❌ Ошибка при добавлении администратора")
    else:
        # Если админы уже есть, проверяем права
        if is_admin(user_id):
            keyboard = [
                [InlineKeyboardButton("⚙️ Админ-панель", callback_data="admin_panel")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "👑 Вы уже являетесь администратором!\n\n"
                "Используйте админ-панель для управления.",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "❌ Доступ запрещен!\n\n"
                "Для добавления администраторов обратитесь к существующему администратору."
            )


async def products_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /products"""
    products = db.get_all_products()
    user_id = update.message.from_user.id
    admin = is_admin(user_id)
    
    if not products:
        keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("📦 Товары не найдены", reply_markup=reply_markup)
        return
    
    text = "📦 Список товаров:\n\n"
    keyboard = []
    
    for product in products:
        text += (
            f"• {product['name']}\n"
            f"  Количество: {product['quantity']} | "
            f"Цена: {product['price']:.2f} руб.\n\n"
        )
        product_name_encoded = product['name'].replace(" ", "_")
        keyboard.append([
            InlineKeyboardButton(
                f"📦 {product['name']}",
                callback_data=f"product_view_{product_name_encoded}"
            )
        ])
        # Кнопки быстрого доступа (только для админов - изменение, все - продажа)
        if admin:
            keyboard.append([
                InlineKeyboardButton("📝 Кол-во", callback_data=f"product_qty_{product_name_encoded}"),
                InlineKeyboardButton("💵 Цена", callback_data=f"product_price_{product_name_encoded}"),
                InlineKeyboardButton("🛒 Продать", callback_data=f"product_sell_{product_name_encoded}")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("🛒 Продать", callback_data=f"product_sell_{product_name_encoded}")
            ])
    
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup)


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
    elif data.startswith("product_view_"):
        # Просмотр конкретного товара
        product_name = data.replace("product_view_", "").replace("_", " ")
        await show_product_detail(query, product_name)
    elif data.startswith("sell_qty_"):
        # Быстрая продажа с выбранным количеством
        parts = data.replace("sell_qty_", "").split("_")
        # Находим количество (последний элемент) и название товара (все остальное)
        quantity = int(parts[-1])
        product_name_encoded = "_".join(parts[:-1])
        product_name = product_name_encoded.replace("_", " ")
        
        success, total_price = db.sell_product(product_name, quantity)
        if success:
            balance = db.get_cashbox_balance()
            keyboard = [
                [InlineKeyboardButton("🛒 Продать еще", callback_data=f"product_sell_{product_name_encoded}")],
                [InlineKeyboardButton("📦 К товару", callback_data=f"product_view_{product_name_encoded}")],
                [InlineKeyboardButton("📦 Список товаров", callback_data="list_products")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"✅ Товар продан:\n"
                f"Товар: {product_name}\n"
                f"Количество: {quantity} шт.\n"
                f"Сумма: {total_price:.2f} руб.\n"
                f"💰 Баланс кассы: {balance:.2f} руб.",
                reply_markup=reply_markup
            )
        else:
            product = db.get_product(product_name)
            keyboard = [
                [InlineKeyboardButton("📦 К товару", callback_data=f"product_view_{product_name_encoded}")],
                [InlineKeyboardButton("📦 Список товаров", callback_data="list_products")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if not product:
                await query.edit_message_text(
                    f"❌ Товар '{product_name}' не найден",
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(
                    f"❌ Недостаточно товара на складе.\n"
                    f"Доступно: {product['quantity']} шт.",
                    reply_markup=reply_markup
                )
    elif data.startswith("sell_custom_"):
        # Ввод другого количества вручную
        product_name_encoded = data.replace("sell_custom_", "")
        product_name = product_name_encoded.replace("_", " ")
        user_id = query.from_user.id
        user_states[user_id] = f"sell_product_{product_name}"
        
        product = db.get_product(product_name)
        available = product['quantity'] if product else 0
        
        nav_keyboard = [
            [InlineKeyboardButton("◀️ Назад к выбору", callback_data=f"product_sell_{product_name_encoded}")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
        ]
        nav_markup = InlineKeyboardMarkup(nav_keyboard)
        await query.edit_message_text(
            f"🛒 Продажа товара: {product_name}\n\n"
            f"Доступно: {available} шт.\n"
            f"Введите количество для продажи:\n\n"
            f"Пример: 5",
            reply_markup=nav_markup
        )
    elif data.startswith("product_qty_"):
        # Быстрое изменение количества товара - проверка прав
        user_id = query.from_user.id
        if not is_admin(user_id):
            keyboard = [
                [InlineKeyboardButton("◀️ Назад", callback_data="list_products")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Доступ запрещен!\n\n"
                "Эта функция доступна только администраторам.",
                reply_markup=reply_markup
            )
            return
        product_name = data.replace("product_qty_", "").replace("_", " ")
        user_states[user_id] = f"update_quantity_{product_name}"
        nav_keyboard = [
            [InlineKeyboardButton("◀️ Назад к товару", callback_data=f"product_view_{data.replace('product_qty_', '')}")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
        ]
        nav_markup = InlineKeyboardMarkup(nav_keyboard)
        await query.edit_message_text(
            f"📝 Изменение количества товара: {product_name}\n\n"
            f"Введите новое количество:\n\n"
            f"Пример: 15",
            reply_markup=nav_markup
        )
    elif data.startswith("product_price_"):
        # Быстрое изменение цены товара - проверка прав
        user_id = query.from_user.id
        if not is_admin(user_id):
            keyboard = [
                [InlineKeyboardButton("◀️ Назад", callback_data="list_products")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Доступ запрещен!\n\n"
                "Эта функция доступна только администраторам.",
                reply_markup=reply_markup
            )
            return
        product_name = data.replace("product_price_", "").replace("_", " ")
        user_states[user_id] = f"update_price_{product_name}"
        nav_keyboard = [
            [InlineKeyboardButton("◀️ Назад к товару", callback_data=f"product_view_{data.replace('product_price_', '')}")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
        ]
        nav_markup = InlineKeyboardMarkup(nav_keyboard)
        await query.edit_message_text(
            f"💵 Изменение цены товара: {product_name}\n\n"
            f"Введите новую цену:\n\n"
            f"Пример: 55.00",
            reply_markup=nav_markup
        )
    elif data.startswith("product_sell_"):
        # Показать кнопки выбора количества для продажи
        product_name = data.replace("product_sell_", "").replace("_", " ")
        product = db.get_product(product_name)
        
        if not product:
            keyboard = [
                [InlineKeyboardButton("📦 Список товаров", callback_data="list_products")],
                [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"❌ Товар '{product_name}' не найден",
                reply_markup=reply_markup
            )
            return
        
        available = product['quantity']
        product_name_encoded = product_name.replace(" ", "_")
        
        # Создаем кнопки с вариантами количества
        quantity_buttons = []
        
        # Кнопки с популярными количествами
        if available >= 1:
            quantity_buttons.append([InlineKeyboardButton("1 шт.", callback_data=f"sell_qty_{product_name_encoded}_1")])
        if available >= 5:
            quantity_buttons.append([InlineKeyboardButton("5 шт.", callback_data=f"sell_qty_{product_name_encoded}_5")])
        if available >= 10:
            quantity_buttons.append([InlineKeyboardButton("10 шт.", callback_data=f"sell_qty_{product_name_encoded}_10")])
        
        # Кнопка "Все" если товара больше 1
        if available > 1:
            quantity_buttons.append([InlineKeyboardButton(f"Все ({available} шт.)", callback_data=f"sell_qty_{product_name_encoded}_{available}")])
        
        # Кнопка для ввода другого количества
        quantity_buttons.append([InlineKeyboardButton("✏️ Другое количество", callback_data=f"sell_custom_{product_name_encoded}")])
        
        # Кнопки навигации
        quantity_buttons.append([
            InlineKeyboardButton("◀️ Назад к товару", callback_data=f"product_view_{product_name_encoded}"),
            InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")
        ])
        
        reply_markup = InlineKeyboardMarkup(quantity_buttons)
        
        await query.edit_message_text(
            f"🛒 Продажа товара: {product_name}\n\n"
            f"📊 Доступно: {available} шт.\n"
            f"💵 Цена: {product['price']:.2f} руб./шт.\n\n"
            f"Выберите количество:",
            reply_markup=reply_markup
        )
    elif data.startswith("product_"):
        await handle_product_action(query, data)
    elif data.startswith("cashbox_"):
        await handle_cashbox_action(query, data)
    elif data == "admin_panel":
        await show_admin_panel(query)
    elif data.startswith("admin_add_"):
        await handle_admin_add(query, data)
    elif data.startswith("admin_remove_"):
        await handle_admin_remove(query, data)
    elif data == "back_main":
        await show_main_menu(query)


async def show_product_detail(query, product_name: str):
    """Показать детальную информацию о товаре с кнопками действий"""
    product = db.get_product(product_name)
    user_id = query.from_user.id
    admin = is_admin(user_id)
    
    if not product:
        keyboard = [
            [InlineKeyboardButton("📦 Список товаров", callback_data="list_products")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"❌ Товар '{product_name}' не найден",
            reply_markup=reply_markup
        )
        return
    
    text = (
        f"📦 Товар: {product['name']}\n\n"
        f"📊 Количество: {product['quantity']}\n"
        f"💵 Цена: {product['price']:.2f} руб.\n"
        f"💰 Общая стоимость: {product['quantity'] * product['price']:.2f} руб.\n"
    )
    
    # Кнопки для быстрых действий с товаром
    product_name_encoded = product['name'].replace(" ", "_")
    keyboard = []
    
    # Только админы могут изменять количество и цену
    if admin:
        keyboard.append([
            InlineKeyboardButton("📝 Изменить количество", callback_data=f"product_qty_{product_name_encoded}"),
            InlineKeyboardButton("💵 Изменить цену", callback_data=f"product_price_{product_name_encoded}")
        ])
    
    # Все могут продавать
    keyboard.append([
        InlineKeyboardButton("🛒 Продать", callback_data=f"product_sell_{product_name_encoded}")
    ])
    
    keyboard.append([
        InlineKeyboardButton("📦 Список товаров", callback_data="list_products"),
        InlineKeyboardButton("◀️ Назад", callback_data="back_main")
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)


async def show_main_menu(query):
    """Показать главное меню"""
    # Сбрасываем состояние пользователя при возврате в главное меню
    user_id = query.from_user.id
    user_states.pop(user_id, None)
    admin = is_admin(user_id)
    
    keyboard = [
        [InlineKeyboardButton("📦 Товары", callback_data="menu_products")],
        [InlineKeyboardButton("💰 Касса", callback_data="menu_cashbox")],
        [InlineKeyboardButton("📊 Список товаров", callback_data="list_products")]
    ]
    
    if admin:
        keyboard.append([InlineKeyboardButton("⚙️ Админ-панель", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    role_text = "👑 Администратор" if admin else "👤 Пользователь"
    await query.edit_message_text(
        f"🏪 Главное меню\n\nВаша роль: {role_text}\n\nВыберите действие:",
        reply_markup=reply_markup
    )


async def show_products_menu(query):
    """Показать меню управления товарами"""
    # Сбрасываем состояние пользователя при возврате в меню товаров
    user_id = query.from_user.id
    user_states.pop(user_id, None)
    admin = is_admin(user_id)
    
    keyboard = []
    
    # Только админы могут добавлять и изменять товары
    if admin:
        keyboard.append([InlineKeyboardButton("➕ Добавить товар", callback_data="product_add")])
        keyboard.append([InlineKeyboardButton("📝 Изменить количество", callback_data="product_quantity")])
        keyboard.append([InlineKeyboardButton("💵 Изменить цену", callback_data="product_price")])
    
    # Все могут продавать
    keyboard.append([InlineKeyboardButton("🛒 Продать товар", callback_data="product_sell")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    role_text = "👑 Администратор" if admin else "👤 Пользователь"
    await query.edit_message_text(
        f"📦 Управление товарами\n\nВаша роль: {role_text}\n\nВыберите действие:",
        reply_markup=reply_markup
    )


async def show_cashbox_menu(query):
    """Показать меню управления кассой"""
    # Сбрасываем состояние пользователя при возврате в меню кассы
    user_id = query.from_user.id
    user_states.pop(user_id, None)
    
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


async def show_admin_panel(query):
    """Показать админ-панель"""
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "❌ Доступ запрещен!\n\n"
            "Эта функция доступна только администраторам.",
            reply_markup=reply_markup
        )
        return
    
    admins = db.get_all_admins()
    text = "⚙️ Админ-панель\n\n"
    text += f"👑 Администраторов: {len(admins)}\n\n"
    
    keyboard = []
    
    # Список админов
    if admins:
        text += "Список администраторов:\n"
        for admin in admins:
            username = admin.get('username', 'Неизвестно')
            text += f"• ID: {admin['user_id']} (@{username})\n"
    
    keyboard.append([InlineKeyboardButton("➕ Добавить админа", callback_data="admin_add_menu")])
    if len(admins) > 1:  # Нельзя удалить последнего админа
        keyboard.append([InlineKeyboardButton("➖ Удалить админа", callback_data="admin_remove_menu")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)


async def handle_admin_add(query, data: str):
    """Обработка добавления админа"""
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "❌ Доступ запрещен!",
            reply_markup=reply_markup
        )
        return
    
    if data == "admin_add_menu":
        await query.edit_message_text(
            "➕ Добавление администратора\n\n"
            "Отправьте ID пользователя Telegram, которого хотите сделать администратором.\n\n"
            "Для получения ID пользователя:\n"
            "1. Попросите пользователя написать боту @userinfobot\n"
            "2. Или используйте @getidsbot\n\n"
            "Введите ID пользователя:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")]
            ])
        )
        user_states[user_id] = "admin_add"
        return


async def handle_admin_remove(query, data: str):
    """Обработка удаления админа"""
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "❌ Доступ запрещен!",
            reply_markup=reply_markup
        )
        return
    
    if data == "admin_remove_menu":
        admins = db.get_all_admins()
        if len(admins) <= 1:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Нельзя удалить последнего администратора!",
                reply_markup=reply_markup
            )
            return
        
        text = "➖ Удаление администратора\n\nВыберите администратора для удаления:\n\n"
        keyboard = []
        
        for admin in admins:
            if admin['user_id'] != user_id:  # Нельзя удалить себя
                username = admin.get('username', 'Неизвестно')
                keyboard.append([
                    InlineKeyboardButton(
                        f"👤 ID: {admin['user_id']} (@{username})",
                        callback_data=f"admin_remove_{admin['user_id']}"
                    )
                ])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
    elif data.startswith("admin_remove_"):
        admin_id = int(data.replace("admin_remove_", ""))
        
        if admin_id == user_id:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Нельзя удалить самого себя!",
                reply_markup=reply_markup
            )
            return
        
        if db.remove_admin(admin_id):
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"✅ Администратор (ID: {admin_id}) удален",
                reply_markup=reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Администратор не найден",
                reply_markup=reply_markup
            )


async def show_products_list(query):
    """Показать список товаров с кнопками"""
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
    keyboard = []
    
    for product in products:
        # Добавляем информацию о товаре в текст
        text += (
            f"• {product['name']}\n"
            f"  Количество: {product['quantity']} | "
            f"Цена: {product['price']:.2f} руб.\n\n"
        )
        # Добавляем кнопки для каждого товара
        product_name_encoded = product['name'].replace(" ", "_")
        keyboard.append([
            InlineKeyboardButton(
                f"📦 {product['name']}",
                callback_data=f"product_view_{product_name_encoded}"
            )
        ])
        # Кнопки быстрого доступа (только для админов - изменение, все - продажа)
        user_id = query.from_user.id
        admin = is_admin(user_id)
        if admin:
            keyboard.append([
                InlineKeyboardButton("📝 Кол-во", callback_data=f"product_qty_{product_name_encoded}"),
                InlineKeyboardButton("💵 Цена", callback_data=f"product_price_{product_name_encoded}"),
                InlineKeyboardButton("🛒 Продать", callback_data=f"product_sell_{product_name_encoded}")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("🛒 Продать", callback_data=f"product_sell_{product_name_encoded}")
            ])
    
    # Добавляем кнопку "Назад"
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup)


async def handle_product_action(query, data: str):
    """Обработка действий с товарами"""
    user_id = query.from_user.id
    admin = is_admin(user_id)
    
    # Проверка прав для админских действий
    if data in ["product_add", "product_quantity", "product_price"] and not admin:
        keyboard = [
            [InlineKeyboardButton("◀️ Назад", callback_data="menu_products")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "❌ Доступ запрещен!\n\n"
            "Эта функция доступна только администраторам.",
            reply_markup=reply_markup
        )
        return
    
    # Кнопки навигации для всех действий
    nav_keyboard = [
        [InlineKeyboardButton("◀️ Назад", callback_data="menu_products")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
    ]
    nav_markup = InlineKeyboardMarkup(nav_keyboard)
    
    if data == "product_add":
        user_states[user_id] = "add_product"
        await query.edit_message_text(
            "➕ Добавление товара\n\n"
            "Введите данные в формате:\n"
            "наименование товара , количество , цена\n\n"
            "Пример: Молоко , 10 , 50.00",
            reply_markup=nav_markup
        )
        return
    
    elif data == "product_quantity":
        # Показать список товаров для выбора
        products = db.get_all_products()
        
        if not products:
            keyboard = [
                [InlineKeyboardButton("◀️ Назад", callback_data="menu_products")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Товары не найдены",
                reply_markup=reply_markup
            )
            return
        
        text = "📝 Выберите товар для изменения количества:\n\n"
        keyboard = []
        
        for product in products:
            product_name_encoded = product['name'].replace(" ", "_")
            keyboard.append([
                InlineKeyboardButton(
                    f"📦 {product['name']} (текущее: {product['quantity']})",
                    callback_data=f"product_qty_{product_name_encoded}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("◀️ Назад", callback_data="menu_products"),
            InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")
        ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text + "Выберите товар из списка:",
            reply_markup=reply_markup
        )
        return
    
    elif data == "product_price":
        # Показать список товаров для выбора
        products = db.get_all_products()
        
        if not products:
            keyboard = [
                [InlineKeyboardButton("◀️ Назад", callback_data="menu_products")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Товары не найдены",
                reply_markup=reply_markup
            )
            return
        
        text = "💵 Выберите товар для изменения цены:\n\n"
        keyboard = []
        
        for product in products:
            product_name_encoded = product['name'].replace(" ", "_")
            keyboard.append([
                InlineKeyboardButton(
                    f"📦 {product['name']} (текущая: {product['price']:.2f} руб.)",
                    callback_data=f"product_price_{product_name_encoded}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("◀️ Назад", callback_data="menu_products"),
            InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")
        ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text + "Выберите товар из списка:",
            reply_markup=reply_markup
        )
        return
    
    elif data == "product_sell":
        # Показать список товаров для выбора
        products = db.get_all_products()
        
        if not products:
            keyboard = [
                [InlineKeyboardButton("◀️ Назад", callback_data="menu_products")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Товары не найдены",
                reply_markup=reply_markup
            )
            return
        
        text = "🛒 Выберите товар для продажи:\n\n"
        keyboard = []
        
        for product in products:
            if product['quantity'] > 0:  # Показываем только товары с количеством > 0
                product_name_encoded = product['name'].replace(" ", "_")
                keyboard.append([
                    InlineKeyboardButton(
                        f"📦 {product['name']} ({product['quantity']} шт.)",
                        callback_data=f"product_sell_{product_name_encoded}"
                    )
                ])
        
        if not keyboard:
            keyboard = [
                [InlineKeyboardButton("◀️ Назад", callback_data="menu_products")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Нет товаров в наличии для продажи",
                reply_markup=reply_markup
            )
            return
        
        keyboard.append([
            InlineKeyboardButton("◀️ Назад", callback_data="menu_products"),
            InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")
        ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text + "Выберите товар из списка:",
            reply_markup=reply_markup
        )
        return


async def handle_cashbox_action(query, data: str):
    """Обработка действий с кассой"""
    user_id = query.from_user.id
    
    # Кнопки навигации для всех действий
    nav_keyboard = [
        [InlineKeyboardButton("◀️ Назад", callback_data="menu_cashbox")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
    ]
    nav_markup = InlineKeyboardMarkup(nav_keyboard)
    
    if data == "cashbox_add":
        user_states[user_id] = "cashbox_add"
        await query.edit_message_text(
            "➕ Пополнение кассы\n\n"
            "Введите сумму для пополнения:\n\n"
            "Пример: 1000.00",
            reply_markup=nav_markup
        )
        return
    
    elif data == "cashbox_withdraw":
        user_states[user_id] = "cashbox_withdraw"
        await query.edit_message_text(
            "➖ Снятие из кассы\n\n"
            "Введите сумму для снятия:\n\n"
            "Пример: 500.00",
            reply_markup=nav_markup
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
    
    # Если пользователь не в состоянии ожидания ввода данных, игнорируем сообщение
    if not state:
        return
    
    # Обработка добавления админа
    if state == "admin_add":
        try:
            admin_id = int(text)
            
            # Проверяем, что не добавляем самого себя (опционально, можно убрать)
            if admin_id == user_id:
                keyboard = [
                    [InlineKeyboardButton("⚙️ Админ-панель", callback_data="admin_panel")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    "ℹ️ Вы уже являетесь администратором.\n"
                    "Для добавления другого администратора введите его ID.",
                    reply_markup=reply_markup
                )
                return
            
            # Username будет "Неизвестно", так как мы не можем получить его по ID
            # без того, чтобы пользователь сам написал боту
            username = "Неизвестно"
            
            if db.add_admin(admin_id, username):
                keyboard = [
                    [InlineKeyboardButton("⚙️ Админ-панель", callback_data="admin_panel")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"✅ Администратор добавлен!\n"
                    f"ID: {admin_id}\n\n"
                    f"Примечание: Username будет обновлен, когда пользователь впервые напишет боту.",
                    reply_markup=reply_markup
                )
            else:
                keyboard = [
                    [InlineKeyboardButton("⚙️ Админ-панель", callback_data="admin_panel")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"❌ Пользователь с ID {admin_id} уже является администратором",
                    reply_markup=reply_markup
                )
            user_states.pop(user_id, None)
            return
        except ValueError:
            keyboard = [
                [InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "❌ Неверный формат. Введите числовой ID пользователя.",
                reply_markup=reply_markup
            )
            return
    
    # Обработка в зависимости от состояния
    if state == "add_product":
        # Проверка прав администратора
        if not is_admin(user_id):
            keyboard = [
                [InlineKeyboardButton("◀️ Назад", callback_data="menu_products")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "❌ Доступ запрещен!\n\n"
                "Эта функция доступна только администраторам.",
                reply_markup=reply_markup
            )
            user_states.pop(user_id, None)
            return
        # Добавление товара: наименование товара , количество , цена
        if "," in text:
            parts = [p.strip() for p in text.split(",")]
            if len(parts) == 3:
                try:
                    name, quantity, price = parts
                    quantity = int(quantity)
                    price = float(price)
                    
                    if db.add_product(name, quantity, price):
                        keyboard = [
                            [InlineKeyboardButton("➕ Добавить еще", callback_data="product_add")],
                            [InlineKeyboardButton("📦 Товары", callback_data="menu_products")],
                            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await update.message.reply_text(
                            f"✅ Товар добавлен:\n"
                            f"Название: {name}\n"
                            f"Количество: {quantity}\n"
                            f"Цена: {price:.2f} руб.",
                            reply_markup=reply_markup
                        )
                    else:
                        keyboard = [
                            [InlineKeyboardButton("◀️ Назад", callback_data="menu_products")],
                            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await update.message.reply_text(
                            f"❌ Товар '{name}' уже существует",
                            reply_markup=reply_markup
                        )
                    user_states.pop(user_id, None)
                    return
                except ValueError:
                    keyboard = [
                        [InlineKeyboardButton("◀️ Назад", callback_data="menu_products")],
                        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(
                        "❌ Неверный формат. Используйте: наименование товара , количество , цена",
                        reply_markup=reply_markup
                    )
                    return
    
    elif state == "update_quantity" or (state and state.startswith("update_quantity_")):
        # Изменение количества: название | количество или просто число для быстрого действия
        product_name = None
        if state.startswith("update_quantity_"):
            product_name = state.replace("update_quantity_", "")
        
        if product_name:
            # Быстрое изменение количества для конкретного товара
            try:
                quantity = int(text)
                if db.update_product_quantity(product_name, quantity):
                    product_name_encoded = product_name.replace(" ", "_")
                    keyboard = [
                        [InlineKeyboardButton("📦 К товару", callback_data=f"product_view_{product_name_encoded}")],
                        [InlineKeyboardButton("📦 Список товаров", callback_data="list_products")],
                        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(
                        f"✅ Количество обновлено:\n"
                        f"Товар: {product_name}\n"
                        f"Новое количество: {quantity}",
                        reply_markup=reply_markup
                    )
                else:
                    keyboard = [
                        [InlineKeyboardButton("📦 Список товаров", callback_data="list_products")],
                        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(
                        f"❌ Товар '{product_name}' не найден",
                        reply_markup=reply_markup
                    )
                user_states.pop(user_id, None)
                return
            except ValueError:
                keyboard = [
                    [InlineKeyboardButton("◀️ Назад", callback_data=f"product_view_{product_name.replace(' ', '_')}")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    "❌ Введите целое число",
                    reply_markup=reply_markup
                )
                return
        else:
            # Стандартное изменение количества: название | количество
            if "|" in text:
                parts = [p.strip() for p in text.split("|")]
                if len(parts) == 2:
                    try:
                        name, quantity = parts
                        quantity = int(quantity)
                        
                        if db.update_product_quantity(name, quantity):
                            keyboard = [
                                [InlineKeyboardButton("📝 Изменить еще", callback_data="product_quantity")],
                                [InlineKeyboardButton("📦 Товары", callback_data="menu_products")],
                                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                            ]
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            await update.message.reply_text(
                                f"✅ Количество обновлено:\n"
                                f"Товар: {name}\n"
                                f"Новое количество: {quantity}",
                                reply_markup=reply_markup
                            )
                        else:
                            keyboard = [
                                [InlineKeyboardButton("◀️ Назад", callback_data="menu_products")],
                                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                            ]
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            await update.message.reply_text(
                                f"❌ Товар '{name}' не найден",
                                reply_markup=reply_markup
                            )
                        user_states.pop(user_id, None)
                        return
                    except ValueError:
                        keyboard = [
                            [InlineKeyboardButton("◀️ Назад", callback_data="menu_products")],
                            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await update.message.reply_text(
                            "❌ Неверный формат. Используйте: название | количество",
                            reply_markup=reply_markup
                        )
                        return
    
    elif state == "update_price" or (state and state.startswith("update_price_")):
        # Проверка прав администратора
        if not is_admin(user_id):
            keyboard = [
                [InlineKeyboardButton("◀️ Назад", callback_data="menu_products")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "❌ Доступ запрещен!\n\n"
                "Эта функция доступна только администраторам.",
                reply_markup=reply_markup
            )
            user_states.pop(user_id, None)
            return
        # Изменение цены: название | цена или просто число для быстрого действия
        product_name = None
        if state.startswith("update_price_"):
            product_name = state.replace("update_price_", "")
        
        if product_name:
            # Быстрое изменение цены для конкретного товара
            try:
                price = float(text)
                if db.update_product_price(product_name, price):
                    product_name_encoded = product_name.replace(" ", "_")
                    keyboard = [
                        [InlineKeyboardButton("📦 К товару", callback_data=f"product_view_{product_name_encoded}")],
                        [InlineKeyboardButton("📦 Список товаров", callback_data="list_products")],
                        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(
                        f"✅ Цена обновлена:\n"
                        f"Товар: {product_name}\n"
                        f"Новая цена: {price:.2f} руб.",
                        reply_markup=reply_markup
                    )
                else:
                    keyboard = [
                        [InlineKeyboardButton("📦 Список товаров", callback_data="list_products")],
                        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(
                        f"❌ Товар '{product_name}' не найден",
                        reply_markup=reply_markup
                    )
                user_states.pop(user_id, None)
                return
            except ValueError:
                keyboard = [
                    [InlineKeyboardButton("◀️ Назад", callback_data=f"product_view_{product_name.replace(' ', '_')}")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    "❌ Введите число (можно с точкой)",
                    reply_markup=reply_markup
                )
                return
        else:
            # Стандартное изменение цены: название | цена
            if "|" in text:
                parts = [p.strip() for p in text.split("|")]
                if len(parts) == 2:
                    try:
                        name, price_str = parts
                        price = float(price_str)
                        
                        if db.update_product_price(name, price):
                            keyboard = [
                                [InlineKeyboardButton("💵 Изменить еще", callback_data="product_price")],
                                [InlineKeyboardButton("📦 Товары", callback_data="menu_products")],
                                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                            ]
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            await update.message.reply_text(
                                f"✅ Цена обновлена:\n"
                                f"Товар: {name}\n"
                                f"Новая цена: {price:.2f} руб.",
                                reply_markup=reply_markup
                            )
                        else:
                            keyboard = [
                                [InlineKeyboardButton("◀️ Назад", callback_data="menu_products")],
                                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                            ]
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            await update.message.reply_text(
                                f"❌ Товар '{name}' не найден",
                                reply_markup=reply_markup
                            )
                        user_states.pop(user_id, None)
                        return
                    except ValueError:
                        keyboard = [
                            [InlineKeyboardButton("◀️ Назад", callback_data="menu_products")],
                            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await update.message.reply_text(
                            "❌ Неверный формат. Используйте: название | цена",
                            reply_markup=reply_markup
                        )
                        return
    
    elif state == "sell_product" or (state and state.startswith("sell_product_")):
        # Продажа товара: название | количество или просто число для быстрого действия
        product_name = None
        if state.startswith("sell_product_"):
            product_name = state.replace("sell_product_", "")
        
        if product_name:
            # Быстрая продажа конкретного товара
            try:
                quantity = int(text)
                success, total_price = db.sell_product(product_name, quantity)
                if success:
                    balance = db.get_cashbox_balance()
                    product_name_encoded = product_name.replace(" ", "_")
                    keyboard = [
                        [InlineKeyboardButton("🛒 Продать еще", callback_data=f"product_sell_{product_name_encoded}")],
                        [InlineKeyboardButton("📦 К товару", callback_data=f"product_view_{product_name_encoded}")],
                        [InlineKeyboardButton("📦 Список товаров", callback_data="list_products")],
                        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(
                        f"✅ Товар продан:\n"
                        f"Товар: {product_name}\n"
                        f"Количество: {quantity}\n"
                        f"Сумма: {total_price:.2f} руб.\n"
                        f"Баланс кассы: {balance:.2f} руб.",
                        reply_markup=reply_markup
                    )
                else:
                    product = db.get_product(product_name)
                    product_name_encoded = product_name.replace(" ", "_")
                    keyboard = [
                        [InlineKeyboardButton("📦 К товару", callback_data=f"product_view_{product_name_encoded}")],
                        [InlineKeyboardButton("📦 Список товаров", callback_data="list_products")],
                        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    if not product:
                        await update.message.reply_text(
                            f"❌ Товар '{product_name}' не найден",
                            reply_markup=reply_markup
                        )
                    else:
                        await update.message.reply_text(
                            f"❌ Недостаточно товара на складе.\n"
                            f"Доступно: {product['quantity']}",
                            reply_markup=reply_markup
                        )
                user_states.pop(user_id, None)
                return
            except ValueError:
                product_name_encoded = product_name.replace(" ", "_")
                keyboard = [
                    [InlineKeyboardButton("◀️ Назад", callback_data=f"product_view_{product_name_encoded}")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    "❌ Введите целое число",
                    reply_markup=reply_markup
                )
                return
        else:
            # Стандартная продажа: название | количество
            if "|" in text:
                parts = [p.strip() for p in text.split("|")]
                if len(parts) == 2:
                    try:
                        name, quantity = parts
                        quantity = int(quantity)
                        
                        success, total_price = db.sell_product(name, quantity)
                        if success:
                            balance = db.get_cashbox_balance()
                            keyboard = [
                                [InlineKeyboardButton("🛒 Продать еще", callback_data="product_sell")],
                                [InlineKeyboardButton("📦 Товары", callback_data="menu_products")],
                                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                            ]
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            await update.message.reply_text(
                                f"✅ Товар продан:\n"
                                f"Товар: {name}\n"
                                f"Количество: {quantity}\n"
                                f"Сумма: {total_price:.2f} руб.\n"
                                f"Баланс кассы: {balance:.2f} руб.",
                                reply_markup=reply_markup
                            )
                        else:
                            product = db.get_product(name)
                            keyboard = [
                                [InlineKeyboardButton("◀️ Назад", callback_data="menu_products")],
                                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                            ]
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            if not product:
                                await update.message.reply_text(
                                    f"❌ Товар '{name}' не найден",
                                    reply_markup=reply_markup
                                )
                            else:
                                await update.message.reply_text(
                                    f"❌ Недостаточно товара на складе.\n"
                                    f"Доступно: {product['quantity']}",
                                    reply_markup=reply_markup
                                )
                        user_states.pop(user_id, None)
                        return
                    except ValueError:
                        keyboard = [
                            [InlineKeyboardButton("◀️ Назад", callback_data="menu_products")],
                            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await update.message.reply_text(
                            "❌ Неверный формат. Используйте: название | количество",
                            reply_markup=reply_markup
                        )
                        return
    
    elif state == "cashbox_add":
        # Пополнение кассы: просто число
        try:
            amount = float(text)
            if amount > 0:
                if db.add_cash(amount, "Пополнение через бота"):
                    balance = db.get_cashbox_balance()
                    keyboard = [
                        [InlineKeyboardButton("➕ Пополнить еще", callback_data="cashbox_add")],
                        [InlineKeyboardButton("💰 Касса", callback_data="menu_cashbox")],
                        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(
                        f"✅ Касса пополнена на {amount:.2f} руб.\n"
                        f"Новый баланс: {balance:.2f} руб.",
                        reply_markup=reply_markup
                    )
                    user_states.pop(user_id, None)
                    return
        except ValueError:
            keyboard = [
                [InlineKeyboardButton("◀️ Назад", callback_data="menu_cashbox")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "❌ Введите положительное число",
                reply_markup=reply_markup
            )
            return
    
    elif state == "cashbox_withdraw":
        # Снятие из кассы: просто число
        try:
            amount = float(text)
            if amount > 0:
                keyboard = [
                    [InlineKeyboardButton("💰 Касса", callback_data="menu_cashbox")],
                    [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                if db.withdraw_cash(amount, "Снятие через бота"):
                    balance = db.get_cashbox_balance()
                    await update.message.reply_text(
                        f"✅ Из кассы снято {amount:.2f} руб.\n"
                        f"Новый баланс: {balance:.2f} руб.",
                        reply_markup=reply_markup
                    )
                else:
                    balance = db.get_cashbox_balance()
                    await update.message.reply_text(
                        f"❌ Недостаточно средств в кассе.\n"
                        f"Текущий баланс: {balance:.2f} руб.",
                        reply_markup=reply_markup
                    )
                user_states.pop(user_id, None)
                return
        except ValueError:
            keyboard = [
                [InlineKeyboardButton("◀️ Назад", callback_data="menu_cashbox")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "❌ Введите положительное число",
                reply_markup=reply_markup
            )
            return
    
    # Если состояние установлено, но формат не подошел - показываем ошибку
    # (это означает, что пользователь в состоянии ожидания ввода, но ввел неверные данные)
    keyboard = [
        [InlineKeyboardButton("◀️ Назад", callback_data="back_main")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "❌ Неверный формат данных.\n\n"
        "Используйте кнопки меню для выбора действия.",
        reply_markup=reply_markup
    )


def main():
    """Главная функция запуска бота"""
    token = os.getenv("BOT_TOKEN")
    
    # Отладочная информация
    logger.info(f"Текущая рабочая директория: {os.getcwd()}")
    logger.info(f"Путь к скрипту: {os.path.dirname(__file__)}")
    logger.info(f"BOT_TOKEN из окружения: {'установлен' if token else 'не найден'}")
    if token:
        logger.info(f"Длина токена: {len(token)} символов")
    
    if not token or token == "your_telegram_bot_token_here":
        logger.error("=" * 60)
        logger.error("ОШИБКА: BOT_TOKEN не найден в переменных окружения!")
        logger.error("=" * 60)
        logger.error("")
        logger.error("Для запуска бота необходимо:")
        logger.error("1. Создать файл .env в корне проекта")
        logger.error("2. Добавить в него строку: BOT_TOKEN=ваш_токен_бота")
        logger.error("3. Получить токен у @BotFather в Telegram")
        logger.error("")
        logger.error("Пример содержимого файла .env:")
        logger.error("BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz")
        logger.error("=" * 60)
        return
    
    # Создание приложения
    application = Application.builder().token(token).build()
    
    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("products", products_command))
    application.add_handler(CommandHandler("cashbox", cashbox_command))
    application.add_handler(CommandHandler("admin", admin_command))
    
    # Регистрация обработчика кнопок
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Регистрация обработчика текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запуск бота
    logger.info("Бот запущен")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

