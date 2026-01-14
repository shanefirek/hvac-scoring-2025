#!/usr/bin/env python3
"""
Bulk update Smartlead lead custom_fields from Supabase data

This reads campaign lead exports (JSON) and Supabase data, then bulk updates via API.

Usage:
    # First, export campaign leads to JSON files (or use provided ones)
    python bulk_update_custom_fields.py --dry-run
    python bulk_update_custom_fields.py  # Execute
"""

import json
import requests
import time
import argparse
from pathlib import Path

SMARTLEAD_API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
SMARTLEAD_BASE_URL = "https://server.smartlead.ai/api/v1"

# Campaign IDs
CAMPAIGNS = {
    'A': 2677089,
    'B': 2677090,
    'C': 2677091
}

def load_supabase_data():
    """Load Supabase leads data"""
    with open('/tmp/supabase_leads_export.json', 'r') as f:
        leads = json.load(f)

    lookup = {}
    for lead in leads:
        email = lead['email'].lower()
        lookup[email] = {
            'reviews_count': lead.get('reviews_count') or 0,
            'service_software': lead.get('service_software') or ''
        }

    print(f"✅ Loaded {len(lookup)} leads from Supabase")
    return lookup

def load_campaign_leads(campaign_file):
    """Load campaign leads from JSON export"""
    if not Path(campaign_file).exists():
        return None

    with open(campaign_file, 'r') as f:
        data = json.load(f)

    return data.get('data', [])

def update_lead(campaign_id, lead_id, email, custom_fields, dry_run=False):
    """Update a single lead's custom fields"""
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
        print(f"      ❌ Failed {email}: {response.status_code} - {response.text}")
        return False

def patch_campaign(tier, campaign_id, campaign_leads, supabase_lookup, dry_run=False):
    """Patch all leads in a campaign"""
    print(f"\n{'='*70}")
    print(f"Patching {tier}-TIER Campaign (ID: {campaign_id})")
    print(f"{'='*70}")

    if not campaign_leads:
        print(f"❌ No campaign leads data. Export first using:")
        print(f"   mcp__smartlead__get_campaign_leads(campaign_id={campaign_id}, limit=500)")
        return 0

    print(f"   Found {len(campaign_leads)} leads in Smartlead")

    matched = 0
    updated = 0
    already_has_review = 0
    missing_in_supabase = 0

    for lead_data in campaign_leads:
        lead = lead_data.get('lead', {})
        lead_id = lead.get('id')
        email = lead.get('email', '').lower()

        # Get current custom fields
        current_custom = lead.get('custom_fields', {})

        # Check if already has review_count
        if current_custom.get('review_count'):
            already_has_review += 1
            continue

        # Match to Supabase
        if email not in supabase_lookup:
            missing_in_supabase += 1
            continue

        matched += 1
        supabase_data = supabase_lookup[email]

        # Merge custom fields (preserve existing, add new)
        new_custom_fields = {
            **current_custom,
            'review_count': str(supabase_data['reviews_count']),
            'service_software': supabase_data['service_software'] or ''
        }

        if dry_run:
            if matched <= 3:  # Show first 3
                print(f"   🔍 Would update: {email}")
                print(f"      review_count: {supabase_data['reviews_count']}")
        else:
            success = update_lead(
                campaign_id,
                lead_id,
                email,
                new_custom_fields
            )

            if success:
                updated += 1
                if updated % 25 == 0:
                    print(f"   ✅ Updated {updated} leads...")
                time.sleep(0.15)  # Rate limiting

    print(f"\n📊 {tier}-Tier Summary:")
    print(f"   Total leads: {len(campaign_leads)}")
    print(f"   Already had review_count: {already_has_review}")
    print(f"   Matched to Supabase: {matched}")
    print(f"   Missing in Supabase: {missing_in_supabase}")

    if dry_run:
        print(f"   Would update: {matched}")
    else:
        print(f"   ✅ Successfully updated: {updated}")

    return updated

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Preview only')
    parser.add_argument('--campaign-data-dir', default='/tmp/smartlead_campaigns',
                       help='Directory with campaign JSON exports')
    args = parser.parse_args()

    print("\n" + "="*70)
    print("SMARTLEAD BULK CUSTOM FIELDS UPDATER")
    print("="*70)

    if args.dry_run:
        print("🔍 DRY RUN MODE")
    else:
        print("⚠️  LIVE MODE - Will update leads")

    # Load Supabase data
    supabase_lookup = load_supabase_data()

    # For each campaign
    total_updated = 0
    for tier, campaign_id in CAMPAIGNS.items():
        campaign_file = f"{args.campaign_data_dir}/campaign_{campaign_id}_leads.json"
        campaign_leads = load_campaign_leads(campaign_file)

        updated = patch_campaign(tier, campaign_id, campaign_leads, supabase_lookup, dry_run=args.dry_run)
        total_updated += updated
        time.sleep(1)

    print("\n" + "="*70)
    print("COMPLETE")
    print("="*70)

    if args.dry_run:
        print(f"\n🔍 Would update {total_updated} leads")
        print(f"\nTo execute: python {__file__}")
    else:
        print(f"\n✅ Updated {total_updated} leads across all campaigns")

    print("\n" + "="*70)

if __name__ == "__main__":
    main()
