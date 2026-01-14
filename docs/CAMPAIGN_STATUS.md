# Appletree Campaign Status

**Last Updated:** January 5, 2026

---

## Current Campaign State

### Active Campaigns

| Campaign | ID | Status | Leads | Emails/Day | Email Accounts |
|----------|-----|--------|-------|------------|----------------|
| A-Tier - Software & Scale | 2677089 | PAUSED | 341 | 200 | 6 |
| B-Tier - Growth Signal | 2677090 | ACTIVE | 271 | 200 | 6 |
| C-Tier - Pain Focus | 2677091 | PAUSED | 3,040 | 200 | 6 |
| **TOTAL** | - | - | **3,652** | **600** | - |

### A/B Test Campaigns (PAUSED - underperformed)

| Campaign | ID | Status | Result |
|----------|-----|--------|--------|
| M&A Variant | 2757801 | PAUSED | 33% opens, 0 clicks |
| 35/100 Variant | 2757802 | PAUSED | 34% opens, 0 clicks |
| Social Proof | 2757804 | PAUSED | 39% opens, 0 clicks |
| Direct Variant | 2757805 | PAUSED | 24% opens, 0 clicks |

**Conclusion:** "Scorecard" pitch failed. Original campaigns (50% opens, 103 clicks) significantly outperformed.

---

## Email Sequence (Updated Jan 5, 2026)

All three tiers now use a 4-email sequence with 3-4 day gaps:

### Sequence Structure

| Email | Subject | Delay | Purpose |
|-------|---------|-------|---------|
| 1 | "Quick question about {{company_name}}" | Day 0 | Curiosity opener, asks question |
| 2 | "Re: Quick question" | +3 days | Short bump, soft CTA |
| 3 | "What most HVAC owners miss" | +3 days | Value hook ($15-30k savings) |
| 4 | "Should I close your file?" | +4 days | Breakup email |

### Tier Differentiation

- **A-Tier:** Email 1 mentions `{{service_software}}` (their tech stack)
- **B-Tier:** Email 1 mentions `{{review_count}}` reviews (their reputation)
- **C-Tier:** Generic "do you handle your own books" opener

### Personalization Fallback

All emails use: `{{#if first_name}}{{first_name}},{{else}}Hey there,{{/if}}`

---

## Email Infrastructure

### Sending Accounts (6 total)

| Email | Type | Daily Limit | Warmup Status |
|-------|------|-------------|---------------|
| team@appletree-tax.com | Gmail | 35 | 100% |
| team@appletree-advisors.com | Outlook | 35 | 100% |
| team@appletree-taxes.com | SMTP/Zoho | 40 | 100% |
| patrick@appletree-tax.com | Gmail | 40 | 100% |
| patrick@appletree-advisors.com | Outlook | 35 | 100% |
| sales@appletree-tax.com | Gmail | 40 | 100% |

**Total Daily Capacity:** ~225 emails/account = ~1,350 emails/day across 6 accounts

### Schedule

- **Days:** Monday - Friday
- **Hours:** 08:00 - 17:30 ET
- **Min time between emails:** 5 minutes

---

## Lead Pipeline

### Supabase (Source of Truth)

| Metric | Count |
|--------|-------|
| Total leads | ~4,100+ |
| A-tier | 341 |
| B-tier | 271 |
| C-tier | 3,040+ |

### Smartlead Sync

All leads from Supabase are synced to Smartlead campaigns. Sync achieved via:
- `scripts/smartlead/push_leads_batch.py` - Batch upload (100 at a time)
- `scripts/smartlead/sync_smartlead_to_supabase.py` - Pull IDs back

---

## Key Scripts

| Script | Purpose |
|--------|---------|
| `scripts/smartlead/update_all_sequences.py` | Update A & B tier sequences |
| `scripts/smartlead/update_c_tier_sequences.py` | Update C tier sequences |
| `scripts/smartlead/push_leads_batch.py` | Batch push leads to Smartlead |
| `scripts/smartlead/sync_smartlead_to_supabase.py` | Sync Smartlead IDs back |

---

## What Changed (Jan 5, 2026)

1. **Sequences rebuilt** - From 2 emails with 10-day gap to 4 emails with 3-4 day gaps
2. **All leads synced** - 3,652 leads across 3 campaigns
3. **All email accounts activated** - 6 accounts across all campaigns
4. **Campaign limits increased** - 200 leads/day per campaign (was 30-100)
5. **Curiosity-based opener** - "Quick question about..." instead of pitch-first

---

## Next Steps

1. Activate A-Tier and C-Tier campaigns (currently PAUSED)
2. Monitor reply rates with new sequences
3. Check click quality (bot vs human)
4. Follow up on any positive replies immediately

---

## API Reference

- **Smartlead API:** `https://server.smartlead.ai/api/v1`
- **API Key:** `38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8`
- **Calendly Link:** `https://calendly.com/appletreepd/30min`
