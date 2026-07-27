import sqlite3
from contextlib import contextmanager

DATABASE = 'restaurant.db'

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize database with tables"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            )
        ''')
        
        # Menu items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                category_id INTEGER,
                available BOOLEAN DEFAULT 1,
                image_url TEXT,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        ''')
        
        # Orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                customer_address TEXT,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Order items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                menu_item_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
            )
        ''')
        
        # Insert sample data if tables are empty
        cursor.execute('SELECT COUNT(*) FROM categories')
        if cursor.fetchone()[0] == 0:
            insert_sample_data(cursor)

        # Drop existing users table if exists
        cursor.execute('DROP TABLE IF EXISTS users')
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                email TEXT NOT NULL,
                full_name TEXT NOT NULL,
                phone TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

def create_user(cursor, username, password_hash, email, full_name, phone=None, address=None):
    """Insert a new user. Returns the new user id."""
    cursor.execute('''
        INSERT INTO users (username, password_hash, email, full_name, phone, address) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (username, password_hash, email, full_name, phone, address))
    return cursor.lastrowid

def get_user_by_username(cursor, username):
    """Return a user row (sqlite3.Row) for the given username or None."""
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    return cursor.fetchone()

def insert_sample_data(cursor):
    """Insert sample menu data"""
    # Categories
    categories = [
        ('Appetizers', 'Start your meal right'),
        ('Main Course', 'Delicious main dishes'),
        ('Desserts', 'Sweet treats'),
        ('Beverages', 'Refreshing drinks')
    ]
    cursor.executemany('INSERT INTO categories (name, description) VALUES (?, ?)', categories)
    
    # Menu items
    menu_items = [
        ('Spring Rolls', 'Crispy vegetable spring rolls', 5.99, 1, 1, 'images/spring-rolls.svg'),
        ('Chicken Wings', 'Spicy buffalo wings', 8.99, 1, 1, 'images/wings.svg'),
        ('Grilled Chicken', 'Herb-marinated grilled chicken', 15.99, 2, 1, 'images/chicken.svg'),
        ('Beef Steak', 'Premium beef steak with sides', 22.99, 2, 1, 'images/steak.svg'),
        ('Vegetable Pasta', 'Fresh pasta with seasonal vegetables', 12.99, 2, 1, 'images/pasta.svg'),
        ('Chocolate Cake', 'Rich chocolate layer cake', 6.99, 3, 1, 'images/cake.svg'),
        ('Ice Cream', 'Vanilla ice cream with toppings', 4.99, 3, 1, 'images/icecream.svg'),
        ('Soft Drink', 'Chilled soft drinks', 2.99, 4, 1, 'images/soda.svg'),
        ('Fresh Juice', 'Freshly squeezed orange juice', 4.99, 4, 1, 'images/juice.svg')
    ]
    cursor.executemany('''
        INSERT INTO menu_items (name, description, price, category_id, available, image_url) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', menu_items)

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")