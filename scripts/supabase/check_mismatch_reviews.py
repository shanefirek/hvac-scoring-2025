#!/usr/bin/env python3
"""Check review counts for mismatched leads"""

import os
import sys
import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
load_dotenv()

mismatched_emails = [
    'sales@rycorhvac.com',
    'office@customclimates.com',
    'sales@masterplumbingandheating.com',
    'service@mcphvac.com',
    'aairsystemstech@gmail.com'
]

url = f"{os.getenv('SUPABASE_URL')}/rest/v1/leads?select=email,company,score,tier,reviews_count,service_software,smartlead_campaign_ids,score_breakdown"
headers = {
    'apikey': os.getenv('SUPABASE_SERVICE_KEY'),
    'Authorization': f"Bearer {os.getenv('SUPABASE_SERVICE_KEY')}"
}

response = requests.get(url, headers=headers)
all_leads = response.json()

print("Review counts for mismatched leads:")
print("="*80)
print()

for email in mismatched_emails:
    lead = next((l for l in all_leads if l.get('email') == email), None)
    if lead:
        campaign_id = lead.get('smartlead_campaign_ids', [None])[0]
        campaign_tier = {2677089: "A", 2677090: "B", 2677091: "C"}.get(campaign_id, "?")

        print(f"{email}")
        print(f"  Company: {lead.get('company')}")
        print(f"  Score: {lead.get('score')} | Calculated tier: {lead.get('tier')}-Tier | In campaign: {campaign_tier}-Tier")
        print(f"  Reviews: {lead.get('reviews_count')}")
        print(f"  Software: {lead.get('service_software') or 'None'}")

        breakdown = lead.get('score_breakdown', {})
        if breakdown:
            print(f"  Score breakdown:")
            print(f"    - Software: {breakdown.get('service_software', 0)} pts")
            print(f"    - Reviews: {breakdown.get('franchise_or_reviews', 0)} pts")
            print(f"    - LinkedIn: {breakdown.get('linkedin', 0)} pts")
            print(f"    - Domain: {breakdown.get('domain', 0)} pts")

        reviews = lead.get('reviews_count', 0)
        if reviews >= 100:
            print(f"  ✅ HIGH REVIEWS ({reviews}) - Could justify B-Tier placement")
        elif reviews >= 25:
            print(f"  ⚠️  MODERATE REVIEWS ({reviews}) - Borderline case")
        else:
            print(f"  ❌ LOW REVIEWS ({reviews}) - Should be in C-Tier")

        print()
