#!/usr/bin/env python3
"""
Batch update Smartlead leads using the working MCP endpoint
"""
import json
import requests
import time

API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
BASE_URL = "https://server.smartlead.ai/api/v1"

# Load updates
with open('/tmp/all_smartlead_updates.json', 'r') as f:
    all_updates = json.load(f)

total_leads = sum(len(updates) for updates in all_updates.values())
print(f"\n{'='*70}")
print(f"BATCH UPDATE VIA SMARTLEAD API")
print(f"{'='*70}")
print(f"Total leads to update: {total_leads}\n")

updated = 0
errors = 0

for tier in ['A', 'B', 'C']:
    leads = all_updates.get(tier, [])
    if not leads:
        continue

    print(f"\n{tier}-Tier: Updating {len(leads)} leads...")

    for i, lead in enumerate(leads, 1):
        campaign_id = lead['campaign_id']
        lead_id = lead['lead_id']
        email = lead['email']

        # Build custom_fields with all existing fields plus new ones
        custom_fields = {
            'tier': lead['tier'],
            'score': lead['score'],
            'review_count': lead['review_count'],
            'service_software': lead['service_software']
        }

        # Make API call
        url = f"{BASE_URL}/campaigns/{campaign_id}/leads/{lead_id}"
        params = {"api_key": API_KEY}
        data = {
            "email": email,
            "custom_fields": custom_fields
        }

        try:
            response = requests.put(url, params=params, json=data, timeout=30)

            if response.status_code == 200:
                updated += 1
                if updated % 10 == 0:
                    print(f"   ✅ {updated}/{total_leads} updated...")
            else:
                errors += 1
                if errors <= 3:
                    print(f"   ❌ {email}: {response.status_code}")

            time.sleep(0.15)  # Rate limiting

        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"   ❌ {email}: {e}")

print(f"\n{'='*70}")
print(f"COMPLETE")
print(f"{'='*70}")
print(f"✅ Updated: {updated}/{total_leads}")
print(f"❌ Errors: {errors}")
print(f"{'='*70}\n")
