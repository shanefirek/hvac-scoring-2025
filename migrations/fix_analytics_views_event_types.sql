-- Fix analytics views to use correct event type names
-- Issue: Views were looking for SENT/OPENED/CLICKED but database has EMAIL_SENT/EMAIL_OPEN/EMAIL_LINK_CLICK

-- Fix campaign_performance view
CREATE OR REPLACE VIEW campaign_performance AS
SELECT
  c.id AS campaign_id,
  c.smartlead_campaign_id,
  c.name AS campaign_name,
  c.tier,
  c.campaign_month,
  c.status,
  c.daily_send_limit,
  c.created_at,
  c.started_at,
  COUNT(DISTINCT ct.lead_id) AS total_leads,
  COUNT(DISTINCT CASE WHEN ct.status = 'ACTIVE' THEN ct.lead_id END) AS active_leads,
  COUNT(DISTINCT CASE WHEN ct.status = 'COMPLETED' THEN ct.lead_id END) AS completed_leads,
  COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_SENT' THEN ae.id END) AS total_sends,
  COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_OPEN' THEN ae.id END) AS total_opens,
  COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_LINK_CLICK' THEN ae.id END) AS total_clicks,
  COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_REPLIED' THEN ae.id END) AS total_replies,
  COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_BOUNCED' THEN ae.id END) AS total_bounces,
  ROUND(100.0 * COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_OPEN' THEN ae.lead_id END) /
    NULLIF(COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_SENT' THEN ae.lead_id END), 0), 2) AS open_rate,
  ROUND(100.0 * COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_LINK_CLICK' THEN ae.lead_id END) /
    NULLIF(COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_SENT' THEN ae.lead_id END), 0), 2) AS click_rate,
  ROUND(100.0 * COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_REPLIED' THEN ae.lead_id END) /
    NULLIF(COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_SENT' THEN ae.lead_id END), 0), 2) AS reply_rate
FROM campaigns c
LEFT JOIN campaign_tracking ct ON c.smartlead_campaign_id = ct.smartlead_campaign_id
LEFT JOIN analytics_events ae ON ct.lead_id = ae.lead_id AND ct.smartlead_campaign_id = ae.smartlead_campaign_id
GROUP BY c.id, c.smartlead_campaign_id, c.name, c.tier, c.campaign_month, c.status, c.daily_send_limit, c.created_at, c.started_at;

-- Fix tier_performance view
CREATE OR REPLACE VIEW tier_performance AS
SELECT
  l.tier,
  COUNT(DISTINCT l.id) AS total_leads,
  ROUND(AVG(l.score), 2) AS avg_score,
  COUNT(DISTINCT ct.id) AS leads_in_campaigns,
  COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_SENT' THEN ae.lead_id END) AS leads_sent_to,
  COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_OPEN' THEN ae.lead_id END) AS leads_opened,
  COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_LINK_CLICK' THEN ae.lead_id END) AS leads_clicked,
  COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_REPLIED' THEN ae.lead_id END) AS leads_replied,
  ROUND(100.0 * COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_OPEN' THEN ae.lead_id END) /
    NULLIF(COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_SENT' THEN ae.lead_id END), 0), 2) AS open_rate,
  ROUND(100.0 * COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_REPLIED' THEN ae.lead_id END) /
    NULLIF(COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_SENT' THEN ae.lead_id END), 0), 2) AS reply_rate
FROM leads l
LEFT JOIN campaign_tracking ct ON l.id = ct.lead_id
LEFT JOIN analytics_events ae ON l.id = ae.lead_id
GROUP BY l.tier
ORDER BY l.tier;

-- Fix lead_performance view
CREATE OR REPLACE VIEW lead_performance AS
SELECT
  l.id,
  l.email,
  l.first_name,
  l.last_name,
  l.company,
  l.tier,
  l.score,
  l.messaging_strategy,
  l.created_at,
  ct.campaign_name,
  ct.status AS campaign_status,
  ct.sequences_sent,
  ct.added_at AS campaign_added_at,
  COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_OPEN' THEN ae.id END) AS total_opens,
  COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_LINK_CLICK' THEN ae.id END) AS total_clicks,
  COUNT(DISTINCT CASE WHEN ae.event_type = 'EMAIL_REPLIED' THEN ae.id END) AS total_replies,
  MIN(CASE WHEN ae.event_type = 'EMAIL_REPLIED' THEN ae.created_at END) AS first_reply_at,
  MAX(ae.created_at) AS last_activity_at
FROM leads l
LEFT JOIN campaign_tracking ct ON l.id = ct.lead_id
LEFT JOIN analytics_events ae ON l.id = ae.lead_id
GROUP BY l.id, l.email, l.first_name, l.last_name, l.company, l.tier, l.score, l.messaging_strategy,
  l.created_at, ct.campaign_name, ct.status, ct.sequences_sent, ct.added_at;

-- Verify the fix
SELECT 'campaign_performance' as view_name, COUNT(*) as row_count FROM campaign_performance
UNION ALL
SELECT 'tier_performance', COUNT(*) FROM tier_performance
UNION ALL
SELECT 'lead_performance', COUNT(*) FROM lead_performance;
