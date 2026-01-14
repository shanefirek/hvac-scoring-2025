# Clay Webhook Configuration Guide

**Configure Clay to automatically send scored leads to n8n → Supabase → Smartlead**

**Last Updated:** November 19, 2025

---

## Overview

This guide shows how to configure Clay's HTTP API column to send webhook payloads to your n8n workflow, which will automatically:
1. Receive the lead data from Clay (with scoring already completed)
2. Store it in Supabase database
3. Make it available for Smartlead campaigns

---

## Prerequisites

- ✅ n8n workflow imported and active (`n8n/hvac_gtm_flywheel.json`)
- ✅ Supabase database deployed with migrations
- ✅ Clay table with enriched HVAC leads
- ✅ Scoring columns completed in Clay (score, tier, messaging_strategy)

---

## Step 1: Get Your n8n Webhook URL

1. Open your n8n instance
2. Navigate to the **HVAC GTM Flywheel** workflow
3. Find the **"Clay Webhook (Lead Enriched)"** node
4. Click to view webhook details
5. Copy the webhook URL:
   ```
   https://[your-n8n-instance].app.n8n.cloud/webhook/clay-webhook
   ```

**Example:**
```
https://mycompany.app.n8n.cloud/webhook/clay-webhook
```

**Important:** This URL must be publicly accessible. If you're self-hosting n8n, ensure it's exposed via ngrok or a public domain.

---

## Step 2: Add HTTP API Column in Clay

### 2.1 Create the Column

1. In your Clay table, click **Add Column**
2. Select **Enrich Data** → **HTTP API**
3. Name it: `Send to n8n`

### 2.2 Configure HTTP Request

**Method:** `POST`

**URL:** (paste your webhook URL from Step 1)
```
https://[your-n8n-instance].app.n8n.cloud/webhook/clay-webhook
```

**Headers:**
```
Content-Type: application/json
```

**Body Type:** `Raw JSON`

---

## Step 3: Build the JSON Payload

### Required Fields

Your Clay table must have these columns completed **before** sending the webhook:

| Clay Column | Required | Description |
|-------------|----------|-------------|
| `Email` | ✅ | Lead email address |
| `First Name` | ✅ | First name |
| `Last Name` | ⚠️ | Last name (optional but recommended) |
| `Company` | ✅ | Company name |
| `Score` | ✅ | Lead score (0-30) |
| `Tier` | ✅ | A/B/C tier classification |
| `Messaging Strategy` | ✅ | Assigned messaging strategy |
| `Domain` | ⚠️ | Website domain (optional) |
| `Linkedin Url` | ⚠️ | LinkedIn profile URL (optional) |
| `Reviews Count` | ⚠️ | Google reviews count (optional) |
| `Field Service Tech` | ⚠️ | FSM software detected (optional) |

### JSON Body Template

```json
{
  "clay_id": "{{record_id}}",
  "email": "{{Email}}",
  "first_name": "{{First Name}}",
  "last_name": "{{Last Name}}",
  "company": "{{Company}}",
  "domain": "{{Domain}}",
  "linkedin_url": "{{Linkedin Url}}",
  "reviews_count": {{Reviews Count}},
  "service_software": "{{Field Service Tech}}",
  "score": {{Score}},
  "tier": "{{Tier}}",
  "messaging_strategy": "{{Messaging Strategy}}",
  "score_breakdown": {
    "service_software": {{Score - Service Software}},
    "reviews": {{Score - Reviews}},
    "linkedin": {{Score - LinkedIn}},
    "domain": {{Score - Domain}}
  }
}
```

**Important Notes:**
- Replace `{{Column Name}}` with your actual Clay column names (case-sensitive!)
- Numeric fields (reviews_count, score) should NOT have quotes
- String fields must have quotes
- Use `record_id` for the unique Clay record identifier

---

## Step 4: Test the Webhook

### 4.1 Test with One Lead

1. Select a single row in your Clay table
2. Click **Run** on the HTTP API column
3. Check the response:

**Success Response:**
```json
{
  "success": true,
  "lead_id": "uuid-of-created-lead",
  "email": "john@hvac.com"
}
```

**Error Response:**
```json
{
  "error": "Missing required field: email"
}
```

### 4.2 Verify in Supabase

1. Open your Supabase dashboard
2. Go to **Database** → **Table Editor**
3. Open the `leads` table
4. Look for the most recently created lead:

```sql
SELECT * FROM leads
ORDER BY created_at DESC
LIMIT 1;
```

**Expected Result:**
- Email matches the Clay lead
- Score, tier, and messaging_strategy are populated
- `last_enriched_at` timestamp is recent

---

## Step 5: Configure When to Run

You have three options for triggering the webhook:

### Option A: Manual Trigger (Recommended for Testing)
- Select leads you want to send
- Click **Run** on the HTTP API column
- Good for: Testing, quality control, selective sending

### Option B: Auto-Run on New Rows
1. Click the HTTP API column settings (⚙️)
2. Enable **Auto-run on new rows**
3. New leads will automatically sync to Supabase
4. Good for: Fully automated pipelines

### Option C: Scheduled Batch Run
1. Use Clay's automation features
2. Set up a weekly/daily schedule
3. Run HTTP API column on all unprocessed leads
4. Good for: Batch processing, controlled sending

---

## Step 6: Bulk Send (After Testing)

Once you've verified the webhook works correctly:

1. Select all leads you want to send (up to 1000 at a time)
2. Click **Run** on the HTTP API column
3. Clay will process them sequentially (may take 5-10 minutes for 100+ leads)
4. Monitor the response column for any errors

**Verify Bulk Import:**
```sql
SELECT tier, COUNT(*) as lead_count
FROM leads
WHERE created_at >= NOW() - INTERVAL '1 hour'
GROUP BY tier
ORDER BY tier;
```

---

## Troubleshooting

### Issue: "Webhook URL not accessible"

**Symptoms:**
- Clay shows connection timeout
- No response received

**Fix:**
1. Verify n8n workflow is **Active** (toggle in top-right)
2. Test the webhook URL in your browser (should return 404 or method not allowed, not connection refused)
3. If self-hosting, ensure n8n is publicly accessible (use ngrok for testing)

### Issue: "Missing required field" error

**Symptoms:**
```json
{
  "error": "Missing required field: email"
}
```

**Fix:**
1. Check that all required Clay columns exist and are filled
2. Verify column names match exactly (case-sensitive)
3. Ensure no empty strings (use Clay's "If empty" formula to handle)

### Issue: Lead appears in Supabase but score is 0

**Symptoms:**
- Lead created successfully
- Score/tier/messaging_strategy are null or 0

**Fix:**
1. Verify scoring columns are completed in Clay **before** sending webhook
2. Check that JSON payload uses correct field names
3. Ensure numeric fields don't have quotes: `"score": {{Score}}` not `"score": "{{Score}}"`

### Issue: Duplicate leads created

**Symptoms:**
- Same email appears multiple times in Supabase

**Expected Behavior:**
- n8n workflow uses `sync_lead_from_clay()` which does UPSERT
- Duplicates should be prevented automatically

**If duplicates occur:**
1. Check Supabase function is working:
   ```sql
   SELECT * FROM leads WHERE email = 'duplicate@example.com';
   ```
2. Verify the `sync_lead_from_clay()` function exists and has UPSERT logic
3. Check n8n execution logs for errors

---

## Advanced Configuration

### Add Custom Fields

To track additional data from Clay, modify the JSON payload:

```json
{
  "clay_id": "{{record_id}}",
  "email": "{{Email}}",
  ...
  "custom_field_1": "{{Your Custom Column}}",
  "custom_field_2": {{Your Numeric Column}}
}
```

Then update the Supabase `leads` table to include these columns.

### Conditional Sending

Only send leads that meet certain criteria:

1. Use Clay's **If** formula to create a "Ready to Send" column
2. Only run HTTP API on leads where "Ready to Send" = TRUE
3. Example conditions:
   - Score > 10
   - Tier = A or B
   - Email verified = TRUE

---

## Monitoring & Analytics

### Check Recent Webhook Activity

In n8n:
1. Go to **Executions** tab
2. Filter by "Clay Webhook (Lead Enriched)"
3. View success/failure rates

### Monitor Lead Import Rate

In Supabase:
```sql
SELECT
  DATE(created_at) as date,
  COUNT(*) as leads_added,
  AVG(score) as avg_score
FROM leads
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### View Leads Ready for Campaigns

```sql
SELECT * FROM leads_ready_for_campaigns
ORDER BY score DESC
LIMIT 50;
```

---

## Example Payload

Here's a complete example of what Clay will send:

```json
{
  "clay_id": "rec_abc123def456",
  "email": "john.smith@johnstonhvac.com",
  "first_name": "John",
  "last_name": "Smith",
  "company": "Johnston HVAC Services",
  "domain": "johnstonhvac.com",
  "linkedin_url": "https://linkedin.com/in/johnsmith-hvac",
  "reviews_count": 247,
  "service_software": "ServiceTitan",
  "score": 27,
  "tier": "A",
  "messaging_strategy": "Software + Scale: Tech-forward operator with systems in place",
  "score_breakdown": {
    "service_software": 15,
    "reviews": 10,
    "linkedin": 3,
    "domain": 2
  }
}
```

**Expected n8n Processing:**
1. Webhook receives payload
2. Parses Clay data
3. Calls Supabase `sync_lead_from_clay()` function via REST API
4. Returns success response to Clay

**Expected Supabase Result:**
```sql
-- Query
SELECT email, company, score, tier, messaging_strategy
FROM leads
WHERE email = 'john.smith@johnstonhvac.com';

-- Result
| email                          | company                  | score | tier | messaging_strategy                                              |
|--------------------------------|--------------------------|-------|------|-----------------------------------------------------------------|
| john.smith@johnstonhvac.com    | Johnston HVAC Services   | 27    | A    | Software + Scale: Tech-forward operator with systems in place   |
```

---

## Next Steps

After successfully configuring Clay webhooks:

1. **Import 5-10 test leads** - Verify end-to-end flow
2. **Bulk import remaining leads** - Send all scored leads to Supabase
3. **Add leads to Smartlead campaigns** - Use n8n manual trigger
4. **Configure Smartlead webhooks** - Enable engagement tracking (see `docs/FLYWHEEL_SETUP.md`)

---

## Support

**Documentation:**
- Full flywheel setup: [docs/FLYWHEEL_SETUP.md](FLYWHEEL_SETUP.md)
- Supabase schema: [docs/SUPABASE_SCHEMA.md](SUPABASE_SCHEMA.md)
- Quick start: [docs/FLYWHEEL_QUICKSTART.md](FLYWHEEL_QUICKSTART.md)

**Troubleshooting:**
1. Check n8n execution logs
2. Query Supabase leads table directly
3. Review this guide for common issues

---

**Last Updated:** November 19, 2025
**Status:** ✅ Ready to use
