from flask import Flask, render_template, url_for, request, session, redirect, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from passlib.hash import sha256_crypt
import urllib

# URL-encode password
password = urllib.parse.quote_plus("F@rhanah13")

# Azure SQL connection string
engine = create_engine(
    f"mssql+pyodbc://sqladmin:{password}@eventportal-sql.database.windows.net/eventhorizon-db?driver=ODBC+Driver+17+for+SQL+Server"
)

db = scoped_session(sessionmaker(bind=engine))

app = Flask(__name__)
app.secret_key = "RadheKrishna"

@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        secure_password = sha256_crypt.encrypt(str(password))

        usernamedata = db.execute("SELECT username FROM users WHERE username=:username",
                                  {"username": username}).fetchone()
        if usernamedata is None:
            if password == confirm:
                db.execute("INSERT INTO users(name, username, password) VALUES(:name, :username, :password)",
                           {"name": name, "username": username, "password": secure_password})
                db.commit()
                flash("You are registered and can now login", "success")
                return redirect(url_for('login'))
            else:
                flash("Passwords do not match", "danger")
                return render_template('register.html')
        else:
            flash("User already exists, please login or contact admin", "danger")
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form.get("name")
        password = request.form.get("password")

        usernamedata = db.execute("SELECT username FROM users WHERE username=:username",
                                  {"username": username}).fetchone()
        passworddata = db.execute("SELECT password FROM users WHERE username=:username",
                                  {"username": username}).fetchone()

        if usernamedata is None:
            flash("No such username", "danger")
            return render_template('login.html')
        else:
            if sha256_crypt.verify(password, passworddata[0]):
                session["log"] = True
                flash("You are now logged in!", "success")
                return redirect(url_for('home'))
            else:
                flash("Incorrect password", "danger")
                return render_template('login.html')
    return render_template('login.html')


@app.route("/logout")
def logout():
    session.clear()
    flash("You are now logged out", "success")
    return redirect(url_for('login'))

@app.route("/")
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)
