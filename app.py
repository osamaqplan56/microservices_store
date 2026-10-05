from flask import Flask, jsonify, request, render_template
import sqlite3
import hashlib
import re
from database import init_db

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('store.db')
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def is_strong_password(password):
    if len(password) < 6:
        return False, "يجب أن تكون كلمة المرور 6 خانات على الأقل."
    if not re.search("[0-9]", password):
        return False, "يجب أن تحتوي على رقم."
    if not re.search("[A-Z]", password):
        return False, "يجب أن تحتوي على حرف كبير."
    return True, "قوية."

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT TOTAL(total_price) as volume FROM orders")
        volume = cursor.fetchone()['volume']
        cursor.execute("SELECT COUNT(order_id) as total_orders FROM orders")
        total_orders = cursor.fetchone()['total_orders']
        cursor.execute("SELECT AVG(rating) as avg_rating FROM reviews")
        avg_rating = cursor.fetchone()['avg_rating'] or 0.0
        conn.close()
        return jsonify({
            "financial_volume": round(volume, 2),
            "total_orders_processed": total_orders,
            "store_average_rating": round(avg_rating, 1)
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/services', methods=['GET'])
def get_services():
    try:
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM services WHERE status = 'active' ORDER BY service_id DESC").fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    try:
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM orders ORDER BY order_id DESC").fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        conn = get_db_connection()
        rows = conn.execute("SELECT user_id, username, user_type, wallet_balance FROM users").fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/messages', methods=['GET'])
def get_messages():
    try:
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM messages ORDER BY message_id DESC").fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/messages/archive', methods=['POST'])
def archive_messages():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE message_id < (SELECT MAX(message_id) - 5 FROM messages)")
        archived_count = conn.total_changes
        conn.commit()
        conn.close()
        return jsonify({
            "status": "success",
            "message": f"🤖 تم تشغيل محرك التحسين: تنظيف {archived_count} رسائل قديمة بنجاح!"
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    try:
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM reviews ORDER BY review_id DESC").fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        is_valid, msg = is_strong_password(data["password"])
        if not is_valid:
            return jsonify({"status": "security_error", "message": msg}), 400
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, email, password_hash, user_type) VALUES (?, ?, ?, ?)", 
                       (data["username"], data["email"], hash_password(data["password"]), data.get("user_type", "both")))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "تم التسجيل بنجاح!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "مسجل مسبقاً"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/services', methods=['POST'])
def add_service():
    try:
        data = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO services (seller_id, title, description, price, delivery_days) VALUES (?, ?, ?, ?, ?)", 
                       (data["seller_id"], data["title"], data.get("description", ""), data["price"], data["delivery_days"]))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "تم نشر الخدمة بنجاح"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/orders', methods=['POST'])
def create_order():
    try:
        data = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT price, seller_id FROM services WHERE service_id = ?", (data["service_id"],))
        service = cursor.fetchone()
        if not service or service["seller_id"] == data["buyer_id"]:
            conn.close()
            return jsonify({"status": "error", "message": "عملية غير صالحة"}), 400
        price = service["price"]
        cursor.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (data["buyer_id"],))
        buyer = cursor.fetchone()
        if not buyer or buyer["wallet_balance"] < price:
            conn.close()
            return jsonify({"status": "error", "message": "رصيد المحفظة غير كافٍ!"}), 400
        cursor.execute("UPDATE users SET wallet_balance = wallet_balance - ? WHERE user_id = ?", (price, data["buyer_id"]))
        cursor.execute("UPDATE users SET wallet_balance = wallet_balance + ? WHERE user_id = ?", (price, service["seller_id"]))
        cursor.execute("INSERT INTO orders (service_id, buyer_id, total_price, status) VALUES (?, ?, ?, 'completed')", 
                       (data["service_id"], data["buyer_id"], price))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "تمت عملية الشراء بنجاح مالي!"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/messages', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (sender_id, receiver_id, message_text) VALUES (?, ?, ?)", 
                       (data["sender_id"], data["receiver_id"], data["message_text"]))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "تم إرسال الرسالة!"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/reviews', methods=['POST'])
def add_review():
    try:
        data = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT service_id, buyer_id FROM orders WHERE order_id = ?", (data["order_id"],))
        order = cursor.fetchone()
        if not order:
            conn.close()
            return jsonify({"status": "error", "message": "الطلب غير موجود"}), 404
        cursor.execute("INSERT INTO reviews (order_id, service_id, buyer_id, rating, comment) VALUES (?, ?, ?, ?, ?)", 
                       (data["order_id"], order["service_id"], order["buyer_id"], data["rating"], data.get("comment", "")))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "🎉 تم حفظ التقييم بنجاح!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "تم تقييم هذا الطلب مسبقاً!"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    init_db()
    print("🚀 جاري تشغيل خادم متجر الخدمات المصغرة المتفوق والمستقر...")
    app.run(debug=True, port=5000)
