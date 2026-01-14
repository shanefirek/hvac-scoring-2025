# Database Architecture Audit

**Date:** November 24, 2025
**Project:** Appletree HVAC Lead Pipeline
**Status:** CRITICAL ISSUES IDENTIFIED

---

## Executive Summary

The database has **structural integrity issues** stemming from inconsistent ID management across tables. The core problem: **`smartlead_lead_id` is not being used as the linking key it was designed to be**, causing tables to be disconnected and analytics to fail.

### The ID Problem (Your Observation)

You correctly identified the issue: **We have 4 ID fields when we should only need 3.**

| ID Field | Purpose | Current State |
|----------|---------|---------------|
| `id` (UUID) | Supabase master identifier | Working correctly |
| `clay_id` | Upstream enrichment tracking | 94% populated (442/469) |
| `smartlead_lead_id` | Downstream campaign tracking | **38% populated (181/469)** |
| `lead_id` (in campaign_tracking) | FK reference to leads.id | Redundant with proper smartlead_lead_id |

**The root cause:** When leads are added to Smartlead campaigns, the `smartlead_lead_id` is not being written back to Supabase. This breaks the entire downstream data flow.

---

## Current State

### Record Counts

| Table | Records | Notes |
|-------|---------|-------|
| `leads` | 469 | Source of truth |
| `campaign_tracking` | 320 | 68% of leads tracked |
| `campaigns` | 3 | A/B/C tier campaigns |
| `analytics_events` | 8 | **Should be ~200+** |
| `sequence_templates` | 9 | Working correctly |

### The Disconnect

```
INTENDED FLOW:
Clay → leads.clay_id → leads.id → smartlead_lead_id → campaign_tracking → analytics_events
         ↓                              ↓                    ↓                    ↓
      94% OK                        38% BROKEN           NOT LINKED           8 RECORDS

ACTUAL STATE:
- leads.smartlead_lead_id: Only 181/469 populated
- campaign_tracking.smartlead_lead_id: 0/320 populated (ALL NULL)
- analytics_events.smartlead_lead_id: Partially populated
- Everything relying on smartlead_lead_id joins: BROKEN
```

---

## Table-by-Table Analysis

### 1. `leads` Table (469 records)

**Primary Key:** `id` (UUID, auto-generated)

**External IDs:**
| Column | Type | Populated | Purpose |
|--------|------|-----------|---------|
| `clay_id` | TEXT | 442 (94%) | Clay enrichment reference |
| `smartlead_lead_id` | BIGINT | 181 (38%) | Smartlead internal ID |
| `email` | TEXT | 469 (100%) | Unique, fallback match key |

**Flag Issue:**
- `in_smartlead = true`: 469 (100%)
- Actually in campaigns: 320 (68%)
- **149 leads marked "in smartlead" but aren't**

### 2. `campaign_tracking` Table (320 records)

**The ID Redundancy You Identified:**

| Column | Type | Purpose | Issue |
|--------|------|---------|-------|
| `id` | UUID | Row identifier | Fine, but rarely needed |
| `lead_id` | UUID | FK to leads.id | Works, but indirect |
| `smartlead_lead_id` | INTEGER | Direct Smartlead link | **100% NULL** |
| `smartlead_lead_map_id` | INTEGER | Smartlead mapping ID | **100% NULL** |

**Why This Is Overkill:**

The table has 4 ID-related columns:
1. `id` - unique row ID (standard, fine)
2. `lead_id` - FK to leads table (necessary for joins)
3. `smartlead_lead_id` - **should be the primary link** but empty
4. `smartlead_lead_map_id` - additional Smartlead reference, also empty

**The intended design:** Use `smartlead_lead_id` as the primary key for Smartlead operations. But since it's never populated, we fall back to `lead_id` → `leads.smartlead_lead_id` joins, which are also broken because `leads.smartlead_lead_id` is only 38% populated.

### 3. `analytics_events` Table (8 records)

**Should have ~200+ records** based on Smartlead activity (213 sends, 127 opens, 14 clicks, 1 reply).

| Column | Type | Purpose | Status |
|--------|------|---------|--------|
| `lead_id` | UUID | FK to leads | Working |
| `smartlead_lead_id` | BIGINT | Direct Smartlead link | Partially populated |
| `campaign_tracking_id` | UUID | FK to campaign_tracking | Working |

**Why only 8 events?**
- n8n webhook was broken Nov 17-24
- Events are now flowing but historical data wasn't captured
- The `smartlead_lead_id` in events doesn't match leads table in many cases

### 4. `campaigns` Table (3 records)

This table is fine. Clean design:
- `id` (UUID) - Supabase identifier
- `smartlead_campaign_id` (INTEGER) - Smartlead reference

---

## The Core Architecture Problem

### Current (Broken) Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CURRENT STATE                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  leads                                                               │
│  ├── id (UUID) ←──────────────────┐                                 │
│  ├── clay_id (94% populated)      │                                 │
│  ├── smartlead_lead_id (38%)  ────┼── NOT USED FOR JOINS            │
│  └── email                        │                                 │
│                                   │                                 │
│  campaign_tracking                │                                 │
│  ├── id (UUID)                    │                                 │
│  ├── lead_id (UUID) ──────────────┘  ← JOINS HERE (indirect)        │
│  ├── smartlead_lead_id ────────────── 100% NULL (useless)           │
│  └── smartlead_lead_map_id ────────── 100% NULL (useless)           │
│                                                                      │
│  analytics_events                                                    │
│  ├── lead_id (UUID) → leads.id                                      │
│  ├── smartlead_lead_id → ??? (no reliable target)                   │
│  └── campaign_tracking_id → campaign_tracking.id                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Proposed (Fixed) Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TARGET STATE                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  THREE PRIMARY IDENTIFIERS:                                          │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ 1. id (UUID)           = Supabase master key (internal)     │    │
│  │ 2. smartlead_lead_id   = Smartlead key (downstream)         │    │
│  │ 3. clay_id             = Clay key (upstream)                │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  leads                                                               │
│  ├── id (UUID) ←─────── Internal reference                          │
│  ├── clay_id ←────────── Clay webhook writeback                     │
│  ├── smartlead_lead_id ← Smartlead API writeback (100% populated)   │
│  └── email ←──────────── Fallback match key only                    │
│                                                                      │
│  campaign_tracking                                                   │
│  ├── id (UUID) ←──────── Row identifier                             │
│  ├── lead_id (UUID) ───→ leads.id (for Supabase joins)              │
│  └── [REMOVE smartlead_lead_id - redundant with lead join]          │
│                                                                      │
│  analytics_events                                                    │
│  ├── lead_id (UUID) ───→ leads.id                                   │
│  └── [smartlead_lead_id used only for webhook parsing]              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Specific Issues Identified

### Issue 1: `smartlead_lead_id` Never Written Back

**Symptom:** Only 181/469 leads have `smartlead_lead_id` populated.

**Cause:** When leads are synced to Smartlead campaigns:
1. Lead is added via Smartlead API
2. Smartlead returns a `lead_id` in the response
3. **This ID is never written back to Supabase**

**Fix:** Every sync to Smartlead must UPDATE the source lead:
```sql
UPDATE leads
SET smartlead_lead_id = {smartlead_response.lead_id}
WHERE id = {supabase_lead_id};
```

### Issue 2: `campaign_tracking.smartlead_lead_id` Always NULL

**Symptom:** All 320 records have `smartlead_lead_id = NULL`.

**Cause:** The sync process creates campaign_tracking records but never populates this field.

**Fix Options:**
1. **Remove the column** - It's redundant since we can JOIN through `lead_id`
2. **Populate it** - Copy from `leads.smartlead_lead_id` when creating records

**Recommendation:** Option 1 (remove). The column is architectural debt.

### Issue 3: `in_smartlead` Flag Inaccurate

**Symptom:** 469 leads have `in_smartlead = true`, but only 320 are in campaigns.

**Fix:**
```sql
UPDATE leads
SET in_smartlead = EXISTS (
  SELECT 1 FROM campaign_tracking
  WHERE campaign_tracking.lead_id = leads.id
);
```

### Issue 4: Tier Mismatch in Campaigns

**Symptom:** Campaign counts don't match tier counts:
- A-Tier campaign: 152 tracking records, but only 57 A-tier leads exist
- B-Tier campaign: 43 tracking records, but 87 B-tier leads exist
- C-Tier campaign: 125 tracking records, but 325 C-tier leads exist

**Possible Causes:**
1. Leads were added to wrong campaigns
2. Lead tiers changed after campaign assignment
3. Duplicate campaign_tracking records

**Investigation Needed:** Run tier comparison query.

### Issue 5: Analytics Events Not Capturing

**Symptom:** Only 8 events in `analytics_events` vs 200+ in Smartlead.

**Cause:** n8n webhook was broken Nov 17-24.

**Status:** Fixed Nov 24, events now flowing.

**Gap:** Historical events need backfill from Smartlead API.

---

## Foreign Key Relationships

### Current Relationships

| Child Table | Column | Parent Table | Parent Column |
|-------------|--------|--------------|---------------|
| campaign_tracking | lead_id | leads | id |
| analytics_events | lead_id | leads | id |
| analytics_events | campaign_tracking_id | campaign_tracking | id |

### Missing Relationships

- `campaign_tracking.smartlead_campaign_id` → `campaigns.smartlead_campaign_id` (not enforced)
- `analytics_events.smartlead_campaign_id` → `campaigns.smartlead_campaign_id` (not enforced)

---

## Views Analysis

All 6 views depend on proper ID relationships:

| View | Status | Issue |
|------|--------|-------|
| `campaign_performance` | Partial | Shows zeros for most metrics |
| `lead_performance` | Partial | Missing engagement data |
| `tier_performance` | Partial | Rates are 0% |
| `daily_activity_stats` | Empty | No events to aggregate |
| `leads_ready_for_campaigns` | Incorrect | Shows 0 (all marked in_smartlead) |
| `recent_replies` | Empty | No reply events recorded |

---

## Recommended Actions

### Immediate (Fix Data Integrity)

1. **Backfill `leads.smartlead_lead_id`** from Smartlead API
   - Query each campaign for leads
   - Match by email
   - UPDATE Supabase with Smartlead IDs
   - **Status:** Partially done (181/469)

2. **Fix `in_smartlead` flag**
   ```sql
   UPDATE leads
   SET in_smartlead = EXISTS (
     SELECT 1 FROM campaign_tracking WHERE lead_id = leads.id
   );
   ```

3. **Backfill `analytics_events`** from Smartlead API
   - Pull historical events for past 7 days
   - INSERT into analytics_events

### Short-term (Fix Architecture)

4. **Remove redundant columns from campaign_tracking:**
   - `smartlead_lead_id` (redundant)
   - `smartlead_lead_map_id` (never used)

5. **Add foreign key constraints:**
   ```sql
   ALTER TABLE campaign_tracking
   ADD CONSTRAINT fk_campaign
   FOREIGN KEY (smartlead_campaign_id)
   REFERENCES campaigns(smartlead_campaign_id);
   ```

6. **Update n8n workflow** to write back `smartlead_lead_id` on sync

### Long-term (Simplify)

7. **Single source of truth for IDs:**
   - `leads.id` (UUID) = Supabase operations
   - `leads.smartlead_lead_id` = Smartlead operations
   - `leads.clay_id` = Clay operations
   - Everything else references `leads.id`

---

## Appendix: Schema Details

### leads Table Schema

```sql
CREATE TABLE leads (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- External system IDs
  clay_id TEXT UNIQUE,
  smartlead_lead_id BIGINT UNIQUE,

  -- Contact info
  email TEXT UNIQUE NOT NULL,
  first_name TEXT,
  last_name TEXT,
  company TEXT,
  domain TEXT,
  phone_number TEXT,
  location TEXT,
  linkedin_url TEXT,

  -- Scoring
  reviews_count INTEGER DEFAULT 0,
  service_software TEXT,
  score INTEGER DEFAULT 0,
  tier TEXT CHECK (tier IN ('A', 'B', 'C')),
  messaging_strategy TEXT,
  score_breakdown JSONB DEFAULT '{}',

  -- Sync tracking
  in_smartlead BOOLEAN DEFAULT false,
  smartlead_campaign_ids INTEGER[] DEFAULT '{}',
  last_smartlead_sync TIMESTAMPTZ,

  -- Metadata
  clay_data JSONB DEFAULT '{}',
  data_source_priority JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  last_enriched_at TIMESTAMPTZ
);
```

### campaign_tracking Table Schema

```sql
CREATE TABLE campaign_tracking (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  smartlead_campaign_id INTEGER NOT NULL,
  campaign_name TEXT NOT NULL,
  campaign_month TEXT,
  tier TEXT,
  status TEXT DEFAULT 'PENDING',
  sequences_sent INTEGER DEFAULT 0,
  added_at TIMESTAMPTZ DEFAULT now(),
  last_send_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,

  -- These columns should be removed (redundant/unused)
  smartlead_lead_id INTEGER,      -- Always NULL
  smartlead_lead_map_id INTEGER,  -- Always NULL

  UNIQUE(lead_id, smartlead_campaign_id)
);
```

---

## Next Steps

1. **Discuss:** Do we want to fully backfill `smartlead_lead_id` or redesign the sync process?
2. **Decide:** Keep or remove `campaign_tracking.smartlead_lead_id`?
3. **Prioritize:** Fix data first, or fix architecture first?

---

*Generated by database audit on November 24, 2025*
