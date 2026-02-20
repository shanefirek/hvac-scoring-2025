# Appletree Outbound - Full Audit

**Date:** February 10, 2026
**Period:** November 13, 2025 - February 10, 2026 (90 days)

---

## Executive Summary

90 days, 13,781 emails sent, 0 meetings booked. Sender reputation is degraded across all active domains. Two of four sending domains are burned. C-Tier HVAC (the largest campaign) has a 24% bounce rate. Marketing Agencies shows the only sign of life with Calendly clicks but 0 replies on v2.

**Recommendation:** Pause all current campaigns. Fresh domains + prewarmed inboxes. Relaunch with Marketing Agencies focus only.

---

## 1. All-Time Numbers

| Metric | Count | Rate |
|--------|-------|------|
| Total sent | 13,781 | - |
| Total opened | 4,332 | 31.4% |
| Total replied | 25 | 0.18% |
| Total bounced | 1,029 | 7.5% |
| Positive replies | 0 | 0% |
| Meetings booked | 0 | 0% |

---

## 2. Campaign Breakdown (All-Time)

### Active Campaigns

| Campaign | ID | Status | Sent | Opens | Open Rate | Replies | Bounced | Bounce Rate |
|----------|-----|--------|------|-------|-----------|---------|---------|-------------|
| HVAC C-Tier | 2677091 | ACTIVE | 10,778 | 2,755 | 35.15% | 17 | 734 | **23.96%** |
| Marketing Agencies v2 | 2885428 | ACTIVE | 1,081 | 151 | 18.70% | 0 | 16 | 3.36% |

### Paused Campaigns

| Campaign | ID | Status | Sent | Opens | Open Rate | Replies | Bounced | Bounce Rate |
|----------|-----|--------|------|-------|-----------|---------|---------|-------------|
| HVAC A-Tier | 2677089 | PAUSED | 348 | 185 | 56.82% | 3 | 6 | 4.55% |
| HVAC B-Tier | 2677090 | PAUSED | 771 | 385 | 55.96% | 1 | 14 | 4.64% |
| Marketing Agencies v1 | 2843683 | PAUSED | 2,048 | 755 | 43.17% | 4 | 254 | **30.46%** |

### Dead Campaigns (A/B Tests - Dec 2025)

| Campaign | ID | Sent | Opens | Replies | Result |
|----------|-----|------|-------|---------|--------|
| M&A Variant | 2757801 | 170 | 59 | 0 | Dead |
| 35/100 Variant | 2757802 | 163 | 61 | 0 | Dead |
| Social Proof | 2757804 | 166 | 73 | 0 | Dead |
| Direct Variant | 2757805 | 164 | 51 | 0 | Dead |

### Other

| Campaign | ID | Status | Notes |
|----------|-----|--------|-------|
| HVAC Re-engagement | 2885427 | DRAFTED | Never launched |
| Longbow Test | 2572120 | ARCHIVED | Pre-launch test |

---

## 3. Email Infrastructure

### All Accounts in Smartlead (10 total)

| Email | Type | Daily Limit | Sending Today | Warmup Rep | Status |
|-------|------|-------------|---------------|------------|--------|
| team@appletree-tax.com | Gmail | 120 | 16 | 100% | Active - on C-Tier + MA v2 |
| patrick@appletree-tax.com | Gmail | 100 | 71 | 100% | Active - on C-Tier + MA v2 |
| sales@appletree-tax.com | Gmail | 100 | 73 | 100% | Active - on C-Tier + MA v2 |
| team@appletree-taxes.com | Zoho SMTP | 120 | 18 | 98% | Active - on C-Tier + MA v2 |
| team@appletree-advisors.com | Outlook | 90 | 0 | 100% | **BURNED** - not on any campaign but still in Smartlead |
| patrick@appletree-advisors.com | Outlook | 100 | 0 | 100% | **BURNED** - not on any campaign but still in Smartlead |
| flora@macrohub.co | Outlook | 80 | 0 | 100% | **BURNED** - not on any campaign but still in Smartlead |
| eden@macrohub.co | Outlook | 30 | 0 | 100% | **BURNED** - still attached to C-Tier! |
| polly@macrohub.co | Outlook | 30 | 0 | 100% | **BURNED** - not on any campaign but still in Smartlead |
| sales@shanefirek.com | Gmail | 15 | 0 | N/A | Test account, inactive |

### Problems Found

1. **eden@macrohub.co is still attached to C-Tier campaign** despite being marked as burned in CLAUDE.md. Should be removed immediately.
2. **5 burned accounts still exist in Smartlead** (advisors x2, macrohub x3). Should be deleted to avoid accidental reuse.
3. **Only 4 healthy accounts** actually sending: team@appletree-tax.com, patrick@appletree-tax.com, sales@appletree-tax.com, team@appletree-taxes.com
4. **Real daily capacity: ~178/day** (16 + 71 + 73 + 18 actual sends today) despite 440/day configured limit. Accounts are underperforming their limits.

### Domain Health

| Domain | Accounts | Status | Notes |
|--------|----------|--------|-------|
| appletree-tax.com | 3 (team, patrick, sales) | Degraded | SPF ok, high volume through this domain, 24% bounce rate on C-Tier |
| appletree-taxes.com | 1 (team) | Degraded | SPF ok, Zoho SMTP, 98% warmup |
| appletree-advisors.com | 2 (team, patrick) | **DEAD** | Missing DKIM/DMARC, 27% sender bounce, 0% open rate |
| macrohub.co | 3 (flora, eden, polly) | **DEAD** | 19% domain bounce rate, 100% bounce on flora |
| shanefirek.com | 1 (sales) | Inactive | Test only |

---

## 4. Current Sequences

### HVAC C-Tier (4 emails, 10 days total)

| # | Subject | Delay | Notes |
|---|---------|-------|-------|
| 1 | Where is {{company_name}}'s CPA? | Day 0 | Reply "fit" CTA |
| 2 | Re: Quick question | +3 days | Calendly 30min link |
| 3 | What most HVAC owners miss | +3 days | Reply "Yes" CTA |
| 4 | Should I close your file? | +4 days | Breakup, no link |

**Issues:** Mixed CTAs (reply "fit" vs Calendly link vs reply "Yes"), 30min meeting link (too long for cold), no value offer.

### Marketing Agencies v2 (4 emails, 10 days total)

| # | Subject | Delay | Notes |
|---|---------|-------|-------|
| 1 | {{company_name}} - quick finance question | Day 0 | 15min Calendly link |
| 2 | Re: {{company_name}} - quick finance question | +3 days | Reply CTA, no link |
| 3 | Quick tax math for {{company_name}} | +3 days | 15min Calendly link |
| 4 | Closing the loop | +4 days | Breakup |

**Better structure** than HVAC. Consistent 15min ask. "$20-50K overpaying" hook. But 0 replies across 1,081 sends.

---

## 5. Lead Database (Supabase)

| Metric | Count |
|--------|-------|
| Total leads | ~4,800 |
| HVAC leads | 4,149 |
| Marketing agency leads | 636 |
| Linked to Smartlead | ~3,750 |
| Has phone | 99.7% |

### Tier Distribution (HVAC)

| Tier | Count | Campaign | Status |
|------|-------|----------|--------|
| A-Tier (ServiceTitan/Jobber users) | 341 | 2677089 | PAUSED |
| B-Tier (Growth signals) | 271 | 2677090 | PAUSED |
| C-Tier (Base) | 3,040 | 2677091 | ACTIVE (burning) |

### Data Quality Issues

- 629 bounced leads still active in C-Tier
- ~186 leads with first_name="there" (old bug, 29% of bounced leads)
- Brendan reported HVAC phone numbers going to closed/sold businesses

---

## 6. Infrastructure Status

### What's Working
- Supabase lead database (stable, schema clean)
- Smartlead API integration (MCP tools functional)
- Lead scoring/tiering (A/B/C system)
- Trigger.dev setup in repo (weekly-pipeline, scraping, enrichment, scoring, sync-to-smartlead)

### What's Broken/Stale
- **n8n webhook sync** - "sus" per Shane, Smartlead event data not flowing back to Supabase
- **notify-lead-reply Edge Function** - No junk filtering despite CLAUDE.md claiming it. Resend API key may not be set. Still sending to Shane, not Patrick.
- **clay-import Edge Function** - Functional but defaults business_type to "marketing_agency" for everything
- **Trigger.dev deploy** - Blocked by missing env vars in cloud (SMARTLEAD_API_KEY, OUTSCRAPER_API_KEY, APIFY_API_TOKEN)
- **sync-from-smartlead task** - Built today, not deployed yet. Would replace n8n for pulling Smartlead data back to Supabase.
- **HVAC Re-engagement campaign** (2885427) - Drafted, never launched
- **A-Tier and B-Tier campaigns** - Paused since at least Jan 24, best leads sitting idle

### Repo State
- Uncommitted changes: 13 files (new scripts, trigger tasks, migrations)
- CLAUDE.md is outdated (doesn't mention Marketing Agencies v2, campaign 2885428)
- Marketing Agencies v1 (2843683) shown as ACTIVE in CLAUDE.md but actually PAUSED

---

## 7. Campaign Timeline

| Date | Event | Impact |
|------|-------|--------|
| Nov 13 | Launched A/B/C tier campaigns | - |
| Nov 24 | Fixed n8n webhook, email normalization | Data cleanup |
| Dec 9 | A/B test launched (Scorecard pitch) | Failed - 0 clicks across 663 sends |
| Dec 20 | Clay enrichment - phone coverage 77%->99.7% | Data quality |
| Jan 5 | Rebuilt sequences (4 emails, 3-4 day gaps) | Current copy |
| Jan 8 | Fixed first_name="there" bug | 1,182 leads affected |
| Jan 15 | Added 636 marketing agency leads | New vertical |
| Jan 15 | team@appletree-advisors.com burned (27% bounce) | -1 account |
| Jan 15 | Added 3 macrohub.co accounts, capacity to 780/day | Temporary boost |
| Jan 15 | Built notify-lead-reply Edge Function | Notifications |
| Jan 15 | First interested reply (JP HVAC) | Never converted |
| Jan 23 | Removed flora@macrohub.co (100% bounce) | -1 account |
| Jan 23 | Set 10% bounce autopause on all campaigns | Safety net |
| Jan 24 | Removed polly + eden@macrohub.co, domain burned | -2 accounts, capacity to 440/day |
| Jan 29 | Created Marketing Agencies v2 + HVAC Re-engagement campaigns | New campaigns |
| Jan 29 | Last meeting with Patrick | Discussed copy, lead magnets |
| Feb 3-4 | 125 bounces in 2 days on C-Tier | Reputation damage |
| Feb 5 | Last email to Patrick | Reported 33 Calendly clicks on MA v2 |
| Feb 10 | eden@macrohub.co still on C-Tier | Should have been removed |

---

## 8. What's Actually Converting

**Nothing is converting to meetings.** But signal exists:

| Signal | Source | Volume |
|--------|--------|--------|
| Calendly clicks (HVAC all-time) | C-Tier + A/B tests | 234 |
| Calendly clicks (MA v2, 2 weeks) | Marketing Agencies v2 | 33 (11.5% click rate) |
| Interested reply | JP HVAC (Jan 15) | 1 - never booked |
| Total replies | All campaigns | 25 (all unsubscribe/not interested) |

**Marketing Agencies v2 has the best signal** - 11.5% click rate in 2 weeks is notable. But 0 replies suggests people are clicking out of curiosity but not compelled enough to respond.

---

## 9. Immediate Action Items

### Critical (Do Now)
1. Remove eden@macrohub.co from C-Tier campaign
2. Delete all 5 burned accounts from Smartlead (advisors x2, macrohub x3)
3. Pause C-Tier campaign - 24% bounce rate is actively destroying sender reputation

### Before Relaunch
4. Buy 2-3 fresh domains (avoid "tax" in domain name)
5. Buy 3-4 prewarmed inboxes (Instantly, Mailforge, or Infraforge)
6. Set up SPF + DKIM + DMARC on new domains from day one
7. Write new 3-email sequence using "7 Ways to Save" lead magnet
8. Load Marketing Agency leads only on new infrastructure

### Infrastructure
9. Set Trigger.dev env vars and deploy (SMARTLEAD_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY)
10. Run sync-from-smartlead task to get Supabase in sync with reality
11. Update CLAUDE.md with current state
12. Clean up bounced leads from Supabase data

### Nice to Have
13. Fix notify-lead-reply Edge Function (add junk filtering, set Resend API key)
14. Switch notification recipient to Patrick
15. Scrape more marketing agency leads for volume

---

## 10. The Decision

Two paths:

**Path A: One Last Shot (Recommended)**
- Fresh domains + prewarmed inboxes
- Marketing Agencies only
- New copy with lead magnet hook
- 50-80/day, 2-3 weeks
- Cost: ~$50-100 for domains + inboxes
- If this doesn't book a meeting, walk away with data

**Path B: Wind Down**
- Pause everything
- Export lead database for Patrick
- Hand off Supabase data + Smartlead access
- Close engagement

Current direction: **Path A** - one last shot focused on Marketing Agencies with clean infrastructure.
