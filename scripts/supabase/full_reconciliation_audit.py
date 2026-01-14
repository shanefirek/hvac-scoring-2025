#!/usr/bin/env python3
"""
Full reconciliation audit: Smartlead campaigns vs Supabase leads
Uses direct API calls instead of MCP tools.
"""

import os
import sys
import json
import requests
from collections import defaultdict
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Initialize clients
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

SMARTLEAD_API_KEY = os.getenv("SMARTLEAD_API_KEY")
SMARTLEAD_BASE_URL = "https://server.smartlead.ai/api/v1"

# Campaign IDs
CAMPAIGNS = {
    "A": 2677089,
    "B": 2677090,
    "C": 2677091
}

def get_supabase_leads():
    """Get all leads from Supabase"""
    print("Fetching all leads from Supabase...")
    response = supabase.table("leads").select(
        "email, tier, score, company, first_name, last_name, in_smartlead, smartlead_lead_id"
    ).execute()

    lookup = {}
    tier_counts = defaultdict(int)

    for lead in response.data:
        email = lead['email'].lower()
        lookup[email] = lead
        tier_counts[lead['tier']] += 1

    print(f"✓ Loaded {len(lookup)} leads from Supabase")
    print(f"  A-tier: {tier_counts['A']}, B-tier: {tier_counts['B']}, C-tier: {tier_counts['C']}")
    return lookup

def get_campaign_leads(campaign_id):
    """Get all leads from a Smartlead campaign via direct API"""
    all_leads = []
    offset = 0
    limit = 100

    while True:
        url = f"{SMARTLEAD_BASE_URL}/campaigns/{campaign_id}/leads"
        params = {"api_key": SMARTLEAD_API_KEY, "limit": limit, "offset": offset}

        response = requests.get(url, params=params)
        data = response.json()

        leads = data.get("data", [])
        all_leads.extend(leads)

        total = int(data.get("total_leads", 0))
        if offset + limit >= total:
            break

        offset += limit

    return all_leads

def analyze_campaign_data(campaign_id, expected_tier, supabase_leads):
    """Analyze a campaign via direct API"""

    print(f"Fetching leads from Smartlead campaign {campaign_id}...")
    lead_data_list = get_campaign_leads(campaign_id)
    leads = lead_data_list

    print(f"\n{'='*70}")
    print(f"{expected_tier}-TIER CAMPAIGN ANALYSIS (ID: {CAMPAIGNS[expected_tier]})")
    print(f"{'='*70}")
    print(f"Total leads in Smartlead: {len(leads)}")

    correct_tier = []
    wrong_tier = []
    not_in_supabase = []
    missing_tier_field = []

    for lead_data in leads:
        lead = lead_data.get('lead', {})
        email = lead.get('email', '').lower()
        custom_fields = lead.get('custom_fields', {})
        smartlead_tier = custom_fields.get('tier', '')

        # Check against Supabase
        if email not in supabase_leads:
            not_in_supabase.append({
                'email': email,
                'company': lead.get('company_name'),
                'smartlead_tier': smartlead_tier
            })
        else:
            supabase_tier = supabase_leads[email]['tier']

            if not smartlead_tier:
                missing_tier_field.append({
                    'email': email,
                    'supabase_tier': supabase_tier,
                    'company': lead.get('company_name')
                })
            elif supabase_tier == expected_tier:
                correct_tier.append(email)
            else:
                wrong_tier.append({
                    'email': email,
                    'supabase_tier': supabase_tier,
                    'smartlead_tier': smartlead_tier,
                    'company': lead.get('company_name'),
                    'score': supabase_leads[email]['score']
                })

    # Print summary
    print(f"\n✅ Correct tier ({expected_tier}): {len(correct_tier)}")
    print(f"❌ Wrong tier: {len(wrong_tier)}")
    print(f"⚠️  Missing tier field: {len(missing_tier_field)}")
    print(f"🔍 Not in Supabase: {len(not_in_supabase)}")

    if wrong_tier:
        print(f"\n📋 TIER MISMATCHES ({len(wrong_tier)} leads):")
        print(f"{'Email':<40} {'Expected':<10} {'Actual':<10} {'Score':<8} Company")
        print("-" * 100)
        for lead in wrong_tier[:20]:  # Show first 20
            print(f"{lead['email']:<40} {expected_tier:<10} {lead['supabase_tier']:<10} {lead['score']:<8} {lead['company'][:30]}")
        if len(wrong_tier) > 20:
            print(f"... and {len(wrong_tier) - 20} more")

    if missing_tier_field:
        print(f"\n⚠️  MISSING TIER FIELD ({len(missing_tier_field)} leads):")
        for lead in missing_tier_field[:10]:
            print(f"  {lead['email']:<40} (Supabase tier: {lead['supabase_tier']})")
        if len(missing_tier_field) > 10:
            print(f"  ... and {len(missing_tier_field) - 10} more")

    if not_in_supabase:
        print(f"\n🔍 NOT IN SUPABASE ({len(not_in_supabase)} leads):")
        for lead in not_in_supabase[:10]:
            print(f"  {lead['email']:<40} {lead['company']}")
        if len(not_in_supabase) > 10:
            print(f"  ... and {len(not_in_supabase) - 10} more")

    return {
        'tier': expected_tier,
        'total': len(leads),
        'correct': len(correct_tier),
        'wrong_tier': wrong_tier,
        'missing_tier_field': missing_tier_field,
        'not_in_supabase': not_in_supabase
    }

def main():
    print("\n" + "="*70)
    print("FULL RECONCILIATION AUDIT")
    print("="*70)

    # Get Supabase data
    supabase_leads = get_supabase_leads()

    # Analyze each campaign
    results = {}

    for tier in ['A', 'B', 'C']:
        campaign_id = CAMPAIGNS[tier]
        result = analyze_campaign_data(campaign_id, tier, supabase_leads)
        if result:
            results[tier] = result

    # Overall summary
    print("\n" + "="*70)
    print("OVERALL SUMMARY")
    print("="*70)

    total_mismatches = sum(len(r['wrong_tier']) for r in results.values())
    total_orphans = sum(len(r['not_in_supabase']) for r in results.values())

    print(f"\n📊 Total tier mismatches: {total_mismatches}")
    print(f"🔍 Total orphan leads (in Smartlead, not in Supabase): {total_orphans}")

    if total_mismatches > 0:
        print(f"\n⚠️  ACTION REQUIRED: {total_mismatches} leads need to be moved to correct campaigns")

    if total_orphans > 0:
        print(f"\n⚠️  ACTION REQUIRED: {total_orphans} leads need to be added to Supabase")

    print()

if __name__ == "__main__":
    main()
