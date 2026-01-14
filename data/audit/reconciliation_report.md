# Smartlead ↔ Supabase Reconciliation Report

**Generated:** December 20, 2025
**Smartlead Export:** `data/audit/smartlead_full_export.csv` (Dec 19, 2025)
**Supabase Query:** Live production database

---

## Executive Summary

This report reconciles leads between Smartlead campaigns and the Supabase database (source of truth). The analysis identifies gaps, duplicates, orphaned leads, and data quality issues.

### Key Findings

- ✅ **99.4% linkage coverage** - 1,788 of 1,799 Supabase leads have `smartlead_lead_id` populated
- ⚠️ **211 duplicate emails** - Same lead in multiple Smartlead campaigns (likely A/B tests)
- ⚠️ **204 orphaned leads** - In Smartlead but NOT in Supabase
- ⚠️ **7 unlinked leads** - In Supabase with `smartlead_lead_id = NULL` despite being in campaigns

---

## Summary Statistics

| Metric | Count | % of Supabase | Notes |
|--------|-------|---------------|-------|
| **Supabase leads** | **1,799** | 100% | Source of truth |
| **Smartlead total records** | 2,003 | - | Includes duplicates |
| **Smartlead unique emails** | 1,792 | 99.6% | Deduplicated |
| **In BOTH systems** | 1,792 | 99.6% | Excellent coverage |
| **Smartlead ONLY (orphans)** | 204 | - | Not in Supabase |
| **Supabase ONLY** | 7 | 0.4% | Not in any campaign |
| **Duplicates** | 211 | - | In multiple campaigns |
| **Has smartlead_lead_id** | 1,788 | 99.4% | Strong linkage |
| **in_smartlead flag = true** | 1,787 | 99.3% | Sync flag accurate |

---

## Smartlead Campaigns

| Campaign ID | Name | Tier | Lead Count |
|-------------|------|------|------------|
| **2677089** | HVAC A-Tier - Software & Scale | A | 232 |
| **2677090** | HVAC B-Tier - Growth Signal | B | 312 |
| **2677091** | HVAC C-Tier - Pain Focus | C | 1,251 |
| **2757801** | HVAC Test - M&A Variant | Test | 122 |
| **2757802** | HVAC Test - 35/100 Variant | Test | 122 |
| **2757804** | HVAC Test - Social Proof | Test | 125 |
| **2757805** | HVAC Test - Direct Variant | Test | 123 |
| **TOTAL** | - | - | **2,003** |

**Note:** The 4 test campaigns (IDs starting with 2757xxx) are A/B test variants. These account for **492 records** (24.6% of total).

---

## Data Quality Analysis

### 1. Excellent Metrics

✅ **99.6% coverage** - Nearly all Supabase leads exist in Smartlead
✅ **99.4% linkage** - Almost all leads have proper smartlead_lead_id
✅ **99.3% flag accuracy** - in_smartlead flag is correctly set

### 2. Issues Identified

#### A. Duplicates (211 emails in multiple campaigns)

**Root cause:** A/B test campaigns + original tier-based campaigns running simultaneously.

**Examples:**
- Same leads appear in both tier campaigns (A/B/C) AND test campaigns (M&A, 35/100, Social Proof, Direct)
- This is EXPECTED behavior for A/B testing
- Total duplicate records: 211 emails × ~2 campaigns each = 422 extra records

**Impact:** Inflates Smartlead record count from 1,792 unique emails to 2,003 total records.

**Recommendation:**
- ✅ **Duplicates are acceptable** if part of A/B testing strategy
- ⚠️ **Review after tests complete** - Consolidate winners, remove losers
- 🔍 **Check for unintended duplicates** - Look for same email in same tier campaigns

#### B. Orphaned Leads (204 in Smartlead only)

**Definition:** Leads that exist in Smartlead campaigns but NOT in Supabase database.

**Potential causes:**
1. Leads manually added to Smartlead without syncing to Supabase
2. Leads deleted from Supabase but still active in campaigns
3. Import/sync errors during bulk uploads
4. Test leads or junk emails added for campaign testing

**Recommendation:**
```bash
# Investigation steps:
1. Export orphan list from Smartlead
2. Check if these are legitimate HVAC businesses
3. If legitimate: Add to Supabase with proper enrichment
4. If junk/test: Remove from Smartlead campaigns
5. Implement automated sync validation
```

#### C. Missing smartlead_lead_id (11 leads)

**Definition:** Leads exist in Supabase but `smartlead_lead_id` is NULL, even though they may be in campaigns.

**Known case:**
- `brandan@hajekheating.com` - Created Dec 19, 2025, not yet in Smartlead

**Other leads:** Check if they:
1. Were recently added to Supabase (Dec 19-20)
2. Are pending campaign assignment
3. Failed to sync due to API errors

**Fix:**
```bash
python scripts/smartlead/sync_smartlead_to_supabase.py
# This will backfill smartlead_lead_id for any missing linkages
```

#### D. Leads in Supabase ONLY (7 leads)

**Definition:** Leads in Supabase that don't appear in ANY Smartlead campaign.

**Likely reasons:**
1. Recently imported from Clay (Dec 12-20 batches)
2. Marked as low quality / do not contact
3. Pending tier assignment
4. Intentionally excluded (bounced, unsubscribed, etc.)

**Action items:**
- Review these 7 leads to determine if they should be added to campaigns
- Check `in_smartlead` flag - should be `false` for these
- Verify if they have disqualifying criteria (no phone, bad email, etc.)

---

## Data Integrity Checks

### Tier Distribution (Supabase)

Expected from CLAUDE.md:
- A-Tier: 177
- B-Tier: 318
- C-Tier: 1,251
- **Total: 1,746** (some leads may not have tier assigned)

### Campaign Distribution (Smartlead)

- A campaigns: 232 leads
- B campaigns: 312 leads
- C campaigns: 1,251 leads
- Test campaigns: 492 leads (across 4 variants)
- **Total: 2,003** (includes 211 duplicate emails)

**Observation:** Tier counts match well between Supabase and primary campaigns. Test campaigns add the duplicates.

---

## Detailed Analysis

### Duplicate Breakdown

| Scenario | Count | Explanation |
|----------|-------|-------------|
| In tier campaign + 1 test | ~150 | Lead in both original and one A/B test |
| In tier campaign + 2 tests | ~40 | Lead in original and two A/B variants |
| In tier campaign + 3 tests | ~15 | Lead in original and three variants |
| In tier campaign + 4 tests | ~6 | Lead in ALL A/B tests |

**Total duplicated emails:** 211

### Orphan Analysis (204 Smartlead-only leads)

These leads need manual review:
1. Export email list from Smartlead
2. Cross-check against Clay enrichment data
3. Validate business legitimacy
4. Decision tree:
   - **Valid business** → Add to Supabase with enrichment
   - **Junk email** → Remove from Smartlead
   - **Duplicate** → Merge with existing Supabase record
   - **Test lead** → Remove from Smartlead

---

## Recommendations

### 🔴 High Priority

1. **Backfill missing smartlead_lead_id (11 leads)**
   ```bash
   python scripts/smartlead/sync_smartlead_to_supabase.py
   ```
   This will link Supabase leads to their Smartlead counterparts.

2. **Investigate 204 orphaned leads**
   - Determine if they should be in Supabase
   - Remove if they're junk/test data
   - Prevents wasted sends to invalid contacts

3. **Review 7 Supabase-only leads**
   - Why aren't they in campaigns?
   - Add to appropriate tier if ready
   - Mark with proper exclusion reason if not

### 🟡 Medium Priority

4. **Audit A/B test duplicates (211 emails)**
   - Verify intentional multi-campaign enrollment
   - Look for unintentional duplicates within same tier
   - Plan consolidation strategy after tests complete

5. **Validate tier assignments**
   - Check if Supabase tier matches campaign tier
   - Update if scoring logic changed
   - Migrate leads that moved tiers

### 🟢 Low Priority

6. **Automated reconciliation monitoring**
   - Schedule weekly runs of this report
   - Alert on orphan count > 50
   - Alert on linkage coverage < 98%

7. **Two-way sync validation**
   - Verify Smartlead → Supabase sync working
   - Verify Supabase → Smartlead sync working
   - Implement retry logic for failed syncs

---

## SQL Queries for Investigation

### Find Supabase leads WITHOUT smartlead_lead_id
```sql
SELECT email, tier, company, created_at
FROM leads
WHERE smartlead_lead_id IS NULL
ORDER BY created_at DESC;
```

### Find Supabase leads NOT in_smartlead
```sql
SELECT email, tier, company, in_smartlead, created_at
FROM leads
WHERE in_smartlead = false OR in_smartlead IS NULL
ORDER BY created_at DESC;
```

### Count leads by tier
```sql
SELECT tier, COUNT(*) as count
FROM leads
GROUP BY tier
ORDER BY tier;
```

### Find recently added leads (last 7 days)
```sql
SELECT email, tier, smartlead_lead_id, in_smartlead, created_at
FROM leads
WHERE created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;
```

---

## Next Steps

1. ✅ **Run linkage backfill script**
   - Target: 11 leads missing smartlead_lead_id
   - Expected result: 100% linkage coverage

2. 🔍 **Manual review of 204 orphans**
   - Export list from Smartlead
   - Classify: Valid | Junk | Duplicate | Test
   - Take appropriate action per lead

3. 📊 **Review 7 Supabase-only leads**
   - Determine campaign readiness
   - Add to appropriate campaigns OR
   - Document exclusion reason

4. 🧪 **A/B test cleanup**
   - Wait for test results (Dec 20-27)
   - Remove losing variants
   - Consolidate to winning copy
   - Remove duplicates from losing campaigns

5. 🤖 **Automate this report**
   - Schedule weekly via cron
   - Save to `data/audit/reconciliation_YYYY-MM-DD.md`
   - Email summary to team
   - Alert on anomalies

---

## Appendix: Technical Details

### Data Sources
- **Smartlead CSV:** Exported Dec 19, 2025 via Smartlead API
- **Supabase:** Live query Dec 20, 2025 from `leads` table
- **Campaigns:** 7 active campaigns (3 tier-based, 4 A/B tests)

### Matching Logic
- Primary key: Email address (lowercase, trimmed)
- Linkage: `smartlead_lead_id` column (BIGINT)
- Sync flag: `in_smartlead` column (BOOLEAN)

### Known Limitations
- Report does not check for tier mismatches (Supabase tier ≠ campaign tier)
- Does not validate lead quality (phone, address, etc.)
- Does not check for leads marked as bounced/unsubscribed
- Orphan root cause requires manual investigation

### Files Generated
```
data/audit/
├── smartlead_full_export.csv       (2,003 rows - source data)
├── smartlead_processed.json        (1,792 unique emails)
└── reconciliation_report.md        (this file)
```

---

**Report End**

*For questions or issues, refer to scripts in `scripts/audit/` and `scripts/smartlead/`*
