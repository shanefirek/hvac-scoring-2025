dio# Smartlead Campaign Automation - Working Solution

**Date:** November 13, 2025
**Status:** ✅ Production-ready workflow
**Campaigns Built:** 3 tiers, 151 leads, ready to launch Monday 11/18

---

## What We Built

### 3 Automated HVAC Campaigns

**Campaign IDs (Nov 2025 batch):**
- **A-Tier (2677089):** 16 leads, 4 emails, software + scale messaging
- **B-Tier (2677090):** 29 leads, 3 emails, growth messaging
- **C-Tier (2677091):** 106 leads, 2 emails, pain-focused messaging

**Configuration:**
- 3 email accounts rotating sends (SMTP, Outlook, Gmail)
- Mon-Fri, 9am-5pm ET sending window
- Daily limits: 10/8/10 leads per campaign = 28 total/day
- Sequences with proper delays (A: 0/4/9/14, B: 0/5/12, C: 0/10)
- Merge tags: {{first_name}}, {{company}}, {{service_software}}, {{review_count}}
- Calendly link embedded in all sequences

---

## The Working Workflow (10 Minutes Start to Finish)

### Step 1: Export from Clay (you already have this)
```
Clay → Export → CSV with columns:
- Company, Normalized First Name, Normalized Name, Final Email
- Reviews Count, Field Service Tech, Score, Verified (2)
```

### Step 2: Clean & Split CSV (30 seconds)
```bash
cd /path/to/appletree-data-pipeline
python3 clean_clay_export.py
```

**Output:**
- `smartlead_imports/leads_a_tier.csv` (20-30 pts)
- `smartlead_imports/leads_b_tier.csv` (10-19 pts)
- `smartlead_imports/leads_c_tier.csv` (0-9 pts)

**What it does:**
- Filters verified emails only
- Calculates tier from score
- Extracts first/last name
- Cleans service_software and review_count
- Outputs 7 clean columns for Smartlead

### Step 3: Build Campaigns (5 minutes)
```bash
python3 build_smartlead_campaigns.py
```

**What it does:**
- Creates 3 campaigns via Smartlead API
- Imports leads with custom fields
- Adds 3 email accounts to each
- Adds sequences with delays
- Configures schedule (send windows, daily limits)
- Leaves campaigns in DRAFT mode

**Output:**
```
✅ A-Tier: Campaign ID 2677089 (16 leads, 4 sequences)
✅ B-Tier: Campaign ID 2677090 (29 leads, 3 sequences)
✅ C-Tier: Campaign ID 2677091 (106 leads, 2 sequences)
```

### Step 4: Verify & Launch (5 minutes)
1. Log into Smartlead
2. Check campaigns 2677089, 2677090, 2677091
3. Send test email to yourself
4. Verify merge tags populate correctly
5. Monday: Change DRAFT → ACTIVE

---

## File Reference

### Scripts
- **`clean_clay_export.py`** - Transforms Clay CSV into tier-specific CSVs
- **`build_smartlead_campaigns.py`** - Creates campaigns via Smartlead API

### Data Files
- **`Clay_HVAC_export_11132025.csv`** - Raw export from Clay (27 columns)
- **`smartlead_imports/leads_a_tier.csv`** - A-tier leads (7 columns, clean)
- **`smartlead_imports/leads_b_tier.csv`** - B-tier leads
- **`smartlead_imports/leads_c_tier.csv`** - C-tier leads

### Configuration
- **`sequences_11_2025_appletree.txt`** - Email copy source
- **`build_smartlead_campaigns.py`** - Has hardcoded:
  - API key (line 19)
  - Email account IDs (line 23)
  - Calendly link (line 26)
  - Sequences with copy (lines 29-321)

---

## Reusing for Week 2+ Batches

### Scenario: 500 New Leads, Same Messaging

**Step 1:** Export from Clay (same format)

**Step 2:** Update input filename
```python
# In clean_clay_export.py, line 12:
INPUT_FILE = "Clay_HVAC_export_11202025.csv"  # New file
```

**Step 3:** Run both scripts
```bash
python3 clean_clay_export.py
python3 build_smartlead_campaigns.py
```

**Done.** New campaigns created in 5 minutes.

### Scenario: Different Messaging (New Sequences)

**Update sequences in `build_smartlead_campaigns.py` lines 29-321:**
```python
"sequences": [
    {
        "seq_number": 1,
        "delay_days": 0,
        "subject": "New subject line",
        "body": "New email body..."
    }
]
```

Then run script.

### Scenario: Different Email Accounts

**Update email account IDs in `build_smartlead_campaigns.py` line 23:**
```python
EMAIL_ACCOUNT_IDS = [12664159, 12663958, 12657708]  # Replace with new IDs
```

### Scenario: Different Daily Limits

**Update in `build_smartlead_campaigns.py` lines 31, 87, 143:**
```python
"max_leads_per_day": 20,  # Increase/decrease per tier
```

---

## What We Learned: MCP vs Direct API

### MCP Tools (Official Smartlead MCP Server)

**What we tested:**
- `mcp__smartlead__create_campaign` ❌ Always failed with 400 errors
- `mcp__smartlead__add_leads_to_campaign` ❌ Failed with 400 errors
- `mcp__smartlead__add_email_accounts_to_campaign` ✅ Worked once

**Problems:**
- Black box - no visibility into actual API calls
- Unclear error messages ("400" with no details)
- Parameters don't match API docs
- Appears to bundle multiple API calls into one (brittle)

**Debugging attempts:**
- Tested 20+ parameter combinations
- Tried minimal/maximal configs
- Attempted to replicate working campaign
- All failed consistently

**Conclusion:** MCP wrapper has bugs or expects different workflow than documented API.

### Direct API Calls (What Works)

**Approach:**
- Hit Smartlead REST API directly via `requests` library
- Full control over payload structure
- See exact error messages
- Can debug/iterate quickly

**Success rate:** 100% (except minor track_settings validation)

**Code quality:**
- ~400 lines of Python
- Well-documented functions
- Easy to modify/extend
- Reusable for future batches

**When to revisit MCP:**
- When official MCP server is updated/fixed
- When we need real-time integration (webhooks, live sync)
- When we want to use other MCP-enabled tools in same workflow

For now: **Direct API is the reliable path.**

---

## API Configuration Reference

### Smartlead API Key
```
38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8
```

**Where it's used:**
- `build_smartlead_campaigns.py` line 19
- Passed as `?api_key=` query param on all API calls

**Security:** Don't commit to public repos (already in `.gitignore`)

### Email Account IDs
```python
SMTP (Zoho):    12664159  # team@appletree-taxes.com
Outlook:        12663958  # team@appletree-advisors.com
Gmail:          12657708  # team@appletree-tax.com
```

**Sending capacity:**
- SMTP: 25/day
- Outlook: 15/day
- Gmail: 15/day
- **Total: 55/day** (we're using 28/day = 51% capacity)

**Warmup status:** All ACTIVE, 100% reputation

### Calendly Link
```
https://calendly.com/appletreepd/30min?month=2022-07
```

**Note:** URL has `?month=2022-07` which might be outdated. Consider:
- Removing date param: `https://calendly.com/appletreepd/30min`
- Adding UTM tracking: `?utm_source=email&utm_campaign=hvac_nov2025`

---

## Smartlead API Endpoints Used

### Campaign Management
```
POST /api/v1/campaigns/create
POST /api/v1/campaigns/{id}/leads
POST /api/v1/campaigns/{id}/email-accounts
POST /api/v1/campaigns/{id}/sequences
POST /api/v1/campaigns/{id}/schedule
POST /api/v1/campaigns/{id}/settings
```

### Rate Limits
- No official limit documented
- Script adds 1-2 second delays between calls
- Total runtime: ~30 seconds for 3 campaigns

### Authentication
- API key via query param: `?api_key={key}`
- All requests need `Content-Type: application/json`

---

## Troubleshooting

### Script fails: "No such file: Clay_HVAC_export_11132025.csv"
**Fix:** Update filename in `clean_clay_export.py` line 12

### Script fails: "Invalid API key"
**Fix:** Check API key in `build_smartlead_campaigns.py` line 19 (might have expired)

### Leads not importing: "Invalid email"
**Fix:** Verify `Verified (2)` column = `true` in Clay export. Script filters unverified automatically.

### Merge tags not working: Shows {{company}} in email
**Fix:**
- Verify custom fields mapped correctly in Smartlead UI
- Check CSV has `company`, `service_software`, `review_count` columns
- Send test email to verify

### Too many/few sends per day
**Fix:** Adjust `max_leads_per_day` in `build_smartlead_campaigns.py`

### Campaigns stuck in DRAFT
**Fix:** This is intentional. Change to ACTIVE in Smartlead UI when ready to launch.

---

## Week 1 Campaign Summary

### By The Numbers
- **151 verified leads** (from 202 scraped, filtered for email verification)
- **9 total email sequences** (4 + 3 + 2 across tiers)
- **3 email domains** rotating sends
- **28 max emails/day** (under 55/day capacity)
- **~450 total sends** over 4 weeks (Nov 18 - Dec 16)

### Lead Distribution
- **A-Tier (16 leads, 11%):** Housecall Pro/ServiceTitan users, high reviews
- **B-Tier (29 leads, 19%):** Growth signals (good reviews OR tech)
- **C-Tier (106 leads, 70%):** Smaller operators, pain-focused

### Messaging Strategy
- **A:** Tech sophistication + scale ("You're running ServiceTitan...")
- **B:** Growth phase ("You're clearly doing something right...")
- **C:** Pain points ("Can't get CPA on the phone...")

### Expected Results (Q4 Baseline)
- **Personal emails (85):** 3-5 replies, 1-2 meetings
- **Catchall emails (66):** 1-2 replies, 0-1 meetings
- **Total:** 4-7 replies, 1-3 meetings by end of December
- **"Talk in January" replies:** Expected and good (follow-up Jan 6)

---

## Next Steps After Launch

### Daily Monitoring (Week 1)
- Check Smartlead dashboard: opens/clicks/replies
- Verify send volume (should see 28 emails/day)
- Monitor bounce rate (should be <1% with verified emails)
- Forward positive replies to Patrick immediately

### Week 2-3: Tech-First Pivot
- Build new scraper targeting ServiceTitan/Jobber/HCP users
- Source methods:
  - Jobber public directory
  - ServiceTitan LinkedIn employee detection
  - Housecall Pro booking widget detection
- Target: 500-1k leads with FSM software
- Geography: Expand to CST (TX, CO, AZ)

### Week 4+: Scale & Optimize
- Analyze response rates by tier
- A/B test messaging strategies
- Adjust scoring weights based on conversion data
- Scale to 10k+ lead database

### January Re-Engagement
- Filter for "talk to me in January" replies
- Send follow-up on Jan 6, 2026:
  - "Reached out in November... heating season slammed you... still planning to stick with current CPA?"
- Convert warm leads to meetings

---

## Future Enhancements

### Potential Improvements (Not Urgent)
- [ ] Add webhook integration for real-time reply notifications
- [ ] Build dashboard for Patrick to see campaign metrics
- [ ] Re-scoring system when new enrichment data available
- [ ] A/B test scoring models (software = 20 pts vs 15 pts)
- [ ] Separate scoring logic for franchises vs independents
- [ ] Track which tier converts best, auto-adjust weights
- [ ] Calendly UTM tracking for attribution

### When to Revisit MCP
- [ ] Test updated Smartlead MCP server (if released)
- [ ] Integrate with other MCP tools (Clay, webhooks, CRM sync)
- [ ] Build real-time sync workflow (Clay → Smartlead ongoing)

---

## Key Takeaways

### What Worked
1. **Direct API approach** - Reliable, transparent, debuggable
2. **Tiered messaging** - Clear differentiation by sophistication
3. **Scoring-first workflow** - FastAPI → Clay → Smartlead clean pipeline
4. **Automated scripts** - 10 min setup, reusable for future batches

### What to Improve
1. **Data sourcing** - Tech-first from the start (not geography-first)
2. **Review count normalization** - Franchises skew high, separate scoring needed
3. **Franchise detection** - Better PE-backed vs owner-operator logic

### Critical Success Factors
- **Email verification** (99%+ accuracy prevents bounces)
- **Warmup domains** (1 month warming = good deliverability)
- **Conservative send limits** (28/day well under 55/day capacity)
- **DRAFT mode testing** (send to yourself before launching)

---

## Resources

- **Smartlead API Docs:** https://helpcenter.smartlead.ai/en/articles/125-full-api-documentation
- **FastAPI Scoring Docs:** See `README.md` for scoring logic
- **Campaign Copy Source:** `sequences_11_2025_appletree.txt`
- **Clay Integration:** See `CLAUDE.md` for HTTP API setup

---

**Last Updated:** November 13, 2025
**Next Review:** After Week 1 campaign results (Nov 18-25, 2025)
**Maintained by:** Claude + Shane (Appletree HVAC project)
