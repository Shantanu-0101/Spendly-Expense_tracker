# Spec: Registration

## Overview

Add working user registration to Spendly. The register page template already
exists with a form that POSTs to `/register`. This step wires up the backend:
validate the input, hash the password, insert the user into the database, and
redirect to the login page on success. This is the first authentication step
and unblocks login (Step 3) and all logged-in features that follow.

## Depends on

- **Step 1 — Database Setup** (users table and `get_db()` helper must exist)

## Routes

- `GET /register` — render the registration form — **public** (already exists,
  no changes needed)
- `POST /register` — validate input, create user, redirect to login — **public**

## Database changes

No database changes. The `users` table already has the required columns:
`id`, `name`, `email`, `password_hash`, `created_at`.

## Templates

- **Modify:** `templates/register.html` — add `value="{{ name }}"` and
  `value="{{ email }}"` to the name and email inputs so values are preserved
  when the form re-renders with an error.
- **Modify:** `templates/base.html` — add a `{% block messages %}` area inside
  `<main>` (above `{% block content %}`) for flash messages, so success/error
  messages can be shown on any page going forward.

## Files to change

- `app.py` — add POST handler for `/register`, add `secret_key` for flash
  messages, import `request`, `redirect`, `url_for`, `flash`
- `templates/register.html` — preserve form values on error, display flash
  messages
- `templates/base.html` — add flash message block

## Files to create

None.

## New dependencies

No new dependencies. `werkzeug.security` and `flask` are already installed.

## Rules for implementation

- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()`
- Parameterised queries only — no string formatting in SQL
- Hash passwords with `werkzeug.security.generate_password_hash`
- Use CSS variables from `style.css` — never hardcode hex colour values
- All templates extend `base.html`
- Validate on the server side (do not rely on HTML5 `required` alone):
  - Name must not be blank
  - Email must contain `@`
  - Password must be at least 8 characters
- If email is already taken, show a clear error — do not expose whether the
  email exists (use a generic message like "An account with this email already
  exists")
- On success: redirect to `/login` with a flash message
  ("Account created — please sign in")
- On validation failure: re-render the form with the error and the previously
  entered name and email (never the password)
- Use `app.secret_key` (read from env var `SECRET_KEY` with a dev fallback)
  to enable Flask sessions and flash messages

## Definition of done

- [ ] Submitting the form with valid data creates a user in the database
- [ ] Password is stored as a hash, not plaintext
- [ ] After successful registration, user is redirected to `/login`
- [ ] A flash message "Account created — please sign in" appears on the login page
- [ ] Submitting with a duplicate email shows an error on the register page
- [ ] Submitting with a blank name shows a validation error
- [ ] Submitting with a password shorter than 8 characters shows a validation error
- [ ] Name and email fields are preserved when the form re-renders with an error
- [ ] Password field is always cleared on re-render
- [ ] The app starts without errors
