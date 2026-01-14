# Clay → n8n → Supabase Integration Setup

**Goal:** Sync 500 enriched leads from Clay to Supabase via n8n webhook

**Time:** 10 minutes

---

## Step 1: Get Your n8n Webhook URL

### **In n8n:**

1. Open your workflow: "HVAC GTM Flywheel - Clay → Supabase → Smartlead"
2. Click the **"Clay Webhook (Lead Enriched)"** node
3. Click **"Copy Production Webhook URL"** button
4. It will look like: `https://your-instance.app.n8n.cloud/webhook/clay-webhook`

**Save this URL** - you'll paste it in Clay.

---

## Step 2: Configure Clay HTTP API Column

### **In Clay Table:**

1. **Add a new column** → **Integrations** → **HTTP API**
2. **Name it:** "Sync to Supabase"

### **HTTP API Configuration:**

**URL:**
```
https://your-instance.app.n8n.cloud/webhook/clay-webhook
```

**Method:** `POST`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "clay_id": "{{Row ID}}",
  "email": "{{Email}}",
  "first_name": "{{First Name}}",
  "last_name": "{{Last Name}}",
  "company": "{{Company}}",
  "domain": "{{Domain}}",
  "linkedin_url": "{{LinkedIn URL}}",
  "reviews_count": {{Reviews Count}},
  "service_software": "{{Service Software}}",
  "score": {{Score}},
  "tier": "{{Tier}}",
  "messaging_strategy": "{{Messaging Strategy}}",
  "score_breakdown": {{Score Breakdown}}
}
```

**Important:**
- Replace `{{Field Name}}` with your actual Clay column names
- Numbers (reviews_count, score) don't have quotes
- JSONB fields (score_breakdown) don't have quotes if they're already JSON

---

## Step 3: Map Your Clay Columns

**Match these Clay columns to the webhook payload:**

| Webhook Field | Your Clay Column Name | Example Value |
|---------------|----------------------|---------------|
| `clay_id` | Row ID (built-in) | `clay_abc123` |
| `email` | Email / Final Email | `john@hvac.com` |
| `first_name` | First Name | `John` |
| `last_name` | Last Name | `Doe` |
| `company` | Company | `HVAC Solutions Inc` |
| `domain` | Domain / Website | `hvacsolutions.com` |
| `linkedin_url` | LinkedIn URL | `https://linkedin.com/in/john` |
| `reviews_count` | Reviews Count | `150` |
| `service_software` | Service Software / FSM | `ServiceTitan` |
| `score` | Score (from API) | `27` |
| `tier` | Tier (from API) | `A` |
| `messaging_strategy` | Messaging Strategy | `Software + Scale` |
| `score_breakdown` | Score Breakdown (JSON) | `{"software": 15, "reviews": 10}` |

---

## Step 4: Example Clay HTTP API Setup

**Here's what it should look like in Clay:**

```
Column Name: Sync to Supabase
Type: HTTP API
Method: POST
URL: https://your-instance.app.n8n.cloud/webhook/clay-webhook

Body:
{
  "clay_id": "/rowId",
  "email": "/enrichments/email/final_email",
  "first_name": "/enrichments/name/first_name",
  "last_name": "/enrichments/name/last_name",
  "company": "/enrichments/company/name",
  "domain": "/enrichments/company/domain",
  "linkedin_url": "/enrichments/linkedin/url",
  "reviews_count": /enrichments/reviews/count,
  "service_software": "/enrichments/software/name",
  "score": /enrichments/scoring/score,
  "tier": "/enrichments/scoring/tier",
  "messaging_strategy": "/enrichments/scoring/strategy",
  "score_breakdown": /enrichments/scoring/breakdown
}
```

**Note:** Clay uses `/path/to/field` syntax - adjust based on your actual column paths.

---

## Step 5: Test with 1 Lead First

### **Before running on all 500:**

1. **Filter your Clay table** to show only 1 row
2. **Run the HTTP API column** on that 1 row
3. **Check for success:**
   - Response should be: `{"success": true, "lead_id": "uuid-here", "email": "john@hvac.com"}`
4. **Verify in Supabase:**
   - Go to Supabase dashboard
   - Check `leads` table
   - You should see 1 new row with that email

### **If it fails:**

**Check n8n:**
- Go to n8n → Executions tab
- Look for failed execution
- Check error message

**Common issues:**
- Wrong webhook URL
- Missing required fields (email, tier, score)
- Field name mismatch (check Clay column names)
- n8n workflow not activated (toggle in n8n UI)

---

## Step 6: Run on All 500 Leads

### **Once test succeeds:**

1. **Remove filter** from Clay table (show all rows)
2. **Select all rows** (or filter to rows you want to sync)
3. **Run the HTTP API column** on selected rows
4. **Clay will send 500 webhooks** to n8n (takes 2-5 minutes)

### **Monitor Progress:**

**In n8n:**
- Go to **Executions** tab
- You should see 500 successful executions
- Each execution = 1 lead synced

**In Supabase:**
- Go to `leads` table
- Check row count (should be 500 or close to it)
- Filter by `created_at >= today` to see new leads

---

## Step 7: Verify Data Quality

### **Quick SQL check in Supabase:**

```sql
-- Check total leads synced
SELECT COUNT(*) FROM leads;

-- Check tier distribution
SELECT tier, COUNT(*) as count
FROM leads
GROUP BY tier
ORDER BY tier;

-- Check recent leads
SELECT email, company, tier, score, created_at
FROM leads
ORDER BY created_at DESC
LIMIT 10;

-- Check for missing data
SELECT
  COUNT(*) FILTER (WHERE email IS NULL) as missing_email,
  COUNT(*) FILTER (WHERE tier IS NULL) as missing_tier,
  COUNT(*) FILTER (WHERE score IS NULL OR score = 0) as missing_score
FROM leads;
```

---

## Troubleshooting

### **"Webhook URL not found"**
- Make sure n8n workflow is **activated** (toggle in top right)
- Check webhook URL is correct (copy from n8n webhook node)

### **"Missing required field: email"**
- Check Clay column name matches exactly
- Make sure field isn't empty in Clay

### **"500 Internal Server Error"**
- Check n8n execution logs for details
- Likely a field type mismatch (string vs number)
- Check Supabase function expects correct data types

### **"Rate limit exceeded"**
- n8n Cloud has execution limits on free tier
- Consider batching (50 at a time) or upgrade plan

### **Leads not appearing in Supabase**
- Check n8n execution succeeded
- Check Supabase `leads` table
- Check `last_enriched_at` timestamp
- If lead already exists, it will update (not duplicate)

---

## Expected Results

After running on 500 leads, you should see:

**In Supabase `leads` table:**
- ~500 rows (or less if duplicates)
- All with valid `email`, `tier`, `score`
- `created_at` timestamps from today
- `last_enriched_at` timestamps from today

**In n8n Executions:**
- 500 successful executions (green checkmarks)
- Each took ~1-2 seconds
- No errors

**Next Step:**
- Now you can query `leads_ready_for_campaigns` view to get leads ready for Smartlead
- Use tier filtering to get A/B/C leads separately

---

## Clay Column Name Cheat Sheet

**If your Clay columns are named differently, update the JSON body:**

Common Clay column name variations:
- `Email` or `Final Email` or `Verified Email`
- `Company` or `Company Name` or `Organization`
- `Domain` or `Website` or `Company Domain`
- `LinkedIn URL` or `LinkedIn Profile` or `Person LinkedIn`
- `Reviews Count` or `Google Reviews` or `Review Count`
- `Service Software` or `FSM Software` or `Field Service Tech`
- `Score` (from your scoring API)
- `Tier` (A/B/C from scoring API)
- `Messaging Strategy` (from scoring API)

**Pro tip:** Click inside the JSON body field in Clay and type `/` - it will show you all available columns.

---

**Last Updated:** November 20, 2025
