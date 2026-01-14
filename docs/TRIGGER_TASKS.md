# Trigger.dev Tasks Documentation

**Last Updated:** December 6, 2025

---

## Overview

Automated weekly lead pipeline for HVAC contractor lead generation using trigger.dev v4.2.0.

**Pipeline Flow:**
```
Outscraper (scrape) → Supabase (store) → Enrichment (software detect) → Scoring (tier assignment) → Smartlead (campaigns)
```

**Schedule:** Every Sunday at 2 AM Eastern (7 AM UTC)

---

## Tasks

### Task 1: `weekly-scrape`

**File:** `src/trigger/weekly-scrape.ts`
**ID:** `weekly-scrape`
**Duration:** 30 minutes max

**Purpose:** Scrape fresh HVAC contractor leads from Outscraper (Google Maps)

**Payload:**
```typescript
{
  states: string[];          // e.g., ["Connecticut", "Maine"]
  limitPerState: number;     // Leads per state (default 100)
}
```

**Behavior:**
1. For each state, initiate Outscraper Google Maps scrape
2. Poll for results (async, ~10s intervals)
3. Parse places (filter for valid emails)
4. Insert into Supabase `leads` table
5. Dedupe by `place_id` (skip existing)

**Returns:**
```typescript
{
  states_processed: number;
  total_scraped: number;
  total_inserted: number;
  total_skipped: number;
  total_errors: number;
}
```

---

### Task 2: `enrich-leads`

**File:** `src/trigger/enrich-leads.ts`
**ID:** `enrich-leads`
**Duration:** 15 minutes max

**Purpose:** Detect field service software (ServiceTitan/Jobber/Housecall Pro) from websites

**Payload:**
```typescript
{
  batchSize?: number;  // Default 50
}
```

**Behavior:**
1. Fetch leads where `enriched_at IS NULL` AND `site IS NOT NULL`
2. For each lead, scrape website (10s timeout)
3. Detect software via keyword matching in HTML
4. Update `service_software` and `enriched_at`
5. Process in batches of 50

**Returns:**
```typescript
{
  leads_processed: number;
  enriched: number;
  software_detected: number;
  failures: number;
  detection_rate: string;  // "15.0%"
}
```

---

### Task 3: `score-leads`

**File:** `src/trigger/score-leads.ts`
**ID:** `score-leads`
**Duration:** 5 minutes max

**Purpose:** Assign score and tier (A/B/C) based on signals

**Payload:**
```typescript
{
  batchSize?: number;  // Default 100
}
```

**Scoring Logic:**
| Signal | Points |
|--------|--------|
| Service Software (ServiceTitan/Jobber/Housecall Pro) | +15 |
| Reviews 500+ | +10 |
| Reviews 100-499 | +7 |
| Reviews 25-99 | +4 |
| Reviews 10-24 | +2 |
| Domain/Website exists | +2 |

**Tiers:**
- **A-Tier:** 20-30 points
- **B-Tier:** 10-19 points
- **C-Tier:** 0-9 points

**Behavior:**
1. Fetch leads where `enriched_at IS NOT NULL` AND `tier IS NULL`
2. Calculate score based on signals
3. Assign tier
4. Update `score`, `tier`, `score_breakdown`

**Returns:**
```typescript
{
  leads_processed: number;
  scored: number;
  failures: number;
  tier_distribution: { A: number; B: number; C: number };
  avg_score: number;
}
```

---

### Task 4: `sync-to-smartlead`

**File:** `src/trigger/sync-to-smartlead.ts`
**ID:** `sync-to-smartlead`
**Duration:** 15 minutes max

**Purpose:** Push scored leads to appropriate Smartlead campaigns

**Payload:**
```typescript
{
  tier?: "A" | "B" | "C";  // Optional: sync only one tier
  batchSize?: number;       // Default 100
}
```

**Campaign Mapping:**
- A-Tier → Campaign 2677089 (`SMARTLEAD_CAMPAIGN_A`)
- B-Tier → Campaign 2677090 (`SMARTLEAD_CAMPAIGN_B`)
- C-Tier → Campaign 2677091 (`SMARTLEAD_CAMPAIGN_C`)

**Behavior:**
1. For each tier, get leads where `tier = X` AND `in_smartlead = false`
2. Format lead for Smartlead API
3. Add to campaign via POST `/campaigns/{id}/leads`
4. Update `smartlead_lead_id`, `in_smartlead`, `smartlead_campaign_ids`, `last_smartlead_sync`

**Returns:**
```typescript
{
  tiers_processed: number;
  total_synced: number;
  total_failed: number;
  tier_results: {
    A: { synced: number; failed: number };
    B: { synced: number; failed: number };
    C: { synced: number; failed: number };
  };
}
```

---

### Task 5: `weekly-pipeline` (Orchestrator)

**File:** `src/trigger/weekly-pipeline.ts`
**ID:** `weekly-pipeline`
**Duration:** 1 hour max
**Schedule:** `0 7 * * 0` (Sundays 7 AM UTC = 2 AM ET)

**Purpose:** Orchestrate full pipeline on weekly schedule

**Execution Flow:**
```
1. weekly-scrape (9 Northeast states, 200 per state = ~1800 leads)
   ↓
2. enrich-leads (batches of 50, up to 3000 leads)
   ↓
3. score-leads (batches of 100, up to 3000 leads)
   ↓
4. sync-to-smartlead (100 per tier, A/B/C)
```

**Returns:**
```typescript
{
  pipeline: "weekly-lead-pipeline";
  duration_seconds: number;
  duration_minutes: number;
  steps: {
    scrape: { ... };
    enrich: { batches: number; total_enriched: number };
    score: { batches: number; total_scored: number };
    sync: { ... };
  };
  timestamp: string;
}
```

---

## Utilities

### `utils/supabase.ts`

**Exports:**
- `supabaseService` - Singleton client
- `Lead` interface - TypeScript type for leads table
- `OutscraperInsert` interface - Insert format

**Key Methods:**
- `insertLeads()` - Batch insert with place_id deduplication
- `getLeadsForEnrichment()` - Fetch unenriched leads
- `updateEnrichment()` - Mark lead as enriched
- `getLeadsForScoring()` - Fetch scored leads
- `updateScore()` - Set score/tier/breakdown
- `getLeadsForSmartlead()` - Fetch leads ready for sync
- `updateSmartleadSync()` - Mark synced to Smartlead

### `utils/outscraper.ts`

**Exports:**
- `outscraperService` - API client
- `OutscraperPlace` interface

**Key Methods:**
- `scrapeHVAC()` - Initiate scrape (returns request ID)
- `pollResults()` - Poll for async results (max 5 min)
- `scrapeAndWait()` - Combined scrape + poll
- `parsePlace()` - Convert to Supabase format

### `utils/software-detect.ts`

**Exports:**
- `detectSoftware()` - Scrape URL and detect software (10s timeout)
- `normalizeUrl()` - Add https:// if missing

**Detection Keywords:**
- ServiceTitan: `servicetitan.com`, `st-widget`, etc.
- Jobber: `getjobber.com`, `jobber-widget`, etc.
- Housecall Pro: `housecallpro.com`, `hcp-widget`, etc.

### `utils/smartlead.ts`

**Exports:**
- `smartleadService` - API client
- `SmartleadLead` interface

**Key Methods:**
- `addLead()` - Add single lead to campaign
- `addLeadsBatch()` - Batch add (up to 100)
- `getCampaignIdForTier()` - Map tier to campaign ID

---

## Environment Variables

```bash
# Supabase
SUPABASE_URL=https://rlmuovkdvbxzyylbiunj.supabase.co
SUPABASE_SERVICE_KEY=your-service-key

# Smartlead
SMARTLEAD_API_KEY=38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8
SMARTLEAD_CAMPAIGN_A=2677089
SMARTLEAD_CAMPAIGN_B=2677090
SMARTLEAD_CAMPAIGN_C=2677091

# Outscraper
OUTSCRAPER_API_KEY=your-outscraper-key
```

---

## Testing

### Test Individual Tasks

```bash
# Start trigger.dev dev server
npx trigger.dev@latest dev

# Trigger tasks manually via dashboard
# http://localhost:3000
```

**Test payloads:**

```typescript
// weekly-scrape
{ states: ["Connecticut"], limitPerState: 10 }

// enrich-leads
{ batchSize: 5 }

// score-leads
{ batchSize: 10 }

// sync-to-smartlead
{ tier: "C", batchSize: 5 }
```

### Monitor Scheduled Task

The `weekly-pipeline` runs automatically every Sunday at 2 AM ET. Check logs in trigger.dev dashboard.

---

## Deployment

```bash
# Deploy to trigger.dev cloud
npx trigger.dev@latest deploy

# Verify deployment
npx trigger.dev@latest list
```

---

## Error Handling

All tasks include:
- **Retry logic:** 2 max attempts (exponential backoff)
- **Timeouts:** Per-task max duration
- **Graceful failures:** One lead failure doesn't block others
- **Detailed logging:** Structured logs with context

**Common Issues:**

1. **Outscraper timeout:** Increase `maxAttempts` in `pollResults()`
2. **Website scrape failures:** Normal - 10s timeout, many sites block bots
3. **Smartlead duplicates:** Handled by Smartlead (returns existing lead_id)
4. **Supabase RLS:** Ensure `SUPABASE_SERVICE_KEY` is service role (bypasses RLS)

---

## Next Steps

1. ✅ Test `weekly-scrape` with small state sample
2. ✅ Verify software detection accuracy
3. ✅ Run `weekly-pipeline` manually (dry run)
4. ⏳ Deploy to trigger.dev cloud
5. ⏳ Monitor first scheduled run (Sunday 2 AM ET)
