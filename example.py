"""Local business lead list from YellowPages.com with the YellowPages Scraper actor on Apify.

1. Searches every TERM in every LOCATION (US only).
2. Writes one row per business to yellowpages_leads.csv (name, phone, split address,
   website, categories, rating, years in business, claimed or not).
3. Prints a summary per search, then the prospects a web or marketing agency would
   call first: businesses with no website or an unclaimed listing, oldest first.

Usage:
    pip install -r requirements.txt
    set APIFY_TOKEN=...   (or export APIFY_TOKEN=... on macOS/Linux)
    python example.py
    python example.py "plumber,roofer" "Charlotte, NC;Austin, TX"
    MAX_RESULTS=200 DETAILS=1 python example.py "dentist" "Denver, CO"
"""
import csv
import os
import sys
from collections import defaultdict
from statistics import median

from apify_client import ApifyClient

TOKEN = os.environ.get("APIFY_TOKEN", "<YOUR_APIFY_TOKEN>")
MAX_RESULTS = int(os.environ.get("MAX_RESULTS", "60"))   # per term x location; you pay per business
DETAILS = os.environ.get("DETAILS", "") == "1"           # adds email when listed; slower

terms = [t.strip() for t in (sys.argv[1] if len(sys.argv) > 1 else "plumber").split(",") if t.strip()]
locations = [l.strip() for l in (sys.argv[2] if len(sys.argv) > 2 else "Austin, TX").split(";") if l.strip()]

run_input = {
    "searchTerms": terms,
    "locations": locations,
    "maxResults": MAX_RESULTS,
    "includeDetails": DETAILS,
}
if DETAILS:
    # Detail pages get through Cloudflare most reliably on US residential proxies.
    run_input["proxyConfiguration"] = {
        "useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"], "apifyProxyCountry": "US",
    }

client = ApifyClient(TOKEN)
run = client.actor("rel8ble/yellowpages-scraper").call(run_input=run_input)
leads = list(client.dataset(run["defaultDatasetId"]).iterate_items())

COLS = ["searchTerm", "location", "name", "phone", "email", "website", "street", "city", "state",
        "zip", "rating", "reviewCount", "yearsInBusiness", "isClaimed", "isServiceAreaOnly",
        "yellowPagesUrl"]

with open("yellowpages_leads.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(COLS + ["categories"])
    for b in leads:
        w.writerow([b.get(c) for c in COLS] + [", ".join(b.get("categories") or [])])
print(f"Saved {len(leads)} businesses to yellowpages_leads.csv\n")

groups = defaultdict(list)
for b in leads:
    groups[(b.get("searchTerm"), b.get("location"))].append(b)

print(f"{'Search':<34}{'Found':>6}{'No site':>9}{'Unclaimed':>11}{'Median yrs':>12}")
for (term, loc), rows in groups.items():
    years = [b["yearsInBusiness"] for b in rows if b.get("yearsInBusiness") is not None]
    print(f"{(str(term) + ' / ' + str(loc))[:33]:<34}{len(rows):>6}"
          f"{sum(1 for b in rows if not b.get('website')):>9}"
          f"{sum(1 for b in rows if b.get('isClaimed') is False):>11}"
          f"{(str(int(median(years))) if years else '-'):>12}")

prospects = [b for b in leads if not b.get("website") or b.get("isClaimed") is False]
prospects.sort(key=lambda b: (bool(b.get("website")), -(b.get("yearsInBusiness") or 0)))
print(f"\nProspects (no website first, then unclaimed listings, oldest first): {len(prospects)}")
for b in prospects[:25]:
    why = "no website" if not b.get("website") else "unclaimed"
    print(f"  {(b.get('name') or '')[:36]:<38}{b.get('phone') or '-':<17}"
          f"{(str(b.get('yearsInBusiness')) + ' yrs') if b.get('yearsInBusiness') else '-':<9}{why}")
