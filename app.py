from flask import Flask, render_template, request, redirect, session
import pyodbc

app = Flask(__name__)
app.secret_key = 'supersecret'

# Azure SQL Database connection string
conn_str = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=tcp:event-horizon.database.windows.net,1433;'
    'DATABASE=eventhorizon-db;'
    'UID=frhnahnr;'
    'PWD=YourSecurePasswordHere;'
    'Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
)

def get_db():
    return pyodbc.connect(conn_str)

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE Email=? AND Password=? AND Role=?", (email, password, role))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user.UserID
            session['email'] = user.Email
            session['role'] = role
            return redirect('/organizer/dashboard' if role == 'organizer' else '/attendee/dashboard')
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect('/events')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = 'attendee'

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE Email=?", (email,))
        if cursor.fetchone():
            return render_template('register.html', error="Email already exists.")

        cursor.execute("INSERT INTO Users (Email, Password, Role) VALUES (?, ?, ?)", (email, password, role))
        conn.commit()
        return render_template('register.html', success="Account created successfully! You may now log in.")
    return render_template('register.html')

@app.route('/organizer/dashboard')
def organizer_dashboard():
    if session.get('role') != 'organizer':
        return redirect('/login')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.*, COUNT(a.AttendeeID) AS Registered
        FROM Events e
        LEFT JOIN Attendees a ON e.EventID = a.EventID
        WHERE e.OrganizerID = ?
        GROUP BY e.EventID, e.Name, e.Date, e.Location, e.Capacity, e.Description, e.OrganizerID
    ''', (session['user_id'],))
    events = cursor.fetchall()
    return render_template('organizer_dashboard.html', events=events)

@app.route('/attendee/dashboard')
def attendee_dashboard():
    if session.get('role') != 'attendee':
        return redirect('/login')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Events ORDER BY Date")
    events = cursor.fetchall()
    return render_template('attendee_dashboard.html', events=events)

@app.route('/events')
def public_events():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Events ORDER BY Date")
    events = cursor.fetchall()
    return render_template('public_events.html', events=events)

@app.route('/add', methods=['GET', 'POST'])
def add_event():
    if session.get('role') != 'organizer':
        return redirect('/login')
    if request.method == 'POST':
        name = request.form['name']
        date = request.form['date']
        location = request.form['location']
        capacity = request.form['capacity']
        description = request.form['description']
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Events (Name, Date, Location, Capacity, Description, OrganizerID) VALUES (?, ?, ?, ?, ?, ?)",
            (name, date, location, capacity, description, session['user_id'])
        )
        conn.commit()
        return redirect('/organizer/dashboard')
    return render_template('add_event.html')

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
        description = request.form['description']
        cursor.execute(
            "UPDATE Events SET Name=?, Date=?, Location=?, Capacity=?, Description=? WHERE EventID=?",
            (name, date, location, capacity, description, event_id)
        )
        conn.commit()
        return redirect('/organizer/dashboard')
    cursor.execute("SELECT * FROM Events WHERE EventID=?", (event_id,))
    event = cursor.fetchone()
    return render_template('edit_event.html', event=event)

@app.route('/delete/<int:event_id>', methods=['GET', 'POST'])
def delete_event(event_id):
    if session.get('role') != 'organizer':
        return redirect('/login')
    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'POST':
        cursor.execute("DELETE FROM Events WHERE EventID=?", (event_id,))
        conn.commit()
        return redirect('/organizer/dashboard')
    cursor.execute("SELECT * FROM Events WHERE EventID=?", (event_id,))
    event = cursor.fetchone()
    return render_template('delete_event.html', event=event)

if __name__ == '__main__':
    app.run(debug=True)
