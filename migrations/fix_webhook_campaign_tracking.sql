-- Fix handle_smartlead_webhook to properly link events to campaign_tracking
-- Issue: campaign_tracking_id was never being set, breaking all analytics views

CREATE OR REPLACE FUNCTION public.handle_smartlead_webhook(
  p_smartlead_lead_id bigint,
  p_email text,
  p_event_type text,
  p_campaign_id integer DEFAULT NULL,
  p_event_data jsonb DEFAULT '{}'::jsonb
)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $function$
DECLARE
  v_lead_uuid UUID;
  v_campaign_tracking_id UUID;
  v_event_id UUID;
BEGIN
  -- Primary lookup: by smartlead_lead_id (preferred)
  SELECT id INTO v_lead_uuid
  FROM leads
  WHERE smartlead_lead_id = p_smartlead_lead_id;

  -- Fallback: by email if no match
  IF v_lead_uuid IS NULL AND p_email IS NOT NULL THEN
    SELECT id INTO v_lead_uuid
    FROM leads
    WHERE LOWER(email) = LOWER(p_email);

    -- If found by email, backfill the smartlead_lead_id
    IF v_lead_uuid IS NOT NULL AND p_smartlead_lead_id IS NOT NULL THEN
      UPDATE leads
      SET smartlead_lead_id = p_smartlead_lead_id,
          updated_at = NOW()
      WHERE id = v_lead_uuid;
    END IF;
  END IF;

  -- If still no match, return error
  IF v_lead_uuid IS NULL THEN
    RETURN json_build_object(
      'success', false,
      'error', 'Lead not found',
      'smartlead_lead_id', p_smartlead_lead_id,
      'email', p_email
    );
  END IF;

  -- NEW: Look up campaign_tracking record
  IF p_campaign_id IS NOT NULL THEN
    SELECT id INTO v_campaign_tracking_id
    FROM campaign_tracking
    WHERE lead_id = v_lead_uuid
    AND smartlead_campaign_id = p_campaign_id;
  END IF;

  -- Insert event into analytics_events (NOW WITH campaign_tracking_id!)
  INSERT INTO analytics_events (
    lead_id,
    campaign_tracking_id,  -- FIXED: Now properly set
    event_type,
    smartlead_campaign_id,
    smartlead_lead_id,
    event_data,
    created_at
  ) VALUES (
    v_lead_uuid,
    v_campaign_tracking_id,  -- FIXED: Link to campaign_tracking
    p_event_type,
    p_campaign_id,
    p_smartlead_lead_id,
    p_event_data,
    NOW()
  )
  RETURNING id INTO v_event_id;

  -- Update lead's updated_at
  UPDATE leads SET updated_at = NOW() WHERE id = v_lead_uuid;

  RETURN json_build_object(
    'success', true,
    'event_id', v_event_id,
    'lead_id', v_lead_uuid,
    'campaign_tracking_id', v_campaign_tracking_id,  -- Include in response
    'event_type', p_event_type
  );
END;
$function$;

-- Backfill existing events with campaign_tracking_id
UPDATE analytics_events ae
SET campaign_tracking_id = ct.id
FROM campaign_tracking ct
WHERE ae.lead_id = ct.lead_id
AND ae.smartlead_campaign_id = ct.smartlead_campaign_id
AND ae.campaign_tracking_id IS NULL;

-- Verify fix
SELECT
  COUNT(*) as total_events,
  COUNT(campaign_tracking_id) as with_tracking_id,
  COUNT(*) - COUNT(campaign_tracking_id) as without_tracking_id
FROM analytics_events;
