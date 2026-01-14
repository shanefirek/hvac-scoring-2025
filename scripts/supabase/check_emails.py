#!/usr/bin/env python3
"""Check if specific emails exist in Supabase"""

import os
import sys
import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
load_dotenv()

check_emails = [
    'shaunsmolarz@hotmail.com',
    'jason@badaop.com',
    'austin@groveoakscapital.com',
    'saitcore@outlook.com',
    'scott@4daughtersdecks.com',
    'saltcitycommercialcleaning@gmail.com'
]

url = f"{os.getenv('SUPABASE_URL')}/rest/v1/leads?select=email,company,score,tier,in_smartlead,smartlead_campaign_ids"
headers = {
    'apikey': os.getenv('SUPABASE_SERVICE_KEY'),
    'Authorization': f"Bearer {os.getenv('SUPABASE_SERVICE_KEY')}"
}

response = requests.get(url, headers=headers)
all_leads = response.json()

print("Checking for emails in Supabase database:")
print("="*60)
print()

found = []
not_found = []

for email in check_emails:
    lead = next((l for l in all_leads if l.get('email', '').lower() == email.lower()), None)
    if lead:
        found.append(lead)
        print(f"✅ FOUND: {email}")
        print(f"   Company: {lead.get('company')}")
        print(f"   Score: {lead.get('score')} | Tier: {lead.get('tier')}")
        print(f"   In Smartlead: {lead.get('in_smartlead')}")
        if lead.get('smartlead_campaign_ids'):
            campaigns = lead.get('smartlead_campaign_ids')
            campaign_names = {2677089: "A-Tier", 2677090: "B-Tier", 2677091: "C-Tier"}
            campaign_str = ", ".join([f"{campaign_names.get(c, c)}" for c in campaigns])
            print(f"   Campaigns: {campaign_str}")
        print()
    else:
        not_found.append(email)

if not_found:
    print(f"❌ NOT FOUND in database ({len(not_found)}):")
    for email in not_found:
        print(f"   - {email}")
    print()

print("="*60)
print(f"Summary: {len(found)} found, {len(not_found)} not found")
