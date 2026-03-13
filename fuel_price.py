"""
Yarrabilba Area — 95 Unleaded Price Tracker
Fetches 95 unleaded prices from the QLD Government Fuel Price API
and writes prices.json for the GitHub Pages dashboard.
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta

FUEL_API_TOKEN = os.environ.get("FUEL_API_TOKEN", "")
API_BASE       = "https://fppdirectapi-prod.fuelpricesqld.com.au"
FUEL_ID        = 5  # 95 Unleaded

MONITORED_STATIONS = [
    {"name": "7-Eleven Logan Village",  "site_id": 61478050, "region_id": 1},
    {"name": "BP Logan Village",        "site_id": 61401679, "region_id": 1},
    {"name": "Shell Logan Village",     "site_id": 61478007, "region_id": 1},
    {"name": "Ampol Yarrabilba",        "site_id": 61477660, "region_id": 1},
    {"name": "Ampol Yarrabilba South",  "site_id": 61478053, "region_id": 1},
    {"name": "Shell Tamborine",         "site_id": 61402264, "region_id": 1},
    {"name": "Ampol Tamborine",         "site_id": 61402467, "region_id": 1},
    {"name": "United Loganlea",         "site_id": 61401773, "region_id": 1},
    {"name": "7-Eleven Loganlea",       "site_id": 61477675, "region_id": 1},
    {"name": "BP Waterford",            "site_id": 61401714, "region_id": 1},
]

PRICE_CEILING = 300  # ignore anything above this


def get_prices(region_id=1):
    headers = {
        "Authorization": f"FPDAPI SubscriberToken={FUEL_API_TOKEN}",
        "Content-Type":  "application/json",
    }
    url  = f"{API_BASE}/Price/GetSitesPrices?countryId=21&geoRegionLevel=3&geoRegionId={region_id}"
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json().get("SitePrices", [])


def find_price(prices, site_id):
    for entry in prices:
        if entry.get("SiteId") == site_id and entry.get("FuelId") == FUEL_ID:
            price = round(entry["Price"] / 10.0, 1)
            if price <= PRICE_CEILING:
                return price
    return None


def build_results():
    region_ids = set(s["region_id"] for s in MONITORED_STATIONS)
    all_prices = {rid: get_prices(rid) for rid in region_ids}
# DEBUG — show all fuel IDs for missing stations
    missing_ids = [61401679, 61478007, 61402264, 61402467, 61401773]
    for entry in all_prices[1]:
        if entry.get("SiteId") in missing_ids:
            print(f"  SiteId={entry['SiteId']}  FuelId={entry['FuelId']}  Price={entry['Price']/10:.1f}c/L")
    results = []
    for station in MONITORED_STATIONS:
        price = find_price(all_prices[station["region_id"]], station["site_id"])
        results.append({"name": station["name"], "price": price})
        print(f"  {station['name']}: {f'{price:.1f}c/L' if price else 'not found'}")
    return results


def write_prices_json(results, fetch_time):
    payload = {
        "last_updated":     fetch_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "last_updated_str": fetch_time.strftime("%A, %d %B %Y at %I:%M %p"),
        "is_mock":          False,
        "stations":         [
            {
                "name":      r["name"],
                "price":     r["price"],
                "price_str": f"{r['price']:.1f}c/L" if r["price"] else "Not reported",
            }
            for r in results
        ],
    }
    with open("prices.json", "w") as f:
        json.dump(payload, f, indent=2)
    print("✅ prices.json updated")


def main():
    aest = timezone(timedelta(hours=10))
    fetch_time = datetime.now(tz=aest)
    print(f"📡 Fetching 95 unleaded prices — {fetch_time.strftime('%d %b %Y %H:%M')}")
    results = build_results()
    write_prices_json(results, fetch_time)


if __name__ == "__main__":
    main()
