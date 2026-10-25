# Spec: Login And Logout

## Overview

Add working login and logout to Spendly. The login page template already
exists with a form that POSTs to `/login`. This step wires up session-based
authentication: verify the user's email and password against the database,
store their identity in the Flask session, protect logged-in routes with a
decorator, and provide a logout endpoint that clears the session. This
completes the authentication system started in Step 2 (Registration) and
unblocks every feature that requires a logged-in user.

## Depends on

- **Step 1 — Database Setup** (users table and `get_db()` helper)
- **Step 2 — Registration** (users can create accounts, `secret_key` is
  configured, flash messages work)

## Routes

- `GET /login` — render the login form — **public** (already exists, needs
  minor change to accept flash messages)
- `POST /login` — validate credentials, start session, redirect to dashboard
  — **public**
- `GET /logout` — clear session, redirect to landing page — **logged-in**
- `GET /dashboard` — the logged-in home page showing the user's name —
  **logged-in**

## Database changes

No database changes. The `users` table already has `email` and
`password_hash` columns needed for authentication.

## Templates

- **Create:** `templates/dashboard.html` — minimal logged-in landing page
  showing the user's name and a link to logout. This serves as proof that
  login works and will be expanded in later steps.
- **Modify:** `templates/login.html` — add `value="{{ email }}"` to the
  email input so the value is preserved on error.
- **Modify:** `templates/base.html` — make the navbar context-aware: show
  "Sign in / Get started" for anonymous users, show "Dashboard / Logout" for
  logged-in users. Use `session.get("user_id")` to decide.

## Files to change

- `app.py` — add POST handler for `/login`, replace `/logout` placeholder,
  add `/dashboard` route, add `login_required` decorator, import
  `check_password_hash` from werkzeug, import `session` from flask
- `templates/base.html` — conditional navbar links
- `templates/login.html` — preserve email on error

## Files to create

- `templates/dashboard.html` — minimal logged-in home page

## New dependencies

No new dependencies. `werkzeug.security.check_password_hash` and
`flask.session` are already available.

## Rules for implementation

- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()`
- Parameterised queries only — no string formatting in SQL
- Passwords verified with `werkzeug.security.check_password_hash`
- Use CSS variables from `style.css` — never hardcode hex values
- All templates extend `base.html`
- **Login validation (server-side):**
  - Email must not be blank
  - Password must not be blank
  - On invalid credentials use a generic message: "Invalid email or
    password" — never reveal whether the email exists
- **Session management:**
  - On successful login, store `user_id` and `user_name` in
    `flask.session`
  - On logout, call `session.clear()`
- **Route protection:**
  - Create a `login_required` decorator using `functools.wraps`
  - If `session.get("user_id")` is `None`, redirect to `/login` with a
    flash message "Please sign in to continue"
  - Apply `login_required` to `/dashboard`, `/logout`, and all future
    logged-in routes
- **Redirects:**
  - After successful login → redirect to `/dashboard`
  - After logout → redirect to `/` (landing page)
  - If a logged-in user visits `/login` or `/register` → redirect to
    `/dashboard`

## Definition of done

- [ ] Submitting the login form with valid credentials logs the user in and
      redirects to `/dashboard`
- [ ] Dashboard page displays the logged-in user's name
- [ ] Submitting with wrong email or password shows "Invalid email or password"
- [ ] Email field is preserved when the login form re-renders with an error
- [ ] Password field is always cleared on re-render
- [ ] Visiting `/dashboard` without logging in redirects to `/login` with a
      flash message
- [ ] Clicking logout clears the session and redirects to the landing page
- [ ] Navbar shows "Sign in / Get started" when logged out
- [ ] Navbar shows "Dashboard / Logout" when logged in
- [ ] A logged-in user visiting `/login` or `/register` is redirected to
      `/dashboard`
- [ ] The app starts without errors
