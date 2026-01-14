# Supabase Live Database Audit
**Date:** November 24, 2025
**Time:** Post-backfill operations
**Status:** Live SQL query results

---

## Executive Summary

### ✅ Major Improvements (Session)
- `smartlead_lead_id` coverage: **32% → 88.3%** (151 → 414 leads)
- `in_smartlead` flag: **Fixed** to match actual campaign membership
- Foreign keys: **Working correctly** with CASCADE rules
- Orphaned records: **0** (perfect referential integrity)

### ⚠️ Critical Issues Remaining
1. **Analytics events gap**: Only 11 events vs 355+ expected
2. **Redundant columns**: `smartlead_lead_id` and `smartlead_lead_map_id` in `campaign_tracking` are 100% NULL
3. **Data type mismatch**: `campaign_tracking.smartlead_lead_id` is INTEGER, should be BIGINT
4. **Campaign tracking stale**: All 320 records stuck in PENDING status

---

## Table-by-Table Analysis

### 1. leads (Source of Truth)

#### Overall State
| Metric | Count | Percentage |
|--------|-------|------------|
| Total leads | 469 | 100% |
| With `smartlead_lead_id` | 414 | 88.3% ✅ |
| Without `smartlead_lead_id` | 55 | 11.7% |
| Marked `in_smartlead=true` | 414 | 88.3% ✅ |
| Missing `clay_id` | 27 | 5.8% |

#### Breakdown by Tier
| Tier | Total | smartlead_id | clay_id | company | in_smartlead |
|------|-------|--------------|---------|---------|--------------|
| A | 57 | 56 (98.2%) | 53 (93.0%) | 57 (100%) | 56 |
| B | 87 | 76 (87.4%) | 83 (95.4%) | 87 (100%) | 76 |
| C | 325 | 282 (86.8%) | 306 (94.2%) | 325 (100%) | 282 |

**Analysis:**
- ✅ `in_smartlead` now accurately reflects campaign membership
- ✅ A-Tier has highest ID coverage (98.2%)
- ⚠️ 55 leads still missing `smartlead_lead_id` (11.7%)
- ⚠️ 27 leads missing `clay_id` (may be manually added)

---

### 2. campaign_tracking (Campaign History)

#### State
| Metric | Value |
|--------|-------|
| Total records | 320 |
| Unique leads | 320 |
| Unique campaigns | 3 |
| Has `smartlead_lead_id` | **0 (0%)** ⚠️ |
| Has `smartlead_lead_map_id` | **0 (0%)** ⚠️ |
| Status = PENDING | **320 (100%)** ⚠️ |
| Status = SYNCED | 0 |
| Status = FAILED | 0 |

**Critical Issues:**
1. **Redundant columns**: `smartlead_lead_id` and `smartlead_lead_map_id` are 100% NULL
   - These duplicate the `leads.smartlead_lead_id` column
   - Provide no additional value
   - **Recommendation**: Remove in migration

2. **Stale status**: All 320 records stuck in PENDING
   - These leads ARE in Smartlead (verified via API)
   - Status should be SYNCED or ACTIVE
   - **Recommendation**: Update status based on actual campaign state

3. **Data type mismatch**:
   - `campaign_tracking.smartlead_lead_id` = INTEGER
   - `leads.smartlead_lead_id` = BIGINT
   - **Recommendation**: Change to BIGINT (or remove column entirely)

---

### 3. analytics_events (Engagement Tracking)

#### Current State
| Metric | Value |
|--------|-------|
| Total events | **11** |
| Unique leads | 9 |
| Unique campaigns | 3 |
| Earliest event | 2025-11-24 14:54:19 UTC |
| Latest event | 2025-11-24 16:49:53 UTC |
| **Time window** | **1 hour 55 minutes** |

#### Events by Type
| Event Type | Count | Unique Leads | Campaigns |
|------------|-------|--------------|-----------|
| EMAIL_SENT | 6 | 6 | 3 |
| EMAIL_LINK_CLICK | 3 | 3 | 2 |
| EMAIL_OPEN | 2 | 2 | 2 |

**Expected vs Actual (from Smartlead):**
| Metric | Smartlead | Supabase | Gap |
|--------|-----------|----------|-----|
| Emails sent | 213 | 6 | **207 missing** ⚠️ |
| Opens | 127 | 2 | **125 missing** ⚠️ |
| Clicks | 14 | 3 | **11 missing** ⚠️ |
| Replies | 1 | 0 | **1 missing** ⚠️ |

**Root Cause:**
- n8n webhook was broken from Nov 17-24
- Only tracking events from last ~2 hours (since fix)
- 7 days of historical events not captured

**Recommendation:**
- Backfill ~344 missing events from Smartlead API
- Use `get_campaign_stats` endpoint for historical data

---

## Schema Validation

### Foreign Keys ✅
| Table | Column | References | Delete Rule | Status |
|-------|--------|------------|-------------|--------|
| analytics_events | lead_id | leads.id | CASCADE | ✅ Working |
| analytics_events | campaign_tracking_id | campaign_tracking.id | CASCADE | ✅ Working |
| campaign_tracking | lead_id | leads.id | CASCADE | ✅ Working |

**Orphaned Records Check:**
- campaign_tracking without lead: **0** ✅
- analytics_events without lead: **0** ✅

### Data Type Issues ⚠️
| Column | Current Type | Expected Type | Issue |
|--------|--------------|---------------|-------|
| `campaign_tracking.smartlead_lead_id` | INTEGER | BIGINT | Mismatch with `leads.smartlead_lead_id` |
| `leads.smartlead_lead_id` | BIGINT | BIGINT | ✅ Correct |
| `analytics_events.smartlead_lead_id` | BIGINT | BIGINT | ✅ Correct |

---

## Recommendations

### High Priority (Data Quality)

1. **Backfill analytics events**
   - Target: ~344 missing events
   - Source: Smartlead `get_campaign_stats` API
   - Events: EMAIL_SENT (207), EMAIL_OPEN (125), EMAIL_LINK_CLICK (11), EMAIL_REPLIED (1)
   - Impact: Critical for analytics and reporting

2. **Update campaign_tracking status**
   - Change all 320 PENDING → SYNCED
   - These leads ARE in Smartlead campaigns
   - SQL: `UPDATE campaign_tracking SET status = 'SYNCED' WHERE status = 'PENDING';`

### Medium Priority (Schema Cleanup)

3. **Remove redundant columns from campaign_tracking**
   - Drop `smartlead_lead_id` (100% NULL, duplicates leads table)
   - Drop `smartlead_lead_map_id` (100% NULL, never used)
   - Migration needed (see below)

4. **Fix remaining 55 leads without smartlead_lead_id**
   - Investigate why these 55 leads aren't in Smartlead
   - Either sync them or mark `in_smartlead=false`

### Low Priority (Architecture)

5. **Fix data type consistency**
   - Change `campaign_tracking.smartlead_lead_id` from INTEGER to BIGINT
   - Or remove column entirely (preferred)

6. **Add missing foreign key for smartlead_campaign_id**
   - Currently no FK between tables and campaigns
   - Would enforce referential integrity

---

## Proposed Migrations

### Migration 1: Remove Redundant Columns
```sql
-- Remove unused columns from campaign_tracking
ALTER TABLE campaign_tracking
DROP COLUMN IF EXISTS smartlead_lead_id,
DROP COLUMN IF EXISTS smartlead_lead_map_id;

-- These columns are 100% NULL and provide no value
-- The smartlead_lead_id is already on the leads table
```

### Migration 2: Update Campaign Status
```sql
-- Update stale PENDING status to SYNCED
UPDATE campaign_tracking
SET status = 'SYNCED'
WHERE status = 'PENDING'
AND lead_id IN (
  SELECT id FROM leads WHERE smartlead_lead_id IS NOT NULL
);

-- Leads not in Smartlead should stay PENDING
```

---

## Data Quality Score

| Category | Score | Status |
|----------|-------|--------|
| **ID Coverage** | 88.3% | 🟡 Good (was 32%) |
| **Flag Accuracy** | 100% | 🟢 Perfect |
| **Event Tracking** | 3.1% | 🔴 Critical (11/355) |
| **Foreign Keys** | 100% | 🟢 Perfect |
| **Schema Consistency** | 75% | 🟡 Needs cleanup |

**Overall Grade: B-** (up from D+ after backfill)

---

## Next Steps

1. ✅ **COMPLETED**: Backfill smartlead_lead_id (88.3% coverage)
2. ✅ **COMPLETED**: Fix in_smartlead flag accuracy
3. ⏳ **IN PROGRESS**: Complete analytics events backfill
4. 🔜 **TODO**: Remove redundant campaign_tracking columns
5. 🔜 **TODO**: Update campaign_tracking status
6. 🔜 **TODO**: Investigate 55 leads without smartlead_lead_id

---

## Appendix: SQL Queries Used

### Query 1: Leads Overview
```sql
SELECT
  COUNT(*) as total_leads,
  COUNT(smartlead_lead_id) as with_smartlead_id,
  COUNT(*) - COUNT(smartlead_lead_id) as without_smartlead_id,
  ROUND(100.0 * COUNT(smartlead_lead_id) / COUNT(*), 1) as pct_with_id,
  COUNT(CASE WHEN in_smartlead = true THEN 1 END) as marked_in_smartlead,
  COUNT(CASE WHEN clay_id IS NULL THEN 1 END) as missing_clay_id
FROM leads;
```

### Query 2: Leads by Tier
```sql
SELECT
  tier,
  COUNT(*) as total,
  COUNT(smartlead_lead_id) as with_smartlead_id,
  COUNT(clay_id) as with_clay_id,
  COUNT(company) as with_company,
  COUNT(CASE WHEN in_smartlead = true THEN 1 END) as marked_in_smartlead
FROM leads
GROUP BY tier
ORDER BY tier;
```

### Query 3: Campaign Tracking State
```sql
SELECT
  COUNT(*) as total_records,
  COUNT(DISTINCT lead_id) as unique_leads,
  COUNT(DISTINCT smartlead_campaign_id) as unique_campaigns,
  COUNT(smartlead_lead_id) as has_smartlead_lead_id,
  COUNT(smartlead_lead_map_id) as has_smartlead_lead_map_id,
  COUNT(CASE WHEN status = 'PENDING' THEN 1 END) as pending,
  COUNT(CASE WHEN status = 'SYNCED' THEN 1 END) as synced,
  COUNT(CASE WHEN status = 'FAILED' THEN 1 END) as failed
FROM campaign_tracking;
```

### Query 4: Analytics Events
```sql
SELECT
  event_type,
  COUNT(*) as count,
  COUNT(DISTINCT lead_id) as unique_leads,
  COUNT(DISTINCT smartlead_campaign_id) as unique_campaigns
FROM analytics_events
GROUP BY event_type
ORDER BY count DESC;
```

### Query 5: Orphaned Records Check
```sql
SELECT
  'campaign_tracking without lead' as issue,
  COUNT(*) as count
FROM campaign_tracking ct
WHERE NOT EXISTS (SELECT 1 FROM leads l WHERE l.id = ct.lead_id)

UNION ALL

SELECT
  'analytics_events without lead' as issue,
  COUNT(*) as count
FROM analytics_events ae
WHERE NOT EXISTS (SELECT 1 FROM leads l WHERE l.id = ae.lead_id);
```

---

**End of Audit Report**
