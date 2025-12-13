# Appletree HVAC Lead Pipeline

**Last Updated:** December 12, 2025 (A/B Test Campaigns Launched)

---

## ✅ CURRENT STATE - December 12, 2025

### New A/B Test Campaign Structure - ACTIVE

**Summary:** Launched 4-variant A/B test with 498 valid email leads. Old tier-based campaigns paused. Focus on testing message variants before scaling.

**Test Campaigns (All ACTIVE):**
| Campaign | ID | Leads | Max/Day | Status |
|----------|-----|-------|---------|--------|
| HVAC Test - M&A Variant | 2757801 | 125 | 25 | ✅ ACTIVE |
| HVAC Test - 35/100 Variant | 2757802 | 125 | 25 | ✅ ACTIVE |
| HVAC Test - Social Proof Variant | 2757804 | 125 | 25 | ✅ ACTIVE |
| HVAC Test - Direct Variant | 2757805 | 123 | 25 | ✅ ACTIVE |
| **TOTAL** | - | **498** | **100/day** | ✅ Running |

**Old Campaigns (PAUSED):**
| Campaign | ID | Status |
|----------|-----|--------|
| HVAC A-Tier - Software & Scale | 2677089 | ⏸️ PAUSED |
| HVAC B-Tier - Growth Signal | 2677090 | ⏸️ PAUSED |
| HVAC C-Tier - Pain Focus | 2677091 | ⏸️ PAUSED |

**Data Sync Status:**
| Metric | Count | Status |
|--------|-------|--------|
| Valid email leads | 498 | ✅ |
| `smartlead_lead_id` synced | 498 (100%) | ✅ |
| `smartlead_campaign_ids` tagged | 498 (100%) | ✅ |

**Email Infrastructure:**
| Mailbox | Provider | Daily Limit | Warmup |
|---------|----------|-------------|--------|
| team@appletree-taxes.com | Zoho SMTP | 40/day | 100% rep |
| team@appletree-advisors.com | Outlook | 35/day | 100% rep |
| team@appletree-tax.com | Gmail | 35/day | 100% rep |
| **TOTAL** | - | **110/day** | ✅ Ready |

**Timeline:**
- First touch all 498 leads: ~5 days at current rate
- With more inboxes (Monday): 2-3 days

---

## 📋 NEXT STEPS (Monday Priority)

### High Priority
1. **Add more inboxes** - Buy pre-warmed or set up new domains to push 200+/day
2. **Add more leads** - Keep pipeline full while tests run
3. **Monitor A/B test results** - Check which variant is winning after 2-3 days of data

### Medium Priority
4. **Analyze variant performance** - Opens, clicks, replies by campaign
5. **Double down on winner** - Shift volume to best-performing variant
6. **Scale infrastructure** - More domains, more sending capacity

### Lower Priority
7. **Re-activate old campaigns** - If test variants underperform originals
8. **Clean up Supabase** - Old campaign tracking data

---

## 📊 December 12 Work Summary

### Completed Today:
1. ✅ **Synced `smartlead_lead_id`** for all 498 valid leads (was 0% → now 100%)
2. ✅ **Tagged `smartlead_campaign_ids`** for all 498 leads
3. ✅ **Paused old A/B/C tier campaigns** (freeing up mailbox capacity)
4. ✅ **Updated test campaigns** to 25 leads/day each (100/day total)
5. ✅ **Activated 4 test campaigns** (manual activation in UI)

### Technical Details:
- Ran 15 SQL batch updates to sync Smartlead IDs from API → Supabase
- Used curl to fetch leads from Smartlead API (MCP pagination was limited)
- Updated campaign schedules via MCP API

---

## 🔥 PREVIOUS: December 10, 2025 Emergency Recovery

### Outscraper CSV Upload Status (Dec 7, 2025)

**Context:** We are in **PRE-TRIGGER.DEV phase** - manually uploading Outscraper leads and fixing data quality issues before automation. Trigger.dev implementation is complete but NOT YET ACTIVATED.

#### Upload Results

| Metric | Count | Rate |
|--------|-------|------|
| **CSV Source** | 569 leads | 100% |
| **Successfully Uploaded** | 509 leads | **89.5%** ✅ |
| **Failed/Missing** | 60 leads | **10.5%** ❌ |
| **Total in Supabase (all time)** | 977 leads | - |

**Source File:** `data/processed/outscraper_valid_deduped.csv`

#### 🚨 Critical Data Quality Issues

**1. Software Detection Failure (CRITICAL)**
- **Problem:** Used WRONG Railway software detection endpoint during upload
- **Correct endpoint:** `https://fastapi-production-85b6.up.railway.app/classify` ✅ (verified working)
- **Wrong endpoint used:** Different repo instance (now broken)
- **Impact:** Only 16/509 leads (3.1%) have software detected
  - ServiceTitan: 8 leads
  - Housecall Pro: 8 leads
  - Jobber: 0 leads
  - **Missing detection: 493 leads** ❌

**2. Tier Misclassification (MASSIVE IMPACT)**

Due to software detection failure, up to **345 leads are potentially in wrong tiers:**

| Current Tier | Count | Has Software | Could Be A-Tier | Could Be B-Tier |
|--------------|-------|--------------|-----------------|-----------------|
| A-Tier | 14 | 14 (100%) | - | - |
| B-Tier | 75 | 2 (2.7%) | **75 leads** 🚨 | - |
| C-Tier | 420 | 0 (0%) | **270 leads** 🚨 | **150 leads** 🚨 |

**Why This Matters:**
- Service software = +15 points in scoring
- B-tier leads with 5-19 points → Jump to A-tier (20-30) with software
- C-tier leads with 5-9 points → Jump to A-tier with software
- C-tier leads with 0-4 points → Jump to B-tier (10-19) with software

**3. Missing Deduplication Data (CRITICAL)**
- ❌ **place_id:** 0/509 populated (0%) - Cannot deduplicate future uploads!
- ❌ **site:** 0/509 populated (0%) - Cannot run enrichment
- ✅ **phone_number:** 508/509 populated (99.8%)
- ✅ **city/state:** 414/509 populated (81.3%)
- ✅ **Scoring logic:** 100% correct for existing data

**4. Schema Documentation Error**
- **CLAUDE.md says:** `phone` (TEXT)
- **Actual schema has:** `phone_number` (TEXT)
- This mismatch likely caused mapping errors during upload

#### Railway Endpoints (Verified Dec 8)

| Endpoint | URL | Status | Purpose |
|----------|-----|--------|---------|
| Scoring App | `https://hvac-scoring-2025-production.up.railway.app/` | ✅ Working | Calculate lead scores |
| Software Detection | `https://fastapi-production-85b6.up.railway.app/classify` | ✅ Working | Detect ServiceTitan/Jobber/Housecall Pro |

**Software Detection Test Results (Dec 8):**
- `totalcomfort.biz` → ServiceTitan detected (95% confidence) ✅
- `greentribehvac.com` → Housecall Pro detected (95% confidence) ✅
- `burkysmaintenance.com` → No software (50% confidence) ✅

#### Immediate Action Items

**Priority 1 - Software Detection Fix:**
1. Re-run software detection on 493 leads missing `service_software`
2. Use correct endpoint: `https://fastapi-production-85b6.up.railway.app/classify`
3. Update Supabase with detected software
4. Recalculate scores (+15 for software)
5. Update tiers based on new scores

**Priority 2 - Data Backfill:**
1. Populate `place_id` from CSV for all 509 leads (deduplication key)
2. Populate `site` from CSV for all 509 leads (website URL)
3. Fix schema documentation: `phone` → `phone_number`

**Priority 3 - Missing Leads:**
1. Identify which 60 leads failed to upload
2. Fix upload script field mappings
3. Retry upload for failed leads

#### Scoring Verification (Dec 8)

**Validation Results:** ✅ Scoring logic is 100% correct for data that exists

Sample verification:
- A-Tier leads: All have scores 21-27 (software detected + high reviews)
- B-Tier leads: Scores 12-17 (high reviews, most lack software)
- C-Tier leads: Scores 2-9 (low reviews, no software)

All calculated scores match actual scores exactly. The issue is NOT the scoring logic, but the missing software detection data.

---

## Current State

### Data Counts ✅ FIXED

| Location | Count | Notes |
|----------|-------|-------|
| Supabase `leads` | 463 | Source of truth (6 duplicates removed) |
| Smartlead campaigns | 468 | A: 167, B: 71, C: 230 |
| Supabase with `smartlead_lead_id` | 424 | **91.6%** linked ✅ |
| Supabase `in_smartlead=true` | 424 | Accurate (matches actual sync status) |
| All emails lowercase | 463 | 100% (CHECK constraint enforced) |

**Status:** ✅ Data integrity **excellent** - 91.6% ID coverage with email normalization and automated sync

### Tier Distribution (Supabase - Current)

| Tier | Count | in_smartlead | has_smartlead_id |
|------|-------|--------------|------------------|
| A | 57 | 56 | 56 (98.2%) |
| B | 87 | 76 | 76 (87.4%) |
| C | 319 | 282 | 282 (88.4%) |

**Note:** 39 leads without `smartlead_lead_id` are intentionally not yet synced to campaigns.

### Active Campaigns (Smartlead) - Nov 24 Audit

| Campaign | ID | Leads | Sent | Opens | Clicks | Replies |
|----------|-----|-------|------|-------|--------|---------|
| HVAC A-Tier - Software & Scale | 2677089 | 167 | 44 | 25 (56.8%) | 5 (11.4%) | 0 |
| HVAC B-Tier - Growth Signal | 2677090 | 71 | 47 | 31 (66.0%) | 9 (19.1%) | 0 |
| HVAC C-Tier - Pain Focus | 2677091 | 230 | 122 | 71 (58.2%) | 0 (0.0%) | 1 |
| **TOTAL** | - | **468** | **213** | **127** | **14** | **1** |

### Campaign Performance Summary

- **Overall Open Rate:** 59.6% (excellent - industry avg 15-25%)
- **Overall Click Rate:** 6.6%
- **Overall Reply Rate:** 0.5% (1 reply)
- **Bounce Rate:** 1.9% (4 bounces - healthy)
- **B-Tier outperforming:** 66% opens, 19.1% clicks
- **C-Tier issue:** 0 clicks despite 58% opens - investigate CTA

---

## Architecture

### Current (Trigger.dev Automation - Dec 2025)

```
Outscraper (Google Maps scraping)
  ↓ trigger.dev task
Supabase (leads table - raw data)
  ↓ trigger.dev task
Software Detection (website scraping)
  ↓ trigger.dev task
Scoring & Tiering (A/B/C assignment)
  ↓ trigger.dev task
Smartlead (email campaigns)
  ↓ webhooks → n8n
Supabase (analytics_events)
```

**Scheduled:** Weekly (Sundays 2 AM ET) via `weekly-pipeline` task

### Legacy (Clay Workflow - Pre-Dec 2025)

```
Clay (enrichment)
  ↓ HTTP API / webhook
Supabase (leads table - source of truth)
  ↓ manual sync
Smartlead (email campaigns)
  ↓ webhooks
Supabase (analytics_events)
```

### Supabase Schema (leads table)

| Column | Type | Purpose |
|--------|------|---------|
| `id` | UUID | Primary key (master identifier) |
| `email` | TEXT | Unique, indexed - fallback matching key (always lowercase ✅) |
| `place_id` | TEXT | **NEW** Outscraper Google Maps ID (unique, for deduplication) |
| `site` | TEXT | **NEW** Website URL (for software detection scraping) |
| `phone` | TEXT | **NEW** Phone number from Outscraper |
| `enriched_at` | TIMESTAMPTZ | **NEW** When software detection completed |
| `clay_id` | TEXT | Clay record ID (legacy, some null) |
| `smartlead_lead_id` | BIGINT | Smartlead internal ID (auto-written by sync script) |
| `company` | TEXT | Company name |
| `domain` | TEXT | Domain name |
| `city`, `state`, `postal_code` | TEXT | Location data |
| `reviews_count` | INTEGER | Google review count |
| `service_software` | TEXT | ServiceTitan/Jobber/Housecall Pro (detected in enrichment) |
| `tier` | TEXT | A/B/C classification |
| `score` | INTEGER | 0-30 points |
| `in_smartlead` | BOOLEAN | Sync flag (auto-updated by sync script) |
| `smartlead_campaign_ids` | INTEGER[] | Campaign IDs |
| `last_smartlead_sync` | TIMESTAMPTZ | Last sync time |
| `created_at`, `updated_at` | TIMESTAMPTZ | Timestamps |

**UUID Strategy:** Supabase UUID is the master identifier. `smartlead_lead_id` is automatically written back by `sync_smartlead_to_supabase.py`, enabling direct API operations and webhook correlation without email matching.

**Email Normalization:** All emails enforced to lowercase via:
- CHECK constraint: `email = LOWER(email)`
- `sync_lead_from_clay()` function normalizes on insert: `p_email := LOWER(TRIM(p_email))`

### Database Functions

- `sync_lead_from_clay()` - Upsert leads from Clay webhooks (auto-normalizes emails to lowercase)
- `sync_lead_to_smartlead(lead_id, smartlead_lead_id, campaign_id)` - Write back Smartlead ID after sync (deprecated - use sync script)
- `handle_smartlead_webhook(smartlead_lead_id, email, event_type, campaign_id, event_data)` - Process webhook events ✅
- `record_smartlead_event()` - Track engagement events (legacy - deprecated)
- `get_leads_for_campaign()` - Query ready leads by tier

### Analytics Views ✅ WORKING

- `campaign_performance`, `lead_performance`, `tier_performance` - Fixed to use correct event types
- `daily_activity_stats`, `leads_ready_for_campaigns`, `recent_replies`
- All views now showing real-time engagement data (fixed Nov 24)

---

## Scoring Logic

**Total possible: 30 points**

| Signal | Points |
|--------|--------|
| Service Software (ServiceTitan, Jobber, Housecall Pro) | +15 |
| Franchise match | +10 |
| Reviews 500+ | +10 |
| Reviews 100-499 | +7 |
| Reviews 25-99 | +4 |
| Reviews 10-24 | +2 |
| LinkedIn URL exists | +3 |
| Domain exists | +2 |

### Tier Thresholds

- **A-Tier:** 20-30 points
- **B-Tier:** 10-19 points
- **C-Tier:** 0-9 points

---

## Email Infrastructure

### Domains

| Domain | SPF Record |
|--------|------------|
| appletree-tax.com | `v=spf1 include:_spf.google.com include:_spf.porkbun.com include:_spf.smartlead.ai ~all` |
| appletree-advisors.com | `v=spf1 include:_spf.porkbun.com include:_spf.smartlead.ai ~all` |
| appletree-taxes.com | `v=spf1 include:zohomail.com include:_spf.porkbun.com include:_spf.smartlead.ai ~all` |

### Campaign Settings

| Setting | Value |
|---------|-------|
| Send hours | 08:30-17:00 ET |
| Send days | Mon-Fri |
| Max leads/day (A) | 30 |
| Max leads/day (B) | 25 |
| Max leads/day (C) | 30 |

---

## Suppression

### Canopy Client List

- File: `canopy_client_list_appletree.csv`
- 865 entries (Patrick's existing clients)
- 14 trades-related businesses identified
- **0 exact matches** with HVAC leads
- No suppression required

### Scripts

- `scripts/suppression/check_trades_overlap.py` - Trades-only exact match check

---

## Key Scripts

### Smartlead (`scripts/smartlead/`)

| Script | Purpose |
|--------|---------|
| `build_smartlead_campaigns.py` | Create tiered campaigns with sequences |
| `sync_smartlead_to_supabase.py` | ✅ Pull leads from Smartlead + auto-write smartlead_lead_id |
| `check_campaign_health.py` | Diagnostic: status, limits, accounts |
| `check_deliverability.py` | Pre-launch DNS/SPF audit |
| `get_campaign_analytics.py` | Pull engagement metrics |
| `update_send_limits.py` | Adjust daily limits |
| `enable_click_tracking.py` | Re-enable tracking on active campaigns |

### Supabase (`scripts/supabase/`)

| Script | Purpose |
|--------|---------|
| `audit_data_quality.py` | Lead data quality audit |
| `update_smartlead_ids.py` | ✅ One-time CSV backfill (now automated via sync script) |

### Analytics (`scripts/analytics/`)

| Script | Purpose |
|--------|---------|
| `backfill_analytics_events.py` | Backfill historical events from Smartlead (ready if needed) |

---

## Data Files

### Processed (`data/processed/`)

| File | Count |
|------|-------|
| `leads_a_tier.csv` | 16 |
| `leads_b_tier.csv` | 29 |
| `leads_c_tier.csv` | 106 |

### Raw (`data/raw/`)

- `HVAC Nov 2025 Appletree - HVAC_draft_appletree_112025.csv` - Original 202 leads
- `Clay_HVAC_export_11132025.csv` - Clay enrichment export

---

## MCP Integration

### Available MCPs (`.mcp.json`)

| MCP | Purpose |
|-----|---------|
| `supabase` | Database queries via `mcp__supabase__execute_sql` |
| `smartlead` | Campaign/lead management via Smartlead API |
| `n8n-mcp` | Workflow node documentation |

---

## Known Issues

1. ~~**No smartlead_lead_id on leads table**~~ - FIXED: Column added as BIGINT
2. ~~**n8n workflow failing**~~ - FIXED Nov 24: Switched to `handle_smartlead_webhook()` function
3. ~~**Data integrity issue**~~ - FIXED: 91.6% coverage (424/463), email normalization + automated sync
4. ~~**Analytics views broken**~~ - FIXED: Updated to use correct event types, now showing real data
5. ~~**analytics_events missing history**~~ - RESOLVED Nov 29: Gap documented (137 events), backfill not pursued, real-time tracking operational
6. **C-Tier zero clicks** - 122 emails sent, 58% opens, 0 clicks - CTA/link issue? (Monitor ongoing)
7. **campaign_tracking redundant columns** - All 319 records have NULL smartlead_lead_id/smartlead_lead_map_id - recommend cleanup
8. **Tier misalignment in campaigns** - Some leads in wrong tier campaigns (1 B in A-Tier, 14 C in B-Tier) - investigate assignment logic

### n8n Workflow Status

**Status:** ✅ OPERATIONAL (Fixed Nov 24, 2025)

**Changes Made:**
1. Updated "Parse Smartlead Event" code node to read correct fields (`to_email`, `sl_email_lead_id`, `subject`)
2. Switched HTTP endpoint from `record_smartlead_event` to `handle_smartlead_webhook`
3. Updated event type constraint to accept Smartlead formats (`EMAIL_LINK_CLICK`, etc.)

**Webhook URL:** `https://shanef.app.n8n.cloud/webhook/smartlead-events`

**Events now tracked:**
- EMAIL_SENT, EMAIL_OPENED, EMAIL_LINK_CLICK, EMAIL_REPLIED
- EMAIL_BOUNCED, EMAIL_UNSUBSCRIBED, EMAIL_SPAM_COMPLAINT

### Event Tracking Gap (Historical Only) - Nov 29 Audit

**Current Supabase Events (Real-time Tracking Active):**

| Campaign | Tier | SENT | OPEN | CLICK | Total |
|----------|------|------|------|-------|-------|
| 2677089 | A-Tier | 27 | 25 | 15 | **67** |
| 2677090 | B-Tier | 72 | 42 | 12 | **126** |
| 2677091 | C-Tier | 56 | 34 | 0 | **90** |
| **TOTAL** | - | **155** | **101** | **27** | **283** |

**Smartlead Reported Stats (Nov 17 - Nov 29):**

| Campaign | Tier | Total Stats* | Gap |
|----------|------|-------------|-----|
| 2677089 | A-Tier | 83 | ~16 events |
| 2677090 | B-Tier | 130 | ~4 events |
| 2677091 | C-Tier | 207 | ~117 events |
| **TOTAL** | - | **420** | **~137 events** |

*Note: "Total Stats" represents individual email sends tracked in Smartlead

**Status:** ✅ Webhook operational - tracking all new events in real-time since Nov 24
**Cause:** n8n was broken Nov 17-24 (7-day gap)
**Decision:** Accepted current state - backfill not pursued due to API timestamp limitations

### Backfill Analysis (Nov 29, 2025)

**Smartlead API Limitation Discovered:**
- API provides aggregate counts (`open_count: 3`) but NOT individual event timestamps
- Only `sent_time` available, meaning backfilled events would have approximate timestamps
- Time-series analytics would be inaccurate for backfilled period

**Decision: Option 1 - Accept Current State** ✅
- Real-time tracking now operational (fixed Nov 24)
- All future events have accurate timestamps
- Historical gap is only 7 days (Nov 17-24)
- Cost/benefit doesn't justify approximate timestamp backfill
- Gap documented as known limitation

**Alternative Options Not Pursued:**
- Option 2: Partial backfill with approximate timestamps
- Option 3: Manual reconciliation

**Reference:** See `/docs/analytics_backfill_report.md` for complete analysis

---

## API Endpoints

### Railway (Lead Scoring)

- URL: `https://hvac-scoring-2025-production.up.railway.app/score-lead`
- Method: POST
- Used by Clay HTTP API column

### Smartlead API

- Key: `38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8`
- Base: `https://server.smartlead.ai/api/v1`

---

## Current Work (In Progress)

### 🔄 December 7-8, 2025 Lead Batch - Smartlead Sync
**Status:** ⚡ IN PROGRESS - 37/509 leads synced (7%)
**Last Updated:** December 8, 2025

**Summary:**
Processing and syncing 509 new Dec 7 leads through software detection → scoring → tier assignment → Smartlead campaigns.

**Progress:**
1. ✅ **Software Detection Complete** - All 509 leads processed
   - Batches 1-15: 42 software detections from ~650 leads (6.5%)
   - Batches 16-25: 1 software detection from 467 leads (0.21%)
   - **Total: 43 software users found (8.4% overall)**
     - ServiceTitan: 16
     - Housecall Pro: 25
     - Jobber: 2

2. ✅ **Tier Assignment Complete** - All leads properly tiered
   - A-tier: 37 leads (all have software)
   - B-tier: 72 leads (6 with software, 66 high-review-count)
   - C-tier: 400 leads (no software)

3. ⚡ **Smartlead Sync - IN PROGRESS**
   - ✅ A-Tier: **37/37 uploaded** to campaign 2677089
   - ⏳ B-Tier: **0/72 remaining** (campaign 2677090)
   - ⏳ C-Tier: **0/400 remaining** (campaign 2677091)

**Next Steps:**
- Export B and C tier leads to JSON/CSV
- Run upload scripts for remaining 472 leads
- Verify all leads appear in correct campaigns
- Mark `in_smartlead=true` in Supabase for synced leads

**Scripts Created:**
- `/tmp/upload_a_tier_leads.py` - ✅ Successfully uploaded 37 A-tier leads
- `/tmp/sync_remaining_leads.py` - Ready for B/C tier upload (needs DATABASE_URL)

---

### ⚡ Trigger.dev Automation - Weekly Lead Pipeline
**Status:** ✅ Implemented, ⏳ Not Tested Yet (On Hold - Manual Processing Active)
**Last Updated:** December 6, 2025

**Summary:**
Complete automation system to replace manual Clay workflow. Bypasses Clay entirely - Outscraper → Supabase → Enrichment → Scoring → Smartlead.

**Architecture:**
```
Outscraper (Google Maps scrape)
  ↓
Supabase (raw leads with place_id)
  ↓
Software Detection (scrape websites for ServiceTitan/Jobber/Housecall Pro)
  ↓
Scoring & Tiering (A/B/C based on signals)
  ↓
Smartlead Campaigns (auto-sync by tier)
```

**Tasks Implemented:**
1. **weekly-scrape** - Scrape 9 Northeast states via Outscraper, dedupe by place_id
2. **enrich-leads** - Detect FSM software from websites (10s timeout per site)
3. **score-leads** - Apply scoring logic (A: 20-30, B: 10-19, C: 0-9 points)
4. **sync-to-smartlead** - Push to appropriate campaigns (2677089/2677090/2677091)
5. **weekly-pipeline** - Orchestrator scheduled for Sundays 2 AM ET

**Key Features:**
- Handles ~1800 leads per week (200 per state × 9 states)
- Batch processing (50 for enrichment, 100 for scoring/sync)
- Retry logic + graceful error handling
- Detailed structured logging

**Schema Updates Made:**
- Added `place_id` (TEXT, UNIQUE) - Outscraper deduplication key
- Added `site` (TEXT) - Website URL for scraping
- Added `enriched_at` (TIMESTAMPTZ) - Track enrichment status
- Added `phone` (TEXT) - Contact info from Outscraper

**Files:**
- Implementation: `src/trigger/` (5 tasks + 4 utilities)
- Documentation: `docs/TRIGGER_TASKS.md`
- Config: `trigger.config.ts`, `.env.example`

**Next Steps:**
1. Add `OUTSCRAPER_API_KEY` to environment variables
2. Test individual tasks via `npx trigger.dev@latest dev`
3. Test full pipeline with small sample (1 state, 10 leads)
4. Deploy to trigger.dev cloud
5. Monitor first scheduled run (Sunday 2 AM ET)

---

## Pending Work

### High Priority

1. **Investigate C-Tier zero clicks** - 122 emails sent, 58% opens, 0 clicks - check CTA/link formatting
2. **Follow up on 11 Calendly clickers** - High-intent prospects who engaged
3. **Investigate tier misalignment** - 1 B-Tier lead in A-Tier campaign, 14 C-Tier leads in B-Tier campaign

### Medium Priority

4. **Fix personalization gaps** - Audit found blank fields in some emails (missing first_name, review count)
5. **Sync remaining 39 leads** - 9 B-Tier, 30 C-Tier not yet in Smartlead campaigns
6. **Update `campaign_tracking` records** - Change 319 PENDING records to actual status
7. **Monitor webhook stability** - Spot check daily to ensure events still flowing

### Lower Priority

8. **Remove redundant `campaign_tracking` columns** - `smartlead_lead_id`, `smartlead_lead_map_id` both 100% NULL
9. **Fix `campaign_tracking.smartlead_lead_id` column type** - INTEGER → BIGINT (if not removed)

### ✅ Completed (Nov 24-29, 2025)

- ~~Reconcile `smartlead_lead_id`~~ - **DONE Nov 24:** 91.6% coverage (424/463)
- ~~Fix `in_smartlead` flag~~ - **DONE Nov 24:** Now accurate
- ~~Email normalization~~ - **DONE Nov 24:** All lowercase + CHECK constraint
- ~~Fix analytics views~~ - **DONE Nov 24:** Updated event types
- ~~Fix n8n webhook~~ - **DONE Nov 24:** Operational
- ~~Fix sync script~~ - **DONE Nov 24:** Auto-writes smartlead_lead_id
- ~~Backfill historical analytics_events~~ - **DONE Nov 29:** Audit complete, gap documented, decision made (accept current state)
- ~~Audit Supabase database~~ - **DONE Nov 29:** Complete integrity validation, excellent data quality

---

## Nov 24 Audit Findings

### Smartlead Audit Highlights

- **B-Tier is top performer:** 66% open rate, 19.1% click rate
- **11 unique Calendly link clickers** - high-intent leads
- **Zero unsubscribes** across 213 emails
- **1.9% bounce rate** - healthy deliverability
- **Personalization issues found:** Some emails sent with blank merge fields

### Supabase Audit Highlights

- **RLS enabled** on all tables (security OK)
- **Indexes in place** (30 total)
- **Foreign keys with CASCADE** working correctly
- ~~**Views exist** but show zeros~~ - **FIXED:** Now showing real-time engagement data
- **Email normalization** enforced via CHECK constraint
- **Data integrity** excellent at 91.6% smartlead_lead_id coverage

---

## Nov 29 Comprehensive Database Audit

### Audit Scope

**Tables Audited:**
- `leads` (463 records)
- `analytics_events` (283 records)
- `campaign_tracking` (319 records)
- `sequence_templates` (6 records)
- `campaigns` (3 records)

**Functions Validated:**
- `sync_lead_from_clay()` ✅
- `handle_smartlead_webhook()` ✅
- `get_leads_for_campaign()` ✅

**Views Validated:**
- `campaign_performance` ✅
- `lead_performance` ✅
- `tier_performance` ✅
- `daily_activity_stats` ✅

### Key Findings

**✅ Excellent Data Integrity:**
1. **RLS Policies:** Enabled on all tables
2. **Indexes:** 30 total indexes properly configured
3. **Foreign Keys:** All with CASCADE, no orphaned records found
4. **Email Normalization:** 100% lowercase via CHECK constraint
5. **Smartlead ID Coverage:** 91.6% (424/463 leads)

**⚠️ Issues Identified:**

1. **campaign_tracking table:**
   - 319 records all with status "PENDING"
   - `smartlead_lead_id` column: 100% NULL
   - `smartlead_lead_map_id` column: 100% NULL
   - **Action:** Remove redundant columns or populate from sync

2. **Tier misalignment:**
   - 1 B-Tier lead found in A-Tier campaign (2677089)
   - 14 C-Tier leads found in B-Tier campaign (2677090)
   - **Action:** Investigate assignment logic and campaign targeting

3. **C-Tier zero clicks:**
   - 122 emails sent, 58% open rate, 0 clicks tracked
   - May be real (no clicks yet) or tracking issue
   - **Action:** Monitor going forward, check CTA/link formatting

### Analytics Gap Resolution

**Gap Identified:** 137 missing events from Nov 17-24 webhook downtime
- A-Tier: ~16 events
- B-Tier: ~4 events
- C-Tier: ~117 events

**Root Cause:** n8n webhook was broken Nov 17-24 (incorrect field parsing)

**Resolution:** Accept current state
- Webhook now operational (fixed Nov 24)
- Real-time tracking working correctly
- Historical gap documented as known limitation
- Smartlead API limitation: only aggregate counts, no individual event timestamps
- Cost/benefit doesn't justify approximate timestamp backfill

**Reference:** See `/docs/analytics_backfill_report.md` for complete analysis

### Deliverables

**Scripts Created:**
- `/scripts/analytics/backfill_analytics_events.py` - Ready if backfill needed in future
**Documentation Created:**
- `/docs/analytics_backfill_report.md` - Comprehensive audit and gap analysis

RULE: ONLY UTILIZE SUBAGENTS WHEN WORKING WITH MCP (SUPABASE, SMARTLEAD, ETC)dam