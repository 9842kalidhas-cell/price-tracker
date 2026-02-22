from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3
import requests
from bs4 import BeautifulSoup
import yagmail

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# ------------------- LOGIN MANAGER -------------------

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ------------------- DATABASE -------------------

import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    create_tables()
# ------------------- USER CLASS -------------------

class User(UserMixin):
    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.email = email
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    if user:
        return User(user["id"], user["username"], user["email"], user["password"])
    return None

# ------------------- EMAIL FUNCTION -------------------

def send_email(receiver_email, product_title, current_price, url):
    try:
        sender_email = "9842kalidhas@gmail.com"
        app_password = "wfjvbnncwrgujpvw"

        yag = yagmail.SMTP(sender_email, app_password)

        subject = "Price Drop Alert!"
        body = f"""
The price dropped!

Product: {product_title}
Current Price: ₹{current_price}

Link: {url}
"""

        yag.send(receiver_email, subject, body)
        print("Email sent successfully!")

    except Exception as e:
        print("Email error:", e)

# ------------------- AMAZON SCRAPER -------------------

def get_amazon_price(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "en-US,en;q=0.9"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return "Error", 0

    soup = BeautifulSoup(response.content, "html.parser")

    title_tag = soup.find(id="productTitle")
    title = title_tag.get_text().strip() if title_tag else "Title not found"

    price = 0

    whole = soup.find("span", class_="a-price-whole")
    fraction = soup.find("span", class_="a-price-fraction")

    if whole and fraction:
        price = whole.get_text().replace(",", "") + fraction.get_text()

    return title, float(price) if price else 0

# ------------------- ROUTES -------------------

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    message = ""

    if request.method == "POST":
        url = request.form["url"]
        target_price = float(request.form["target_price"])

        title, price = get_amazon_price(url)

        if isinstance(price, str):
            price = float(price.replace(",", "").replace("₹", "").strip())
        else:
            price = float(price)

        if price <= target_price:
            send_email(current_user.email, title, price, url)
            message = f"Price dropped! Email sent to {current_user.email}"
        else:
            message = f"Current price is ₹{price}. Waiting for price drop."

    return render_template("index.html", message=message)

# ------------------- REGISTER -------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, password)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")

# ------------------- LOGIN -------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if user:
            if user["password"] == password:   # check password separately
                user_obj = User(
                    user["id"],
                    user["username"],
                    user["email"],
                    user["password"]
                )
                login_user(user_obj)
                return redirect(url_for("index"))

        return "Invalid username or password"

    return render_template("login.html")
 
# ------------------- LOGOUT -------------------

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ------------------- RUN -------------------

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)