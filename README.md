# YellowPages scraper in Python: get US business leads (name, phone, address, website, email) from YellowPages.com search results with a simple API

A short tutorial for pulling **local business leads from YellowPages.com** in Python with the [YellowPages Scraper](https://apify.com/rel8ble/yellowpages-scraper) actor on Apify. Give it search terms (`plumber`, `dentist`) and US locations (`Austin, TX` or a ZIP) and get one row per business: name, phone, address split into street / city / state / ZIP, website, categories, rating, opening hours, years in business and whether the listing is claimed. Turn on `includeDetails` to add the email (when the business listed one), description, payment methods, social links and GPS coordinates. YellowPages has no public API; this is a working stand-in for lead generation, CRM enrichment and local market sizing.

> Disclosure: I built this actor; it's a paid tool on Apify ($1.50 per 1,000 businesses). The code in this repo is MIT-licensed.

## How it works

The actor fetches YellowPages search pages over plain HTTP (no headless browser), 30 listings per page, in parallel. YellowPages sits behind Cloudflare, so challenged pages are retried on a fresh proxy session automatically. Duplicates are removed before saving. In the real test run used below, 256 businesses across 6 searches were collected.

## Quick start (Python)

```bash
pip install apify-client
```

```python
from apify_client import ApifyClient

client = ApifyClient("<YOUR_APIFY_TOKEN>")

run = client.actor("rel8ble/yellowpages-scraper").call(run_input={
    "searchTerms": ["plumber", "dentist"],
    "locations": ["Austin, TX", "Denver, CO"],   # every term is searched in every location
    "maxResults": 60,                            # per term x location
    "includeDetails": False,                     # True adds email, description, GPS (slower)
})

for b in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(b["name"], b["phone"], b["city"], b["state"], b["website"])
```

[`example.py`](example.py) is the runnable version, built for agency prospecting: it saves every business to `yellowpages_leads.csv`, prints a summary per search, and lists the businesses with **no website** or an **unclaimed listing**, oldest first.

```bash
pip install -r requirements.txt
export APIFY_TOKEN=<YOUR_APIFY_TOKEN>
python example.py                                             # plumber in Austin, TX
python example.py "plumber,roofer" "Charlotte, NC;Austin, TX"
MAX_RESULTS=200 DETAILS=1 python example.py "dentist" "Denver, CO"
```

## Quick start (Node.js)

```js
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: '<YOUR_APIFY_TOKEN>' });
const run = await client.actor('rel8ble/yellowpages-scraper').call({
    searchTerms: ['roofing contractors'], locations: ['Charlotte, NC'], maxResults: 30,
});
const { items } = await client.dataset(run.defaultDatasetId).listItems();
console.log(items.map((b) => `${b.name} | ${b.phone} | ${b.website ?? 'no website'}`));
```

## Plain HTTP (curl, Google Apps Script, anything)

One call runs the actor and returns the results. Use `format=csv` for a spreadsheet, `format=json` for code:

```bash
curl -X POST "https://api.apify.com/v2/acts/rel8ble~yellowpages-scraper/run-sync-get-dataset-items?format=csv"   -H "Authorization: Bearer <YOUR_APIFY_TOKEN>"   -H "Content-Type: application/json"   -d '{"searchTerms":["plumber"],"locations":["Austin, TX"],"maxResults":100}'   -o results.csv
```

The sync endpoint waits up to 5 minutes; for bigger runs use the clients above (they wait as long as needed). [`example.js`](example.js) is a runnable Node.js version that writes `yellowpages_leads.csv` (`npm install`, then `APIFY_TOKEN=... node example.js`).

## No code: n8n, Make, Zapier, Google Sheets

- **n8n**: import [`n8n/workflow.json`](n8n/workflow.json) (Workflows > Import from file), replace `YOUR_APIFY_TOKEN`, and add a Google Sheets "Append or update row" node after it, matched on `ypid` so weekly runs don't create duplicates. It uses n8n's built-in HTTP Request node, so no community node is needed (the official Apify node, `@apify/n8n-nodes-apify`, works too).
- **Make**: Apify app > "Run an Actor" (actor `rel8ble/yellowpages-scraper`, wait for finish on, input JSON as above) > Apify "Get Dataset Items" > Google Sheets "Add a Row" or your CRM module.
- **Zapier**: Apify app > "Run Actor" action (or the "Finished Actor Run" trigger on a scheduled run) > "Fetch Dataset Items" > Google Sheets / HubSpot / Airtable.
- **Google Sheets only**: run it from the [Store page](https://apify.com/rel8ble/yellowpages-scraper) form, download CSV and import. Useful columns: name, phone, street, city, state, zip, website, categories, rating, yearsInBusiness, isClaimed.
- **AI agents**: the Apify MCP server (https://mcp.apify.com) lets Claude, ChatGPT or Cursor call `rel8ble/yellowpages-scraper` as a tool.

## Input

| Field | Default | What it does |
|---|---|---|
| `searchTerms` | - | What you'd type in the YellowPages "Find" box: `plumber`, `dentist`, `pizza` |
| `locations` | - | US city + state or ZIP: `Charlotte, NC`, `Austin, TX`, `10001` |
| `startUrls` | - | Optional: paste YellowPages search URLs (keeps the sorting and filters you set on the site) |
| `maxResults` | 100 | Businesses per term x location (0 = everything, up to about 3,000) |
| `includeDetails` | false | Adds email, description, hours, payment methods, services, social links, founded year, coordinates. One extra request per business |
| `includeSponsored` | false | Include the paid ad cards shown above the results |
| `proxyConfiguration` | Apify Proxy | Use RESIDENTIAL (US) for `includeDetails` or big runs |

## Output sample (real row, run of 24 Sep 2026)

One business = one item. This is a "pizza" result in Charlotte, NC with `includeDetails: true`, with the review snippet, thumbnail and image URLs left out:

```json
{
  "searchTerm": "pizza",
  "location": "Charlotte, NC",
  "position": 2,
  "name": "House of Pizza",
  "ypid": "10704527",
  "categories": ["Pizza", "American Restaurants", "Italian Restaurants"],
  "rating": 4,
  "reviewCount": 4,
  "tripAdvisorRating": 4,
  "tripAdvisorReviewCount": 45,
  "priceRange": null,
  "phone": "(704) 568-9410",
  "address": "3640 Central Ave, Charlotte, NC 28205",
  "street": "3640 Central Ave",
  "city": "Charlotte",
  "state": "NC",
  "zip": "28205",
  "website": null,
  "yellowPagesUrl": "https://www.yellowpages.com/charlotte-nc/mip/house-of-pizza-10704527",
  "openingHours": ["Mo-Su 11:00-23:00"],
  "openStatus": "closed now",
  "yearsInBusiness": 47,
  "yearsWithYellowPages": null,
  "isServiceAreaOnly": false,
  "isSponsored": false,
  "isClaimed": false,
  "searchPage": 1,
  "scrapedAt": "2026-09-24T05:27:44.239Z",
  "email": null,
  "description": null,
  "paymentMethods": ["discover"],
  "foundedYear": 1979,
  "latitude": 35.21561,
  "longitude": -80.782845,
  "services": ["Daily Specials"],
  "socialLinks": [],
  "extraPhones": ["Phone: (704) 568-9411"],
  "aka": null
}
```

A 47-year-old restaurant with no website and an unclaimed listing: exactly the kind of row `example.py` puts at the top of the prospect list.

### What the summary looks like on that sample

The same 256-business run, as `example.py` prints it:

| Search | Found | No website | Unclaimed listing | Median years in business |
|---|---|---|---|---|
| roofing contractors / Charlotte, NC | 12 | 2 | 0 | 34 |
| pizza / Charlotte, NC | 9 | 1 | 8 | 20 |
| dentist / Austin, TX | 56 | 2 | 43 | 25 |
| plumber / Austin, TX | 60 | 8 | 50 | 40 |
| dentist / Denver, CO | 60 | 3 | 51 | 23 |
| plumber / Denver, CO | 59 | 1 | 47 | 38 |

Across all 256: 17 businesses had no website and 199 had an unclaimed listing. Email only comes with `includeDetails`: in this run 12 of the 21 detail rows (57%) had one.

## Pricing

Pay per result: **$1.50 per 1,000 businesses** saved. 10,000 leads cost $15. Duplicates are removed before saving, so you pay for unique businesses only. The Apify free plan's $5 monthly credit covers about 3,300 leads.

## Limits

- **United States only.** YellowPages.com covers US businesses. Canadian, Australian and other Yellow Pages sites are separate and not covered.
- **About 3,000 results per search** (YellowPages serves roughly 100 pages of 30). For a whole metro area, split by suburb or ZIP code.
- **Email needs `includeDetails`** and only exists when the business published one. Detail mode opens one extra page per business, so it is slower.
- **Cloudflare.** Blocked pages are retried on new proxy sessions. For `includeDetails` or large runs use the RESIDENTIAL (US) proxy group. A detail page that still fails is saved without the extra fields (`detailsError`), so the listing is never lost.
- **No full review texts**, only the snippet shown on the results page.
- The data is public business information. Follow YellowPages' terms and anti-spam and privacy laws (CAN-SPAM, GDPR, CCPA) when you contact anyone.

## Links

- Actor on the Apify Store: https://apify.com/rel8ble/yellowpages-scraper
- Apify Python client: https://docs.apify.com/api/client/python

## License

MIT (this example code). The actor itself is a paid Apify tool.
