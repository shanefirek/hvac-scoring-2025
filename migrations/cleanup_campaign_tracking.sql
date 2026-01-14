-- Migration: Cleanup campaign_tracking table
-- Date: 2025-12-09
-- Purpose: Remove redundant columns and fix stale statuses
-- 
-- Issues addressed:
-- 1. smartlead_lead_id column is 100% NULL (duplicates leads.smartlead_lead_id)
-- 2. smartlead_lead_map_id column is 100% NULL (never used)
-- 3. All 320 records stuck in PENDING status despite being synced

-- ============================================
-- STEP 1: Remove redundant columns
-- ============================================

-- These columns provide no value - smartlead_lead_id is already on the leads table
-- and smartlead_lead_map_id was never populated

ALTER TABLE campaign_tracking
DROP COLUMN IF EXISTS smartlead_lead_id;

ALTER TABLE campaign_tracking
DROP COLUMN IF EXISTS smartlead_lead_map_id;

-- ============================================
-- STEP 2: Update stale PENDING statuses
-- ============================================

-- Leads that have a smartlead_lead_id in the leads table ARE synced
-- Update their campaign_tracking status accordingly

UPDATE campaign_tracking ct
SET status = 'SYNCED',
    updated_at = NOW()
WHERE status = 'PENDING'
AND EXISTS (
  SELECT 1 FROM leads l 
  WHERE l.id = ct.lead_id 
  AND l.smartlead_lead_id IS NOT NULL
);

-- ============================================
-- STEP 3: Verify the changes
-- ============================================

-- Run these queries to verify:
-- 
-- Check column removal:
-- SELECT column_name FROM information_schema.columns 
-- WHERE table_name = 'campaign_tracking';
--
-- Check status update:
-- SELECT status, COUNT(*) FROM campaign_tracking GROUP BY status;











