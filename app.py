from flask import Flask, render_template, request, redirect, url_for, session
import pyodbc
import os

app = Flask(__name__)
app.secret_key = 'supersecret'  # For session management

# Azure SQL connection
def get_db():
    conn_str = os.getenv("AZURE_SQL_CONNECTIONSTRING")
    if not conn_str:
        raise Exception("AZURE_SQL_CONNECTIONSTRING is not set.")
    return pyodbc.connect(conn_str)

# HOME PAGE
@app.route('/')
def index():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    return render_template('index.html', events=events)

# LOGIN PAGE
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form['role']
        session['role'] = role
        return redirect(url_for('dashboard'))
    return render_template('login.html')

# DASHBOARD FOR ORGANIZERS
@app.route('/dashboard')
def dashboard():
    if session.get('role') != 'organizer':
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    return render_template('dashboard.html', events=events)

# ADD NEW EVENT
@app.route('/add', methods=['POST'])
def add_event():
    if session.get('role') != 'organizer':
        return redirect(url_for('login'))
    name = request.form['name']
    date = request.form['date']
    location = request.form['location']
    capacity = request.form['capacity']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO events (name, date, location, capacity) VALUES (?, ?, ?, ?)", 
                   (name, date, location, capacity))
    conn.commit()
    return redirect(url_for('dashboard'))

# REGISTER FOR EVENT
@app.route('/register/<int:event_id>', methods=['POST'])
def register(event_id):
    name = request.form['name']
    contact = request.form['contact']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO registrations (event_id, name, contact) VALUES (?, ?, ?)", 
                   (event_id, name, contact))
    conn.commit()
    return redirect(url_for('index'))

# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# RUN ON AZURE PORT
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))  # Azure expects port 8000
    app.run(host='0.0.0.0', port=port)
