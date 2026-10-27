# Spec: Backend Route For Profile Page

## Overview

Wire the `/profile` route to real database queries so the profile page displays the logged-in user's actual data instead of hardcoded values. Step 4 established the full UI layout (user info card, summary stats, transaction history table, category breakdown) with static data. This step keeps the same template contract — same variable names, same structure — but builds each dict/list from live queries against the `users` and `expenses` tables using the session user's ID. After this step the profile page is fully functional for any registered user.

## Depends on

- **Step 1 — Database Setup** (`users` and `expenses` tables, `get_db()` helper)
- **Step 2 — Registration** (users can create accounts)
- **Step 3 — Login & Logout** (session contains `user_id`, `login_required` decorator exists)
- **Step 4 — Profile Page** (hardcoded UI) — `templates/profile.html` must exist and expect the `user`, `stats`, `transactions`, and `categories` context variables

## Routes

- `GET /profile` — render the profile page with real data — **logged-in** (already exists, implementation changes only)

No new routes.

## Database changes

No database changes. The existing `users` and `expenses` tables contain all required columns.

## Templates

No template changes. `templates/profile.html` already renders the four context variables (`user`, `stats`, `transactions`, `categories`) created in Step 4. This step only changes the Python side.

## Files to change

- `app.py` — replace the hardcoded dicts in the `profile()` view function with database queries:
  1. **User info** — query `users` table for the logged-in user's `name`, `email`, and `created_at`; derive `initials` (first letter of each word in the name, uppercased) and format `member_since` as a human-readable month + year string (e.g. "January 2025")
  2. **Summary stats** — query `expenses` for the logged-in user:
     - `total_spent`: `SUM(amount)`, formatted as `₹{value:.2f}` (default `₹0.00`)
     - `transaction_count`: `COUNT(*)` (default `0`)
     - `top_category`: the category with the highest total amount (default `—`)
  3. **Transactions** — query all expenses for the logged-in user ordered by `date DESC`; each row needs `date`, `description`, `category`, and `amount` formatted as `₹{value:.2f}`
  4. **Categories** — query expenses grouped by `category` with `SUM(amount)` per group, ordered by total descending; compute each category's `percent` as a rounded integer of its share of the overall total; format `total` as `₹{value:.2f}`

## Files to create

None.

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()`
- Parameterised queries only — never string-format SQL
- Passwords hashed with werkzeug (no changes to auth in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Authentication guard: the existing `@login_required` decorator stays; use `session["user_id"]` to scope every query to the logged-in user
- Keep the exact same context variable names and structure that `profile.html` expects from Step 4 (`user`, `stats`, `transactions`, `categories`) so the template works without changes
- Format all currency values with the rupee sign and two decimal places: `₹{value:.2f}`
- Handle the empty-state gracefully: a user with zero expenses should see `₹0.00` for total, `0` for count, `—` for top category, an empty transaction table, and an empty category list — no errors
- Close the database connection after use
- Derive initials from the user's name dynamically (e.g. "Nitish Kumar" → "NK", "Alice" → "A")
- Format `member_since` from the `created_at` timestamp (e.g. "2025-01-15 12:00:00" → "January 2025")

## Definition of done

- [ ] Visiting `/profile` while logged in returns HTTP 200 with the logged-in user's real name and email
- [ ] The user info card shows correct initials derived from the user's name
- [ ] The member-since date reflects the user's actual `created_at` value
- [ ] Summary stats show the correct total spent, transaction count, and top category computed from the user's expenses
- [ ] A user with zero expenses sees `₹0.00` total, `0` transactions, `—` top category, and empty lists — no errors
- [ ] The transaction history table lists the user's actual expenses, newest first
- [ ] The category breakdown shows real per-category totals and correct percentage values
- [ ] Percentages in the category breakdown add up to approximately 100 (within rounding)
- [ ] Each user sees only their own data — not other users' expenses
- [ ] No hardcoded data remains in the `profile()` view function
- [ ] The template renders identically to Step 4's layout (no template changes needed)
- [ ] The app starts without errors
