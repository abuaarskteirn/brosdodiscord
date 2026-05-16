from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

import os
import json
from datetime import datetime, timezone

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("WEB_SECRET_KEY", "change-me")

OWNER_USERNAME = os.getenv("OWNER_USERNAME", "owner")
OWNER_PASSWORD = os.getenv("OWNER_PASSWORD", "password")

DATA_FILE = "data.json"


# =========================
# DATA
# =========================

def load_data():

    if not os.path.exists(DATA_FILE):

        data = {
            "orders": {},
            "warnings": {},
            "web_users": {}
        }

        save_data(data)

        return data

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    data.setdefault("orders", {})
    data.setdefault("warnings", {})
    data.setdefault("web_users", {})

    if OWNER_USERNAME not in data["web_users"]:

        data["web_users"][OWNER_USERNAME] = {
            "password_hash": generate_password_hash(
                OWNER_PASSWORD
            ),

            "rank": "Owner",

            "active": True,

            "created_at": datetime.now(
                timezone.utc
            ).isoformat()
        }

        save_data(data)

    return data


def save_data(data):

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# =========================
# USER
# =========================

def current_user():

    username = session.get("username")

    if not username:
        return None

    data = load_data()

    user = data["web_users"].get(username)

    if not user:
        return None

    return {
        "username": username,
        "rank": user["rank"]
    }


def logged_in():
    return current_user() is not None


# =========================
# STYLING
# =========================

BASE = """
<style>

body{
    margin:0;
    background:#0b1120;
    color:white;
    font-family:Arial;
}

.nav{
    background:#111827;
    padding:15px;
    display:flex;
    gap:15px;
}

.nav a{
    color:white;
    text-decoration:none;
    font-weight:bold;
}

.container{
    padding:25px;
}

.card{
    background:#111827;
    padding:20px;
    border-radius:14px;
    margin-bottom:20px;
}

input, select, button{
    width:100%;
    padding:12px;
    margin-top:10px;
    border:none;
    border-radius:10px;
}

button{
    background:#2563eb;
    color:white;
    cursor:pointer;
}

table{
    width:100%;
    border-collapse:collapse;
    background:#111827;
}

th, td{
    padding:12px;
    border-bottom:1px solid #374151;
}

.badge{
    background:#2563eb;
    padding:5px 10px;
    border-radius:999px;
}

</style>
"""


def page(content):

    user = current_user()

    nav = ""

    if user:

        nav = f"""
        <div class="nav">

            <a href="/">Dashboard</a>

            <a href="/orders">Orders</a>

            <a href="/warnings">Warnings</a>

            <a href="/users">Users</a>

            <a href="/logout">Logout</a>

        </div>
        """

    return f"""
    <!DOCTYPE html>

    <html>

    <head>

        <title>BrosDoDiscord Dashboard</title>

        {BASE}

    </head>

    <body>

        {nav}

        <div class="container">

            {content}

        </div>

    </body>

    </html>
    """


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        data = load_data()

        user = data["web_users"].get(username)

        if user:

            if check_password_hash(
                user["password_hash"],
                password
            ):

                session["username"] = username

                return redirect("/")

    return render_template_string(page("""

    <div class="card">

        <h1>BrosDoDiscord Login</h1>

        <form method="POST">

            <input
                name="username"
                placeholder="Username"
                required
            >

            <input
                name="password"
                type="password"
                placeholder="Password"
                required
            >

            <button type="submit">

                Login

            </button>

        </form>

    </div>

    """))


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================
# DASHBOARD
# =========================

@app.route("/")
def dashboard():

    if not logged_in():
        return redirect("/login")

    data = load_data()

    orders = data["orders"]

    total_revenue = sum(
        float(o.get("total", 0))
        for o in orders.values()
    )

    total_orders = len(orders)

    completed_orders = len([
        o for o in orders.values()
        if o.get("status") == "complete"
    ])

    return render_template_string(page(f"""

    <h1>BrosDoDiscord Dashboard</h1>

    <div class="card">

        <h2>Total Revenue</h2>

        <p>${total_revenue:.2f}</p>

    </div>

    <div class="card">

        <h2>Total Orders</h2>

        <p>{total_orders}</p>

    </div>

    <div class="card">

        <h2>Completed Orders</h2>

        <p>{completed_orders}</p>

    </div>

    """))


# =========================
# ORDERS
# =========================

@app.route("/orders")
def orders():

    if not logged_in():
        return redirect("/login")

    data = load_data()

    rows = ""

    for oid, order in data["orders"].items():

        rows += f"""

        <tr>

            <td>#{oid}</td>

            <td>{order.get("title")}</td>

            <td>{order.get("service")}</td>

            <td>

                <span class="badge">

                    {order.get("status")}

                </span>

            </td>

            <td>${float(order.get("total", 0)):.2f}</td>

            <td>${float(order.get("dev_cut", 0)):.2f}</td>

        </tr>
        """

    return render_template_string(page(f"""

    <h1>Orders</h1>

    <table>

        <tr>

            <th>ID</th>

            <th>Title</th>

            <th>Service</th>

            <th>Status</th>

            <th>Total</th>

            <th>Dev Cut</th>

        </tr>

        {rows}

    </table>

    """))


# =========================
# WARNINGS
# =========================

@app.route("/warnings")
def warnings():

    if not logged_in():
        return redirect("/login")

    data = load_data()

    rows = ""

    for uid, warns in data["warnings"].items():

        for warn in warns:

            rows += f"""

            <tr>

                <td>{uid}</td>

                <td>{warn.get("reason")}</td>

                <td>{warn.get("moderator")}</td>

                <td>{warn.get("time")}</td>

            </tr>
            """

    return render_template_string(page(f"""

    <h1>Warnings</h1>

    <table>

        <tr>

            <th>User ID</th>

            <th>Reason</th>

            <th>Moderator</th>

            <th>Time</th>

        </tr>

        {rows}

    </table>

    """))


# =========================
# USERS
# =========================

@app.route("/users", methods=["GET", "POST"])
def users():

    if not logged_in():
        return redirect("/login")

    data = load_data()

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        rank = request.form.get("rank")

        data["web_users"][username] = {

            "password_hash": generate_password_hash(
                password
            ),

            "rank": rank,

            "active": True,

            "created_at": datetime.now(
                timezone.utc
            ).isoformat()
        }

        save_data(data)

        return redirect("/users")

    rows = ""

    for username, user in data["web_users"].items():

        rows += f"""

        <tr>

            <td>{username}</td>

            <td>{user.get("rank")}</td>

            <td>{user.get("created_at")}</td>

        </tr>
        """

    return render_template_string(page(f"""

    <h1>Website Users</h1>

    <div class="card">

        <h2>Add User</h2>

        <form method="POST">

            <input
                name="username"
                placeholder="Username"
                required
            >

            <input
                name="password"
                placeholder="Password"
                required
            >

            <select name="rank">

                <option>Owner</option>

                <option>Manager</option>

                <option>Developer</option>

                <option>Support</option>

                <option>Viewer</option>

            </select>

            <button type="submit">

                Add User

            </button>

        </form>

    </div>

    <table>

        <tr>

            <th>Username</th>

            <th>Rank</th>

            <th>Created</th>

        </tr>

        {rows}

    </table>

    """))


# =========================
# START
# =========================

if __name__ == "__main__":

    load_data()

    app.run(
        host="0.0.0.0",
        port=5000
    )
