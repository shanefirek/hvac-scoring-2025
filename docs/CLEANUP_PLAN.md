# Supabase Cleanup + Clay Pipeline Plan

**Created:** December 10, 2025
**Status:** IN PROGRESS
**QA Agent:** TBD (assigns at end)

---

## Overview

Fix security issues, restore wiped tables, then build Clay → Supabase → Smartlead pipeline.

---

## Phase 1: Fix Security Issues

### Task 1.1: Enable RLS on leads table
**Status:** COMPLETED
**Assigned:** Main Agent
**SQL:**
```sql
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
```
**Sign-off:** Main Agent - Dec 10, 2025

---

### Task 1.2: Fix SECURITY DEFINER views (6 views)
**Status:** COMPLETED
**Assigned:** Claude Code

Recreate these views with `security_invoker = true`:
- `lead_performance` ✅
- `leads_ready_for_campaigns` ✅
- `campaign_performance` ✅
- `daily_activity_stats` ✅
- `recent_replies` ✅
- `tier_performance` ✅

**Migration:** `fix_security_definer_views` applied Dec 10, 2025

**Sign-off:** Claude Code - Dec 10, 2025

---

### Task 1.3: Fix function search_path (8 functions)
**Status:** COMPLETED
**Assigned:** Main Agent

Add `SET search_path = public` to these functions:
- `update_updated_at_column` ✅
- `merge_lead_data` ✅
- `get_leads_for_campaign` ✅
- `record_smartlead_event` ✅
- `sync_lead_from_clay` (2 versions) ✅
- `sync_lead_to_smartlead` ✅
- `handle_smartlead_webhook` ✅

**Migration Applied:** `fix_function_search_paths`

**Sign-off:** Main Agent - Dec 10, 2025

---

## Phase 2: Restore Wiped Tables

### Task 2.1: Backfill analytics_events from Smartlead API
**Status:** COMPLETED
**Assigned:** Claude Code

Pull historical events from all 3 campaigns:
- Campaign 2677089 (A-Tier): 216 stats → 370 events
- Campaign 2677090 (B-Tier): 295 stats → 472 events
- Campaign 2677091 (C-Tier): 515 stats → 742 events

**Results:**
- Total events inserted: **1,580**
- Final analytics_events count: **1,584**
- Unmatched emails (not in Supabase): 40

**Event Breakdown:**
| Event Type | Count |
|------------|-------|
| EMAIL_SENT | 972 |
| EMAIL_OPEN | 488 |
| EMAIL_LINK_CLICK | 101 |
| EMAIL_BOUNCED | 15 |
| EMAIL_REPLIED | 8 |

**Script:** `scripts/recovery/backfill_analytics_from_smartlead.py`

**Sign-off:** Claude Code - Dec 10, 2025

---

### Task 2.2: Rebuild campaign_tracking table
**Status:** PENDING
**Assigned:** AVAILABLE

For each lead with `smartlead_lead_id`, create campaign_tracking record:
- Match lead to campaign via Smartlead API
- Set status based on current state (ACTIVE/COMPLETED/etc)

**Sign-off:** _______________

---

## Phase 3: Build Clay Pipeline

### Task 3.1: Create Edge Function sync-to-smartlead
**Status:** COMPLETED
**Assigned:** Main Agent

**Trigger:** INSERT/UPDATE where `tier IS NOT NULL AND in_smartlead = false`

**Logic:**
- A-Tier → Campaign 2677089 ✅
- B-Tier → Campaign 2677090 ✅
- C-Tier → Campaign 2677091 ✅
- Write back `smartlead_lead_id` ✅
- Set `in_smartlead = true` ✅

**Deployed:**
- Edge Function: `sync-to-smartlead` (v1)
- URL: `https://rlmuovkdvbxzyylbiunj.supabase.co/functions/v1/sync-to-smartlead`
- Database Trigger: `trigger_sync_to_smartlead` on `leads` table
- Trigger Function: `queue_lead_for_smartlead_sync()`

**Usage:**
```bash
# Manual call (with service role key)
curl -X POST https://rlmuovkdvbxzyylbiunj.supabase.co/functions/v1/sync-to-smartlead \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"lead_id": "uuid-here"}'

# Batch call
curl -X POST ... -d '{"lead_ids": ["uuid1", "uuid2", "uuid3"]}'
```

**Note:** Automatic trigger requires `SUPABASE_SERVICE_ROLE_KEY` in Supabase Vault.

**Sign-off:** Main Agent - Dec 10, 2025

---

### Task 3.2: Update sync_lead_from_clay() function
**Status:** PENDING
**Assigned:** AVAILABLE

Add support for new columns from Clay:
- linkedin_url
- employee_count
- revenue
- Any other enrichment fields

**Sign-off:** _______________

---

### Task 3.3: Build Clay table (Manual)
**Status:** PENDING
**Assigned:** USER (Manual in Clay UI)

Columns needed:
- email, first_name, last_name, company, domain
- reviews_count, service_software, score, tier
- place_id, phone, city, state, postal_code
- linkedin_url, employee_count, revenue

**Sign-off:** _______________

---

## Phase 4: QA & Verification

### Task 4.1: Final QA
**Status:** PENDING
**Assigned:** QA AGENT

Verify:
- [ ] All 7 security errors resolved (run `mcp__supabase__get_advisors`)
- [ ] analytics_events restored (~280+ rows)
- [ ] campaign_tracking populated (~850 rows)
- [ ] Edge Function deployed and working
- [ ] sync_lead_from_clay() handles all columns
- [ ] End-to-end test: insert test lead → appears in Smartlead

**Sign-off:** _______________

---

## Current Data State (Dec 10 Audit)

| Metric | Value |
|--------|-------|
| Total leads | 850 |
| With smartlead_lead_id | 850 (100%) |
| With clay_id | 424 (50%) |
| With place_id | 211 (25%) |
| campaign_tracking rows | 0 (WIPED) |
| analytics_events rows | 1,584 (RESTORED ✅) |

---

## Campaign IDs Reference

| Tier | Campaign ID |
|------|-------------|
| A-Tier | 2677089 |
| B-Tier | 2677090 |
| C-Tier | 2677091 |

---

## Agent Assignment Log

| Task | Agent | Started | Completed |
|------|-------|---------|-----------|
| 1.1 RLS | Main | Dec 10 | Dec 10 |
| 1.2 Views | Claude Code | Dec 10 | Dec 10 |
| 1.3 Functions | Main Agent | Dec 10 | Dec 10 |
| 2.1 Analytics | Claude Code | Dec 10 | Dec 10 |
| 2.2 Tracking | | | |
| 3.1 Edge Fn | Main Agent | Dec 10 | Dec 10 |
| 3.2 Sync Fn | | | |
| 4.1 QA | | | |

---

## How to Claim a Task

1. Find a task with **Status: PENDING** and **Assigned: AVAILABLE**
2. Update the task's Assigned field to your agent identifier
3. Update Status to **IN PROGRESS**
4. When done, update Status to **COMPLETED** and add sign-off
5. Update the Agent Assignment Log

---

## Notes

- Use `mcp__supabase__apply_migration` for DDL changes
- Use `mcp__supabase__execute_sql` for queries
- Use `mcp__smartlead__*` tools for Smartlead API calls
- All emails in leads table are lowercase (enforced by CHECK constraint)
