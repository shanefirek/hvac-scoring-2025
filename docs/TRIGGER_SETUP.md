# Trigger.dev Setup & Testing Guide

**Last Updated:** December 8, 2025
**Status:** Ready for testing and deployment

---

## Overview

Trigger.dev automation framework is implemented and ready to replace manual Clay workflow. This guide covers setup, testing, and deployment.

## Current Implementation Status

### ✅ Completed
- [x] Trigger.dev SDK installed (v4.2.0)
- [x] Project configured (proj_anceawkgglmxzvyxdugw)
- [x] All 5 tasks implemented
- [x] Supabase integration
- [x] Smartlead integration
- [x] Environment variables template created

### ⏳ Pending
- [ ] Outscraper API key configured
- [ ] Trigger.dev secret key configured
- [ ] Individual tasks tested
- [ ] End-to-end pipeline tested
- [ ] Deployed to Trigger.dev cloud

---

## Environment Variables Required

### 1. Get Trigger.dev Secret Key

```bash
# Login to Trigger.dev (opens browser)
npx trigger.dev@latest login

# This will authenticate you and save credentials
# Then you can get your secret key from:
# https://cloud.trigger.dev/projects/proj_anceawkgglmxzvyxdugw/apikeys
```

### 2. Get Outscraper API Key

Sign up at https://outscraper.com and get your API key from the dashboard.

### 3. Update .env file

```bash
# Edit .env and replace these placeholders:
OUTSCRAPER_API_KEY=your-outscraper-api-key-here  # Replace this
TRIGGER_SECRET_KEY=your-trigger-secret-key-here  # Replace this
```

**Current .env status:**
- ✅ Supabase credentials configured
- ✅ Smartlead API key configured
- ✅ Campaign IDs configured (A: 2677089, B: 2677090, C: 2677091)
- ✅ Railway endpoints configured
- ⚠️ Outscraper API key: PLACEHOLDER
- ⚠️ Trigger.dev secret: PLACEHOLDER

---

## Implemented Tasks

### 1. weekly-scrape
**File:** `src/trigger/weekly-scrape.ts`
**Purpose:** Scrape HVAC businesses from 9 Northeast states via Outscraper

**Inputs:**
```typescript
{
  states: string[],      // 9 states: NY, PA, NJ, MA, CT, RI, VT, NH, ME
  limitPerState: number  // Default 200
}
```

**Process:**
- Queries Outscraper API for "HVAC" in each state
- Deduplicates by `place_id` (Google Maps unique ID)
- Inserts new leads into Supabase `leads` table
- Returns: `{ scraped: number, duplicates: number }`

### 2. enrich-leads
**File:** `src/trigger/enrich-leads.ts`
**Purpose:** Detect FSM software (ServiceTitan/Jobber/Housecall Pro) from websites

**Inputs:**
```typescript
{
  batchSize: number  // Default 50 leads per run
}
```

**Process:**
- Fetches leads where `enriched_at IS NULL` and `site IS NOT NULL`
- Scrapes each website (10s timeout)
- Detects software keywords via Railway endpoint
- Updates `service_software` and `enriched_at` columns
- Returns: `{ enriched: number, leads_processed: number }`

### 3. score-leads
**File:** `src/trigger/score-leads.ts`
**Purpose:** Apply scoring logic and assign A/B/C tiers

**Inputs:**
```typescript
{
  batchSize: number  // Default 100 leads per run
}
```

**Scoring System (0-30 points):**
- Service software: +15
- Franchise match: +10
- Reviews 500+: +10
- Reviews 100-499: +7
- Reviews 25-99: +4
- Reviews 10-24: +2
- LinkedIn URL: +3
- Domain exists: +2

**Tier Thresholds:**
- A-Tier: 20-30 points
- B-Tier: 10-19 points
- C-Tier: 0-9 points

**Process:**
- Fetches leads where `score IS NULL`
- Calculates score based on signals
- Assigns tier
- Updates `score` and `tier` columns
- Returns: `{ scored: number, leads_processed: number }`

### 4. sync-to-smartlead
**File:** `src/trigger/sync-to-smartlead.ts`
**Purpose:** Upload leads to appropriate Smartlead campaigns by tier

**Inputs:**
```typescript
{
  batchSize: number  // Default 100 per tier
}
```

**Process:**
- Fetches leads where `in_smartlead = false` by tier
- Uploads to campaigns (A: 2677089, B: 2677090, C: 2677091)
- Max 50 leads per API call (Smartlead limitation)
- Updates `in_smartlead`, `smartlead_lead_id`, `last_smartlead_sync`
- Returns: `{ a_tier: number, b_tier: number, c_tier: number }`

### 5. weekly-pipeline
**File:** `src/trigger/weekly-pipeline.ts`
**Purpose:** Orchestrator that chains all tasks together

**Schedule:** Every Sunday at 2 AM ET (7 AM UTC)

**Process:**
1. Scrape ~1800 leads (200 per state × 9 states)
2. Enrich in batches of 50 until all processed
3. Score in batches of 100 until all processed
4. Sync to Smartlead in batches of 100 per tier
5. Return summary with timing and counts

---

## Testing Steps

### Step 1: Start Trigger.dev Dev Server

```bash
npx trigger.dev@latest dev
```

This starts a local development server that:
- Watches for code changes
- Exposes tasks for testing
- Provides real-time logs
- Opens dashboard at http://localhost:3030

### Step 2: Test Individual Tasks

#### Test weekly-scrape (1 state, 10 leads)
```bash
# In Trigger.dev dashboard, manually trigger:
Task: weekly-scrape
Payload:
{
  "states": ["Rhode Island"],
  "limitPerState": 10
}
```

Expected output:
```json
{
  "scraped": 10,
  "duplicates": 0
}
```

#### Test enrich-leads (5 leads)
```bash
# Manually trigger:
Task: enrich-leads
Payload:
{
  "batchSize": 5
}
```

Expected output:
```json
{
  "enriched": 5,
  "leads_processed": 5
}
```

#### Test score-leads (10 leads)
```bash
# Manually trigger:
Task: score-leads
Payload:
{
  "batchSize": 10
}
```

Expected output:
```json
{
  "scored": 10,
  "leads_processed": 10
}
```

#### Test sync-to-smartlead (5 per tier)
```bash
# Manually trigger:
Task: sync-to-smartlead
Payload:
{
  "batchSize": 5
}
```

Expected output:
```json
{
  "a_tier": 2,
  "b_tier": 3,
  "c_tier": 5
}
```

### Step 3: Test Full Pipeline (Small Sample)

```bash
# Manually trigger weekly-pipeline with small sample
Task: weekly-pipeline
Payload: {}  # Uses default parameters
```

**Modify weekly-pipeline temporarily for testing:**
```typescript
// In src/trigger/weekly-pipeline.ts, change:
limitPerState: 10  // Instead of 200
```

Expected flow:
1. Scrape 90 leads (10 × 9 states)
2. Enrich all 90 leads
3. Score all 90 leads
4. Sync all 90 leads to campaigns

---

## Deployment

### Step 1: Pre-deployment Checklist

- [ ] All environment variables configured
- [ ] Individual tasks tested successfully
- [ ] Small sample pipeline tested successfully
- [ ] No TypeScript errors: `npx tsc --noEmit`

### Step 2: Deploy to Trigger.dev Cloud

```bash
npx trigger.dev@latest deploy
```

This will:
1. Build your project
2. Upload to Trigger.dev cloud
3. Activate scheduled tasks
4. Return deployment URL

### Step 3: Verify Deployment

```bash
# Check deployment status
npx trigger.dev@latest whoami

# View runs in dashboard
open https://cloud.trigger.dev/projects/proj_anceawkgglmxzvyxdugw/runs
```

### Step 4: Monitor First Scheduled Run

**Next scheduled run:** Sunday at 2 AM ET

**What to monitor:**
1. Total execution time (~30-60 minutes expected)
2. Leads scraped (~1800 expected)
3. Software detection rate (~8-10% expected)
4. Tier distribution (A: ~5%, B: ~15%, C: ~80%)
5. Smartlead sync success rate (target: 95%+)

**Dashboard locations:**
- Trigger.dev: https://cloud.trigger.dev/projects/proj_anceawkgglmxzvyxdugw
- Supabase: https://supabase.com/dashboard/project/rlmuovkdvbxzyylbiunj
- Smartlead: https://app.smartlead.ai/campaigns

---

## Troubleshooting

### Issue: Outscraper API Rate Limit

**Symptom:** Scraping fails with 429 error
**Solution:** Reduce `limitPerState` or add delay between states

```typescript
// In src/trigger/weekly-scrape.ts
await new Promise(resolve => setTimeout(resolve, 2000)); // 2s delay
```

### Issue: Software Detection Timeout

**Symptom:** Many leads timeout during enrichment
**Solution:** Already configured to 10s timeout, just logs and continues

### Issue: Smartlead Duplicate Leads

**Symptom:** API returns 400 "duplicate email"
**Solution:** Already handled - uses `ignore_duplicate_leads_in_other_campaign: true`

### Issue: Memory/Timeout on Large Batches

**Symptom:** Task crashes during processing
**Solution:** Reduce batch sizes in .env or task parameters

---

## Success Metrics

### Target Performance (After First Run)

| Metric | Target |
|--------|--------|
| Leads scraped/week | ~1800 |
| Software detection rate | 8-10% |
| Tier A percentage | 5% (~90 leads) |
| Tier B percentage | 15% (~270 leads) |
| Tier C percentage | 80% (~1440 leads) |
| Smartlead sync rate | 95%+ |
| Task failure rate | <5% |
| Total pipeline time | <60 minutes |

### Monitoring Queries

```sql
-- Weekly scrape count
SELECT COUNT(*), DATE(created_at)
FROM leads
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at);

-- Software detection coverage
SELECT
  COUNT(*) FILTER (WHERE enriched_at IS NOT NULL) as enriched,
  COUNT(*) as total,
  ROUND(100.0 * COUNT(*) FILTER (WHERE enriched_at IS NOT NULL) / COUNT(*), 1) as pct
FROM leads;

-- Tier distribution
SELECT tier, COUNT(*)
FROM leads
GROUP BY tier
ORDER BY tier;

-- Smartlead sync rate
SELECT
  COUNT(*) FILTER (WHERE in_smartlead = true) as synced,
  COUNT(*) as total,
  ROUND(100.0 * COUNT(*) FILTER (WHERE in_smartlead = true) / COUNT(*), 1) as pct
FROM leads
WHERE tier IS NOT NULL;
```

---

## Next Steps

1. **Obtain API Keys**
   - Get Outscraper API key: https://outscraper.com
   - Get Trigger.dev secret: https://cloud.trigger.dev/projects/proj_anceawkgglmxzvyxdugw/apikeys

2. **Test Locally**
   - Run `npx trigger.dev@latest dev`
   - Test each task individually with small samples
   - Verify database updates

3. **Deploy**
   - Run `npx trigger.dev@latest deploy`
   - Monitor first scheduled run (next Sunday 2 AM ET)

4. **Monitor & Optimize**
   - Check campaign performance weekly
   - Adjust scoring thresholds if needed
   - Optimize batch sizes for performance

---

## Files Reference

### Task Files
- `src/trigger/weekly-scrape.ts` - Outscraper scraping
- `src/trigger/enrich-leads.ts` - Software detection
- `src/trigger/score-leads.ts` - Scoring & tiering
- `src/trigger/sync-to-smartlead.ts` - Campaign sync
- `src/trigger/weekly-pipeline.ts` - Orchestrator

### Utility Files
- `src/trigger/utils/supabase.ts` - Supabase client
- `src/trigger/utils/outscraper.ts` - Outscraper API wrapper
- `src/trigger/utils/software-detect.ts` - Website scraping
- `src/trigger/utils/smartlead.ts` - Smartlead API wrapper

### Configuration
- `trigger.config.ts` - Trigger.dev configuration
- `.env` - Environment variables
- `package.json` - Dependencies

---

## Support Resources

- **Trigger.dev Docs:** https://trigger.dev/docs
- **Trigger.dev Discord:** https://trigger.dev/discord
- **Outscraper Docs:** https://outscraper.com/docs
- **Smartlead API:** https://help.smartlead.ai/en/collections/8858799-api-documentation
- **Supabase Docs:** https://supabase.com/docs
