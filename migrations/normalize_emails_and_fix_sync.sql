-- Normalize all emails to lowercase and fix sync_lead_from_clay function
-- Issue: Mixed case emails breaking matching, sync script not writing back smartlead_lead_id

-- Step 1: Normalize all existing emails to lowercase
UPDATE leads SET email = LOWER(email);

-- Step 2: Fix sync_lead_from_clay() function to normalize emails on insert/update
CREATE OR REPLACE FUNCTION sync_lead_from_clay(
  p_clay_id TEXT,
  p_email TEXT,
  p_first_name TEXT,
  p_last_name TEXT,
  p_company TEXT,
  p_domain TEXT,
  p_linkedin_url TEXT,
  p_reviews_count INTEGER,
  p_service_software TEXT,
  p_score INTEGER,
  p_tier TEXT,
  p_messaging_strategy TEXT,
  p_score_breakdown JSONB,
  p_clay_data JSONB
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
  v_lead_id UUID;
BEGIN
  -- Normalize email to lowercase
  p_email := LOWER(TRIM(p_email));

  -- Upsert: Insert or update lead
  INSERT INTO leads (
    clay_id,
    email,
    first_name,
    last_name,
    company,
    domain,
    linkedin_url,
    reviews_count,
    service_software,
    score,
    tier,
    messaging_strategy,
    score_breakdown,
    clay_data,
    last_enriched_at,
    created_at,
    updated_at
  ) VALUES (
    p_clay_id,
    p_email,  -- Already normalized above
    p_first_name,
    p_last_name,
    p_company,
    p_domain,
    p_linkedin_url,
    p_reviews_count,
    p_service_software,
    p_score,
    p_tier,
    p_messaging_strategy,
    p_score_breakdown,
    p_clay_data,
    NOW(),
    NOW(),
    NOW()
  )
  ON CONFLICT (email)
  DO UPDATE SET
    clay_id = COALESCE(EXCLUDED.clay_id, leads.clay_id),
    first_name = COALESCE(EXCLUDED.first_name, leads.first_name),
    last_name = COALESCE(EXCLUDED.last_name, leads.last_name),
    company = COALESCE(EXCLUDED.company, leads.company),
    domain = COALESCE(EXCLUDED.domain, leads.domain),
    linkedin_url = COALESCE(EXCLUDED.linkedin_url, leads.linkedin_url),
    reviews_count = COALESCE(EXCLUDED.reviews_count, leads.reviews_count),
    service_software = COALESCE(EXCLUDED.service_software, leads.service_software),
    score = EXCLUDED.score,
    tier = EXCLUDED.tier,
    messaging_strategy = EXCLUDED.messaging_strategy,
    score_breakdown = EXCLUDED.score_breakdown,
    clay_data = EXCLUDED.clay_data,
    last_enriched_at = NOW(),
    updated_at = NOW()
  RETURNING id INTO v_lead_id;

  RETURN v_lead_id;
END;
$$;

-- Step 3: Add constraint to prevent future mixed-case emails
ALTER TABLE leads
ADD CONSTRAINT email_lowercase
CHECK (email = LOWER(email));

-- Verify normalization worked
SELECT
  'Total leads' as check_name,
  COUNT(*) as count
FROM leads

UNION ALL

SELECT
  'Leads with mixed case (should be 0)' as check_name,
  COUNT(*) as count
FROM leads
WHERE email != LOWER(email);
