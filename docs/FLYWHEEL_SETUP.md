# HVAC GTM Flywheel Setup Guide

**Complete automation system:** Clay → n8n → Supabase → Smartlead

**Last Updated:** November 19, 2025

---

## Architecture Overview

```
┌─────────────────── AUTOMATED FLYWHEEL ───────────────────┐
│                                                           │
│  Clay (enrichment)                                        │
│    ↓ webhook trigger                                      │
│  n8n: Parse → Score (Railway) → Supabase                  │
│    ↓ lead stored in DB                                    │
│  Supabase: Single source of truth                         │
│    ↓ manual trigger or schedule                           │
│  n8n: Query ready leads → Add to Smartlead campaigns      │
│    ↓ engagement events                                    │
│  Smartlead → n8n webhook → Supabase analytics             │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

**Key Benefits:**
- ✅ **No manual CSV exports** - Clay webhooks directly to n8n
- ✅ **Single source of truth** - All lead data in Supabase
- ✅ **Real-time analytics** - Smartlead events flow back to Supabase
- ✅ **Version-controlled sequences** - Email copy in database, not hardcoded
- ✅ **One workflow** - Everything in a single n8n workflow

---

## Prerequisites

### 1. Supabase Project
- ✅ Created and migrations applied (schema, views, functions)
- ✅ Service role key available
- ✅ Postgres connection URL

### 2. n8n Instance
- Self-hosted or n8n Cloud
- Webhook URLs publicly accessible
- Environment variables configured

### 3. Existing Services
- Clay account with enrichment tables
- Railway scoring API: `https://hvac-scoring-2025-production.up.railway.app`
- Smartlead account with API key

### 4. Optional
- Slack webhook URL for reply notifications

---

## Step 1: Supabase Setup (Already Complete)

The following migrations have been applied:

1. **Schema migration** - Creates 5 tables:
   - `leads` - Master lead database
   - `campaign_tracking` - Lead → campaign mapping
   - `analytics_events` - Engagement tracking
   - `sequence_templates` - Email copy (9 sequences loaded)
   - `campaigns` - Smartlead campaign metadata

2. **Views migration** - Analytics dashboards:
   - `lead_performance` - Per-lead engagement summary
   - `campaign_performance` - Campaign-level metrics
   - `tier_performance` - A/B/C tier comparison
   - `daily_activity_stats` - Daily event counts
   - `leads_ready_for_campaigns` - Unassigned leads
   - `recent_replies` - Last 100 replies

3. **Functions migration** - Helper functions:
   - `sync_lead_from_clay()` - Upserts lead data
   - `record_smartlead_event()` - Records engagement events
   - `get_leads_for_campaign()` - Returns leads ready for campaigns

4. **Seed data** - Loaded 9 email sequences (A1-A4, B1-B3, C1-C2)

**Verify setup:**
```sql
-- Check tables exist
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- Check sequences loaded
SELECT tier, sequence_number, subject FROM sequence_templates ORDER BY tier, sequence_number;

-- Check views
SELECT * FROM leads_ready_for_campaigns LIMIT 5;
```

---

## Step 2: n8n Setup

### Install the Workflow

1. **Import workflow JSON:**
   ```bash
   # In n8n UI: Workflows → Import from File
   # Upload: n8n/hvac_gtm_flywheel.json
   ```

2. **Configure Supabase connection:**
   - Go to: Credentials → Add Credential → Postgres
   - Name: `Supabase Postgres`
   - Host: `db.[your-project-ref].supabase.co`
   - Database: `postgres`
   - User: `postgres`
   - Password: `[your-supabase-password]`
   - Port: `5432`
   - SSL: `require`

3. **Set environment variables:**
   ```bash
   # In n8n settings or .env file
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   SUPABASE_SERVICE_KEY=eyJhbGc...  # Optional for direct API calls
   ```

4. **Activate the workflow:**
   - Click "Active" toggle in top-right
   - Verify webhook URLs are shown

5. **Note your webhook URLs:**
   ```
   Clay webhook: https://your-n8n.app/webhook/clay
   Smartlead webhook: https://your-n8n.app/webhook/smartlead-events
   ```

---

## Step 3: Clay Integration

### Configure Clay to Send Webhooks

**Complete Guide:** See [docs/CLAY_WEBHOOK_SETUP.md](CLAY_WEBHOOK_SETUP.md) for full step-by-step instructions.

**Quick Setup:**

1. **In your Clay table, add HTTP API column:**
   - Column type: `Enrich Data > HTTP API`
   - Method: `POST`
   - URL: `https://your-n8n.app/webhook/clay-webhook`

2. **Request body (JSON):**
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

**Important:** Clay must complete scoring **before** sending webhook. Include score, tier, and messaging_strategy fields.

3. **Test with one lead:**
   - Select a row
   - Run the HTTP API column
   - Check n8n execution log
   - Verify lead appears in Supabase `leads` table

**Detailed Instructions:** [docs/CLAY_WEBHOOK_SETUP.md](CLAY_WEBHOOK_SETUP.md)

---

## Step 4: Smartlead Webhook Configuration

### Set Up Engagement Event Webhooks

1. **In each Smartlead campaign:**
   - Go to: Campaign Settings → Webhooks
   - Click "Add Webhook"

2. **Webhook configuration:**
   - Name: `n8n GTM Flywheel`
   - URL: `https://your-n8n.app/webhook/smartlead-events`
   - Events to send:
     - ✅ Email Sent
     - ✅ Email Opened
     - ✅ Email Clicked
     - ✅ Email Replied
     - ✅ Email Bounced
     - ✅ Unsubscribed

3. **Repeat for all 3 campaigns (A/B/C tiers)**

4. **Test webhook:**
   - Send test email in Smartlead
   - Check n8n execution log
   - Verify event appears in Supabase `analytics_events` table

---

## Step 5: Testing End-to-End

### Test 1: Clay → Supabase

```bash
# Send test webhook to n8n
curl -X POST https://your-n8n.app/webhook/clay \
  -H "Content-Type: application/json" \
  -d '{
    "clay_id": "test-123",
    "email": "john@testhvac.com",
    "first_name": "John",
    "last_name": "Doe",
    "company": "Test HVAC Co",
    "reviews_count": 150,
    "service_software": "ServiceTitan"
  }'
```

**Verify in Supabase:**
```sql
SELECT * FROM leads WHERE email = 'john@testhvac.com';
-- Should show: score = 27, tier = 'A', messaging_strategy = '...'
```

### Test 2: Smartlead → Supabase

```bash
# Send test event
curl -X POST https://your-n8n.app/webhook/smartlead-events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "OPENED",
    "lead_email": "john@testhvac.com",
    "campaign_id": 2677089,
    "sequence_number": 1,
    "subject": "Test email",
    "stats_id": "test-stats-123"
  }'
```

**Verify in Supabase:**
```sql
SELECT * FROM analytics_events WHERE lead_id = (SELECT id FROM leads WHERE email = 'john@testhvac.com');
-- Should show the OPENED event
```

### Test 3: Manual Lead Add to Campaign

1. **In n8n, click "Execute Workflow" on manual trigger node**
2. **Workflow will:**
   - Query `leads_ready_for_campaigns` view
   - Get active campaigns for current month
   - Add top-scoring leads to Smartlead (respects daily limits)
   - Update `campaign_tracking` table

3. **Verify in Supabase:**
```sql
SELECT * FROM campaign_tracking ORDER BY added_at DESC LIMIT 10;
```

---

## Step 6: Daily Operations

### How the Flywheel Runs

**Daily (Automated):**
1. **Clay enriches leads** → Triggers n8n webhook
2. **n8n processes lead:**
   - Scores via Railway API
   - Upserts to Supabase `leads` table
3. **You manually trigger "Add to Campaigns"** (or schedule it)
4. **n8n adds ready leads** to active Smartlead campaigns
5. **Smartlead sends emails** → Triggers engagement webhooks
6. **n8n records events** in Supabase `analytics_events`

**Manual triggers:**
- Add leads to campaigns: Click "Execute Workflow" in n8n
- Create monthly campaigns: Runs automatically 1st of month (or manual)

---

## Step 7: Monitoring & Analytics

### Supabase Dashboard Queries

**Check lead pipeline health:**
```sql
-- Leads by tier and status
SELECT
  tier,
  COUNT(*) as total_leads,
  COUNT(DISTINCT CASE WHEN EXISTS (
    SELECT 1 FROM campaign_tracking ct
    WHERE ct.lead_id = leads.id
  ) THEN leads.id END) as in_campaigns,
  ROUND(AVG(score), 2) as avg_score
FROM leads
GROUP BY tier
ORDER BY tier;
```

**Campaign performance:**
```sql
SELECT * FROM campaign_performance
ORDER BY campaign_month DESC, tier;
```

**Recent activity:**
```sql
SELECT * FROM daily_activity_stats
WHERE activity_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY activity_date DESC, event_type;
```

**Leads ready to send:**
```sql
SELECT tier, COUNT(*) as ready_leads
FROM leads_ready_for_campaigns
GROUP BY tier;
```

### n8n Execution Monitoring

1. **View executions:** n8n → Executions tab
2. **Check for errors:** Filter by "Error" status
3. **Review data flow:** Click execution → View input/output per node

---

## Troubleshooting

### Issue: Clay webhook not triggering n8n

**Check:**
- Is n8n workflow active?
- Is webhook URL correct in Clay HTTP API column?
- Check n8n execution log for incoming requests

**Fix:**
```bash
# Test manually
curl -X POST https://your-n8n.app/webhook/clay \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

### Issue: Lead not appearing in Supabase

**Check:**
- Did Railway scoring API return valid response?
- Check n8n execution log for "Upsert to Supabase" node
- Is email valid format?

**Fix:**
```sql
-- Check if lead exists
SELECT * FROM leads WHERE email = 'problem@example.com';

-- Check for constraint violations
SELECT * FROM pg_stat_activity WHERE state = 'idle in transaction';
```

### Issue: Smartlead webhooks not working

**Check:**
- Is webhook URL publicly accessible?
- Are webhooks enabled in Smartlead campaign settings?
- Check Smartlead webhook execution logs

**Fix:**
```bash
# Test webhook manually
curl -X POST https://your-n8n.app/webhook/smartlead-events \
  -H "Content-Type: application/json" \
  -d '{"event_type": "SENT", "lead_email": "test@example.com", "campaign_id": 123}'
```

### Issue: Duplicate leads in Supabase

**Not a problem!** The `sync_lead_from_clay()` function uses `ON CONFLICT (email) DO UPDATE`, so duplicates are automatically handled.

**Verify:**
```sql
-- Check for duplicate emails (should return 0 rows)
SELECT email, COUNT(*)
FROM leads
GROUP BY email
HAVING COUNT(*) > 1;
```

---

## Advanced Configuration

### Monthly Campaign Auto-Creation

The workflow includes a scheduled trigger (1st of each month) to create campaigns. To customize:

1. **Edit the "Monthly Campaign Builder" schedule node**
2. **Update cron expression:**
   - `0 0 1 * *` - 1st of month at midnight
   - `0 9 1 * *` - 1st of month at 9am
   - `0 9 * * 1` - Every Monday at 9am

3. **Add Smartlead campaign creation logic** (requires additional nodes - see below)

### A/B Testing Sequences

To test different email copy:

1. **Add new version to Supabase:**
```sql
INSERT INTO sequence_templates (tier, sequence_number, subject, body, delay_days, version, active)
VALUES ('A', 1, 'New subject line test', 'New body copy...', 0, 2, true);

-- Deactivate old version
UPDATE sequence_templates
SET active = false
WHERE tier = 'A' AND sequence_number = 1 AND version = 1;
```

2. **n8n will automatically use the active version** when creating campaigns

---

## Next Steps

### Week 1: Foundation
- [x] Supabase schema deployed
- [x] n8n workflow imported
- [ ] Clay webhook configured
- [ ] Smartlead webhooks configured
- [ ] Test end-to-end with 5 leads

### Week 2: Automation
- [ ] Add 50 leads from Clay
- [ ] Monitor n8n executions
- [ ] Verify analytics in Supabase
- [ ] Configure Slack notifications

### Week 3: Scale
- [ ] Add 200+ leads
- [ ] Build Supabase dashboard in Retool/Grafana
- [ ] Set up daily reports (email or Slack)
- [ ] Optimize sequence templates based on data

### Future Enhancements
- [ ] Auto-create monthly campaigns (currently manual trigger)
- [ ] Lead scoring model updates based on conversion data
- [ ] Reply sentiment analysis (AI categorization)
- [ ] Automatic lead re-engagement after 6 months
- [ ] Integration with Patrick's CRM

---

## Support & Resources

**Documentation:**
- Supabase docs: https://supabase.com/docs
- n8n docs: https://docs.n8n.io
- Smartlead API: https://helpcenter.smartlead.ai/en/articles/125-full-api-documentation

**Troubleshooting:**
1. Check n8n execution logs
2. Query Supabase tables directly
3. Review this document
4. Check `docs/` folder for campaign-specific guides

**Contact:**
- Questions about setup: Review this doc
- Questions about sequences: See `sequences/sequences_11_2025_appletree.txt`
- Questions about scoring: See `scripts/scoring/main.py`

---

**Last Updated:** November 19, 2025
**Maintained by:** Shane + Claude (Appletree HVAC GTM Flywheel)
