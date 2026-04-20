import os
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import json

app = Flask(__name__)

# Database configuration for local and PythonAnywhere
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "raffle_system.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT, last_name TEXT, email TEXT UNIQUE)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS Tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER, is_paid INTEGER DEFAULT 0,
            payment_reference TEXT, FOREIGN KEY (owner_id) REFERENCES Users (user_id))''')

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/register', methods=['POST'])
def register():
    f_name = request.form['f_name']
    l_name = request.form['l_name']
    email = request.form['email']
    count = int(request.form.get('count', 1))

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Users (first_name, last_name, email) VALUES (?, ?, ?)", 
                       (f_name, l_name, email))
        user_id = cursor.lastrowid
        for _ in range(count):
            cursor.execute("INSERT INTO Tickets (owner_id, is_paid, payment_reference) VALUES (?, 0, ?)", 
                           (user_id, email))
        conn.commit()
        return redirect(url_for('instructions', email=email, count=count))
    except sqlite3.IntegrityError:
        return "<h1>Already Registered</h1><p>This email is already in our system.</p><a href='/'>Go Back</a>"
    finally:
        conn.close()

@app.route('/instructions')
def instructions():
    email = request.args.get('email')
    count = request.args.get('count', 1)
    total_price = int(count) * 50 
    return render_template('instructions.html', email=email, count=count, price=total_price)

@app.route('/draw')
def draw():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.ticket_id, u.first_name, u.last_name 
        FROM Tickets t 
        JOIN Users u ON t.owner_id = u.user_id 
        WHERE t.is_paid = 1
    """)
    paid_entries = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('draw.html', entries=paid_entries)

@app.route('/verify/<key>/<email>')
def verify(key, email):
    if key != "milan77":
        return "Unauthorized", 403
    conn = get_db_connection()
    conn.execute("UPDATE Tickets SET is_paid = 1 WHERE payment_reference = ?", (email,))
    conn.commit()
    conn.close()
    return f"Success! Verified tickets for {email}."

if __name__ == '__main__':
    app.run(debug=True)