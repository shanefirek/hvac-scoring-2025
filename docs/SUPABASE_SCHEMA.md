# Supabase Database Schema - Quick Reference

**Project:** Appletree HVAC Lead Pipeline  
**Database:** `rlmuovkdvbxzyylbiunj.supabase.co`  
**Last Updated:** 2025-12-07

> **For trigger.dev agents:** This doc provides complete schema knowledge without querying the database via MCP.

---

## Core Architecture

```
Outscraper/Clay → Railway APIs → leads table
Smartlead campaigns → Webhooks → analytics_events table  
Campaign tracking → Views → Analytics
```

---

## Tables

### `leads` (Master lead database)

| Column | Type | Key Info |
|--------|------|----------|
| `id` | uuid | PK, master identifier |
| `email` | text | UNIQUE, always lowercase, CHECK constraint |
| `smartlead_lead_id` | bigint | Smartlead internal ID (backfilled after sync) |
| `first_name`, `last_name` | text | Lead name |
| `company`, `domain` | text | Company info |
| `city`, `state`, `postal_code` | text | Location |
| `reviews_count` | integer | Google review count |
| `service_software` | text | ServiceTitan/Jobber/Housecall Pro |
| `score` | integer | 0-30 points |
| `tier` | text | A/B/C (A=20-30, B=10-19, C=0-9) |
| `messaging_strategy` | text | Messaging approach |
| `score_breakdown` | jsonb | Scoring details |
| `in_smartlead` | boolean | In any Smartlead campaign? |
| `smartlead_campaign_ids` | integer[] | Campaign IDs array |
| `created_at`, `updated_at` | timestamptz | Timestamps |

**Important:** Email is ALWAYS lowercase via CHECK constraint. UUID is master ID.

---

### `analytics_events` (Smartlead webhook events)

| Column | Type | Key Info |
|--------|------|----------|
| `id` | uuid | PK |
| `lead_id` | uuid | FK → leads.id (CASCADE) |
| `smartlead_campaign_id` | integer | Campaign ID |
| `smartlead_lead_id` | bigint | Smartlead lead ID |
| `event_type` | text | EMAIL_SENT/EMAIL_OPEN/EMAIL_LINK_CLICK/EMAIL_REPLIED/EMAIL_BOUNCED/etc |
| `sequence_number` | integer | Email sequence 1-10 |
| `email_subject` | text | Email subject |
| `event_data` | jsonb | Extra metadata |
| `created_at` | timestamptz | Event time |

**Valid event types:** EMAIL_SENT, EMAIL_OPEN, EMAIL_LINK_CLICK, EMAIL_REPLIED, EMAIL_BOUNCED, EMAIL_UNSUBSCRIBED, EMAIL_SPAM_COMPLAINT, LEAD_UNSUBSCRIBED, OUT_OF_OFFICE

---

### `campaign_tracking` (Campaign membership)

| Column | Type | Key Info |
|--------|------|----------|
| `id` | uuid | PK |
| `lead_id` | uuid | FK → leads.id (CASCADE), UNIQUE with campaign_id |
| `smartlead_campaign_id` | integer | Campaign ID |
| `campaign_name` | text | Campaign name |
| `tier` | text | A/B/C |
| `status` | text | SYNCED/ACTIVE/COMPLETED/PAUSED/BOUNCED/UNSUBSCRIBED |
| `sequences_sent` | integer | Sequences sent count |
| `added_at`, `last_send_at` | timestamptz | Timestamps |

**Note:** Redundant columns (`smartlead_lead_id`, `smartlead_lead_map_id`) removed Dec 2025. Use `lead_id` → `leads.smartlead_lead_id` for Smartlead lookups.

---

### `campaigns` (Campaign definitions)

| Column | Type | Key Info |
|--------|------|----------|
| `id` | uuid | PK |
| `smartlead_campaign_id` | integer | Smartlead campaign ID |
| `name` | text | Campaign name |
| `tier` | text | A/B/C |

---

### `sequence_templates` (Email sequences)

| Column | Type | Key Info |
|--------|------|----------|
| `id` | uuid | PK |
| `campaign_id` | uuid | FK → campaigns.id |
| `sequence_number` | integer | 1-10 |
| `subject` | text | Email subject |
| `body` | text | Email body template |

---

## Key RPC Functions

### `handle_smartlead_webhook()` ⭐ PRIMARY WEBHOOK FUNCTION

**Purpose:** Process Smartlead webhook events (replaces n8n)  
**Returns:** json `{success, event_id, lead_id, event_type}`

**Parameters:**
```typescript
{
  p_smartlead_lead_id: bigint,  // Smartlead lead ID (preferred)
  p_email: string,              // Email (fallback lookup)
  p_event_type: string,         // Event type (required)
  p_campaign_id: number,        // Campaign ID
  p_event_data: object          // Extra metadata
}
```

**Behavior:**
1. Lookup lead by smartlead_lead_id (preferred) or email (fallback)
2. If found by email, backfill smartlead_lead_id to leads table
3. Insert event into analytics_events
4. Update leads.updated_at

**Example (trigger.dev):**
```typescript
const { data } = await supabase.rpc('handle_smartlead_webhook', {
  p_smartlead_lead_id: payload.sl_email_lead_id,
  p_email: payload.to_email,
  p_event_type: 'EMAIL_OPEN',
  p_campaign_id: 2677089,
  p_event_data: { subject: payload.subject }
});
```

---

### `sync_lead_from_clay()`

**Purpose:** Upsert leads from enrichment pipeline  
**Returns:** uuid (lead ID)

**Key parameters:** email (required, auto-lowercased), first_name, last_name, company, domain, reviews_count, service_software, score, tier, messaging_strategy, score_breakdown, city, state, postal_code

**Behavior:** ON CONFLICT (email) DO UPDATE, keeps non-NULL values

---

## Views

### `campaign_performance`
Campaign-level metrics: total_sends, total_opens, total_clicks, total_replies, open_rate, click_rate, reply_rate

### `lead_performance`  
Lead-level engagement: total_opens, total_clicks, total_replies, first_reply_at, last_activity_at

### `tier_performance`
Tier aggregations: total_leads, avg_score, open_rate, reply_rate

### `recent_replies`
Last 100 replies with lead info, campaign, sequence number

---

## Indexes

**Fast lookups on:**
- `leads.email` (UNIQUE)
- `leads.smartlead_lead_id` (UNIQUE partial WHERE NOT NULL)
- `analytics_events.lead_id`
- `analytics_events.event_type`
- `analytics_events.created_at DESC`

---

## Foreign Keys

```
leads.id
  ├→ campaign_tracking.lead_id (CASCADE)
  │   └→ analytics_events.campaign_tracking_id (CASCADE)
  └→ analytics_events.lead_id (CASCADE)
```

**Deleting a lead cascades to all related events**

---

## Active Campaigns

| ID | Name | Tier | Daily Limit |
|----|------|------|-------------|
| 2677089 | HVAC A-Tier - Software & Scale | A | 30 |
| 2677090 | HVAC B-Tier - Growth Signal | B | 25 |
| 2677091 | HVAC C-Tier - Pain Focus | C | 30 |

---

## Scoring System

| Signal | Points |
|--------|--------|
| Service Software (ServiceTitan/Jobber/Housecall Pro) | +15 |
| Franchise | +10 |
| Reviews 500+ | +10 |
| Reviews 100-499 | +7 |
| Reviews 25-99 | +4 |
| Reviews 10-24 | +2 |
| LinkedIn URL | +3 |
| Domain | +2 |

**Tiers:** A (20-30), B (10-19), C (0-9)

---

## Security

- RLS enabled on all tables
- All access via service role key
- Email normalization enforced via CHECK constraint
- Email validation via regex CHECK constraint

---

## For trigger.dev Migration

**Current:** n8n webhook → `handle_smartlead_webhook()`  
**Future:** trigger.dev webhook → same function

**No schema changes needed** - just swap webhook URL in Smartlead campaigns.

**New webhook endpoint will:**
1. Receive Smartlead webhook POST
2. Parse payload (to_email, sl_email_lead_id, event_type, campaign_id)
3. Call `supabase.rpc('handle_smartlead_webhook', {...})`
4. Return 200 OK

**That's it!** The function handles all lead lookup, backfilling, and event insertion.
