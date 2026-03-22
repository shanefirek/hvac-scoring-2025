# Appletree Lead Pipeline

**Last Updated:** March 11, 2026

---

## Project Status

**WINDING DOWN** — Patrick gave a 2-week ultimatum (~March 5). No appointments booked in 90+ days (~14k sends). MA v2 is running on autopilot. No active development needed.

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

### Tier Distribution (HVAC)

| Tier | Count |
|------|-------|
| A-Tier (Software users) | 341 |
| B-Tier (Growth signals) | 271 |
| C-Tier (Base) | 3,040 |

---

## Campaign Status

### Campaigns

| Campaign | ID | Status |
|----------|-----|--------|
| MA v2 | 2885428 | **ACTIVE** (best performer, 6.2% CTR) |
| A-Tier | 2677089 | PAUSED |
| B-Tier | 2677090 | PAUSED |
| C-Tier | 2677091 | PAUSED |
| Marketing Agencies v1 | 2843683 | PAUSED |

### All-Time Results (Nov 13, 2025 - March 2026)

| Metric | Count | Rate |
|--------|-------|------|
| Emails sent | ~13,781 | - |
| Meetings booked | 0 | - |
| Interested replies | 1 | - |
| Best campaign | MA v2 | 6.2% CTR |

### A/B Test Campaigns (DEAD)

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
| team@appletree-tax.com | Gmail | 120 | Active |
| team@appletree-taxes.com | Zoho | 120 | Active |
| patrick@appletree-tax.com | Gmail | 100 | Active |
| sales@appletree-tax.com | Gmail | 100 | Active |

**Burned/Removed Accounts:**
- team@appletree-advisors.com (27% sender bounce rate)
- patrick@appletree-advisors.com (0% open rate, going to spam)
- flora@macrohub.co, polly@macrohub.co, eden@macrohub.co (domain burned)

### Domains

| Domain | Status |
|--------|--------|
| appletree-tax.com | Degraded |
| appletree-taxes.com | Degraded |
| appletree-advisors.com | BURNED - DO NOT USE |
| macrohub.co | BURNED - DO NOT USE |

---

## Clay Enrichment (March 2026)

Burned ~10k Clay credits enriching both datasets in workspace `712043`.

### Clay Tables

| Table | ID | Rows | Purpose |
|-------|----|------|---------|
| HVAC Enrich + Normalize | `t_0t749xwPUKnCynCytVj` | 8,882 (2,902 filtered) | HVAC lead enrichment |
| Marketing Agencies - Phone Enrichment | `t_0tb2ost97mWbznEHo5W` | 636 | MA lead enrichment |

**Table URLs:**
- HVAC: `https://app.clay.com/workspaces/712043/tables/t_0t749xwPUKnCynCytVj`
- MA: `https://app.clay.com/workspaces/712043/tables/t_0tb2ost97mWbznEHo5W`

### Enrichment Fields Created

**HVAC Table:**
| Field | ID | Type | Credits |
|-------|----|------|---------|
| Company Enrichment (MixRank) | `f_0tbqww5jahAu5fr3Xev` | `enrich-company-with-mixrank-v2` | 1/row |

**MA Table:**
| Field | ID | Type | Credits |
|-------|----|------|---------|
| Company Enrichment (MixRank) | `f_0tbqww8DFCbtQj2vVGd` | `enrich-company-with-mixrank-v2` | 1/row |
| Search Query (formula) | `f_0tbqxfx4ZQCSEnWX7kE` | Formula: name + domain | 0 |
| Find & Enrich Person (MixRank) | `f_0tbqxan55dy58hkVdys` | `enrich-person-with-mixrank-from-search` | 2/row |
| Agency Deep Dive (Claygent) | `f_0tbrbf8Z3BJUHcYUPVd` | Claygent (clay-argon) | ~10/row |

### HVAC Clean Export

**File:** `exports/hvac-clean-2902.csv`
**Rows:** 2,902 (filtered: has website, 10-400 reviews, verified email)

| Field | Coverage |
|-------|----------|
| Phone | 99% |
| Email | 100% |
| Domain | 100% |
| Score + Tier | 99% |
| Company Enrichment | 50% (small local shops often not in MixRank) |
| Contact Name | 27% |
| LinkedIn | 23% |

**Tier Breakdown (filtered):**
| Tier | Count |
|------|-------|
| A-Tier | 269 |
| B-Tier | 187 |
| C-Tier | 2,437 |

### Clay Enrichment Lessons Learned

- MixRank company enrichment input must be `company_identifier` (not `domain`)
- Wiza LinkedIn enrichment requires connected auth account — can't use Clay credits
- Cannot change `actionKey` on existing enrichment field — must delete and recreate
- `literalInputs` overrides `inputMapping` for same keys
- Template syntax in enrichment inputs can cause "r.trim is not a function" — use formula columns instead
- ~50% of small local HVAC companies return SUCCESS_NO_DATA from MixRank
- Clay credits remaining: ~271

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

- Receives Smartlead webhook on reply
- Filters junk (OOO, bounces, unsubscribes, short replies)
- Enriches from Supabase (phone, location, tier)
- Sends formatted email with lead info

**Webhooks:** Configured on all campaigns

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

## Key Files

| File | Purpose |
|------|---------|
| `docs/full-audit-2026-02-10.md` | Full campaign audit |
| `docs/dns-email-auth.md` | DNS setup, DMARC status, Resend config |
| `exports/hvac-clean-2902.csv` | Clean HVAC dataset (2,902 rows) |
| `supabase/functions/notify-lead-reply/` | Lead reply notification edge function |
| `supabase/functions/clay-import/` | Clay import edge function |
| `src/trigger/utils/smartlead.ts` | Smartlead utilities |

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
| `clay` | Clay table automation — enrichment, sourcing, field/record CRUD |
| `supabase` | Database queries, lead management, edge functions |
| `smartlead` | Campaign/lead management |
| `n8n-mcp` | Workflow docs |

### Clay MCP — Workspace Rules

- **Always use Shane's personal workspace: `712043`**
- **NEVER use the TAM workspace (`34090`)** — that belongs to a different project
- When calling any Clay tool that requires a `workspaceId`, use `712043`
- Session cookies expire — if you get 401 errors, ask the user to refresh the cookie from Chrome DevTools (Application → Cookies → `connect.sid` on app.clay.com)

---

## Lead Generation Repo

**Repo:** `../appletree-lead-gen`

Trigger.dev pipeline for scraping new leads via Apify.

**Tasks:**
| Task | Purpose |
|------|---------|
| `leads.scrape.hvac` | Main orchestrator |
| `leads.scrape.google-maps` | Apify Google Maps scrape |
| `leads.scrape.emails` | Apify contact/email scrape |
| `leads.insert.batch` | Dedupe + insert to Supabase |

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
- **Jan 15:** Found team@appletree-advisors.com burned - removed from all campaigns
- **Jan 15:** Added 3 pre-warmed macrohub.co accounts, bumped capacity to 780/day
- **Jan 15:** Built lead reply notification Edge Function with junk filtering
- **Jan 15:** First interested reply - Jordyn from JP HVAC asking for pricing
- **Jan 17:** Built appletree-lead-gen repo with Trigger.dev + Apify
- **Jan 23-24:** Removed all macrohub.co accounts (domain burned), capacity reduced to 440/day
- **Feb 10:** Full campaign audit — 90 days, ~14k sends, 0 meetings
- **Feb 12:** Ordered 6 new inboxes from SmartSenders (never delivered)
- **Feb 19:** Patrick gave 2-week ultimatum. Decision to let MA v2 coast on autopilot
- **Mar 11:** Burned ~10k Clay credits enriching HVAC + MA datasets. Exported clean HVAC dataset (2,902 rows)
