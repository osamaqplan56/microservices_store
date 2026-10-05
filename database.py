import sqlite3

def init_db():
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()

    # 1. جدول المستخدمين (تمت إضافة حقل wallet_balance الافتراضي 100$ للمحاكاة)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            user_type TEXT CHECK(user_type IN ('buyer', 'seller', 'both')) DEFAULT 'both',
            wallet_balance REAL DEFAULT 100.0, -- رصيد وهمي أولي لتجربة الشراء
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. جدول الخدمات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            service_id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL CHECK(price >= 5),
            delivery_days INTEGER NOT NULL CHECK(delivery_days > 0),
            status TEXT CHECK(status IN ('active', 'paused')) DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    ''')

    # 3. جدول الطلبات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_id INTEGER,
            buyer_id INTEGER,
            order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT CHECK(status IN ('pending', 'in_progress', 'delivered', 'completed', 'cancelled')) DEFAULT 'pending',
            total_price REAL NOT NULL,
            FOREIGN KEY (service_id) REFERENCES services(service_id),
            FOREIGN KEY (buyer_id) REFERENCES users(user_id)
        )
    ''')

    # ➕ ميزة 1: جدول تقييمات الخدمات (Reviews)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER UNIQUE, -- التقييم يكون مرتبط بطلب شراء مكتمل واحد فقط
            service_id INTEGER,
            buyer_id INTEGER,
            rating INTEGER CHECK(rating BETWEEN 1 AND 5),
            comment TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (service_id) REFERENCES services(service_id),
            FOREIGN KEY (buyer_id) REFERENCES users(user_id)
        )
    ''')

    # ➕ ميزة 2: جدول الرسائل والتواصل الداخلي (Messages)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            receiver_id INTEGER,
            message_text TEXT NOT NULL,
            sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(user_id),
            FOREIGN KEY (receiver_id) REFERENCES users(user_id)
        )
    ''')

    conn.commit()
    conn.close()
    print("🚀 تم تحديث وتكبير هيكل قاعدة البيانات وإضافة الجداول المتقدمة بنجاح!")

if __name__ == '__main__':
    init_db()
