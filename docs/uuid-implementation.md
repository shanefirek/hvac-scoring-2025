# UUID Implementation Guide

## Core Principle

**Supabase UUID is the master identifier.** All external systems (Clay, Smartlead) reference back to it.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ID HIERARCHY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  MASTER: Supabase `id` (UUID)                                   │
│    │                                                             │
│    ├── clay_id (TEXT) - enrichment tracking, optional           │
│    │                                                             │
│    ├── smartlead_lead_id (INTEGER) - written back after sync    │
│    │                                                             │
│    └── email (TEXT) - unique constraint, fallback matching key  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. Lead Creation (Clay → Supabase)

```
Clay enriches lead
    ↓
Webhook/API call to Supabase
    ↓
Supabase generates UUID (id column, auto)
    ↓
Stores: id, email, clay_id, company, tier, score
    ↓
in_smartlead = false, smartlead_lead_id = null
```

### 2. Smartlead Sync (Supabase → Smartlead)

```
Query: SELECT * FROM leads WHERE in_smartlead = false AND tier IS NOT NULL
    ↓
POST to Smartlead /api/v1/campaigns/{id}/leads
    ↓
Smartlead returns lead_id in response
    ↓
UPDATE leads SET smartlead_lead_id = {response.lead_id}, in_smartlead = true
```

### 3. Event Tracking (Smartlead → Supabase)

```
Smartlead webhook fires (open, click, reply)
    ↓
Payload contains smartlead_lead_id
    ↓
Query: SELECT id FROM leads WHERE smartlead_lead_id = {payload.lead_id}
    ↓
Insert into analytics_events with Supabase UUID as foreign key
```

---

## Schema

### Leads Table (Updated)

```sql
CREATE TABLE leads (
    -- Master identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- External system IDs
    clay_id TEXT UNIQUE,                    -- Clay record ID (optional)
    smartlead_lead_id INTEGER UNIQUE,       -- Smartlead internal ID (set after sync)

    -- Universal matching key
    email TEXT UNIQUE NOT NULL,

    -- Lead data
    first_name TEXT,
    last_name TEXT,
    company TEXT,
    domain TEXT,

    -- Scoring
    score INTEGER,
    tier TEXT CHECK (tier IN ('A', 'B', 'C')),

    -- Sync tracking
    in_smartlead BOOLEAN DEFAULT false,
    smartlead_campaign_ids INTEGER[],
    last_smartlead_sync TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE UNIQUE INDEX idx_leads_email ON leads(email);
CREATE UNIQUE INDEX idx_leads_smartlead_id ON leads(smartlead_lead_id) WHERE smartlead_lead_id IS NOT NULL;
CREATE INDEX idx_leads_in_smartlead ON leads(in_smartlead) WHERE in_smartlead = false;
```

### Migration: Add smartlead_lead_id

```sql
-- Migration: add_smartlead_lead_id
ALTER TABLE leads ADD COLUMN IF NOT EXISTS smartlead_lead_id INTEGER;
CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_smartlead_id ON leads(smartlead_lead_id) WHERE smartlead_lead_id IS NOT NULL;
```

---

## Matching Logic

### Primary Match (Preferred)

```python
# When smartlead_lead_id exists
lead = supabase.from_('leads').select('*').eq('smartlead_lead_id', smartlead_id).single()
```

### Fallback Match (Legacy Data)

```python
# When smartlead_lead_id is null, match by email
lead = supabase.from_('leads').select('*').eq('email', email).single()
```

### Reconciliation Script

```python
def reconcile_smartlead_ids():
    """
    One-time script to backfill smartlead_lead_id for existing synced leads.
    """
    # Get leads marked in_smartlead but missing smartlead_lead_id
    leads = supabase.from_('leads') \
        .select('id, email') \
        .eq('in_smartlead', True) \
        .is_('smartlead_lead_id', 'null') \
        .execute()

    for lead in leads.data:
        # Query Smartlead by email
        sl_lead = smartlead.get_lead_by_email(lead['email'])

        if sl_lead:
            # Write back smartlead_lead_id
            supabase.from_('leads') \
                .update({'smartlead_lead_id': sl_lead['id']}) \
                .eq('id', lead['id']) \
                .execute()
```

---

## Sync Script (Pseudocode)

```python
def sync_leads_to_smartlead(tier: str, campaign_id: int):
    """
    Sync leads from Supabase to Smartlead with ID writeback.
    """
    # 1. Get unsyced leads for tier
    leads = supabase.from_('leads') \
        .select('id, email, first_name, last_name, company') \
        .eq('tier', tier) \
        .eq('in_smartlead', False) \
        .execute()

    for lead in leads.data:
        # 2. Add to Smartlead
        response = smartlead.add_lead_to_campaign(
            campaign_id=campaign_id,
            email=lead['email'],
            first_name=lead['first_name'],
            last_name=lead['last_name'],
            company_name=lead['company']
        )

        # 3. Write back Smartlead ID
        if response.get('lead_id'):
            supabase.from_('leads') \
                .update({
                    'smartlead_lead_id': response['lead_id'],
                    'in_smartlead': True,
                    'smartlead_campaign_ids': [campaign_id],
                    'last_smartlead_sync': datetime.utcnow().isoformat()
                }) \
                .eq('id', lead['id']) \
                .execute()
```

---

## ID Summary

| Column | Type | Source | Purpose |
|--------|------|--------|---------|
| `id` | UUID | Supabase (auto) | Master identifier |
| `clay_id` | TEXT | Clay | Enrichment tracking |
| `smartlead_lead_id` | INTEGER | Smartlead (writeback) | Campaign operations |
| `email` | TEXT | Clay/manual | Unique constraint, fallback match |

---

## Rules

1. **Never use Clay ID as primary key** - Clay IDs change when leads are re-enriched
2. **Always write back Smartlead ID** - Enables direct API operations on leads
3. **Email is fallback, not primary** - Use for reconciliation when IDs are missing
4. **Supabase UUID is immutable** - Never changes once created
