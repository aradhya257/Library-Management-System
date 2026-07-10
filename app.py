from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = 'library_secret_key'

# ---------------- MYSQL CONNECTION (SAFE MODE) ----------------
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="@aradhya",
        database="library_db"
    )
except:
    db = None

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('home.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if not db:
            return "Database not connected"

        username = request.form['username']
        password = request.form['password']

        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()

        if user:
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('index.html', error="Invalid Username or Password")

    return render_template('index.html')

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# ---------------- ADD BOOK ----------------
@app.route('/add_book', methods=['POST'])
def add_book():
    if 'user' not in session:
        return redirect(url_for('login'))

    if not db:
        return "Database not connected"

    data = request.form
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO books (book_name, author, publication, branch, price, quantity)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (data['book_name'], data['author'], data['publication'], data['branch'], data['price'], data['quantity']))
    db.commit()

    return redirect(url_for('dashboard'))

# ---------------- BOOK REPORT ----------------
@app.route('/book_report')
def book_report():
    if 'user' not in session:
        return redirect(url_for('login'))

    if not db:
        return "Database not connected"

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()

    return render_template('book_report.html', books=books)

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# ---------------- RUN SERVER ----------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
