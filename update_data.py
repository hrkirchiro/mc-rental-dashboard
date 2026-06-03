"""
Montgomery County Rental Dashboard — Auto-Update Script
Runs quarterly via GitHub Actions.
Fetches Zillow Research CSVs, filters for Montgomery County MD ZIP codes,
and writes the results to data.json in the same repository.
"""

import json
import csv
import requests
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

# ── Zillow CSV filenames per bedroom type ─────────────────────────────────────
ZILLOW_FILES = {
    "studio": "MedianAskingRent_Studio_MedianAskingRent.csv",
    "1br":    "MedianAskingRent_OneBedroomMedianAskingRent.csv",
    "2br":    "MedianAskingRent_TwoBedroomMedianAskingRent.csv",
    "3br":    "MedianAskingRent_ThreeBedroomMedianAskingRent.csv",
}
ZILLOW_BASE = "https://files.zillowstatic.com/research/public_csvs/medianAskingRent"


def fetch_zillow(bd_key):
    url = f"{ZILLOW_BASE}/{ZILLOW_FILES[bd_key]}"
    print(f"  Fetching {url}")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return list(csv.DictReader(StringIO(r.text)))


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


def main():
    print("── Montgomery County Rental Dashboard: Data Update ──\n")

    all_data = {}   # { neighborhood: { studio, 1br, 2br, 3br, lat, lng } }
    latest_date = ""

    for bd_key in ["studio", "1br", "2br", "3br"]:
        print(f"Fetching {bd_key}...")
        try:
            raw = fetch_zillow(bd_key)
            nbhd_vals, latest_date = extract(raw)
            for nbhd, vals in nbhd_vals.items():
                all_data.setdefault(nbhd, {})[bd_key] = avg(vals)
            print(f"  {len(nbhd_vals)} neighborhoods found.\n")
        except Exception as e:
            print(f"  Warning: could not fetch {bd_key} — {e}\n")

    # Build output list, sorted by neighborhood name
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

    print(f"data.json written — {len(neighborhoods)} neighborhoods.")


if __name__ == "__main__":
    main()
