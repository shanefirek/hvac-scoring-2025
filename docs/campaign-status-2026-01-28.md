# Appletree Outbound Campaign Status

**Date:** January 28, 2026
**Prepared for:** New agent handoff

---

## Executive Summary

Cold email outreach for Appletree Business Services targeting HVAC companies and marketing agencies. Running since Nov 13, 2025. ~9,500 emails sent, 21 replies, 0 booked meetings. Currently at reduced sending capacity due to burned email accounts.

---

## Email Account Health

### HEALTHY - Use These

| Account | Type | Bounce Rate | Open Rate | Daily Limit | Status |
|---------|------|-------------|-----------|-------------|--------|
| team@appletree-tax.com | Gmail | 5.3% | 68% | 120 | Active, sending |
| team@appletree-taxes.com | Zoho | 4.9% | 43% | 120 | Active, sending |
| sales@appletree-tax.com | Gmail | 7.2% | 67% | 100 | Active, sending |
| patrick@appletree-tax.com | Gmail | 7.7% | 69% | 100 | Active, sending |
| **eden@macrohub.co** | Outlook | 2.7% | 38% | 80 | Warmed, NOT connected |
| **polly@macrohub.co** | Outlook | 4.5% | 40% | 80 | Warmed, NOT connected |

**Current capacity:** 440/day (4 active accounts)
**Potential capacity:** 600/day (if eden + polly added)

### BURNED - Do Not Use

| Account | Bounce Rate | Open Rate | Problem |
|---------|-------------|-----------|---------|
| flora@macrohub.co | **121%** | 12% | Catastrophic bounces, domain reputation destroyed |
| patrick@appletree-advisors.com | **69.5%** | 11% | Going to spam, missing DKIM/DMARC |
| team@appletree-advisors.com | **17.4%** | 33% | High bounces, domain issues |

**Note:** The entire appletree-advisors.com domain has DNS auth issues (missing DKIM/DMARC). Do not use any accounts on this domain.

---

## Campaign Status

### Active Campaigns

| Campaign | ID | Status | Total Leads | Not Started | Sent | Opens | Clicks | Replies |
|----------|-----|--------|-------------|-------------|------|-------|--------|---------|
| C-Tier HVAC | 2677091 | ACTIVE | 3,040 | 1,021 | 6,532 | 39% | 140 | 13 |
| Marketing Agencies | 2843683 | ACTIVE | 1,066 | 331 | 1,889 | 38% | **0** | 4 |

### Paused Campaigns

| Campaign | ID | Status | Total Leads | Not Started | Sent | Opens | Clicks | Replies |
|----------|-----|--------|-------------|-------------|------|-------|--------|---------|
| A-Tier HVAC | 2677089 | PAUSED | 341 | 218 | 348 | 53% | 51 | 3 |
| B-Tier HVAC | 2677090 | PAUSED | 271 | 0 | 771 | 50% | 84 | 1 |

### Dead Campaigns (A/B Tests - Don't Use)

- 2757801 - M&A Variant (0 clicks)
- 2757802 - 35/100 Variant (0 clicks)
- 2757804 - Social Proof (0 clicks)
- 2757805 - Direct Variant (0 clicks)

---

## Critical Issues

### 1. Marketing Agencies: 0 Clicks
The Marketing Agencies campaign has **no Calendly link** in the email copy. Emails ask for "15 min" meetings but don't provide a booking link. This needs to be fixed.

**Calendly link to add:** `https://calendly.com/appletreepd/30min`

### 2. High Bounce Rate on Marketing Agencies (13%)
252 bounces on 1,889 sent. This was caused by the burned macrohub accounts (flora) before they were removed. Should stabilize now.

### 3. Reduced Sending Capacity
Down from 780/day to 440/day after removing burned accounts. Can increase to 600/day by adding eden@macrohub.co and polly@macrohub.co to campaigns.

---

## Lead Database (Supabase)

| Metric | Count |
|--------|-------|
| Total leads | ~5,200 |
| HVAC leads | 4,146 |
| Marketing agency leads | 1,066 |
| Has smartlead_lead_id | ~4,000 |

### Business Types
- hvac: 4,146
- marketing_agency: 1,066

### HVAC Tier Distribution
- A-Tier (Software users): 341
- B-Tier (Growth signals): 271
- C-Tier (Base): 3,040+

---

## Sequence Structure

All campaigns use 4-email sequences with 3-day gaps:

| Email | Delay | Purpose |
|-------|-------|---------|
| 1 | Day 0 | Opener |
| 2 | +3 days | Bump |
| 3 | +3 days | Value hook |
| 4 | +3 days | Breakup |

---

## Key Scripts

| Script | Purpose |
|--------|---------|
| `scripts/smartlead/push_marketing_leads.py` | Push marketing agency leads to Smartlead |
| `scripts/smartlead/push_leads_batch.py` | Push HVAC leads by tier to Smartlead |
| `scripts/smartlead/sync_smartlead_to_supabase.py` | Sync smartlead_lead_id back to Supabase |
| `scripts/smartlead/get_campaign_analytics.py` | Pull engagement metrics |

---

## API Keys & Endpoints

| Service | Details |
|---------|---------|
| Smartlead API | `https://server.smartlead.ai/api/v1` |
| Smartlead Key | `38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8` |
| Supabase URL | `https://rlmuovkdvbxzyylbiunj.supabase.co` |
| Calendly | `https://calendly.com/appletreepd/30min` |

---

## Immediate Action Items

1. **Add Calendly link to Marketing Agencies sequences** - Currently 0 clicks because no link
2. **Add eden@macrohub.co and polly@macrohub.co to campaigns** - Both are healthy (2.7% and 4.5% bounce), will increase capacity from 440 to 600/day
3. **Do NOT use flora@macrohub.co** - 121% bounce rate, burned
4. **Do NOT use any appletree-advisors.com accounts** - Domain has DNS auth issues
5. **Consider unpausing A-Tier and B-Tier campaigns** - Both have leads waiting

---

## Historical Context

- **Nov 13, 2025:** Campaigns launched
- **Jan 15, 2026:** Added macrohub.co accounts, imported marketing agency leads
- **Jan 23, 2026:** Removed flora@macrohub.co (100% bounces), patrick@appletree-advisors.com (spam)
- **Jan 24, 2026:** Thought entire macrohub.co domain was burned, but data shows only flora was bad
- **Jan 28, 2026:** Added 431 new marketing agency leads from Clay, pushed 866 total to Smartlead

---

## MCP Tools Available

- `smartlead` - Campaign/lead management, analytics
- `supabase` - Database queries, lead management
- `n8n-mcp` - Workflow docs (if needed)

Use these for any campaign management tasks.
