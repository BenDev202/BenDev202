#!/usr/bin/env python3
"""
fetch_contributions.py — Scrape real GitHub contribution data.

Fetches the contribution calendar from GitHub's public profile page
(no API token required) and extracts per-day counts by joining
<td> cells to their corresponding <tool-tip> elements.

Usage:
    python scripts/fetch_contributions.py <username>

Output:
    data/contributions.json

The script also cross-checks the computed total against the
"N contributions in the last year" heading GitHub shows on the page.
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup


def fetch_contributions_html(username: str) -> str:
    """Fetch the contributions page HTML."""
    url = f"https://github.com/users/{username}/contributions"
    headers = {
        "User-Agent": f"github-profile-readme-bot/{username}",
    }
    print(f"Fetching {url}...")
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_contributions(html: str) -> dict:
    """
    Parse contribution data from the HTML.

    GitHub's current markup (mid-2026):
    - Each day: <td class="ContributionCalendar-day" data-date="YYYY-MM-DD"
                    data-level="0-4" id="contribution-day-component-X-Y">
    - Counts are in: <tool-tip for="contribution-day-component-X-Y">
                      N contributions on Month Day.</tool-tip>
      (or "No contributions on Month Day.")

    We build a for→tooltip lookup and join by ID.
    """
    soup = BeautifulSoup(html, "html.parser")

    # ── Extract the "N contributions in the last year" heading ──
    page_total = None
    heading = soup.find("h2", class_="f4")
    if heading:
        text = heading.get_text(strip=True)
        m = re.match(r"([\d,]+)\s+contributions?", text)
        if m:
            page_total = int(m.group(1).replace(",", ""))

    # ── Build tooltip lookup: id → text ──
    tooltip_map = {}
    for tip in soup.find_all("tool-tip"):
        for_id = tip.get("for", "")
        if for_id:
            tooltip_map[for_id] = tip.get_text(strip=True)

    # ── Extract calendar cells ──
    days = []
    for td in soup.find_all("td", class_="ContributionCalendar-day"):
        date_str = td.get("data-date")
        level_str = td.get("data-level", "0")
        cell_id = td.get("id", "")


        if not date_str:
            continue

        # Try to get count from tooltip
        count = 0
        tip_text = tooltip_map.get(cell_id, "")
        if tip_text:
            # "5 contributions on July 15." or "No contributions on July 15."
            first_word = tip_text.split()[0] if tip_text.split() else ""
            if first_word.isdigit():
                count = int(first_word)

        days.append({
            "date": date_str,
            "count": count,
            "level": int(level_str),
        })

    # Sort by date
    days.sort(key=lambda d: d["date"])

    return {
        "days": days,
        "page_total": page_total,
    }


def compute_stats(days: list[dict]) -> dict:
    """Compute derived statistics from the day list."""
    if not days:
        return {
            "total_last_year": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "best_day": {"date": None, "count": 0},
            "monthly_totals": {},
        }

    total = sum(d["count"] for d in days)

    # Best day
    best = max(days, key=lambda d: d["count"])

    # Monthly totals
    monthly = {}
    for d in days:
        month_key = d["date"][:7]  # "YYYY-MM"
        monthly[month_key] = monthly.get(month_key, 0) + d["count"]

    # Streaks — work backwards from the most recent day
    sorted_days = sorted(days, key=lambda d: d["date"], reverse=True)

    # Current streak: consecutive non-zero ending at most recent day
    current_streak = 0
    for d in sorted_days:
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    # Longest streak: anywhere in the window
    longest_streak = 0
    streak = 0
    for d in sorted(days, key=lambda d: d["date"]):
        if d["count"] > 0:
            streak += 1
            longest_streak = max(longest_streak, streak)
        else:
            streak = 0

    return {
        "total_last_year": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly_totals": monthly,
    }


def main():

    if len(sys.argv) < 2:
        print("Usage: python scripts/fetch_contributions.py <username>")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python scripts/fetch_contributions.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    html = fetch_contributions_html(username)

    print("Parsing contribution data...")
    parsed = parse_contributions(html)
    days = parsed["days"]
    page_total = parsed["page_total"]

    print(f"Found {len(days)} days of contribution data")

    stats = compute_stats(days)

    # Cross-check total
    if page_total is not None:
        if stats["total_last_year"] == page_total:
            print(f"✓ Total matches page heading: {page_total:,}")
        else:
            print(
                f"⚠ Total mismatch! Computed: {stats['total_last_year']:,}, "
                f"Page shows: {page_total:,}"
            )
            print("  (This may indicate the scraper's HTML assumptions are wrong.)")
    else:
        print("⚠ Could not find page total heading for cross-check")

    # Build output
    output = {
        "username": username,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "days": days,
        **stats,
    }

    os.makedirs("data", exist_ok=True)
    out_path = "data/contributions.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Done → {out_path}")
    print(f"  Total: {stats['total_last_year']:,}")
    print(f"  Current streak: {stats['current_streak']} days")
    print(f"  Longest streak: {stats['longest_streak']} days")
    print(f"  Best day: {stats['best_day']['date']} ({stats['best_day']['count']})")


if __name__ == "__main__":
    main()

