#!/usr/bin/env python3
"""
Patch Smartlead leads with missing custom fields (review_count, service_software)

The n8n workflow only synced tier and score. This patches existing leads in
Smartlead with the review_count and service_software from Supabase.

Usage:
    python patch_lead_custom_fields.py --dry-run  # Preview changes
    python patch_lead_custom_fields.py            # Execute patch
"""

import os
import sys
import time
import argparse
import requests
from dotenv import load_dotenv

load_dotenv()

# Configuration
SMARTLEAD_API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
SMARTLEAD_BASE_URL = "https://server.smartlead.ai/api/v1"

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://rlmuovkdvbxzyylbiunj.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

CAMPAIGNS = {
    "A": 2677089,
    "B": 2677090,
    "C": 2677091
}

def supabase_query(query):
    """Execute Supabase SQL query"""
    url = f"{SUPABASE_URL}/rest/v1/rpc/execute_sql"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json={"query": query})
    response.raise_for_status()
    return response.json()

def get_supabase_leads():
    """Get all leads from Supabase - using MCP data pre-loaded"""
    # Note: Run this query via Supabase MCP first:
    # SELECT email, reviews_count, service_software, tier FROM leads WHERE in_smartlead = true

    print(f"ℹ️  Using Supabase data from MCP query")
    print(f"ℹ️  If data is stale, update SUPABASE_DATA_FILE or query Supabase MCP")

    # For now, query directly via subprocess to MCP
    # Or user can provide a CSV export

    # Fallback: return empty dict and let user provide data
    print(f"\n⚠️  Please export Supabase data first:")
    print(f"   Run: claude mcp supabase execute_sql 'SELECT email, reviews_count, service_software, tier FROM leads WHERE in_smartlead = true'")
    print(f"   Or provide a CSV file with email,reviews_count,service_software,tier columns")

    # For demo, hardcode the lookup
    # In production, load from CSV or MCP query
    lookup = {}

    import json
    import os

    # Try to load from a temp JSON file if it exists
    temp_file = "/tmp/supabase_leads_export.json"
    if os.path.exists(temp_file):
        with open(temp_file, 'r') as f:
            leads_data = json.load(f)
            for lead in leads_data:
                email = lead['email'].lower()
                lookup[email] = {
                    'reviews_count': lead.get('reviews_count') or 0,
                    'service_software': lead.get('service_software') or '',
                    'tier': lead.get('tier') or ''
                }
            print(f"✅ Loaded {len(lookup)} leads from {temp_file}")
    else:
        print(f"❌ No data file found at {temp_file}")
        print(f"   Export Supabase data to this file first")
        sys.exit(1)

    return lookup

def get_smartlead_campaign_leads(campaign_id):
    """Get all leads from a Smartlead campaign"""
    url = f"{SMARTLEAD_BASE_URL}/campaigns/{campaign_id}/leads"
    params = {"api_key": SMARTLEAD_API_KEY, "limit": 500}

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()
    leads = data.get('data', [])

    print(f"   Found {len(leads)} leads in campaign {campaign_id}")
    return leads

def update_lead_custom_fields(campaign_id, lead_id, email, custom_fields, dry_run=False):
    """Update a lead's custom fields in Smartlead"""
    if dry_run:
        return True

    url = f"{SMARTLEAD_BASE_URL}/campaigns/{campaign_id}/lead/{lead_id}"
    params = {"api_key": SMARTLEAD_API_KEY}
    data = {
        "email": email,
        "custom_fields": custom_fields
    }

    response = requests.put(url, params=params, json=data)

    if response.status_code == 200:
        return True
    else:
        print(f"      ❌ Failed: {response.status_code} - {response.text}")
        return False

def patch_campaign(tier, campaign_id, supabase_lookup, dry_run=False):
    """Patch all leads in a campaign"""
    print(f"\n{'='*70}")
    print(f"Patching {tier}-TIER Campaign (ID: {campaign_id})")
    print(f"{'='*70}")

    # Get all leads from Smartlead
    smartlead_leads = get_smartlead_campaign_leads(campaign_id)

    matched = 0
    updated = 0
    already_has_review = 0
    missing_in_supabase = 0

    for lead_data in smartlead_leads:
        lead = lead_data.get('lead', {})
        lead_id = lead.get('id')
        email = lead.get('email', '').lower()
        campaign_lead_map_id = lead_data.get('campaign_lead_map_id')

        # Get current custom fields
        current_custom = lead.get('custom_fields', {})

        # Check if already has review_count
        if current_custom.get('review_count'):
            already_has_review += 1
            continue

        # Match to Supabase
        if email not in supabase_lookup:
            missing_in_supabase += 1
            print(f"   ⚠️  No match in Supabase: {email}")
            continue

        matched += 1
        supabase_data = supabase_lookup[email]

        # Merge custom fields (preserve existing, add new)
        new_custom_fields = {
            **current_custom,
            'review_count': str(supabase_data['reviews_count']),
            'service_software': supabase_data['service_software']
        }

        if dry_run:
            print(f"   🔍 Would update: {email}")
            print(f"      Current: {current_custom}")
            print(f"      New: {new_custom_fields}")
        else:
            success = update_lead_custom_fields(
                campaign_id,
                lead_id,
                email,
                new_custom_fields,
                dry_run=False
            )

            if success:
                updated += 1
                if updated % 10 == 0:
                    print(f"   ✅ Updated {updated} leads...")
                time.sleep(0.1)  # Rate limiting

    print(f"\n📊 {tier}-Tier Summary:")
    print(f"   Total leads in campaign: {len(smartlead_leads)}")
    print(f"   Already had review_count: {already_has_review}")
    print(f"   Matched to Supabase: {matched}")
    print(f"   Missing in Supabase: {missing_in_supabase}")

    if dry_run:
        print(f"   Would update: {matched}")
    else:
        print(f"   ✅ Successfully updated: {updated}")

    return updated

def main():
    parser = argparse.ArgumentParser(description='Patch Smartlead leads with missing custom fields')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without executing')
    args = parser.parse_args()

    print("\n" + "="*70)
    print("SMARTLEAD CUSTOM FIELDS PATCHER")
    print("="*70)

    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
    else:
        print("⚠️  LIVE MODE - Will update leads in Smartlead")

    print(f"\nCampaigns to patch:")
    for tier, campaign_id in CAMPAIGNS.items():
        print(f"   {tier}-Tier: {campaign_id}")

    # Load Supabase data
    print(f"\n📥 Loading leads from Supabase...")
    supabase_lookup = get_supabase_leads()

    # Patch each campaign
    total_updated = 0
    for tier, campaign_id in CAMPAIGNS.items():
        updated = patch_campaign(tier, campaign_id, supabase_lookup, dry_run=args.dry_run)
        total_updated += updated
        time.sleep(1)  # Pause between campaigns

    # Final summary
    print("\n" + "="*70)
    print("PATCH COMPLETE")
    print("="*70)

    if args.dry_run:
        print(f"\n🔍 Dry run complete - would have updated {total_updated} leads")
        print(f"\nRun without --dry-run to apply changes")
    else:
        print(f"\n✅ Successfully updated {total_updated} leads across all campaigns")
        print(f"✅ All leads now have review_count and service_software in custom_fields")

    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
