#!/usr/bin/env python3
"""
Patch Smartlead leads using MCP tools directly

This script outputs MCP commands that you can run via Claude Code to update leads.
"""

import json

# Load Supabase data
with open('/tmp/supabase_leads_export.json', 'r') as f:
    supabase_leads = json.load(f)

# Create lookup by email
lookup = {}
for lead in supabase_leads:
    email = lead['email'].lower()
    lookup[email] = {
        'reviews_count': lead.get('reviews_count') or 0,
        'service_software': lead.get('service_software') or '',
        'tier': lead.get('tier') or ''
    }

print(f"Loaded {len(lookup)} leads from Supabase\n")

# Campaign IDs
campaigns = {
    'A': 2677089,
    'B': 2677090,
    'C': 2677091
}

print("=" * 70)
print("SMARTLEAD LEAD CUSTOM FIELDS PATCH COMMANDS")
print("=" * 70)
print("\nFor each campaign, run these mcp__smartlead__get_campaign_leads calls")
print("to get lead data, then update_campaign_lead for each one.\n")

for tier, campaign_id in campaigns.items():
    print(f"\n# {tier}-Tier Campaign ({campaign_id})")
    print(f"# First, get leads: mcp__smartlead__get_campaign_leads(campaign_id={campaign_id}, limit=500)")
    print(f"# Then for each lead, match by email and update custom_fields\n")

print("\nTo update a lead, use this MCP command format:")
print("mcp__smartlead__update_campaign_lead(")
print("  campaign_id=CAMPAIGN_ID,")
print("  lead_id=LEAD_ID,")
print("  email='lead@example.com',")
print("  custom_fields={")
print("    'score': '15',")
print("    'tier': 'A',")
print("    'review_count': '500',  # ADD THIS")
print("    'service_software': 'ServiceTitan'  # ADD THIS")
print("  }")
print(")\n")

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Total Supabase leads to match: {len(lookup)}")
print(f"Campaigns to update: {len(campaigns)}")
print("\nNext steps:")
print("1. Use Claude Code to call mcp__smartlead__get_campaign_leads for each campaign")
print("2. Match leads by email")
print("3. Update each lead's custom_fields with review_count and service_software")
print("=" * 70)
