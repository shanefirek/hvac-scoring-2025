# GTM Flywheel Quick Start

**Get your Clay → Supabase → Smartlead automation running in 30 minutes**

**Date:** November 19, 2025

---

## What Was Built

A **fully automated GTM engine** that eliminates manual CSV exports:

```
Clay enriches lead
  ↓ (automatic webhook)
n8n receives webhook
  ↓ (scores via Railway API)
Supabase stores lead
  ↓ (you click "Add to campaigns" in n8n)
n8n adds leads to Smartlead
  ↓ (Smartlead sends emails)
Smartlead webhooks engagement events
  ↓ (automatic webhook)
n8n records in Supabase
  ↓ (real-time analytics)
View dashboards in Supabase
```

---

## What's Already Done ✅

### Supabase Database (3 Migrations Applied)

**Tables:**
- ✅ `leads` - Master lead database (160+ leads ready to migrate)
- ✅ `campaign_tracking` - Lead → campaign mapping
- ✅ `analytics_events` - Engagement tracking (opens, clicks, replies)
- ✅ `sequence_templates` - **9 sequences loaded** (A1-A4, B1-B3, C1-C2)
- ✅ `campaigns` - Campaign metadata

**Views (Analytics):**
- ✅ `lead_performance` - Per-lead engagement
- ✅ `campaign_performance` - Campaign metrics
- ✅ `tier_performance` - A/B/C comparison
- ✅ `daily_activity_stats` - Daily event counts
- ✅ `leads_ready_for_campaigns` - Unassigned leads
- ✅ `recent_replies` - Last 100 replies

**Functions:**
- ✅ `sync_lead_from_clay()` - Upsert leads from webhooks
- ✅ `record_smartlead_event()` - Record engagement events
- ✅ `get_leads_for_campaign()` - Get leads ready to send

### n8n Workflow

- ✅ Single workflow JSON created (`n8n/hvac_gtm_flywheel.json`)
- ✅ Clay webhook handler (parse → score → upsert)
- ✅ Smartlead event handler (opens, clicks, replies)
- ✅ Manual trigger to add leads to campaigns
- ✅ Monthly campaign builder (scheduled)

### Documentation

- ✅ `docs/FLYWHEEL_SETUP.md` - Complete setup guide
- ✅ `docs/SUPABASE_SCHEMA.md` - Database reference
- ✅ `docs/FLYWHEEL_QUICKSTART.md` - This file
- ✅ `README.md` updated with flywheel architecture

---

## Next Steps (30 Minutes to Launch)

### Step 1: Import n8n Workflow (5 min)

1. Open your n8n instance
2. Click **Workflows** → **Import from File**
3. Upload: `n8n/hvac_gtm_flywheel.json`
4. Click **Save**

### Step 2: Configure Supabase Connection (10 min)

1. In n8n, go to **Credentials** → **Add Credential**
2. Select **Postgres**
3. Fill in details:
   ```
   Name: Supabase Postgres
   Host: db.[YOUR-PROJECT-REF].supabase.co
   Database: postgres
   User: postgres
   Password: [YOUR-SUPABASE-PASSWORD]
   Port: 5432
   SSL: Require
   ```
4. Click **Test** → Should see "Connection successful"
5. Click **Save**

### Step 3: Activate Workflow and Get Webhook URLs (2 min)

1. In n8n workflow, click **Active** toggle (top-right)
2. Note your webhook URLs:
   ```
   Clay webhook:
   https://[your-n8n].app/webhook/clay

   Smartlead webhook:
   https://[your-n8n].app/webhook/smartlead-events
   ```
3. Copy both URLs to a note

### Step 4: Configure Clay Webhook (8 min)

1. Open your Clay table with enriched HVAC leads
2. Add new column: **Enrich Data → HTTP API**
3. Configure:
   - **Method:** POST
   - **URL:** `https://[your-n8n].app/webhook/clay`
   - **Headers:** `Content-Type: application/json`
   - **Body:**
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
       "service_software": "{{Field Service Tech}}"
     }
     ```
4. Click **Run** on one lead to test
5. Check n8n execution log (should see successful execution)
6. Check Supabase:
   ```sql
   SELECT * FROM leads ORDER BY created_at DESC LIMIT 1;
   ```

### Step 5: Test with 5 Leads (5 min)

1. In Clay, select 5 leads
2. Run the HTTP API column on all 5
3. Verify in Supabase:
   ```sql
   SELECT email, tier, score, messaging_strategy
   FROM leads
   ORDER BY created_at DESC
   LIMIT 5;
   ```
4. All 5 should appear with scores and tiers

---

## How to Use Daily

### Add Leads to Smartlead Campaigns

**Manual Trigger (Recommended for now):**

1. Open n8n workflow
2. Click **Execute Workflow** on "Manual: Add Leads to Campaigns" node
3. Workflow will:
   - Query `leads_ready_for_campaigns`
   - Add top-scoring leads to Smartlead (respects daily limits)
   - Update `campaign_tracking` table

**View added leads:**
```sql
SELECT
  l.email,
  l.tier,
  ct.campaign_name,
  ct.added_at
FROM campaign_tracking ct
JOIN leads l ON ct.lead_id = l.id
WHERE ct.added_at >= CURRENT_DATE
ORDER BY ct.added_at DESC;
```

### Monitor Engagement

**View today's activity:**
```sql
SELECT
  event_type,
  COUNT(*) as events,
  COUNT(DISTINCT lead_id) as unique_leads
FROM analytics_events
WHERE created_at >= CURRENT_DATE
GROUP BY event_type
ORDER BY events DESC;
```

**View recent replies:**
```sql
SELECT * FROM recent_replies
WHERE reply_time >= CURRENT_DATE
ORDER BY reply_time DESC;
```

**Campaign performance:**
```sql
SELECT * FROM campaign_performance
ORDER BY campaign_month DESC, tier;
```

---

## Troubleshooting

### "Lead not appearing in Supabase"

**Check:**
1. Did n8n execution succeed? (Check execution log)
2. Did Railway scoring API respond? (Check n8n node output)
3. Is email valid? (Constraint violation)

**Fix:**
```sql
-- Check if lead exists
SELECT * FROM leads WHERE email = 'problem@example.com';
```

### "Webhook not triggering n8n"

**Check:**
1. Is workflow **Active**?
2. Is webhook URL correct in Clay?
3. Is n8n instance publicly accessible?

**Fix:**
```bash
# Test webhook manually
curl -X POST https://[your-n8n].app/webhook/clay \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "company": "Test Co"}'
```

### "Smartlead events not recording"

**Check:**
1. Are webhooks configured in Smartlead campaigns?
2. Is webhook URL correct?
3. Are events being sent? (Check Smartlead webhook logs)

**Fix:**
Configure webhooks in each Smartlead campaign:
- Settings → Webhooks → Add Webhook
- URL: `https://[your-n8n].app/webhook/smartlead-events`
- Events: SENT, OPENED, CLICKED, REPLIED, BOUNCED, UNSUBSCRIBED

---

## Migration from Manual CSV Workflow

### Import Your 160 Existing Leads

**Option 1: Bulk import via SQL**
```sql
-- Export your current CSV to Supabase
-- Use Supabase dashboard: Database → Import data
```

**Option 2: Trigger Clay webhook for all rows**
1. Select all leads in Clay
2. Run HTTP API column on all rows
3. Wait for n8n to process (will take ~5-10 minutes for 160 leads)

**Verify import:**
```sql
SELECT tier, COUNT(*) as lead_count
FROM leads
GROUP BY tier
ORDER BY tier;

-- Expected:
-- A | 16
-- B | 28
-- C | 106
```

---

## Analytics Dashboard (Bonus)

### Useful Queries

**Pipeline health:**
```sql
SELECT
  tier,
  COUNT(*) as total,
  COUNT(DISTINCT CASE
    WHEN EXISTS (SELECT 1 FROM campaign_tracking ct WHERE ct.lead_id = leads.id)
    THEN leads.id
  END) as in_campaigns,
  COUNT(*) - COUNT(DISTINCT CASE
    WHEN EXISTS (SELECT 1 FROM campaign_tracking ct WHERE ct.lead_id = leads.id)
    THEN leads.id
  END) as ready_to_add
FROM leads
GROUP BY tier;
```

**Reply rate by tier:**
```sql
SELECT * FROM tier_performance
ORDER BY reply_rate DESC;
```

**Today's adds:**
```sql
SELECT
  ct.tier,
  COUNT(*) as leads_added
FROM campaign_tracking ct
WHERE ct.added_at >= CURRENT_DATE
GROUP BY ct.tier;
```

---

## What's Next

### Week 1: Foundation
- [ ] Import n8n workflow
- [ ] Configure Clay webhook
- [ ] Test with 5 leads
- [ ] Migrate 160 existing leads
- [ ] Configure Smartlead webhooks

### Week 2: Automation
- [ ] Add new leads daily from Clay
- [ ] Monitor analytics in Supabase
- [ ] Build custom dashboards (Retool, Grafana, or Metabase)
- [ ] Set up Slack notifications for replies

### Week 3: Optimization
- [ ] A/B test sequence versions
- [ ] Analyze tier performance
- [ ] Adjust scoring weights based on conversions
- [ ] Scale to 500+ leads

---

## Support

**Documentation:**
- Full setup: [docs/FLYWHEEL_SETUP.md](FLYWHEEL_SETUP.md)
- Database schema: [docs/SUPABASE_SCHEMA.md](SUPABASE_SCHEMA.md)
- Campaign setup: [docs/SMARTLEAD_SETUP.md](SMARTLEAD_SETUP.md)

**Quick Links:**
- Supabase dashboard: https://supabase.com/dashboard
- n8n docs: https://docs.n8n.io
- Smartlead API: https://helpcenter.smartlead.ai

---

**Built:** November 19, 2025
**Status:** ✅ Ready to deploy
**Estimated Setup Time:** 30 minutes
