#!/usr/bin/env python3
"""
Campaign Health Check - Real-time diagnostic for send issues

Checks:
1. API connectivity (is Cloudflare blocking us?)
2. Campaign status (ACTIVE/PAUSED/DRAFT)
3. Today's send stats (how many sent vs limit)
4. Last send time (when was the last email sent?)
5. Email account health (any blocks?)

Usage:
    python check_campaign_health.py
"""

import requests
import json
from datetime import datetime, timezone

# Configuration
API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
BASE_URL = "https://server.smartlead.ai/api/v1"

# Campaign IDs (from audit_smartlead_campaigns.py)
CAMPAIGNS = {
    "A": {"id": 2677089, "name": "A-Tier: Software & Scale", "daily_limit": 30},
    "B": {"id": 2677090, "name": "B-Tier: Growth Signal", "daily_limit": 25},
    "C": {"id": 2677091, "name": "C-Tier: Pain Focus", "daily_limit": 30}
}

def api_call(method, endpoint, data=None, timeout=10):
    """Make API call to Smartlead with timeout"""
    url = f"{BASE_URL}{endpoint}"
    params = {"api_key": API_KEY}
    headers = {"Content-Type": "application/json"}

    try:
        if method == "GET":
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, params=params, json=data, headers=headers, timeout=timeout)

        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print(f"⏱️  API TIMEOUT - Cloudflare may be blocking requests")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Status code: {e.response.status_code}")
            if e.response.status_code >= 500:
                print(f"   ⚠️  Server error - Likely Cloudflare outage impact")
        return None

def test_api_connectivity():
    """Test if we can reach Smartlead API"""
    print("="*70)
    print("🔌 API CONNECTIVITY TEST")
    print("="*70 + "\n")

    print("Testing connection to Smartlead API...")

    # Try to get email accounts (lightweight endpoint)
    result = api_call("GET", "/email-accounts", timeout=5)

    if result is None:
        print("❌ FAILED - Cannot reach Smartlead API")
        print("\n⚠️  LIKELY CAUSE: Cloudflare outage blocking API requests")
        print("   → Wait for Cloudflare to recover")
        print("   → Check https://www.cloudflarestatus.com/")
        print("   → Try again in 15-30 minutes\n")
        return False
    else:
        print("✅ SUCCESS - Smartlead API is accessible\n")
        return True

def check_campaign_status(campaign_id, campaign_name, daily_limit):
    """Check single campaign health"""
    print(f"\n📊 {campaign_name}")
    print("-" * 70)

    # Get campaign info
    info = api_call("GET", f"/campaigns/{campaign_id}")

    if not info:
        print("   ❌ Could not retrieve campaign data")
        return

    # Campaign status
    status = info.get("status", "UNKNOWN")
    status_icon = "✅" if status == "SCHEDULED" else "❌"
    print(f"   {status_icon} Status: {status}")

    if status != "SCHEDULED":
        print(f"      ⚠️  Campaign is NOT running (must be SCHEDULED to send)")
        print(f"      → Go to Smartlead UI and change status to SCHEDULED")

    # Send limits
    max_daily = info.get("max_leads_per_day", 0)
    limit_ok = max_daily == daily_limit
    print(f"   {'✅' if limit_ok else '⚠️'} Daily limit: {max_daily} {'(OK)' if limit_ok else f'(Expected: {daily_limit})'}")

    # Get campaign stats (analytics endpoint)
    stats = api_call("GET", f"/campaigns/{campaign_id}/analytics")

    if stats:
        # Check today's sends
        sent_today = stats.get("sent_today", 0)
        opened_today = stats.get("opened_today", 0)
        replied_today = stats.get("replied_today", 0)

        print(f"\n   📈 Today's Activity:")
        print(f"      Sent: {sent_today}/{max_daily}")
        print(f"      Opened: {opened_today}")
        print(f"      Replied: {replied_today}")

        if sent_today == 0:
            print(f"      ⚠️  ZERO sends today - campaign may be stalled")

        if sent_today >= max_daily:
            print(f"      ⚠️  Daily limit reached - no more sends until tomorrow")

    # Get recent leads to check last send time
    leads = api_call("GET", f"/campaigns/{campaign_id}/leads?limit=5")

    if leads and "data" in leads:
        lead_list = leads["data"]

        if lead_list:
            print(f"\n   🕐 Recent Activity:")

            # Find most recent send
            last_sent_time = None
            for lead in lead_list:
                sent_at = lead.get("last_sent_at")
                if sent_at:
                    if last_sent_time is None or sent_at > last_sent_time:
                        last_sent_time = sent_at

            if last_sent_time:
                # Convert timestamp to readable format
                try:
                    dt = datetime.fromtimestamp(last_sent_time, tz=timezone.utc)
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")

                    # Calculate how long ago
                    now = datetime.now(timezone.utc)
                    delta = now - dt
                    hours_ago = delta.total_seconds() / 3600

                    print(f"      Last send: {time_str}")
                    print(f"      ({hours_ago:.1f} hours ago)")

                    if hours_ago > 24:
                        print(f"      ⚠️  No sends in 24+ hours - campaign may be stuck")
                except Exception as e:
                    print(f"      Last send timestamp: {last_sent_time}")
            else:
                print(f"      ⚠️  No recent sends found")

def check_email_accounts():
    """Check email account health"""
    print("\n" + "="*70)
    print("📧 EMAIL ACCOUNT HEALTH")
    print("="*70 + "\n")

    accounts = api_call("GET", "/email-accounts")

    if not accounts or not isinstance(accounts, list):
        print("❌ Could not retrieve email accounts")
        return

    for account in accounts:
        email = account.get("from_email", "unknown")
        account_id = account.get("id", "unknown")

        # Check if account is active
        is_active = account.get("active", False)
        warmup = account.get("warmup_enabled", False)
        smtp_status = account.get("smtp_status", "unknown")

        status_icon = "✅" if is_active and smtp_status == "connected" else "❌"

        print(f"{status_icon} {email}")

        if not is_active:
            print(f"   ⚠️  Account is DISABLED")

        if smtp_status != "connected":
            print(f"   ⚠️  SMTP not connected: {smtp_status}")

        if warmup:
            print(f"   ℹ️  Warmup mode: ON")

def main():
    """Run complete health check"""
    print("\n" + "="*70)
    print("🏥 SMARTLEAD CAMPAIGN HEALTH CHECK")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Test API first
    if not test_api_connectivity():
        print("\n⚠️  DIAGNOSIS: Cloudflare outage is blocking Smartlead API")
        print("   → Wait for Cloudflare to recover")
        print("   → No action needed on your end")
        print("   → Campaigns will resume automatically once API is accessible\n")
        return

    # Check each campaign
    print("\n" + "="*70)
    print("📊 CAMPAIGN STATUS")
    print("="*70)

    for tier in ["A", "B", "C"]:
        config = CAMPAIGNS[tier]
        check_campaign_status(config["id"], config["name"], config["daily_limit"])

    # Check email accounts
    check_email_accounts()

    # Summary
    print("\n" + "="*70)
    print("💡 NEXT STEPS")
    print("="*70 + "\n")

    print("""
If you see issues above:

1. ❌ Status is not SCHEDULED
   → Go to Smartlead UI → Campaigns → Change to SCHEDULED

2. ⚠️  Zero sends today + campaign is SCHEDULED
   → Check if today is a send day (Mon-Fri only)
   → Check if current time is within send window (9am-5pm ET)
   → Try manually triggering a test send in Smartlead UI

3. ⚠️  Daily limit reached
   → This is normal, wait until tomorrow
   → Or increase daily limit if needed

4. ⚠️  Email account issues
   → Check DNS records (SPF/DKIM/DMARC)
   → Reconnect SMTP in Smartlead UI
   → Check if account is being warmed up

5. 🔌 Cloudflare blocking API
   → Wait for outage to resolve
   → Check https://www.cloudflarestatus.com/
   → Campaigns will auto-resume when API recovers
    """)

    print("="*70 + "\n")

if __name__ == "__main__":
    main()
