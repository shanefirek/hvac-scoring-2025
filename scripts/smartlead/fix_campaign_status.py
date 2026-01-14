#!/usr/bin/env python3
"""
Quick fix: Set campaigns to SCHEDULED and re-enable email accounts
"""

import requests

API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
BASE_URL = "https://server.smartlead.ai/api/v1"

CAMPAIGNS = [2677089, 2677090, 2677091]

def api_call(method, endpoint, data=None):
    """Make API call"""
    url = f"{BASE_URL}{endpoint}"
    params = {"api_key": API_KEY}
    headers = {"Content-Type": "application/json"}

    try:
        if method == "GET":
            response = requests.get(url, params=params, headers=headers)
        elif method == "POST":
            response = requests.post(url, params=params, json=data, headers=headers)
        elif method == "PATCH":
            response = requests.patch(url, params=params, json=data, headers=headers)

        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

print("🔧 FIXING CAMPAIGN STATUS...\n")

# Fix campaign status
for campaign_id in CAMPAIGNS:
    print(f"Updating campaign {campaign_id}...")

    # Try to update status to SCHEDULED
    result = api_call("POST", f"/campaigns/{campaign_id}/status", {"status": "SCHEDULED"})

    if result:
        print(f"✅ Campaign {campaign_id} set to SCHEDULED")
    else:
        # Try alternate endpoint
        result = api_call("PATCH", f"/campaigns/{campaign_id}", {"status": "SCHEDULED"})
        if result:
            print(f"✅ Campaign {campaign_id} set to SCHEDULED")
        else:
            print(f"⚠️  Could not update campaign {campaign_id} via API")

print("\n🔧 FIXING EMAIL ACCOUNTS...\n")

# Get email accounts
accounts = api_call("GET", "/email-accounts")

if accounts and isinstance(accounts, list):
    for account in accounts:
        account_id = account.get("id")
        email = account.get("from_email")

        print(f"Re-enabling {email}...")

        # Try to enable account
        result = api_call("PATCH", f"/email-accounts/{account_id}", {"active": True})

        if result:
            print(f"✅ {email} re-enabled")
        else:
            print(f"⚠️  Could not re-enable {email} via API - may need manual UI fix")

print("\n✅ DONE! Re-run health check to verify:\n")
print("   python3 scripts/smartlead/check_campaign_health.py\n")
