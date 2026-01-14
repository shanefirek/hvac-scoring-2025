# Infrastructure Audit - December 10, 2025

## Executive Summary

**STATUS: CRITICAL - COMPLETE ATTRIBUTION LOSS**

The December 10th data restoration has resulted in **complete loss of Smartlead attribution**. While 850 leads are now in Supabase, we've lost all connection to the 853 active leads in Smartlead campaigns that have been running since November 13th.

---

## Current State Analysis

### 🔴 Supabase Database (Restored Dec 10, 2025)

**Total Leads:** 850
- A-Tier: 98 leads
- B-Tier: 134 leads
- C-Tier: 618 leads

**Critical Issues:**
- ❌ **ZERO** leads have `clay_id` (all NULL)
- ❌ **Only 1** lead has `smartlead_lead_id` (likely test data)
- ❌ **ZERO** leads have `in_smartlead=true` flag
- ❌ **ZERO** leads have `smartlead_campaign_ids` populated
- ❌ **Only 2** events in `analytics_events` table (was 283+ before)
- ✅ Email normalization working (all lowercase)
- ✅ Schema intact with all columns
- ✅ Proper indexes and constraints

**Data Source:** `/data/raw/HVAC_clay_validated_manual_12_10_2025.csv`
- Manually validated in Clay
- No `clay_id` column in CSV
- No `smartlead_lead_id` in CSV (except 1 lead)
- Fresh UUIDs generated on insert (disconnected from old data)

---

### 🟢 Smartlead Campaigns (Running Since Nov 13)

**Active Campaigns:**
1. **A-Tier (ID: 2677089)** - "Software & Scale"
   - Total Leads: 97 (vs 98 in Supabase)
   - Status: ACTIVE
   - Leads have `custom_fields`: tier, domain, review_count, service_software
   - Smartlead IDs: 2945804626-2945804692 range

2. **B-Tier (ID: 2677090)** - "Growth Signal"
   - Total Leads: 143 (vs 134 in Supabase)
   - Status: ACTIVE
   - 9 extra leads not in Supabase

3. **C-Tier (ID: 2677091)** - "Pain Focus"
   - Total Leads: 613 (vs 618 in Supabase)
   - Status: ACTIVE
   - 5 leads in Supabase not in Smartlead

**Total in Smartlead:** 853 leads across active campaigns

**Sample Lead Structure (Smartlead):**
```json
{
  "id": 2945804648,
  "email": "timmy@moderntempcontrol.com",
  "first_name": "Timothy",
  "last_name": "Donahue",
  "company_name": "Modern Temperature Control",
  "custom_fields": {
    "tier": "A",
    "domain": "moderntempcontrol.com",
    "reviews_count": "78",
    "service_software": "Housecall Pro"
  }
}
```

---

### 🟡 Clay Integration

**Status:** DISCONNECTED

**Available Scripts:**
- `scripts/clay/sync_clay_validated_to_supabase.py` - Manual sync script
  - Reads CSV export from Clay
  - Deletes ALL existing Supabase leads
  - Inserts fresh data from Clay
  - **Last used:** December 10, 2025 (caused current state)

**Clay Workflow (Legacy):**
1. Clay enriches leads (service software detection, scoring)
2. Manual CSV export from Clay
3. Run `sync_clay_validated_to_supabase.py`
4. Leads land in Supabase with NO `clay_id`

**Problem:** No webhook integration, no real-time sync, no Clay record IDs preserved

---

## Attribution Gap Analysis

### What We Lost

1. **Smartlead Lead IDs:** Cannot correlate Supabase leads to Smartlead campaign leads
   - Old data: 424/463 leads had `smartlead_lead_id` (91.6% coverage)
   - New data: 1/850 leads have `smartlead_lead_id` (0.1% coverage)

2. **Clay Record IDs:** Cannot trace leads back to Clay tables
   - Old data: Some leads had `clay_id`
   - New data: 0/850 leads have `clay_id`

3. **Analytics Events:** Lost all historical engagement tracking
   - Before: 283 events (EMAIL_SENT, EMAIL_OPENED, EMAIL_LINK_CLICK)
   - After: 2 events (likely test data)

4. **Campaign Assignment:** Cannot determine which campaign a lead belongs to
   - `smartlead_campaign_ids` array is empty for all leads
   - `in_smartlead` flag is false for all leads

### Email Matching Strategy (Current Fallback)

**Can Match:** Email is unique in both systems
- Supabase: 850 unique emails (constraint enforced)
- Smartlead: 853 unique emails across campaigns

**Risks:**
- Email changes in either system break the link
- No validation that email matches are correct tier
- Cannot detect if lead moved between campaigns

---

## Schema Analysis

### Supabase `leads` Table (34 columns)

**Unique Constraints:**
- `id` (UUID) - Primary key
- `email` (TEXT) - Unique, lowercase enforced
- `clay_id` (TEXT) - Unique but ALL NULL
- `smartlead_lead_id` (BIGINT) - Unique but 1/850 populated
- `place_id` (TEXT) - Unique (Outscraper ID for deduplication)

**Critical Columns for Attribution:**
```sql
clay_id                  TEXT       -- ❌ ALL NULL
smartlead_lead_id        BIGINT     -- ❌ 1/850 populated
smartlead_campaign_ids   INTEGER[]  -- ❌ ALL empty arrays
in_smartlead             BOOLEAN    -- ❌ ALL false
last_smartlead_sync      TIMESTAMP  -- ❌ ALL NULL
```

**Indexes:** 13 total (well-optimized)
- Unique index on `smartlead_lead_id` (WHERE NOT NULL)
- Unique index on `clay_id` (WHERE NOT NULL)
- Email, tier, location indexes present

---

## Data Flow Comparison

### Original Flow (Nov 2024 - Working)

```
Clay (enrichment)
  ↓ webhook with clay_id
Supabase (leads with clay_id)
  ↓ sync_smartlead_to_supabase.py
Smartlead (campaigns with leads)
  ↓ auto-write smartlead_lead_id back
Supabase (leads with both IDs)
  ↓ webhooks
n8n → analytics_events
```

**Attribution:** ✅ 91.6% coverage via `smartlead_lead_id`

### Current Flow (Dec 10, 2025 - Broken)

```
Clay (manual enrichment)
  ↓ CSV export (no clay_id)
Supabase (DELETE ALL, fresh insert)
  ↓ NO SYNC
Smartlead (853 orphaned leads)
  ↓ webhooks broken
Supabase (0 attribution)
```

**Attribution:** ❌ 0% coverage

---

## Root Cause Analysis

### Timeline of Failure

1. **November 13, 2024:** Original campaigns launched with 463 leads
   - Leads synced properly with `smartlead_lead_id`
   - Analytics tracking via webhooks working

2. **November 17-24, 2024:** n8n webhook failure
   - 137 events lost during 7-day outage
   - Fixed Nov 24, tracking resumed

3. **November-December 2024:** Campaign growth
   - Leads increased from 463 → 853 in Smartlead
   - Supabase became corrupted (977 leads with duplicates)

4. **December 10, 2025:** Manual restoration attempt
   - Exported 850 leads from Clay (manually validated)
   - Used `sync_clay_validated_to_supabase.py` to WIPE and reload
   - **Lost all `clay_id` values** (not in CSV export)
   - **Lost all `smartlead_lead_id` values** (not synced)
   - **Lost all analytics events** (deleted with leads)

### The Critical Mistake

**Script: `sync_clay_validated_to_supabase.py:122-123`**
```python
# ⚠️ DESTRUCTIVE OPERATION
supabase.table('leads').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
```

This deleted:
- All existing lead records (with attribution)
- All foreign key relationships to `analytics_events`
- All `clay_id` and `smartlead_lead_id` mappings

**Should have used:** UPSERT by email instead of DELETE ALL

---

## Recovery Options

### Option 1: Email-Based Re-Sync (RECOMMENDED)

**Strategy:** Match Supabase ↔ Smartlead by email, write back IDs

**Steps:**
1. Pull all leads from Smartlead campaigns (2677089, 2677090, 2677091)
2. Match by email (lowercase) to Supabase leads
3. Write `smartlead_lead_id` back to Supabase
4. Set `in_smartlead=true` and `smartlead_campaign_ids`
5. Verify tier alignment

**Expected Coverage:** ~840/850 matches (98%)
- A-Tier: 97/98 (1 mismatch)
- B-Tier: 134/143 (9 extra in Smartlead)
- C-Tier: 613/618 (5 extra in Supabase)

**Risks:**
- Tier misalignment (some leads in wrong campaigns)
- Cannot recover lost analytics events
- Cannot recover original `clay_id`

**Script to Create:** `scripts/recovery/rebuild_attribution_from_email.py`

---

### Option 2: Restore from Backup (IF AVAILABLE)

**Strategy:** Restore Supabase to state before Dec 10

**Requirements:**
- Supabase backup from Dec 9 or earlier
- Must contain leads with `smartlead_lead_id` populated

**Benefits:**
- Recovers all attribution
- Recovers analytics events
- Recovers `clay_id` if it existed

**Drawbacks:**
- Loses any manual validation done in Clay
- May restore corrupted data (977 leads)

---

### Option 3: Rebuild from Clay + Smartlead (CLEAN SLATE)

**Strategy:** Treat Smartlead as source of truth, pull fresh

**Steps:**
1. Pull all 853 leads from Smartlead with full details
2. Enrich missing fields from Supabase CSV (by email match)
3. Create new Supabase records with proper attribution
4. Set up Clay webhook integration for future

**Benefits:**
- Clean, accurate data
- Full attribution from Smartlead
- Fixes tier misalignment

**Drawbacks:**
- Most time-intensive
- Requires Clay webhook setup
- Loses any Supabase-only leads

---

## Recommended Actions (Priority Order)

### IMMEDIATE (Today)

1. **Run Email-Based Re-Sync** (Option 1)
   - Create `scripts/recovery/rebuild_attribution_from_email.py`
   - Match by email, write back `smartlead_lead_id`
   - Restore `in_smartlead` flags and campaign IDs
   - Verify tier alignment

2. **Audit Tier Misalignment**
   - Check if leads in Smartlead match their Supabase tier
   - Document any tier changes needed

3. **Document Data Gaps**
   - List 9 B-Tier leads in Smartlead not in Supabase
   - List 5 C-Tier leads in Supabase not in Smartlead
   - List 1 A-Tier lead mismatch

### SHORT-TERM (This Week)

4. **Fix Clay Integration**
   - Set up Clay webhook to write `clay_id` on insert
   - Use `sync_lead_from_clay()` function instead of delete-all script
   - Test webhook with 5 test leads

5. **Prevent Future Data Loss**
   - Archive `sync_clay_validated_to_supabase.py` (rename to `.bak`)
   - Update CLAUDE.md with DO NOT DELETE warning
   - Create proper upsert script that preserves IDs

6. **Analytics Recovery Assessment**
   - Determine if webhook events can backfill missing data
   - Document acceptable loss (Dec 10 forward only)

### LONG-TERM (Next 2 Weeks)

7. **Implement Proper Clay → Supabase Flow**
   - Clay table webhook → `sync_lead_from_clay()` function
   - Real-time sync with `clay_id` preservation
   - No manual CSV exports

8. **Add Backup Strategy**
   - Daily Supabase backups (retain 30 days)
   - Pre-sync snapshot before any destructive operations
   - Document restore procedure

9. **Rebuild Analytics Pipeline**
   - Verify n8n webhook still functional
   - Backfill what we can from Smartlead API
   - Accept Dec 10 data loss

---

## Technical Debt Created

1. **No Clay Record IDs:** Cannot correlate to Clay tables
2. **Incomplete Analytics:** Lost 281 events from Dec 10 deletion
3. **Tier Misalignment:** Leads in wrong campaigns need investigation
4. **Lead Count Discrepancies:** 850 vs 853 needs reconciliation
5. **Fragile Email Matching:** Single point of failure for attribution

---

## Files Modified/Created

**Restoration Scripts (Dec 10):**
- `/tmp/restore_via_psycopg2.py` - PostgreSQL direct restore
- `/tmp/fix_sql_apostrophes.py` - SQL escaping fixes
- `/tmp/restore_batch_[1-17].sql` - 17 SQL batch files

**Existing Scripts:**
- `scripts/clay/sync_clay_validated_to_supabase.py` - ⚠️ DANGEROUS (deletes all)
- `scripts/smartlead/sync_smartlead_to_supabase.py` - Not run during restore

**To Create:**
- `scripts/recovery/rebuild_attribution_from_email.py` - Email-based re-sync
- `scripts/clay/upsert_clay_leads.py` - Safer alternative to delete-all

---

## Conclusion

We successfully restored **850 leads** to Supabase, but lost **all attribution** to the 853 active Smartlead campaign leads. The use of a destructive sync script (`sync_clay_validated_to_supabase.py`) wiped critical linking data (`clay_id`, `smartlead_lead_id`) that connected systems.

**Immediate Priority:** Rebuild attribution via email matching to restore the connection between Supabase and Smartlead campaigns.

**Long-term Fix:** Implement proper Clay webhook integration and deprecate destructive sync scripts.

---

Generated: December 10, 2025
