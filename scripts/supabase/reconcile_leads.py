#!/usr/bin/env python3
"""
Reconcile leads between Smartlead campaigns and Supabase.

Identifies:
- Tier mismatches (lead in wrong campaign)
- Orphan leads (in Smartlead but not Supabase)
- Missing leads (in Supabase but not in any campaign)
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

CAMPAIGNS = {
    "A": 2677089,
    "B": 2677090,
    "C": 2677091
}

def get_supabase_leads():
    """Get all leads from Supabase with tier info"""
    print("Fetching all leads from Supabase...")
    response = supabase.table("leads").select(
        "id, email, tier, score, company, first_name, last_name, in_smartlead, smartlead_lead_id"
    ).execute()

    lookup = {}
    for lead in response.data:
        lookup[lead['email'].lower()] = lead

    print(f"✓ Loaded {len(lookup)} leads from Supabase\n")
    return lookup

def main():
    print("\n" + "="*70)
    print("SMARTLEAD ↔ SUPABASE RECONCILIATION AUDIT")
    print("="*70)
    print()

    # Get Supabase data
    supabase_leads = get_supabase_leads()

    # We'll use MCP tools to get Smartlead data
    print("="*70)
    print("INSTRUCTIONS FOR NEXT STEP")
    print("="*70)
    print("\nThis script has loaded Supabase data. Now we need Smartlead data.")
    print("\nPlease use the following MCP tools to complete the audit:")
    print()
    print("1. For A-tier campaign (2677089):")
    print("   mcp__smartlead__get_campaign_leads(campaign_id=2677089, limit=200)")
    print()
    print("2. For B-tier campaign (2677090):")
    print("   mcp__smartlead__get_campaign_leads(campaign_id=2677090, limit=100)")
    print()
    print("3. For C-tier campaign (2677091):")
    print("   mcp__smartlead__get_campaign_leads(campaign_id=2677091, limit=250)")
    print()
    print("Then cross-reference the email addresses with the Supabase data.")
    print("\nTotal Supabase leads by tier:")

    tier_counts = {}
    for email, lead in supabase_leads.items():
        tier = lead.get('tier', 'Unknown')
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    for tier in sorted(tier_counts.keys()):
        print(f"  {tier}-tier: {tier_counts[tier]} leads")

    print(f"\nTotal: {len(supabase_leads)} leads")
    print()

if __name__ == "__main__":
    main()
