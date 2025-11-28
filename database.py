"""
Модуль для работы с базой данных складского учета
"""
import sqlite3
from typing import List, Dict, Optional, Tuple


class Database:
    """Класс для управления базой данных склада"""
    
    def __init__(self, db_path: str = "warehouse.db"):
        """
        Инициализация базы данных
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Получить соединение с базой данных"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Инициализация таблиц базы данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица товаров
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                quantity INTEGER NOT NULL DEFAULT 0,
                price REAL NOT NULL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица кассы
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cashbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL DEFAULT 0.0,
                transaction_type TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Инициализация кассы, если её нет
        cursor.execute("SELECT COUNT(*) FROM cashbox")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO cashbox (amount, transaction_type, description)
                VALUES (0.0, 'initial', 'Начальный баланс')
            """)
        
        conn.commit()
        conn.close()
    
    # === Управление товарами ===
    
    def add_product(self, name: str, quantity: int = 0, price: float = 0.0) -> bool:
        """
        Добавить новый товар
        
        Args:
            name: Наименование товара
            quantity: Количество
            price: Цена
            
        Returns:
            True если успешно, False если товар уже существует
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO products (name, quantity, price)
                VALUES (?, ?, ?)
            """, (name, quantity, price))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def get_product(self, name: str) -> Optional[Dict]:
        """Получить товар по наименованию"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM products WHERE name = ?
        """, (name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_all_products(self) -> List[Dict]:
        """Получить все товары"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM products ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_product_quantity(self, name: str, quantity: int) -> bool:
        """
        Обновить количество товара
        
        Args:
            name: Наименование товара
            quantity: Новое количество
            
        Returns:
            True если успешно, False если товар не найден
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE products SET quantity = ? WHERE name = ?
        """, (quantity, name))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def update_product_price(self, name: str, price: float) -> bool:
        """
        Обновить цену товара
        
        Args:
            name: Наименование товара
            price: Новая цена
            
        Returns:
            True если успешно, False если товар не найден
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE products SET price = ? WHERE name = ?
        """, (price, name))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def add_product_quantity(self, name: str, quantity: int) -> bool:
        """
        Добавить количество к существующему товару
        
        Args:
            name: Наименование товара
            quantity: Количество для добавления
            
        Returns:
            True если успешно, False если товар не найден
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE products SET quantity = quantity + ? WHERE name = ?
        """, (quantity, name))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    # === Продажа товара ===
    
    def sell_product(self, name: str, quantity: int) -> Tuple[bool, Optional[float]]:
        """
        Продать товар
        
        Args:
            name: Наименование товара
            quantity: Количество для продажи
            
        Returns:
            (success, total_price) - успех операции и общая стоимость
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Получить товар
        product = self.get_product(name)
        if not product:
            conn.close()
            return (False, None)
        
        if product['quantity'] < quantity:
            conn.close()
            return (False, None)
        
        # Обновить количество
        cursor.execute("""
            UPDATE products SET quantity = quantity - ? WHERE name = ?
        """, (quantity, name))
        
        # Рассчитать стоимость
        total_price = product['price'] * quantity
        
        # Добавить в кассу
        cursor.execute("""
            INSERT INTO cashbox (amount, transaction_type, description)
            VALUES (?, 'sale', ?)
        """, (total_price, f"Продажа: {name} x{quantity}"))
        
        conn.commit()
        conn.close()
        
        return (True, total_price)
    
    # === Управление кассой ===
    
    def get_cashbox_balance(self) -> float:
        """Получить текущий баланс кассы"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT SUM(amount) FROM cashbox")
        result = cursor.fetchone()[0]
        conn.close()
        
        return result if result else 0.0
    
    def add_cash(self, amount: float, description: str = "") -> bool:
        """
        Добавить деньги в кассу
        
        Args:
            amount: Сумма
            description: Описание операции
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO cashbox (amount, transaction_type, description)
            VALUES (?, 'income', ?)
        """, (amount, description or "Пополнение кассы"))
        
        conn.commit()
        conn.close()
        
        return True
    
    def withdraw_cash(self, amount: float, description: str = "") -> bool:
        """
        Снять деньги из кассы
        
        Args:
            amount: Сумма
            description: Описание операции
            
        Returns:
            True если успешно, False если недостаточно средств
        """
        balance = self.get_cashbox_balance()
        if balance < amount:
            return False
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO cashbox (amount, transaction_type, description)
            VALUES (?, 'expense', ?)
        """, (-amount, description or "Снятие из кассы"))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_cashbox_history(self, limit: int = 10) -> List[Dict]:
        """Получить историю операций кассы"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM cashbox 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

