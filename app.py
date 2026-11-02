import os
import functools
import sqlite3
from datetime import date, datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-fallback-key")

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Auth decorator                                                      #
# ------------------------------------------------------------------ #

def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Please sign in to continue")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "GET":
        return render_template("register.html", name="", email="")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    error = None
    if not name:
        error = "Name is required"
    elif "@" not in email:
        error = "A valid email address is required"
    elif len(password) < 8:
        error = "Password must be at least 8 characters"

    if error:
        return render_template("register.html", error=error, name=name, email=email)

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return render_template(
            "register.html",
            error="An account with this email already exists",
            name=name,
            email=email,
        )
    conn.close()

    flash("Account created — please sign in")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "GET":
        return render_template("login.html", email="")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        return render_template("login.html", error="Invalid email or password", email=email)

    conn = get_db()
    user = conn.execute(
        "SELECT id, name, password_hash FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password", email=email)

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", name=session["user_name"])


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("landing"))


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/profile")
@login_required
def profile():
    user_id = session["user_id"]
    conn = get_db()

    row = conn.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?", (user_id,)
    ).fetchone()

    initials = "".join(w[0].upper() for w in row["name"].split() if w)
    try:
        created_dt = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")
        member_since = created_dt.strftime("%B %Y")
    except (TypeError, ValueError):
        member_since = row["created_at"] or "Unknown"

    user = {
        "name": row["name"],
        "email": row["email"],
        "initials": initials,
        "member_since": member_since,
    }

    today = date.today()
    first_of_month = today.replace(day=1)
    is_all_time = request.args.get("range") == "all"

    if is_all_time:
        date_from = None
        date_to = None
    else:
        raw_from = request.args.get("from")
        raw_to = request.args.get("to")
        try:
            date_from = datetime.strptime(raw_from, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            date_from = first_of_month
        try:
            date_to = datetime.strptime(raw_to, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            date_to = today
        if date_from > date_to:
            date_from, date_to = date_to, date_from

    if is_all_time:
        date_where = ""
        date_params = []
    else:
        date_where = "AND e.date >= ? AND e.date <= ?"
        date_params = [date_from.isoformat(), date_to.isoformat()]

    stats_row = conn.execute(
        f"SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS cnt "
        f"FROM expenses e WHERE e.user_id = ? {date_where}",
        [user_id] + date_params,
    ).fetchone()

    total_spent = stats_row["total"]
    transaction_count = stats_row["cnt"]

    top_row = conn.execute(
        f"SELECT category FROM expenses e WHERE e.user_id = ? {date_where} "
        f"GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
        [user_id] + date_params,
    ).fetchone()

    stats = {
        "total_spent": f"₹{total_spent:.2f}",
        "transaction_count": transaction_count,
        "top_category": top_row["category"] if top_row else "—",
    }

    txn_rows = conn.execute(
        f"SELECT date, description, category, amount FROM expenses e "
        f"WHERE e.user_id = ? {date_where} ORDER BY e.date DESC",
        [user_id] + date_params,
    ).fetchall()

    transactions = [
        {
            "date": r["date"],
            "description": r["description"],
            "category": r["category"],
            "amount": f"₹{r['amount']:.2f}",
        }
        for r in txn_rows
    ]

    cat_rows = conn.execute(
        f"SELECT category, SUM(amount) AS total FROM expenses e "
        f"WHERE e.user_id = ? {date_where} "
        f"GROUP BY category ORDER BY total DESC",
        [user_id] + date_params,
    ).fetchall()

    categories = [
        {
            "name": c["category"],
            "total": f"₹{c['total']:.2f}",
            "percent": round(c["total"] / total_spent * 100) if total_spent > 0 else 0,
        }
        for c in cat_rows
    ]

    conn.close()

    last_month_end = first_of_month - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    three_months_ago = today - timedelta(days=90)

    presets = [
        {"label": "This month", "key": "this_month",
         "url": url_for("profile", **{"from": first_of_month.isoformat(), "to": today.isoformat()})},
        {"label": "Last month", "key": "last_month",
         "url": url_for("profile", **{"from": last_month_start.isoformat(), "to": last_month_end.isoformat()})},
        {"label": "Last 3 months", "key": "last_3_months",
         "url": url_for("profile", **{"from": three_months_ago.isoformat(), "to": today.isoformat()})},
        {"label": "All time", "key": "all",
         "url": url_for("profile", range="all")},
    ]

    if is_all_time:
        active_preset = "all"
    elif date_from == first_of_month and date_to == today:
        active_preset = "this_month"
    elif date_from == last_month_start and date_to == last_month_end:
        active_preset = "last_month"
    elif date_from == three_months_ago and date_to == today:
        active_preset = "last_3_months"
    else:
        active_preset = "custom"

    day_fmt = "%#d" if os.name == "nt" else "%-d"
    if is_all_time:
        date_label = "Showing all time"
    else:
        fmt = f"%b {day_fmt}, %Y"
        date_label = f"Showing {date_from.strftime(fmt)} – {date_to.strftime(fmt)}"

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
        presets=presets,
        active_preset=active_preset,
        date_from=date_from.isoformat() if date_from else "",
        date_to=date_to.isoformat() if date_to else "",
        date_label=date_label,
    )


@app.route("/expenses/add")
@login_required
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
@login_required
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
@login_required
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
