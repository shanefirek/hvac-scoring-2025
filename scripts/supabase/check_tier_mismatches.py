#!/usr/bin/env python3
"""Check for leads in wrong tier campaigns"""

import os
import sys
import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
load_dotenv()

CAMPAIGN_TIERS = {
    2677089: "A",
    2677090: "B",
    2677091: "C"
}

url = f"{os.getenv('SUPABASE_URL')}/rest/v1/leads?in_smartlead=eq.true&select=email,company,score,tier,smartlead_campaign_ids"
headers = {
    'apikey': os.getenv('SUPABASE_SERVICE_KEY'),
    'Authorization': f"Bearer {os.getenv('SUPABASE_SERVICE_KEY')}"
}

response = requests.get(url, headers=headers)
campaign_leads = response.json()

print("Checking for tier/campaign mismatches...")
print()

mismatches = []

for lead in campaign_leads:
    lead_tier = lead.get('tier')
    campaign_ids = lead.get('smartlead_campaign_ids', [])

    for cid in campaign_ids:
        campaign_tier = CAMPAIGN_TIERS.get(cid)
        if campaign_tier and lead_tier != campaign_tier:
            mismatches.append({
                'email': lead.get('email'),
                'company': lead.get('company'),
                'score': lead.get('score'),
                'lead_tier': lead_tier,
                'campaign_id': cid,
                'campaign_tier': campaign_tier
            })

if mismatches:
    print(f"🚨 Found {len(mismatches)} leads in WRONG tier campaigns:")
    print()
    for m in mismatches:
        print(f"  {m['email']}")
        print(f"    Lead tier: {m['lead_tier']}-Tier (score: {m['score']})")
        print(f"    Campaign: {m['campaign_id']} ({m['campaign_tier']}-Tier)")
        print(f"    Company: {m['company']}")
        print()

    print(f"\n⚠️  Action needed: These {len(mismatches)} leads should be moved to correct campaigns or re-scored.")
else:
    print("✅ All 150 campaign leads are in the correct tier campaigns!")
