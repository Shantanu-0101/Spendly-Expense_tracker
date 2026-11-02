import re
from datetime import date, timedelta

import pytest


def html_of(response):
    return response.data.decode("utf-8")


def active_presets(html):
    return re.findall(r'filter-preset--active">([^<]+)<', html)


def stat_values(html):
    return re.findall(r'<span class="profile-stat-value">([^<]*)</span>', html)


def row_count(html):
    return html.count('<td class="text-right tabular-nums">')


@pytest.fixture
def user(make_user, login):
    user_id = make_user(name="Asha Rao", email="asha@example.com")
    login(user_id, "Asha Rao")
    return user_id


# ------------------------------------------------------------------ #
# Access                                                              #
# ------------------------------------------------------------------ #

def test_profile_requires_login(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


# ------------------------------------------------------------------ #
# Default range                                                       #
# ------------------------------------------------------------------ #

def test_default_shows_current_month_only(client, user, add_expense):
    today = date.today()
    add_expense(user, 50.00, "Food", today.isoformat(), "This month lunch")
    add_expense(user, 999.00, "Bills", "2020-01-15", "Old bill")

    html = html_of(client.get("/profile"))

    assert "This month lunch" in html
    assert "Old bill" not in html
    assert stat_values(html) == ["₹50.00", "1", "Food"]
    assert active_presets(html) == ["This month"]


def test_default_label_shows_current_month_range(client, user):
    today = date.today()
    html = html_of(client.get("/profile"))
    assert f"Showing {today.strftime('%b')} 1, {today.year}" in html


# ------------------------------------------------------------------ #
# Custom range                                                        #
# ------------------------------------------------------------------ #

def test_custom_range_scopes_stats_transactions_and_categories(client, user, add_expense):
    add_expense(user, 40.00, "Food", "2025-03-05", "Inside A")
    add_expense(user, 60.00, "Transport", "2025-03-20", "Inside B")
    add_expense(user, 500.00, "Bills", "2025-04-02", "Outside")

    html = html_of(client.get("/profile?from=2025-03-01&to=2025-03-31"))

    assert "Inside A" in html and "Inside B" in html
    assert "Outside" not in html
    assert stat_values(html) == ["₹100.00", "2", "Transport"]
    assert row_count(html) == 2
    assert 'style="width: 60%"' in html
    assert 'style="width: 40%"' in html
    assert "badge-bills" not in html
    assert active_presets(html) == ["Custom"]
    assert "Showing Mar 1, 2025 – Mar 31, 2025" in html


def test_range_boundaries_are_inclusive(client, user, add_expense):
    add_expense(user, 10.00, "Food", "2025-06-01", "First day")
    add_expense(user, 20.00, "Food", "2025-06-30", "Last day")

    html = html_of(client.get("/profile?from=2025-06-01&to=2025-06-30"))

    assert "First day" in html and "Last day" in html
    assert stat_values(html)[0] == "₹30.00"


def test_from_after_to_is_swapped(client, user, add_expense):
    add_expense(user, 25.00, "Health", "2025-05-10", "Pharmacy")

    swapped = html_of(client.get("/profile?from=2025-05-31&to=2025-05-01"))
    normal = html_of(client.get("/profile?from=2025-05-01&to=2025-05-31"))

    assert "Pharmacy" in swapped
    assert stat_values(swapped) == stat_values(normal)
    assert 'name="from" value="2025-05-01"' in swapped
    assert 'name="to" value="2025-05-31"' in swapped


def test_custom_range_inputs_are_prefilled(client, user):
    html = html_of(client.get("/profile?from=2025-02-01&to=2025-02-28"))
    assert 'name="from" value="2025-02-01"' in html
    assert 'name="to" value="2025-02-28"' in html


# ------------------------------------------------------------------ #
# Presets                                                             #
# ------------------------------------------------------------------ #

def test_all_time_shows_every_expense(client, user, add_expense):
    add_expense(user, 10.00, "Food", "2019-01-01", "Ancient")
    add_expense(user, 20.00, "Food", date.today().isoformat(), "Recent")

    html = html_of(client.get("/profile?range=all"))

    assert "Ancient" in html and "Recent" in html
    assert stat_values(html) == ["₹30.00", "2", "Food"]
    assert active_presets(html) == ["All time"]
    assert "Showing all time" in html


def test_last_month_preset_is_highlighted_and_scoped(client, user, add_expense):
    first_of_month = date.today().replace(day=1)
    last_month_end = first_of_month - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    add_expense(user, 70.00, "Shopping", last_month_start.isoformat(), "Last month buy")
    add_expense(user, 5.00, "Food", first_of_month.isoformat(), "This month snack")

    html = html_of(client.get(
        f"/profile?from={last_month_start.isoformat()}&to={last_month_end.isoformat()}"
    ))

    assert "Last month buy" in html
    assert "This month snack" not in html
    assert active_presets(html) == ["Last month"]


def test_last_three_months_preset_covers_90_days(client, user, add_expense):
    today = date.today()
    add_expense(user, 15.00, "Food", (today - timedelta(days=89)).isoformat(), "Within 90")
    add_expense(user, 15.00, "Food", (today - timedelta(days=120)).isoformat(), "Beyond 90")

    start = (today - timedelta(days=90)).isoformat()
    html = html_of(client.get(f"/profile?from={start}&to={today.isoformat()}"))

    assert "Within 90" in html
    assert "Beyond 90" not in html
    assert active_presets(html) == ["Last 3 months"]


def test_preset_links_are_rendered(client, user):
    today = date.today()
    first_of_month = today.replace(day=1)
    html = html_of(client.get("/profile"))

    for label in ["This month", "Last month", "Last 3 months", "All time"]:
        assert f">{label}</a>" in html
    assert f"/profile?from={first_of_month.isoformat()}&amp;to={today.isoformat()}" in html
    assert "/profile?range=all" in html


def test_filter_form_uses_get(client, user):
    html = html_of(client.get("/profile"))
    assert re.search(r'<form class="filter-custom"[^>]*method="get"', html)
    assert 'type="date" name="from"' in html
    assert 'type="date" name="to"' in html


# ------------------------------------------------------------------ #
# Invalid input                                                       #
# ------------------------------------------------------------------ #

@pytest.mark.parametrize("query", [
    "from=garbage&to=nonsense",
    "from=2025-13-45&to=2025-02-30",
    "from=&to=",
    "from=2025/01/01&to=2025/01/31",
    "from=2025-01-01'%20OR%201=1--&to=2025-01-31",
    "range=everything",
])
def test_invalid_params_fall_back_to_current_month(client, user, add_expense, query):
    add_expense(user, 999.00, "Bills", "2020-01-15", "Old bill")

    response = client.get(f"/profile?{query}")
    html = html_of(response)

    assert response.status_code == 200
    assert "Old bill" not in html
    assert "Traceback" not in html


def test_only_from_given_defaults_to_today(client, user, add_expense):
    add_expense(user, 12.00, "Food", date.today().isoformat(), "Today item")
    html = html_of(client.get("/profile?from=2020-01-01"))
    assert "Today item" in html
    assert f'name="to" value="{date.today().isoformat()}"' in html


# ------------------------------------------------------------------ #
# Empty state and isolation                                           #
# ------------------------------------------------------------------ #

def test_empty_range_shows_zero_state(client, user, add_expense):
    add_expense(user, 50.00, "Food", "2025-01-10")

    response = client.get("/profile?from=2024-01-01&to=2024-01-31")
    html = html_of(response)

    assert response.status_code == 200
    assert stat_values(html) == ["₹0.00", "0", "—"]
    assert row_count(html) == 0
    assert "profile-cat-row" not in html


def test_other_users_expenses_are_never_shown(client, user, make_user, add_expense):
    other = make_user(name="Other Person", email="other@example.com")
    add_expense(other, 777.00, "Bills", "2025-03-10", "Not mine")
    add_expense(user, 10.00, "Food", "2025-03-10", "Mine")

    html = html_of(client.get("/profile?range=all"))

    assert "Mine" in html
    assert "Not mine" not in html
    assert stat_values(html) == ["₹10.00", "1", "Food"]


def test_user_info_is_unaffected_by_filter(client, user, add_expense):
    add_expense(user, 10.00, "Food", "2025-03-10")

    for query in ["", "?range=all", "?from=2000-01-01&to=2000-01-31"]:
        html = html_of(client.get(f"/profile{query}"))
        assert "Asha Rao" in html
        assert "asha@example.com" in html
        assert ">AR<" in html
        assert "Member since" in html
