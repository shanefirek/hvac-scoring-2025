#!/usr/bin/env python3
"""
Self-contained script to patch ALL Smartlead leads with custom fields from Supabase

Gets leads from Smartlead API, matches to Supabase data, updates custom_fields.

Usage:
    python patch_all_leads.py --dry-run  # Preview
    python patch_all_leads.py            # Execute
"""

import json
import requests
import time
import argparse

API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
BASE_URL = "https://server.smartlead.ai/api/v1"

CAMPAIGNS = {'A': 2677089, 'B': 2677090, 'C': 2677091}

def load_supabase_data():
    """Load Supabase data from JSON"""
    with open('/tmp/supabase_leads_export.json', 'r') as f:
        leads = json.load(f)

    lookup = {}
    for lead in leads:
        email = lead['email'].lower()
        lookup[email] = {
            'reviews_count': lead.get('reviews_count') or 0,
            'service_software': lead.get('service_software') or ''
        }

    return lookup

def get_campaign_leads_paginated(campaign_id):
    """Get all leads from a campaign using pagination"""
    all_leads = []
    offset = 0
    limit = 100

    while True:
        url = f"{BASE_URL}/campaigns/{campaign_id}/leads"
        params = {
            "api_key": API_KEY,
            "offset": offset,
            "limit": limit
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            leads_batch = data.get('data', [])
            if not leads_batch:
                break

            all_leads.extend(leads_batch)
            offset += limit

            if len(leads_batch) < limit:
                break

            time.sleep(0.2)  # Rate limiting

        except Exception as e:
            print(f"   ⚠️  API error at offset {offset}: {e}")
            break

    return all_leads

def update_lead(campaign_id, lead_id, email, custom_fields):
    """Update a lead's custom fields"""
    url = f"{BASE_URL}/campaigns/{campaign_id}/lead/{lead_id}"
    params = {"api_key": API_KEY}
    data = {"email": email, "custom_fields": custom_fields}

    response = requests.put(url, params=params, json=data, timeout=30)
    return response.status_code == 200

def patch_campaign(tier, campaign_id, supabase_lookup, dry_run=False):
    """Patch all leads in a campaign"""
    print(f"\n{'='*70}")
    print(f"{tier}-TIER Campaign (ID: {campaign_id})")
    print(f"{'='*70}")

    # Get all leads
    print("   📥 Fetching leads from Smartlead...")
    leads = get_campaign_leads_paginated(campaign_id)
    print(f"   Found {len(leads)} leads")

    matched = 0
    updated = 0
    already_has = 0
    missing = 0
    errors = 0

    for lead_data in leads:
        lead = lead_data.get('lead', {})
        email = lead.get('email', '').lower()
        lead_id = lead.get('id')
        current_custom = lead.get('custom_fields', {})

        # Skip if already has review_count
        if current_custom.get('review_count'):
            already_has += 1
            continue

        # Match to Supabase
        if email not in supabase_lookup:
            missing += 1
            continue

        matched += 1
        supabase_data = supabase_lookup[email]

        # Build new custom fields
        new_custom = {
            **current_custom,
            'review_count': str(supabase_data['reviews_count']),
            'service_software': supabase_data['service_software'] or ''
        }

        if dry_run:
            if matched <= 3:
                print(f"   🔍 {email}: +review_count={supabase_data['reviews_count']}")
        else:
            try:
                if update_lead(campaign_id, lead_id, email, new_custom):
                    updated += 1
                    if updated % 20 == 0:
                        print(f"   ✅ {updated} updated...")
                else:
                    errors += 1
                time.sleep(0.1)
            except Exception as e:
                errors += 1
                print(f"   ❌ {email}: {e}")

    print(f"\n   Summary:")
    print(f"   - Total: {len(leads)}")
    print(f"   - Already has data: {already_has}")
    print(f"   - Matched: {matched}")
    print(f"   - Missing in Supabase: {missing}")
    if not dry_run:
        print(f"   - ✅ Updated: {updated}")
        if errors:
            print(f"   - ❌ Errors: {errors}")

    return updated

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    print("\n" + "="*70)
    print("SMARTLEAD CUSTOM FIELDS PATCHER")
    print("="*70)
    print("🔍 DRY RUN" if args.dry_run else "⚠️  LIVE MODE")

    # Load Supabase
    print("\n📥 Loading Supabase data...")
    supabase_lookup = load_supabase_data()
    print(f"✅ {len(supabase_lookup)} leads loaded")

    # Patch each campaign
    total = 0
    for tier, campaign_id in CAMPAIGNS.items():
        updated = patch_campaign(tier, campaign_id, supabase_lookup, args.dry_run)
        total += updated
        time.sleep(1)

    print("\n" + "="*70)
    print("✅ COMPLETE" if not args.dry_run else "🔍 DRY RUN COMPLETE")
    print("="*70)
    print(f"\n{'Would update' if args.dry_run else 'Updated'}: {total} leads\n")

if __name__ == "__main__":
    main()
