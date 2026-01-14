# Appletree HVAC Lead Pipeline

**Last Updated:** January 8, 2026

---

## Current State

### Lead Database (Supabase)

| Metric | Count |
|--------|-------|
| Total leads | 4,149 |
| Linked to Smartlead | 3,119 |
| Has phone | 99.7% |
| Has city/state | 90.5% |

### Tier Distribution

| Tier | Count |
|------|-------|
| A-Tier (Software users) | 341 |
| B-Tier (Growth signals) | 271 |
| C-Tier (Base) | 3,040 |

### First Name Data (Fixed Jan 8)

| Status | Count |
|--------|-------|
| Has real first_name | 1,544 (37%) |
| first_name = NULL | 2,605 (63%) |

*Fixed 1,182 leads that had first_name = "there" (literal string) → set to NULL*

---

## Campaign Status

### Main Campaigns

| Campaign | ID | Status | Leads | Not Started | In Progress |
|----------|-----|--------|-------|-------------|-------------|
| A-Tier | 2677089 | PAUSED | 341 | 218 | 118 |
| B-Tier | 2677090 | PAUSED | 271 | 0 (burned) | 264 |
| C-Tier | 2677091 | **NEEDS REACTIVATION** | 3,040 | 2,012 | 1,010 |

### Results (Nov 13 - Jan 8)

| Metric | Count | Rate |
|--------|-------|------|
| Emails sent | 2,914 | - |
| Opens | 1,272 | 44% |
| Clicks (Calendly) | 214 | 7% |
| Replies | 12 | 0.4% |
| Booked calls | 0 | - |

### A/B Test Campaigns (DEAD - don't use)

| Campaign | ID | Result |
|----------|-----|--------|
| M&A Variant | 2757801 | 0 clicks, killed |
| 35/100 Variant | 2757802 | 0 clicks, killed |
| Social Proof | 2757804 | 0 clicks, killed |
| Direct Variant | 2757805 | 0 clicks, killed |

---

## Email Infrastructure

### Accounts (6 total, 360/day capacity)

| Email | Type | Daily Limit | Age |
|-------|------|-------------|-----|
| team@appletree-tax.com | Gmail | 70 | 2.5 months |
| team@appletree-advisors.com | Outlook | 70 | 2.5 months |
| team@appletree-taxes.com | Zoho | 65 | 2.5 months |
| patrick@appletree-tax.com | Gmail | 50 | 3 weeks |
| patrick@appletree-advisors.com | Outlook | 50 | 3 weeks |
| sales@appletree-tax.com | Gmail | 55 | 3 weeks |

**Schedule:** Mon-Fri 08:00-17:30 ET

### Domains

| Domain | Status |
|--------|--------|
| appletree-tax.com | SPF configured |
| appletree-advisors.com | SPF configured |
| appletree-taxes.com | SPF configured |

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
                              n8n webhooks → Supabase (analytics_events)
```

---

## Key Scripts

| Script | Purpose |
|--------|---------|
| `scripts/smartlead/sync_smartlead_to_supabase.py` | Pull leads + write smartlead_lead_id |
| `scripts/smartlead/sync_first_names_to_smartlead.py` | Sync first_name from Supabase → Smartlead |
| `scripts/smartlead/get_campaign_analytics.py` | Pull engagement metrics |

---

## API Endpoints

| Service | URL |
|---------|-----|
| Smartlead | `https://server.smartlead.ai/api/v1` |
| Smartlead Key | `38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8` |
| Calendly | `https://calendly.com/appletreepd/30min` |

---

## MCP Integration

| MCP | Purpose |
|-----|---------|
| `supabase` | Database queries, lead management |
| `smartlead` | Campaign/lead management |
| `n8n-mcp` | Workflow docs |

---

## Historical Notes

- **Nov 13:** Launched campaigns
- **Nov 24:** Fixed n8n webhook, email normalization
- **Dec 9:** A/B test launched (Scorecard pitch) - failed, 0 clicks
- **Dec 20:** Clay enrichment - phone 77%→99.7%
- **Dec 21:** Sales export - 310 engaged leads
- **Jan 5:** Rebuilt sequences (4 emails, 3-4 day gaps)
- **Jan 8:** Fixed first_name="there" bug (1,182 leads), synced 3,119 leads to Smartlead, bumped email limits to 360/day

---

## TODO

- [ ] Reactivate C-Tier campaign in Smartlead UI
- [ ] Monitor new sequence performance
- [ ] Consider warming more email accounts to hit 500-600/day
