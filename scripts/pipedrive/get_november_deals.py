#!/usr/bin/env python3
"""Fetch Pipedrive deals created in November 2025"""

import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
load_dotenv()

PIPEDRIVE_API_TOKEN = os.getenv('PIPEDRIVE_API_TOKEN')

if not PIPEDRIVE_API_TOKEN:
    print("❌ PIPEDRIVE_API_TOKEN not found in .env")
    sys.exit(1)

# Get deals created in November 2025
url = "https://api.pipedrive.com/v1/deals"
params = {
    'api_token': PIPEDRIVE_API_TOKEN,
    'start': 0,
    'limit': 500,
    'sort': 'add_time DESC'
}

print("Fetching deals from Pipedrive...")
response = requests.get(url, params=params)
data = response.json()

if not data.get('success'):
    print(f"❌ Pipedrive API error: {data}")
    sys.exit(1)

deals = data.get('data', [])

# Filter for November 2025
november_deals = []
for deal in deals:
    add_time = deal.get('add_time')
    if add_time:
        # Parse date (format: "2025-11-20 14:23:45")
        deal_date = datetime.strptime(add_time, "%Y-%m-%d %H:%M:%S")
        if deal_date.year == 2025 and deal_date.month == 12:
            person = deal.get('person_name')
            # Get person details for email
            person_id = deal.get('person_id', {}).get('value') if isinstance(deal.get('person_id'), dict) else deal.get('person_id')

            email = None
            if person_id:
                person_url = f"https://api.pipedrive.com/v1/persons/{person_id}"
                person_params = {'api_token': PIPEDRIVE_API_TOKEN}
                person_response = requests.get(person_url, params=person_params)
                person_data = person_response.json()
                if person_data.get('success') and person_data.get('data'):
                    emails = person_data['data'].get('email', [])
                    if emails:
                        email = emails[0].get('value') if isinstance(emails, list) else emails

            november_deals.append({
                'name': person or 'No name',
                'email': email or 'No email',
                'deal_title': deal.get('title'),
                'added': add_time
            })

print(f"\nPipedrive Deals Created in December 2025: {len(november_deals)}")
print("="*60)
print()

for deal in november_deals:
    print(f"{deal['name']}")
    print(f"  Email: {deal['email']}")
    print(f"  Deal: {deal['deal_title']}")
    print(f"  Created: {deal['added']}")
    print()

if not november_deals:
    print("No deals found for December 2025")
