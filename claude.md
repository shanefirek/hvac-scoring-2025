# Appletree Lead Pipeline

**Last Updated:** January 17, 2026

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

### All-Time Results (Nov 13 - Jan 16)

| Metric | Count | Rate |
|--------|-------|------|
| Emails sent | 4,333 | - |
| Opens | 1,891 | 44% |
| Clicks (Calendly) | 234 | 5% |
| Replies | 15 | 0.3% |
| Interested replies | 1 | - |

### A/B Test Campaigns (DEAD - don't use)

| Campaign | ID | Result |
|----------|-----|--------|
| M&A Variant | 2757801 | 0 clicks, killed |
| 35/100 Variant | 2757802 | 0 clicks, killed |
| Social Proof | 2757804 | 0 clicks, killed |
| Direct Variant | 2757805 | 0 clicks, killed |

---

## Email Infrastructure

### Accounts (8 total, 780/day capacity)

| Email | Type | Daily Limit | Status |
|-------|------|-------------|--------|
| team@appletree-tax.com | Gmail | 120 | Active |
| team@appletree-taxes.com | Zoho | 120 | Active |
| patrick@appletree-tax.com | Gmail | 100 | Active |
| patrick@appletree-advisors.com | Outlook | 100 | Active |
| sales@appletree-tax.com | Gmail | 100 | Active |
| polly@macrohub.co | Outlook | 80 | Active (pre-warmed) |
| eden@macrohub.co | Outlook | 80 | Active (pre-warmed) |
| flora@macrohub.co | Outlook | 80 | Active (pre-warmed) |

**Removed:** team@appletree-advisors.com (burned - 27% sender bounce rate on Jan 14)

**Schedule:** Sun-Sat 08:00-17:30 ET (7 days/week)

### Domains

| Domain | Status |
|--------|--------|
| appletree-tax.com | SPF, healthy |
| appletree-advisors.com | SPF only (missing DKIM/DMARC) |
| appletree-taxes.com | SPF, healthy |
| macrohub.co | Pre-warmed marketplace domain |

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

**Current recipient:** shane@shanefirek.com (testing)
**Production:** Change to patrick@appletreebusiness.com

---

## Key Scripts

| Script | Purpose |
|--------|---------|
| `scripts/smartlead/sync_smartlead_to_supabase.py` | Pull leads + write smartlead_lead_id |
| `scripts/smartlead/sync_first_names_to_smartlead.py` | Sync first_name from Supabase → Smartlead |
| `scripts/smartlead/get_campaign_analytics.py` | Pull engagement metrics |
| `scripts/import_marketing_leads.py` | Import marketing agency leads from CSV |

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

---

## TODO

- [ ] Unpause A-Tier and B-Tier campaigns in Smartlead UI
- [ ] Test lead reply notification (add Resend API key, run test curl)
- [ ] Switch notification recipient to Patrick when ready
- [ ] Add DKIM/DMARC to appletree-advisors.com domain
- [x] ~~Build lead gen repo with Apify + Trigger.dev~~ → `../appletree-lead-gen`
- [ ] Init Trigger.dev in lead-gen repo (`npx trigger.dev@latest init --override-config`)
- [ ] Add more leads as current pipeline burns through (~2 weeks at 780/day)
