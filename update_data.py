"""
Montgomery County Rental Dashboard — Auto-Update Script
Runs monthly via GitHub Actions.

Data sources:
  - Zillow ZORI ZIP-level CSV (seasonally adjusted) — monthly rent totals by ZIP
  - HUD FY2026 bedroom ratios for Washington DC metro — studio/1BR/2BR/3BR breakdown

Update schedule:
  - Script runs automatically on the 1st of every month
  - HUD bedroom ratios (4 numbers) should be updated once per year each October
    when HUD releases new Fair Market Rents at huduser.gov/portal/datasets/fmr.html
"""

import csv
import json
import os
import sys
import requests
from io import StringIO

# ── Zillow ZORI ZIP-level file (seasonally adjusted) ─────────────────────────
ZILLOW_URL = (
    "https://files.zillowstatic.com/research/public_csvs/zori/"
    "Zip_zori_uc_sfrcondomfr_sm_sa_month.csv"
)

ZILLOW_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.zillow.com/research/data/",
}

# ── HUD FY2026 bedroom ratios — Washington DC metro (DC-VA-MD-WV MSA) ────────
# These are the official HUD bedroom size ratios relative to 2-bedroom rent.
# Update these once per year each October when HUD releases new FMRs at:
# https://www.huduser.gov/portal/datasets/fmr.html
HUD_RATIOS = {
    "studio": 0.74,   # studio  = 74% of 2BR rent
    "1br":    0.88,   # 1BR     = 88% of 2BR rent
    "2br":    1.00,   # 2BR     = base (100%)
    "3br":    1.28,   # 3BR     = 128% of 2BR rent
}
HUD_RATIO_YEAR = "FY2026"

# ── Montgomery County MD ZIP → Neighborhood ───────────────────────────────────
ZIP_TO_NEIGHBORHOOD = {
    "20814": "Bethesda",
    "20815": "Chevy Chase",
    "20816": "Bethesda",
    "20817": "Potomac",
    "20850": "Rockville",
    "20851": "Rockville",
    "20852": "North Bethesda",
    "20853": "Rockville",
    "20854": "Potomac",
    "20855": "Germantown",
    "20866": "Burtonsville",
    "20871": "Germantown",
    "20874": "Germantown",
    "20876": "Germantown",
    "20877": "Gaithersburg",
    "20878": "Gaithersburg",
    "20879": "Gaithersburg",
    "20886": "Montgomery Village",
    "20895": "Kensington",
    "20901": "Silver Spring",
    "20902": "Silver Spring",
    "20903": "Silver Spring",
    "20904": "Silver Spring",
    "20905": "Silver Spring",
    "20906": "Silver Spring",
    "20910": "Silver Spring",
    "20912": "Takoma Park",
    "20832": "Olney",
}

# ── Lat/Lng for map display ───────────────────────────────────────────────────
COORDS = {
    "Bethesda":           [38.9847, -77.0947],
    "Chevy Chase":        [38.9651, -77.0769],
    "Potomac":            [39.0176, -77.2085],
    "North Bethesda":     [39.0437, -77.1168],
    "Silver Spring":      [38.9954, -77.0311],
    "Rockville":          [39.0840, -77.1528],
    "Kensington":         [39.0209, -77.0766],
    "Gaithersburg":       [39.1434, -77.2014],
    "Germantown":         [39.1732, -77.2717],
    "Montgomery Village": [39.1618, -77.2000],
    "Burtonsville":       [39.1079, -76.9316],
    "Olney":              [39.1537, -77.0658],
    "Takoma Park":        [39.0120, -77.0072],
}

MIN_NEIGHBORHOODS = 5  # safety check — bail if fewer than this found


def fetch_zillow():
    """Download the ZORI ZIP-level CSV from Zillow."""
    print(f"Downloading Zillow ZORI data...")
    print(f"  URL: {ZILLOW_URL}")
    r = requests.get(ZILLOW_URL, headers=ZILLOW_HEADERS, timeout=60)
    r.raise_for_status()
    print(f"  Downloaded {len(r.content) // 1024} KB")
    return list(csv.DictReader(StringIO(r.text)))


def get_latest_date_col(rows):
    """Find the most recent date column that has actual data."""
    date_cols = sorted(k for k in rows[0] if k[:4].isdigit())
    for col in reversed(date_cols):
        if any(r.get(col, "").strip() for r in rows[:200]):
            return col
    return date_cols[-1] if date_cols else None


def extract_mc_data(rows, date_col):
    """Filter to Montgomery County MD ZIPs and return {neighborhood: [values]}."""
    result = {}
    for row in rows:
        z = str(row.get("RegionName", "")).zfill(5)
        state  = row.get("State", "")
        county = row.get("CountyName", "")
        if state != "MD" or "Montgomery" not in county:
            continue
        if z not in ZIP_TO_NEIGHBORHOOD:
            continue
        v = row.get(date_col, "").strip()
        if not v:
            continue
        try:
            nbhd = ZIP_TO_NEIGHBORHOOD[z]
            result.setdefault(nbhd, []).append(float(v))
        except ValueError:
            continue
    return result


def load_existing():
    """Load current data.json as fallback if fetch fails."""
    if os.path.exists("data.json"):
        try:
            with open("data.json") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def main():
    print("── Montgomery County Rental Dashboard: Monthly Data Update ──")
    print(f"   Using HUD {HUD_RATIO_YEAR} bedroom ratios for DC metro\n")

    existing = load_existing()

    # ── Fetch ─────────────────────────────────────────────────────────────────
    try:
        rows = fetch_zillow()
    except Exception as e:
        print(f"\nFETCH FAILED: {e}")
        if existing:
            print("Keeping existing data.json untouched — website unchanged.")
        sys.exit(1)

    if not rows:
        print("ERROR: No rows returned from Zillow.")
        sys.exit(1)

    # ── Find latest date ───────────────────────────────────────────────────────
    date_col = get_latest_date_col(rows)
    if not date_col:
        print("ERROR: No date columns found.")
        sys.exit(1)
    print(f"Most recent data: {date_col[:7]}\n")

    # ── Extract Montgomery County ──────────────────────────────────────────────
    nbhd_vals = extract_mc_data(rows, date_col)
    print(f"Neighborhoods found: {len(nbhd_vals)}")

    # ── Safety check ──────────────────────────────────────────────────────────
    if len(nbhd_vals) < MIN_NEIGHBORHOODS:
        print(f"\nSAFETY CHECK FAILED: only {len(nbhd_vals)} neighborhoods found.")
        if existing:
            print("Keeping existing data.json untouched.")
        sys.exit(1)

    # ── Build output with HUD bedroom ratios ──────────────────────────────────
    neighborhoods = []
    for name in sorted(nbhd_vals):
        base_2br = round(sum(nbhd_vals[name]) / len(nbhd_vals[name]))
        entry = {
            "name":   name,
            "studio": round(base_2br * HUD_RATIOS["studio"]),
            "1br":    round(base_2br * HUD_RATIOS["1br"]),
            "2br":    base_2br,
            "3br":    round(base_2br * HUD_RATIOS["3br"]),
        }
        if name in COORDS:
            entry["lat"], entry["lng"] = COORDS[name]
        neighborhoods.append(entry)
        print(f"  {name}: studio=${entry['studio']:,}  "
              f"1BR=${entry['1br']:,}  2BR=${entry['2br']:,}  3BR=${entry['3br']:,}")

    output = {
        "last_updated":  date_col[:7],
        "hud_ratio_year": HUD_RATIO_YEAR,
        "source": (
            "Zillow ZORI ZIP-level seasonally adjusted + "
            f"HUD {HUD_RATIO_YEAR} bedroom ratios (DC metro)"
        ),
        "neighborhoods": neighborhoods,
    }

    with open("data.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\ndata.json written — {len(neighborhoods)} neighborhoods "
          f"as of {date_col[:7]}.")


if __name__ == "__main__":
    main()
