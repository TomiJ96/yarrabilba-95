"""
Yarrabilba Area — Multi-Fuel Price Tracker
Fetches 91, 95, 98 and Diesel prices from the QLD Government Fuel Price API
and writes prices.json for the GitHub Pages dashboard.
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta

FUEL_API_TOKEN = os.environ.get("FUEL_API_TOKEN", "")
API_BASE       = "https://fppdirectapi-prod.fuelpricesqld.com.au"

FUEL_TYPES = {
    2:    "91",
    5:    "95",
    8:    "98",
    3:    "diesel",
    6:    "diesel",
    14:   "diesel",
    1000: "diesel",
}

PRICE_CEILING = 500

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


def get_prices(region_id=1):
    headers = {
        "Authorization": f"FPDAPI SubscriberToken={FUEL_API_TOKEN}",
        "Content-Type":  "application/json",
    }
    url  = f"{API_BASE}/Price/GetSitesPrices?countryId=21&geoRegionLevel=3&geoRegionId={region_id}"
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json().get("SitePrices", [])


def find_fuel_prices(prices, site_id):
    result = {"91": None, "95": None, "98": None, "diesel": None}
    for entry in prices:
        if entry.get("SiteId") == site_id and entry.get("FuelId") in FUEL_TYPES:
            price = round(entry["Price"] / 10.0, 1)
            if price <= PRICE_CEILING:
                label = FUEL_TYPES[entry["FuelId"]]
                if result[label] is None or price < result[label]:
                    result[label] = price
    return result


def build_results():
    region_ids = set(s["region_id"] for s in MONITORED_STATIONS)
    all_prices = {rid: get_prices(rid) for rid in region_ids}
    results = []
    for station in MONITORED_STATIONS:
        fuels = find_fuel_prices(all_prices[station["region_id"]], station["site_id"])
        results.append({"name": station["name"], "fuels": fuels})
        fuel_str = "  ".join([f"{k}={v:.1f}c/L" if v else f"{k}=—" for k, v in fuels.items()])
        print(f"  {station['name']}: {fuel_str}")
    return results


def write_prices_json(results, fetch_time):
    payload = {
        "last_updated":     fetch_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "last_updated_str": fetch_time.strftime("%A, %d %B %Y at %I:%M %p"),
        "stations":         [
            {
                "name":  r["name"],
                "fuels": r["fuels"],
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
    print(f"📡 Fetching fuel prices — {fetch_time.strftime('%d %b %Y %H:%M')}")
    results = build_results()
    write_prices_json(results, fetch_time)


if __name__ == "__main__":
    main()
