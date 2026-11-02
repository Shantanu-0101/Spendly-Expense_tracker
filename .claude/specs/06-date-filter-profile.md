# Spec: Date Filter for Profile Page

## Overview

Add a date-range filter to the profile page so the user can narrow the
transactions table, summary stats, and category breakdown to a specific
time window.  The filter sits above the stats row as a small form with
start / end date inputs and a handful of quick-pick buttons ("This month",
"Last month", "Last 3 months", "All time").  Selecting a range reloads
the page with `?from=YYYY-MM-DD&to=YYYY-MM-DD` query parameters; the
back-end uses those to scope every expense query to that window.  With no
parameters, the page defaults to the current calendar month.  User info
(name, email, initials, member since) is never affected by the filter.

## Depends on

- **Step 1 — Database Setup** (`users` and `expenses` tables, `get_db()`)
- **Step 2 — Registration** (users can create accounts)
- **Step 3 — Login & Logout** (session, `login_required`)
- **Step 5 — Backend Profile Route** (profile page wired to real database
  queries; this step modifies those queries to accept a date window)

## Routes

- `GET /profile` — already exists; add support for optional query
  parameters `from` (start date, inclusive) and `to` (end date, inclusive).
  Both values are date strings in `YYYY-MM-DD` format.  Behaviour:
  - **Both present and valid** → scope expenses to
    `WHERE date >= ? AND date <= ?`
  - **Missing or invalid** → default to the current calendar month
    (first day of this month through today)

No new routes.

## Database changes

No database changes.  Existing `expenses.date` column (TEXT in
`YYYY-MM-DD` format) already supports range comparisons via plain
string inequality.

## Templates

- **Modify:** `templates/profile.html`
  - Insert a date-filter bar between the profile header and the stats
    row.  The bar contains:
    1. Quick-pick buttons: "This month" (default), "Last month",
       "Last 3 months", "All time" — each is a link that sets the
       correct `from`/`to` query parameters.
    2. Two `<input type="date">` fields labelled "From" and "To",
       plus a "Filter" submit button for a custom range.
  - The active quick-pick button (or "Custom" if a manual range is
    entered) is visually highlighted.
  - Display a human-readable label of the active range below the
    filter bar, e.g. "Showing Nov 1 – Nov 2, 2026".

## Files to change

- `app.py` — update the `profile()` view function:
  1. Parse `request.args.get("from")` and `request.args.get("to")`
  2. Validate with `datetime.strptime`; on failure fall back to
     this-month default
  3. Pass `date_from` and `date_to` strings into every expense
     query's `WHERE` clause
  4. Send `date_from`, `date_to`, and the active preset name to the
     template context
- `templates/profile.html` — add the filter bar (described above)
- `static/css/style.css` — add styles for the filter bar, quick-pick
  buttons, date inputs, and the active-state highlight

## Files to create

None.

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()`
- Parameterised queries only — never string-format user input into SQL
- Passwords hashed with werkzeug (no auth changes in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Validate both `from` and `to` with `datetime.strptime(value, "%Y-%m-%d")`
  inside a try/except; on any failure, silently fall back to the current-month
  default — never show a Python traceback
- Ensure `from` ≤ `to`; if the user sends `from` > `to`, swap them
- The "All time" preset omits the date filter entirely (no WHERE clause
  on date), so the user sees every expense they have ever entered
- Keep the same context variable names and structure that
  `profile.html` already expects (`user`, `stats`, `transactions`,
  `categories`) — only add new variables for the filter state
- Format the human-readable date range using Python's `strftime` with
  `%b %-d, %Y` (e.g. "Nov 1, 2026"); on Windows use `%#d` instead of
  `%-d` to strip the leading zero
- The filter form uses GET (a plain link / form with method GET), not POST
- Quick-pick buttons are `<a>` links, not JavaScript — the page works
  without JS
- The filter bar must be responsive: quick-pick buttons wrap on narrow
  screens; date inputs stack vertically on mobile

## Definition of done

- [ ] `/profile` with no query parameters shows the current month's data
- [ ] `/profile?from=2026-11-01&to=2026-11-30` scopes stats, transactions,
      and categories to November 2026
- [ ] Clicking "This month" highlights that button and shows this month's
      data
- [ ] Clicking "Last month" shows the previous month's data
- [ ] Clicking "Last 3 months" shows the last 90 days of data
- [ ] Clicking "All time" removes the date filter — every expense appears
- [ ] Entering a custom date range in the inputs and clicking "Filter"
      reloads the page with the correct query parameters
- [ ] Invalid or missing query parameters fall back to the current-month
      default — no errors or tracebacks
- [ ] `from` > `to` is silently swapped so the query still works
- [ ] Summary stats (total spent, transaction count, top category) update
      to reflect the selected date range
- [ ] Category breakdown percentages update to reflect the selected range
- [ ] User info card (name, email, initials, member since) is unaffected
      by the filter
- [ ] The filter bar is responsive and usable on mobile
- [ ] The app starts without errors
