// Runnable Node.js example for the Yellow Pages scraper on Apify: https://apify.com/rel8ble/yellowpages-scraper
// npm install && APIFY_TOKEN=<YOUR_APIFY_TOKEN> node example.js
import { ApifyClient } from 'apify-client';
import { writeFileSync } from 'node:fs';

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });
const run = await client.actor('rel8ble/yellowpages-scraper').call({
        "searchTerms": [
            "plumber"
        ],
        "locations": [
            "Austin, TX"
        ],
        "maxResults": 100
    });
const { items } = await client.dataset(run.defaultDatasetId).listItems();

// Leads -> yellowpages_leads.csv, deduped on ypid, CRM-ready columns
const seen = new Set();
const rows = items
    .filter((b) => !seen.has(b.ypid) && seen.add(b.ypid))
    .map((b) => ({ name: b.name, phone: b.phoneE164 ?? b.phone, street: b.street, city: b.city, state: b.state,
        zip: b.zip, website: b.website, categories: (b.categories || []).join('; '), rating: b.rating,
        yearsInBusiness: b.yearsInBusiness, claimed: b.isClaimed, email: b.email ?? '' }));

const esc = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
const header = Object.keys(rows[0] ?? {});
writeFileSync('yellowpages_leads.csv', [header.join(','), ...rows.map((row) => header.map((h) => esc(row[h])).join(','))].join('\n'));
console.log(`${rows.length} rows -> yellowpages_leads.csv`);
