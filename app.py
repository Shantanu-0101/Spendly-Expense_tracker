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

PRESET_LABELS = {
    "this_month": "This month",
    "last_month": "Last month",
    "last_3_months": "Last 3 months",
    "all": "All time",
}
TRANSACTION_LIMIT = 50


def format_day(d):
    return f"{d:%b} {d.day}, {d.year}"


@app.route("/profile")
@login_required
def profile():
    user_id = session["user_id"]

    today = date.today()
    first_of_month = today.replace(day=1)
    last_month_end = first_of_month - timedelta(days=1)
    preset_ranges = {
        "this_month": (first_of_month, today),
        "last_month": (last_month_end.replace(day=1), last_month_end),
        "last_3_months": (today - timedelta(days=90), today),
        "all": (None, None),
    }

    range_key = request.args.get("range")
    if range_key in preset_ranges:
        active_preset = range_key
        date_from, date_to = preset_ranges[range_key]
    else:
        try:
            date_from = datetime.strptime(request.args.get("from", ""), "%Y-%m-%d").date()
            date_to = datetime.strptime(request.args.get("to", ""), "%Y-%m-%d").date()
        except ValueError:
            active_preset = "this_month"
            date_from, date_to = preset_ranges["this_month"]
        else:
            active_preset = "custom"
            if date_from > date_to:
                date_from, date_to = date_to, date_from

    if date_from is None:
        date_where, date_params = "", []
    else:
        date_where = "AND date >= ? AND date <= ?"
        date_params = [date_from.isoformat(), date_to.isoformat()]

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if row is None:
            session.clear()
            flash("Please sign in to continue")
            return redirect(url_for("login"))

        cat_rows = conn.execute(
            f"SELECT category, SUM(amount) AS total, COUNT(*) AS cnt FROM expenses "
            f"WHERE user_id = ? {date_where} "
            f"GROUP BY category ORDER BY total DESC, category",
            [user_id] + date_params,
        ).fetchall()

        txn_rows = conn.execute(
            f"SELECT date, description, category, amount FROM expenses "
            f"WHERE user_id = ? {date_where} ORDER BY date DESC, id DESC LIMIT ?",
            [user_id] + date_params + [TRANSACTION_LIMIT],
        ).fetchall()
    finally:
        conn.close()

    parts = row["name"].split()
    initials = (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()
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

    total_spent = sum(c["total"] for c in cat_rows)
    stats = {
        "total_spent": f"₹{total_spent:.2f}",
        "transaction_count": sum(c["cnt"] for c in cat_rows),
        "top_category": cat_rows[0]["category"] if cat_rows else "—",
    }

    transactions = [
        {
            "date": r["date"],
            "description": r["description"],
            "category": r["category"],
            "amount": f"₹{r['amount']:.2f}",
        }
        for r in txn_rows
    ]

    categories = [
        {
            "name": c["category"],
            "total": f"₹{c['total']:.2f}",
            "percent": round(c["total"] / total_spent * 100) if total_spent > 0 else 0,
        }
        for c in cat_rows
    ]

    presets = [
        {"key": key, "label": label, "url": url_for("profile", range=key)}
        for key, label in PRESET_LABELS.items()
    ]

    if date_from is None:
        date_label = "Showing all time"
    else:
        date_label = f"Showing {format_day(date_from)} – {format_day(date_to)}"

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
