"""
Montgomery County Rental Dashboard — Auto-Update Script
Runs quarterly via GitHub Actions.
Fetches Zillow Research CSVs, filters for Montgomery County MD ZIP codes,
and writes the results to data.json only if valid data was found.
If the fetch fails or returns no results, the existing data.json is kept untouched.
"""

import json
import csv
import requests
import os
import sys
from io import StringIO
from datetime import date

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
    "20860": "Sandy Spring",
    "20861": "Burtonsville",
    "20862": "Burtonsville",
    "20866": "Burtonsville",
    "20868": "Burtonsville",
    "20871": "Germantown",
    "20872": "Damascus",
    "20874": "Germantown",
    "20876": "Germantown",
    "20877": "Gaithersburg",
    "20878": "Gaithersburg",
    "20879": "Gaithersburg",
    "20880": "Montgomery Village",
    "20882": "Damascus",
    "20886": "Montgomery Village",
    "20895": "Kensington",
    "20896": "Garrett Park",
    "20899": "Gaithersburg",
    "20901": "Silver Spring",
    "20902": "Silver Spring",
    "20903": "Silver Spring",
    "20904": "Silver Spring",
    "20905": "Silver Spring",
    "20906": "Silver Spring",
    "20910": "Silver Spring",
    "20912": "Takoma Park",
    "20837": "Poolesville",
    "20832": "Olney",
    "20833": "Brookeville",
    "20838": "Barnesville",
    "20841": "Boyds",
    "20842": "Dickerson",
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
    "Damascus":           [39.2751, -77.0416],
    "Olney":              [39.1537, -77.0658],
    "Takoma Park":        [38.9812, -77.0072],
    "Burtonsville":       [39.1079, -76.9316],
    "Poolesville":        [39.1454, -77.4160],
    "Sandy Spring":       [39.1440, -77.0058],
    "Garrett Park":       [39.0298, -77.0908],
    "Brookeville":        [39.1776, -77.0577],
}

# ── Zillow CSV filenames — tries multiple known naming patterns ───────────────
ZILLOW_CANDIDATES = {
    "studio": [
        "MedianAskingRent_Studio_MedianAskingRent.csv",
        "MedianAskingRent_Studio.csv",
    ],
    "1br": [
        "MedianAskingRent_OneBedroomMedianAskingRent.csv",
        "MedianAskingRent_1Bedroom.csv",
        "MedianAskingRent_OneBedroom.csv",
    ],
    "2br": [
        "MedianAskingRent_TwoBedroomMedianAskingRent.csv",
        "MedianAskingRent_2Bedroom.csv",
        "MedianAskingRent_TwoBedroom.csv",
    ],
    "3br": [
        "MedianAskingRent_ThreeBedroomMedianAskingRent.csv",
        "MedianAskingRent_3Bedroom.csv",
        "MedianAskingRent_ThreeBedroom.csv",
    ],
}
ZILLOW_BASE = "https://files.zillowstatic.com/research/public_csvs/medianAskingRent"
MIN_NEIGHBORHOODS = 5  # safety threshold — must find at least this many or we bail


def fetch_zillow(bd_key):
    """Try each known filename until one works. Returns parsed CSV rows."""
    for filename in ZILLOW_CANDIDATES[bd_key]:
        url = f"{ZILLOW_BASE}/{filename}"
        print(f"  Trying {url} ...")
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200 and len(r.text) > 100:
                print(f"  Found: {filename}")
                return list(csv.DictReader(StringIO(r.text)))
        except requests.RequestException as e:
            print(f"  Request error: {e}")
    print(f"  WARNING: could not fetch any file for {bd_key}")
    return []


def extract(rows):
    """Return {neighborhood: [values]} and the latest date column label."""
    if not rows:
        return {}, ""
    date_cols = sorted(k for k in rows[0] if k[:4].isdigit())
    if not date_cols:
        return {}, ""
    latest = date_cols[-1]
    print(f"  Latest date column: {latest}")
    result = {}
    for row in rows:
        z = str(row.get("RegionName", "")).zfill(5)
        if row.get("StateName") != "MD" or z not in ZIP_TO_NEIGHBORHOOD:
            continue
        nbhd = ZIP_TO_NEIGHBORHOOD[z]
        try:
            val = float(row[latest])
            result.setdefault(nbhd, []).append(val)
        except (ValueError, KeyError):
            continue
    return result, latest


def avg(vals):
    return round(sum(vals) / len(vals)) if vals else None


def load_existing():
    """Load the current data.json so we can fall back to it if needed."""
    if os.path.exists("data.json"):
        try:
            with open("data.json") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def main():
    print("── Montgomery County Rental Dashboard: Data Update ──\n")

    existing = load_existing()
    all_data = {}
    latest_date = ""
    fetch_errors = 0

    for bd_key in ["studio", "1br", "2br", "3br"]:
        print(f"Fetching {bd_key}...")
        raw = fetch_zillow(bd_key)
        if not raw:
            fetch_errors += 1
            print(f"  Skipping {bd_key} — no data returned.\n")
            continue
        nbhd_vals, latest_date = extract(raw)
        for nbhd, vals in nbhd_vals.items():
            all_data.setdefault(nbhd, {})[bd_key] = avg(vals)
        print(f"  {len(nbhd_vals)} neighborhoods found.\n")

    total_neighborhoods = len(all_data)
    print(f"Total neighborhoods found: {total_neighborhoods}")

    # ── Safety check — only write if we got meaningful data ──────────────────
    if total_neighborhoods < MIN_NEIGHBORHOODS:
        print(f"\nSAFETY CHECK FAILED: only found {total_neighborhoods} neighborhoods "
              f"(minimum is {MIN_NEIGHBORHOODS}).")
        if existing:
            print("Keeping existing data.json untouched — no changes written.")
            print("The website will continue showing the previous data.")
        else:
            print("No existing data.json found either. Website will show an error until data is available.")
        sys.exit(1)  # exit with error so GitHub Actions marks the run as failed (visible warning)

    # ── Build and write output ────────────────────────────────────────────────
    neighborhoods = []
    for name in sorted(all_data.keys()):
        entry = {"name": name}
        entry.update(all_data[name])
        coords = COORDS.get(name)
        if coords:
            entry["lat"], entry["lng"] = coords
        neighborhoods.append(entry)

    output = {
        "last_updated": latest_date or str(date.today()),
        "source": "Zillow Research — Median Asking Rent by ZIP",
        "neighborhoods": neighborhoods,
    }

    with open("data.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\ndata.json written successfully — {len(neighborhoods)} neighborhoods.")
    if fetch_errors:
        print(f"Note: {fetch_errors} bedroom type(s) had fetch errors and were skipped.")


if __name__ == "__main__":
    main()
