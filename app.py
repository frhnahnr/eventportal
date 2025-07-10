from flask import Flask, render_template, request, redirect, url_for, session
import pyodbc
import os

app = Flask(__name__)
app.secret_key = 'supersecret'

# Database connection (Azure SQL)
def get_db():
    conn_str = os.getenv("DATABASE_URL")
    if not conn_str:
        raise Exception("DATABASE_URL is not set.")
    conn = pyodbc.connect(conn_str)
    conn.autocommit = True
    return conn

@app.route('/')
def index():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Events")
    events = cursor.fetchall()
    return render_template('index.html', events=events)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE Email=? AND Password=?", (email, password))
        user = cursor.fetchone()
        if user:
            session['user_id'] = user[0]
            session['role'] = user[3]
            return redirect(url_for('dashboard'))
        else:
            return "Login failed"
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Users (Email, Password, Role) VALUES (?, ?, ?)", (email, password, role))
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    role = session['role']
    conn = get_db()
    cursor = conn.cursor()

    if role == 'Organizer':
        cursor.execute("SELECT * FROM Events WHERE OrganizerID=?", (user_id,))
        events = cursor.fetchall()
    else:
        cursor.execute("""
            SELECT E.* FROM Events E
            JOIN Registrations R ON E.EventID = R.EventID
            WHERE R.AttendeeID=?
        """, (user_id,))
        events = cursor.fetchall()

    return render_template('dashboard.html', events=events, role=role)

@app.route('/create', methods=['GET', 'POST'])
def create_event():
    if 'user_id' not in session or session['role'] != 'Organizer':
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        date = request.form['date']
        location = request.form['location']
        capacity = request.form['capacity']
        organizer_id = session['user_id']
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Events (Name, Date, Location, Capacity, OrganizerID) VALUES (?, ?, ?, ?, ?)",
            (name, date, location, capacity, organizer_id)
        )
        return redirect(url_for('dashboard'))
    return render_template('create.html')

@app.route('/register_event/<int:event_id>')
def register_event(event_id):
    if 'user_id' not in session or session['role'] != 'Attendee':
        return redirect(url_for('login'))

    attendee_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Registrations (EventID, AttendeeID) VALUES (?, ?)", (event_id, attendee_id))
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Azure-compatible port setup
if __name__ == '__main__':
    import sys
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
