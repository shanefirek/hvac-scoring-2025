# Appletree Lead Pipeline

**Last Updated:** January 24, 2026

---

## Current State

### Lead Database (Supabase)

| Metric | Count |
|--------|-------|
| Total leads | ~4,800 |
| HVAC leads | 4,149 |
| Marketing agency leads | 636 |
| Linked to Smartlead | ~3,750 |
| Has phone | 99.7% |

### Business Types

| Type | Count |
|------|-------|
| hvac | 4,149 |
| marketing_agency | 636 |

### Tier Distribution (HVAC)

| Tier | Count |
|------|-------|
| A-Tier (Software users) | 341 |
| B-Tier (Growth signals) | 271 |
| C-Tier (Base) | 3,040 |

---

## Campaign Status

### Active Campaigns

| Campaign | ID | Status | Leads | Not Started | Schedule |
|----------|-----|--------|-------|-------------|----------|
| A-Tier | 2677089 | PAUSED (unpause in UI) | 341 | 218 | 7 days |
| B-Tier | 2677090 | PAUSED (unpause in UI) | 271 | 0 | 7 days |
| C-Tier | 2677091 | ACTIVE | 3,040 | 1,817 | 7 days |
| Marketing Agencies | 2843683 | ACTIVE | 636 | 436 | 7 days |

### All-Time Results (Nov 13 - Jan 24)

| Metric | Count | Rate |
|--------|-------|------|
| Emails sent | ~5,500 | - |
| Opens | ~2,400 | 44% |
| Clicks (Calendly) | 234 | 4% |
| Replies | 17 | 0.3% |
| Interested replies | 1 | - |
| Booked meetings | 0 | - |

### A/B Test Campaigns (DEAD - don't use)

| Campaign | ID | Result |
|----------|-----|--------|
| M&A Variant | 2757801 | 0 clicks, killed |
| 35/100 Variant | 2757802 | 0 clicks, killed |
| Social Proof | 2757804 | 0 clicks, killed |
| Direct Variant | 2757805 | 0 clicks, killed |

---

## Email Infrastructure

### Accounts (4 total, 440/day capacity)

| Email | Type | Daily Limit | Status |
|-------|------|-------------|--------|
| team@appletree-tax.com | Gmail | 120 | Active (100% warmup) |
| team@appletree-taxes.com | Zoho | 120 | Active (98% warmup) |
| patrick@appletree-tax.com | Gmail | 100 | Active (100% warmup) |
| sales@appletree-tax.com | Gmail | 100 | Active (100% warmup) |

**Removed Accounts:**
- team@appletree-advisors.com (burned - 27% sender bounce rate, Jan 14)
- patrick@appletree-advisors.com (0% open rate, going to spam - missing DKIM/DMARC, Jan 23)
- flora@macrohub.co (100% bounce rate, burned domain, Jan 23)
- polly@macrohub.co (burned domain - 19% domain bounce rate, Jan 24)
- eden@macrohub.co (burned domain - 19% domain bounce rate, Jan 24)

**Bounce Autopause:** 10% threshold set on all campaigns

**Schedule:** Sun-Sat 08:00-17:30 ET (7 days/week)

### Domains

| Domain | Status |
|--------|--------|
| appletree-tax.com | SPF, healthy |
| appletree-taxes.com | SPF, healthy |
| appletree-advisors.com | SPF only (missing DKIM/DMARC) - DO NOT USE |
| macrohub.co | BURNED - 19% bounce rate, removed all accounts |

---

## Sequence Structure (All Tiers)

| Email | Subject | Delay | Purpose |
|-------|---------|-------|---------|
| 1 | Quick question about {{company_name}} | Day 0 | Curiosity opener |
| 2 | Re: Quick question | +3 days | Bump |
| 3 | What most HVAC owners miss | +3 days | Value hook |
| 4 | Should I close your file? | +4 days | Breakup |

**Template:** `{{#if first_name}}Hey {{first_name}},{{else}}Hey there,{{/if}}`

---

## Architecture

```
Clay (enrichment) → Supabase (leads) → Smartlead (campaigns)
                                        ↓
                              Webhooks → Supabase Edge Function
                                        ↓
                              Email notification to Patrick
```

---

## Lead Reply Notifications

**Edge Function:** `notify-lead-reply`
**URL:** `https://rlmuovkdvbxzyylbiunj.supabase.co/functions/v1/notify-lead-reply`

**Features:**
- Receives Smartlead webhook on reply
- Filters junk (OOO, bounces, unsubscribes, "no longer monitored", etc.)
- Enriches from Supabase (phone, location, tier)
- Sends formatted email with lead info + reply button + call button

**Junk Filters:**
- Out of office / auto-replies
- Invalid email bounces
- Unsubscribe requests
- "No longer monitored" / "not monitored"
- Very short replies (<10 chars)

**Current recipient:** shanefirek@gmail.com (testing)
**Production:** Uncomment Patrick's email in Edge Function when ready

**Webhooks:** Configured on all 4 campaigns (see [`docs/dns-email-auth.md`](docs/dns-email-auth.md))

---

## Key Scripts

| Script | Purpose |
|--------|---------|
| `scripts/smartlead/sync_smartlead_to_supabase.py` | Pull leads + write smartlead_lead_id |
| `scripts/smartlead/sync_first_names_to_smartlead.py` | Sync first_name from Supabase → Smartlead |
| `scripts/smartlead/get_campaign_analytics.py` | Pull engagement metrics |
| `scripts/import_marketing_leads.py` | Import marketing agency leads from CSV |
| `scripts/dns-manager.ts` | DNS/email auth CLI (SPF/DKIM/DMARC, Resend, Porkbun) |

---

## Documentation

| Doc | Purpose |
|-----|---------|
| [`docs/dns-email-auth.md`](docs/dns-email-auth.md) | DNS setup, DMARC status, Resend config, lead notifications |

---

## API Endpoints

| Service | URL |
|---------|-----|
| Smartlead | `https://server.smartlead.ai/api/v1` |
| Smartlead Key | `38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8` |
| Calendly | `https://calendly.com/appletreepd/30min` |
| Edge Function | `https://rlmuovkdvbxzyylbiunj.supabase.co/functions/v1/notify-lead-reply` |

---

## MCP Integration

| MCP | Purpose |
|-----|---------|
| `supabase` | Database queries, lead management, edge functions |
| `smartlead` | Campaign/lead management |
| `n8n-mcp` | Workflow docs |

---

## Lead Generation Repo

**Repo:** `../appletree-lead-gen`

Trigger.dev pipeline for scraping new leads via Apify.

```bash
cd ../appletree-lead-gen
npx trigger.dev@latest init --override-config
cp .env.example .env
npm run dev
```

**Tasks:**
| Task | Purpose |
|------|---------|
| `leads.scrape.hvac` | Main orchestrator |
| `leads.scrape.google-maps` | Apify Google Maps scrape |
| `leads.scrape.emails` | Apify contact/email scrape |
| `leads.insert.batch` | Dedupe + insert to Supabase |

**Usage:**
```typescript
await tasks.trigger("leads.scrape.hvac", {
  locations: [{ city: "Boston", state: "MA" }],
  maxPerQuery: 100,
  enrichEmails: true,
});
```

---

## Historical Notes

- **Nov 13:** Launched campaigns
- **Nov 24:** Fixed n8n webhook, email normalization
- **Dec 9:** A/B test launched (Scorecard pitch) - failed, 0 clicks
- **Dec 20:** Clay enrichment - phone 77%→99.7%
- **Dec 21:** Sales export - 310 engaged leads
- **Jan 5:** Rebuilt sequences (4 emails, 3-4 day gaps)
- **Jan 8:** Fixed first_name="there" bug (1,182 leads), synced 3,119 leads to Smartlead
- **Jan 15:** Imported 636 marketing agency leads, created Marketing Agencies campaign
- **Jan 15:** Found team@appletree-advisors.com burned (37 sender bounces, 27% rate) - removed from all campaigns
- **Jan 15:** Added 3 pre-warmed macrohub.co accounts, bumped capacity to 780/day
- **Jan 15:** Enabled weekend sending (7 days/week) on all campaigns
- **Jan 15:** Built lead reply notification Edge Function with junk filtering
- **Jan 15:** First interested reply - Jordyn from JP HVAC asking for pricing ($400k revenue, wants tax CPA)
- **Jan 17:** Built appletree-lead-gen repo with Trigger.dev + Apify for automated lead scraping
- **Jan 23:** Removed flora@macrohub.co (100% bounce rate) and patrick@appletree-advisors.com (0% open rate)
- **Jan 23:** Set 10% bounce autopause threshold on all campaigns
- **Jan 24:** Removed polly@macrohub.co and eden@macrohub.co - entire macrohub.co domain burned (19% bounce rate)
- **Jan 24:** Capacity reduced from 780/day to 440/day (4 healthy accounts remaining)

---

## TODO

- [ ] Unpause A-Tier and B-Tier campaigns in Smartlead UI
- [ ] Test lead reply notification (add Resend API key, run test curl)
- [ ] Switch notification recipient to Patrick when ready
- [x] ~~Add DKIM/DMARC to appletree-advisors.com domain~~ → Domain burned, not using
- [x] ~~Build lead gen repo with Apify + Trigger.dev~~ → `../appletree-lead-gen`
- [ ] Init Trigger.dev in lead-gen repo (`npx trigger.dev@latest init --override-config`)
- [ ] Add more leads as current pipeline burns through (~3 weeks at 440/day)
- [ ] Consider spinning up new accounts on appletree-tax.com or appletree-taxes.com domains to increase capacity
