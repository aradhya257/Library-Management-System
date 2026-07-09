from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = 'library_secret_key'

# ---------------- MYSQL CONNECTION ----------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="@aradhya",
    database="library_db"
)

# =================================================
@app.route('/')
def home():
    return render_template('home.html')


# ---------------- LOGIN PAGE ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = db.cursor()
        query = "SELECT * FROM users WHERE username=%s AND password=%s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()

        if user:
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template(
                'index.html',
                error="Invalid Username or Password"
            )

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

    book_name = request.form['book_name']
    author = request.form['author']
    publication = request.form['publication']
    branch = request.form['branch']
    price = request.form['price']
    quantity = request.form['quantity']

    cursor = db.cursor()
    query = """
        INSERT INTO books
        (book_name, author, publication, branch, price, quantity)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (book_name, author, publication, branch, price, quantity))
    db.commit()

    return redirect(url_for('dashboard'))


# ---------------- BOOK REPORT ----------------
@app.route('/book_report')
def book_report():
    if 'user' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()

    return render_template('book_report.html', books=books)


# ---------------- BOOK REQUEST ----------------
@app.route('/book_request', methods=['GET', 'POST'])
def book_request():
    if 'user' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)

    # 1️⃣ Students fetch
    cursor.execute("SELECT student_name, roll_no FROM students")
    students = cursor.fetchall()

    # 2️⃣ Books fetch (only available)
    cursor.execute("SELECT book_name FROM books WHERE quantity > 0")
    books = cursor.fetchall()

    if request.method == 'POST':
        student_name = request.form['student_name']
        book_name = request.form['book_name']

        cursor.execute(
            """
            INSERT INTO book_requests
            (student_name, book_name, request_date, status)
            VALUES (%s, %s, CURDATE(), 'Pending')
            """,
            (student_name, book_name)
        )
        db.commit()

        return redirect(url_for('dashboard'))

    return render_template(
        'book_request.html',
        students=students,
        books=books
    )


# ---------------- REQUEST REPORT ----------------
@app.route('/request_report')
def request_report():
    if 'user' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM book_requests")
    requests = cursor.fetchall()

    return render_template('request_report.html', requests=requests)

#-----------------Delete request report--------------
@app.route('/delete_request/<int:id>')
def delete_request(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor()
    cursor.execute("DELETE FROM book_requests WHERE id = %s", (id,))
    db.commit()

    return redirect(url_for('request_report'))


# ---------------- APPROVE REQUEST ----------------
@app.route('/approve/<int:request_id>')
def approve_request(request_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM book_requests WHERE id=%s", (request_id,))
    req = cursor.fetchone()

    if req and req['status'] == 'Pending':

        cursor.execute(
            "SELECT id FROM books WHERE book_name=%s AND quantity > 0",
            (req['book_name'],)
        )
        book = cursor.fetchone()

        if not book:
            return "Book not available"

        book_id = book['id']

        cursor.execute(
            "UPDATE books SET quantity = quantity - 1 WHERE id=%s",
            (book_id,)
        )

        cursor.execute(
            """
            INSERT INTO issued_books
            (student_name, book_id, book_name, issue_date, return_date, status)
            VALUES (%s, %s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 7 DAY), 'Issued')
            """,
            (req['student_name'], book_id, req['book_name'])
        )

        cursor.execute(
            "UPDATE book_requests SET status='Approved' WHERE id=%s",
            (request_id,)
        )

        db.commit()

    return redirect(url_for('request_report'))


# ---------------- ISSUED BOOKS ----------------
@app.route('/issued_books')
def issued_books():
    if 'user' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM issued_books")
    data = cursor.fetchall()

    return render_template('issued_books.html', data=data)

# ---------------- RETURN BOOK ----------------
@app.route('/return/<int:id>')
def return_book(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM issued_books WHERE id=%s", (id,))
    book = cursor.fetchone()

    if book and book['status'] == 'Issued':

        cursor.execute(
            "UPDATE issued_books SET status='Returned' WHERE id=%s",
            (id,)
        )

        cursor.execute(
            "UPDATE books SET quantity = quantity + 1 WHERE book_name=%s",
            (book['book_name'],)
        )

        db.commit()

    return redirect(url_for('issued_books'))

#-----------------Book delete-----------------
@app.route('/delete_book/<int:id>')
def delete_book(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor()
    cursor.execute("DELETE FROM books WHERE id=%s", (id,))
    db.commit()

    return redirect(url_for('book_report'))

#-----------------Book Edit and Update-------------
@app.route('/edit_book/<int:id>')
def edit_book(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM books WHERE id=%s", (id,))
    book = cursor.fetchone()

    return render_template('edit_book.html', book=book)

@app.route('/update_book/<int:id>', methods=['POST'])
def update_book(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    book_name = request.form['book_name']
    author = request.form['author']
    publication = request.form['publication']
    branch = request.form['branch']
    price = request.form['price']
    quantity = request.form['quantity']

    cursor = db.cursor()
    cursor.execute(
        """
        UPDATE books
        SET book_name=%s, author=%s, publication=%s,
            branch=%s, price=%s, quantity=%s
        WHERE id=%s
        """,
        (book_name, author, publication, branch, price, quantity, id)
    )
    db.commit()

    return redirect(url_for('book_report'))


# ---------------- ADD STUDENT ----------------
@app.route('/add_student_page')
def add_student_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('add_student.html')


@app.route('/add_student', methods=['POST'])
def add_student():
    if 'user' not in session:
        return redirect(url_for('login'))

    student_name = request.form['student_name']
    roll_no = request.form['roll_no']
    branch = request.form['branch']
    year = request.form['year']
    mobile = request.form['mobile']

    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO students
        (student_name, roll_no, branch, year, mobile)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (student_name, roll_no, branch, year, mobile)
    )
    db.commit()

    return redirect(url_for('add_student_page'))


# ---------------- STUDENT REPORT ----------------
@app.route('/student_report')
def student_report():
    if 'user' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    return render_template('student_report.html', students=students)

#-------------------Delete student-----------------
@app.route('/delete_student/<int:id>')
def delete_student(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor()
    cursor.execute("DELETE FROM students WHERE id=%s", (id,))
    db.commit()

    return redirect(url_for('student_report'))

#-------------------Edit student-------------------
@app.route('/edit_student/<int:id>')
def edit_student(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students WHERE id=%s", (id,))
    student = cursor.fetchone()

    return render_template('edit_student.html', student=student)

@app.route('/update_student/<int:id>', methods=['POST'])
def update_student(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    student_name = request.form['student_name']
    roll_no = request.form['roll_no']
    branch = request.form['branch']
    year = request.form['year']
    mobile = request.form['mobile']

    cursor = db.cursor()
    cursor.execute(
        """
        UPDATE students
        SET student_name=%s, roll_no=%s, branch=%s, year=%s, mobile=%s
        WHERE id=%s
        """,
        (student_name, roll_no, branch, year, mobile, id)
    )
    db.commit()

    return redirect(url_for('student_report'))

#------------------Delete Issued book record-----------
@app.route('/delete_issued/<int:id>')
def delete_issued(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor()
    cursor.execute("DELETE FROM issued_books WHERE id = %s", (id,))
    db.commit()

    return redirect(url_for('issued_books'))

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


# ---------------- RUN SERVER ----------------
if __name__ == '__main__':
   app.run(debug=True)