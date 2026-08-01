import sys
import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_contributions(username, output_dir="data"):
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "contributions.json")

    url = f"https://github.com/users/{username}/contributions"
    headers = {
        "User-Agent": "GitHub-Contribution-Graph-Scraper/2.0 (+https://github.com/BenDev202/BenDev202)"
    }

    print(f"Fetching contributions for {username} from {url}...")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching contributions: {e}", file=sys.stderr)
        # If we cannot fetch but there's an existing JSON file, we shouldn't overwrite it with empty/bad data
        if os.path.exists(output_path):
            print("Preserving existing contributions.json due to fetch failure.")
            sys.exit(0)
        else:
            print("No existing contributions file to preserve. Exiting with error.", file=sys.stderr)
            sys.exit(1)

    soup = BeautifulSoup(response.text, "html.parser")
    days = soup.find_all("td", class_="ContributionCalendar-day")
    tooltips = soup.find_all("tool-tip")

    if not days:
        print("Warning: No contribution days found in the parsed HTML.", file=sys.stderr)
        # Handle empty data gracefully
        empty_data = {
            "username": username,
            "total_last_year": 0,
            "streak_current": 0,
            "streak_longest": 0,
            "best_day": {"date": None, "count": 0},
            "monthly_totals": {},
            "days": []
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(empty_data, f, indent=2)
        print(f"Written empty fallback contributions data to {output_path}")
        return

    # Build tooltip lookup map: tool-tip 'for' ID -> tooltip text
    tooltip_map = {}
    for t in tooltips:
        for_id = t.get("for")
        if for_id:
            tooltip_map[for_id] = t.text.strip()

    # Parse each day
    parsed_days = []
    total_scraped = 0

    for day in days:
        day_id = day.get("id")
        date_str = day.get("data-date")
        level_str = day.get("data-level", "0")

        if not date_str:
            continue

        # Default fallback count
        count = 0

        # Look up exact count in tooltip
        if day_id and day_id in tooltip_map:
            tooltip_text = tooltip_map[day_id]
            # Format is usually: "N contributions on Month Day." or "No contributions on..."
            first_token = tooltip_text.split()[0]
            if first_token.lower() == "no":
                count = 0
            else:
                try:
                    count = int(first_token.replace(",", ""))
                except ValueError:
                    count = 0
        else:
            # Fallback based on level if tooltip not found
            try:
                level = int(level_str)
                count = level # Rough estimate
            except ValueError:
                count = 0

        parsed_days.append({
            "date": date_str,
            "count": count,
            "level": int(level_str) if level_str.isdigit() else 0
        })
        total_scraped += count

    # Sort days chronologically just in case GitHub markup returns them in a different order
    parsed_days.sort(key=lambda d: d["date"])

    # Calculate Streaks
    # Current streak: consecutive days with > 0 contributions ending at the most recent day in the dataset,
    # or ending yesterday/today (to allow timezone delays).
    current_streak = 0
    longest_streak = 0
    temp_streak = 0

    for day in parsed_days:
        if day["count"] > 0:
            temp_streak += 1
            if temp_streak > longest_streak:
                longest_streak = temp_streak
        else:
            temp_streak = 0

    # Determine current streak from the end
    # We trace backwards from the end of parsed_days
    if parsed_days:
        # Check from the last element
        idx = len(parsed_days) - 1
        # If today has 0, check yesterday. If both are 0, current streak is 0.
        # Let's count backwards starting from the latest day with > 0 contributions,
        # provided it's within the last 2 days.
        if parsed_days[idx]["count"] > 0:
            start_idx = idx
        elif idx > 0 and parsed_days[idx - 1]["count"] > 0:
            start_idx = idx - 1
        else:
            start_idx = -1

        if start_idx != -1:
            for k in range(start_idx, -1, -1):
                if parsed_days[k]["count"] > 0:
                    current_streak += 1
                else:
                    break

    # Best day count & date
    best_day_date = None
    best_day_count = 0
    for day in parsed_days:
        if day["count"] > best_day_count:
            best_day_count = day["count"]
            best_day_date = day["date"]

    # Monthly totals (YYYY-MM -> sum)
    monthly_totals = {}
    for day in parsed_days:
        # date is YYYY-MM-DD
        year_month = day["date"][:7] # YYYY-MM
        monthly_totals[year_month] = monthly_totals.get(year_month, 0) + day["count"]

    # Write stats
    result_data = {
        "username": username,
        "total_last_year": total_scraped,
        "streak_current": current_streak,
        "streak_longest": longest_streak,
        "best_day": {
            "date": best_day_date,
            "count": best_day_count
        },
        "monthly_totals": monthly_totals,
        "days": parsed_days
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2)

    print(f"Successfully scraped contributions.")
    print(f"Total contributions: {total_scraped}")
    print(f"Current streak: {current_streak}")
    print(f"Longest streak: {longest_streak}")
    print(f"Best day: {best_day_count} on {best_day_date}")
    print(f"Data saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/fetch_contributions.py <username>")
        sys.exit(1)

    username_arg = sys.argv[1]
    fetch_contributions(username_arg)
