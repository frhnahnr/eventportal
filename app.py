from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from flask import Flask, render_template, request, redirect, session
import pyodbc
import os

app = Flask(__name__)
app.secret_key = 'supersecret'
DB_FILE = 'events.db'

# Initialize database
def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE Users (
                UserID INTEGER PRIMARY KEY AUTOINCREMENT,
                Email TEXT NOT NULL,
                Password TEXT NOT NULL,
                Role TEXT NOT NULL
            )
        ''')

        # Events table
        cursor.execute('''
            CREATE TABLE Events (
                EventID INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT NOT NULL,
                Date TEXT NOT NULL,
                Location TEXT NOT NULL,
                Capacity INTEGER,
                OrganizerID INTEGER,
                FOREIGN KEY (OrganizerID) REFERENCES Users(UserID)
            )
        ''')

        # Attendees table
        cursor.execute('''
            CREATE TABLE Attendees (
                AttendeeID INTEGER PRIMARY KEY AUTOINCREMENT,
                FullName TEXT,
                Email TEXT,
                EventID INTEGER,
                FOREIGN KEY (EventID) REFERENCES Events(EventID)
            )
        ''')

        # Sample accounts
        cursor.execute("INSERT INTO Users (Email, Password, Role) VALUES (?, ?, ?)",
                       ("organizer@example.com", "123456", "organizer"))
        cursor.execute("INSERT INTO Users (Email, Password, Role) VALUES (?, ?, ?)",
                       ("attendee@example.com", "123456", "attendee"))

        conn.commit()
        conn.close()
# Get Azure SQL connection string from environment variable
conn_str = os.getenv("AZURE_SQL_CONNECTIONSTRING")

# Helper to get database connection
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn = pyodbc.connect(conn_str)
    conn.autocommit = True
    return conn

init_db()

@app.route('/')
def home():
    return redirect('/login')
@@ -74,54 +26,56 @@ def login():
        role = request.form['role']

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM Users WHERE Email=? AND Password=? AND Role=?",
            (email, password, role)).fetchone()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE Email=? AND Password=? AND Role=?", (email, password, role))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user['UserID']
            session['email'] = user['Email']
            session['user_id'] = user.UserID
            session['email'] = user.Email
            session['role'] = role
            if role == 'organizer':
                return redirect('/organizer/dashboard')
            elif role == 'attendee':
                return redirect('/attendee/dashboard')
            return redirect(f"/{role}/dashboard")
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/events')

# Organizer dashboard
@app.route('/organizer/dashboard')
def organizer_dashboard():
    if session.get('role') != 'organizer':
        return redirect('/login')
    conn = get_db()
    events = conn.execute('''
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*, COUNT(a.AttendeeID) AS Registered
        FROM Events e
        LEFT JOIN Attendees a ON e.EventID = a.EventID
        WHERE e.OrganizerID = ?
        GROUP BY e.EventID
    ''', (session['user_id'],)).fetchall()
        GROUP BY e.EventID, e.Name, e.Date, e.Location, e.Capacity, e.Description, e.OrganizerID
    """, (session['user_id'],))
    events = cursor.fetchall()
    return render_template('organizer_dashboard.html', events=events)

@app.route('/events')
def public_events():
    conn = get_db()
    events = conn.execute("SELECT * FROM Events ORDER BY Date").fetchall()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Events ORDER BY Date")
    events = cursor.fetchall()
    return render_template('public_events.html', events=events)

# Attendee dashboard
@app.route('/attendee/dashboard')
def attendee_dashboard():
    if session.get('role') != 'attendee':
        return redirect('/login')
    conn = get_db()
    events = conn.execute("SELECT * FROM Events").fetchall()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Events")
    events = cursor.fetchall()
    return render_template('attendee_dashboard.html', events=events)

@app.route('/register', methods=['GET', 'POST'])
@@ -133,18 +87,17 @@ def register():
        role = 'attendee'

        conn = get_db()
        existing = conn.execute("SELECT * FROM Users WHERE Email=?", (email,)).fetchone()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE Email=?", (email,))
        existing = cursor.fetchone()

        if existing:
            return render_template('register.html', error="Email already exists.")

        conn.execute("INSERT INTO Users (Email, Password, Role) VALUES (?, ?, ?)",
                     (email, password, role))
        conn.commit()

        cursor.execute("INSERT INTO Users (Email, Password, Role) VALUES (?, ?, ?)", (email, password, role))
        return render_template('register.html', success="Account created successfully! You may now log in.")
    return render_template('register.html')

# Add new event
@app.route('/add', methods=['GET', 'POST'])
def add_event():
    if session.get('role') != 'organizer':
@@ -155,50 +108,55 @@ def add_event():
        location = request.form['location']
        capacity = request.form['capacity']
        description = request.form['description']

        conn = get_db()
        conn.execute(
            "INSERT INTO Events (Name, Date, Location, Capacity, Description, OrganizerID) VALUES (?, ?, ?, ?, ?, ?)",
            (name, date, location, capacity, description, session['user_id'])
        )
        conn.commit()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Events (Name, Date, Location, Capacity, Description, OrganizerID)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, date, location, capacity, description, session['user_id']))
        return redirect('/organizer/dashboard')
    return render_template('add_event.html')

# Edit event
@app.route('/edit/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    if session.get('role') != 'organizer':
        return redirect('/login')

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        date = request.form['date']
        location = request.form['location']
        capacity = request.form['capacity']
        description = request.form['description']  # ✅ ADD THIS LINE

        conn.execute("""
        description = request.form['description']
        cursor.execute("""
            UPDATE Events
            SET Name=?, Date=?, Location=?, Capacity=?, Description=?
            WHERE EventID=?
        """, (name, date, location, capacity, description, event_id))  # ✅ INCLUDE Description in query
        conn.commit()
        """, (name, date, location, capacity, description, event_id))
        return redirect('/organizer/dashboard')

    event = conn.execute("SELECT * FROM Events WHERE EventID=?", (event_id,)).fetchone()
    cursor.execute("SELECT * FROM Events WHERE EventID=?", (event_id,))
    event = cursor.fetchone()
    return render_template('edit_event.html', event=event)

# Delete event
@app.route('/delete/<int:event_id>', methods=['GET', 'POST'])
def delete_event(event_id):
    if session.get('role') != 'organizer':
        return redirect('/login')

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        conn.execute("DELETE FROM Events WHERE EventID=?", (event_id,))
        conn.commit()
        cursor.execute("DELETE FROM Events WHERE EventID=?", (event_id,))
        return redirect('/organizer/dashboard')
    event = conn.execute("SELECT * FROM Events WHERE EventID=?", (event_id,)).fetchone()

    cursor.execute("SELECT * FROM Events WHERE EventID=?", (event_id,))
    event = cursor.fetchone()
    return render_template('delete_event.html', event=event)

@app.route('/attendee/register/<int:event_id>', methods=['GET', 'POST'])
@@ -207,28 +165,22 @@ def register_for_event(event_id):
        return redirect('/login')

    conn = get_db()
    cursor = conn.cursor()

    # ✅ Check if already registered
    existing = conn.execute(
        "SELECT * FROM Attendees WHERE Email=? AND EventID=?",
        (session['email'], event_id)
    ).fetchone()
    cursor.execute("SELECT * FROM Attendees WHERE Email=? AND EventID=?", (session['email'], event_id))
    existing = cursor.fetchone()

    if existing:
        return render_template('attendee_registration_result.html', message="You are already registered for this event.")

    if request.method == 'POST':
        full_name = request.form['full_name']
        conn.execute(
            "INSERT INTO Attendees (FullName, Email, EventID) VALUES (?, ?, ?)",
            (full_name, session['email'], event_id)
        )
        conn.commit()
        cursor.execute("INSERT INTO Attendees (FullName, Email, EventID) VALUES (?, ?, ?)", (full_name, session['email'], event_id))
        return render_template('attendee_registration_result.html', message="Successfully registered for the event!")

    event = conn.execute("SELECT * FROM Events WHERE EventID=?", (event_id,)).fetchone()
    cursor.execute("SELECT * FROM Events WHERE EventID=?", (event_id,))
    event = cursor.fetchone()
    return render_template('attendee_register_event.html', event=event)


if __name__ == '__main__':
    app.run(debug=True)
