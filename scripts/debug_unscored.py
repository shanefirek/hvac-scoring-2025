#!/usr/bin/env python3
"""Check enrichment data for unscored leads"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load env from parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()

# List of the 27 emails we know are unscored
unscored_emails = [
    'office@jamroghvac.com',
    'cthvacservices@gmail.com',
    'timmy@moderntempcontrol.com',
    'contact@hajekheating.com',
    'contact@lairdshvac.com'
]

# Fetch these specific leads
url = f"{os.getenv('SUPABASE_URL')}/rest/v1/leads?select=email,company,score,tier,clay_data,domain,reviews_count,service_software,linkedin_url"
headers = {
    'apikey': os.getenv('SUPABASE_SERVICE_KEY'),
    'Authorization': f"Bearer {os.getenv('SUPABASE_SERVICE_KEY')}"
}

response = requests.get(url, headers=headers)
all_leads = response.json()

# Find our unscored emails
print(f'Checking first 5 unscored leads for enrichment data:')
print()

for email in unscored_emails:
    lead = next((l for l in all_leads if l.get('email') == email), None)
    if lead:
        clay_data = lead.get('clay_data')
        print(f"{email}:")
        print(f"  company: {lead.get('company')}")
        print(f"  score: {lead.get('score')}")
        print(f"  tier: {lead.get('tier')}")
        print(f"  domain: {lead.get('domain')}")
        print(f"  reviews_count: {lead.get('reviews_count')}")
        print(f"  service_software: {lead.get('service_software')}")
        print(f"  linkedin_url: {lead.get('linkedin_url')}")
        if clay_data:
            print(f"  clay_data.score: {clay_data.get('score')}")
            print(f"  clay_data.tier: {clay_data.get('tier')}")
            print(f"  clay_data.reviews_count: {clay_data.get('reviews_count')}")
        else:
            print(f"  clay_data: None")
        print()
