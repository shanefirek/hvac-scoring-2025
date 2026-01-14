# Smartlead Campaign Launch Guide

**Status:** Ready to build campaigns
**Launch Date:** Monday, November 18, 2025

---

## What's Been Built

✅ Email sequences parsed and structured (3 tiers, 9 total emails)
✅ Campaign configuration scripts created
✅ Merge tags formatted for Smartlead
✅ Delays configured (A: 0,4,9,14 | B: 0,5,12 | C: 0,10)

---

## What You Need to Provide

### 1. Smartlead Email Account IDs

Get these from Smartlead dashboard:
- Go to Settings → Email Accounts
- Copy the numeric ID for each sending domain
- You mentioned 3 email accounts - need all 3 IDs

**Format:** `[12345, 67890, 11223]`

### 2. Sender Configuration

**Who's sending?**
- Name: "Patrick" or "Patrick from Appletree"
- Email: patrick@appletreebusiness.com (or your warmup domain)
- Reply-to: Same or different?

### 3. Calendly Link

Replace `[Calendly link]` placeholder in sequences:
- Patrick's booking URL
- Should be 15-min call slot
- Example: `https://calendly.com/patrick-appletree/15min`

---

## Execution Plan (Not Over-Engineering)

### Option 1: Use Smartlead MCP (Recommended)
**You give me:**
- Email account IDs
- Sender email/name
- Calendly link

**I execute via Claude:**
- Create 3 campaigns via MCP tools (2 minutes)
- Add sequences with delays
- Configure settings
- Leave in DRAFT mode
- Return campaign IDs

**You do:**
- Import leads from Clay CSV (Smartlead web UI, 5 minutes)
- Send test email to yourself
- Click "Activate" on Monday

**Total time:** 10 minutes
**Complexity:** Low
**Maintenance:** None

### Option 2: Manual Smartlead UI Setup
**You do everything in Smartlead web UI:**
- Create 3 campaigns manually
- Copy-paste sequences from sequences_11_2025_appletree.txt
- Configure delays manually
- Import leads
- Launch

**Total time:** 45-60 minutes
**Complexity:** Medium
**Maintenance:** None

---

## Recommended: Option 1 (MCP Automation)

**Why:**
- 10 minutes vs 60 minutes
- No copy-paste errors
- Delays configured correctly
- All settings standardized
- Can reuse for Week 2+ batches

**Not over-engineering because:**
- You provide 3 pieces of info once
- I run commands once
- No ongoing automation/webhooks/services
- No n8n, no API maintenance
- Just campaign setup automation

---

## After Campaigns Are Created

### 1. Import Leads (Manual, One-Time)

**In Clay:**
- Export table to CSV
- Ensure columns: `email`, `first_name`, `last_name`, `company`, `tier`, `service_software`, `review_count`

**In Smartlead:**
- Campaign → Import Leads → Upload CSV
- Map Clay columns to Smartlead fields
- Map custom fields: `service_software` → `{{service_software}}`, `review_count` → `{{review_count}}`
- Import leads filtered by tier:
  - A-Tier campaign: Filter CSV for tier = "A" (28 leads)
  - B-Tier campaign: Filter CSV for tier = "B" (65 leads)
  - C-Tier campaign: Filter CSV for tier = "C" (67 leads)

### 2. Test Before Launch

**Send test email to yourself:**
- Add your email as lead
- Set custom fields: `company` = "Test Co", `service_software` = "ServiceTitan", `review_count` = "500"
- Send sequence 1
- Verify merge tags populate correctly
- Verify Calendly link works

### 3. Activate Campaigns

**Monday, Nov 18:**
- Campaign Settings → Status → ACTIVE
- Verify send limits: 10/8/10 leads per day
- Monitor first day sends (should see ~28 emails go out)

---

## Daily Monitoring (No Automation Needed)

**Check Smartlead dashboard:**
- Opens/clicks/replies
- Any bounces (should be <1% with verified emails)
- Lead status progression

**Handle replies manually:**
- Forward positive replies to Patrick
- Tag "talk in January" replies for follow-up
- Unsubscribe requests processed automatically

---

## Week 2+ Workflow (Reusable)

**When you have 500+ new leads:**

1. Score leads via FastAPI (already built)
2. Export Clay CSV
3. Give me the CSV
4. I run same MCP script → campaigns created
5. You import leads
6. Activate

**Same 10-minute process, scales to any volume**

---

## What to Provide Now

Reply with:

```
Email Account IDs: [12345, 67890, 11223]
Sender Name: Patrick
Sender Email: patrick@appletreebusiness.com
Reply Email: patrick@appletreebusiness.com
Calendly: https://calendly.com/patrick-appletree/15min
```

I'll create all 3 campaigns and return campaign IDs + next steps.

---

## Questions?

**"Should I set up n8n?"**
No. This is batch work, not real-time sync.

**"Should I automate lead imports?"**
No. 160 leads now, maybe 500/month later. Manual import = 5 minutes.

**"What if I need to change sequences?"**
MCP tools can update campaigns. Give me new copy, I update all 3 in 2 minutes.

**"What about monitoring/dashboards?"**
Smartlead dashboard is sufficient. If you want custom reporting later, we can build it.

---

**Ready to build campaigns. Provide the 5 config values above.**
