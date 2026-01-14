#!/usr/bin/env python3
"""
Deliverability Pre-Launch Check

Checks critical deliverability factors before Monday launch:
1. Email account DNS verification (SPF/DKIM/DMARC)
2. Email account warmup status
3. Recent send history (should be minimal for cold accounts)
4. Bounce/complaint rates
5. Domain reputation

Usage:
    python check_deliverability.py
"""

import requests
import json

API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
BASE_URL = "https://server.smartlead.ai/api/v1"

CAMPAIGN_IDS = [2677089, 2677090, 2677091]

def api_call(method, endpoint, data=None):
    """Make API call to Smartlead"""
    url = f"{BASE_URL}{endpoint}"
    params = {"api_key": API_KEY}
    headers = {"Content-Type": "application/json"}

    try:
        if method == "GET":
            response = requests.get(url, params=params, headers=headers)

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
        return None

def check_email_accounts():
    """Check all email accounts for deliverability issues"""
    print("\n" + "="*70)
    print("EMAIL ACCOUNT DELIVERABILITY CHECK")
    print("="*70 + "\n")

    # Get all email accounts
    result = api_call("GET", "/email-accounts")

    if not result or not isinstance(result, list):
        print("❌ Could not retrieve email accounts")
        return

    print(f"Found {len(result)} email accounts\n")

    for account in result:
        email = account.get("from_email", "unknown")
        account_id = account.get("id", "unknown")

        print(f"\n📧 {email} (ID: {account_id})")
        print("-" * 70)

        # DNS Verification Status
        print("\n   DNS Verification:")
        spf_status = account.get("spf_status", "unknown")
        dkim_status = account.get("dkim_status", "unknown")
        dmarc_status = account.get("dmarc_status", "unknown")

        print(f"      {'✅' if spf_status == 'verified' else '❌'} SPF: {spf_status}")
        print(f"      {'✅' if dkim_status == 'verified' else '❌'} DKIM: {dkim_status}")
        print(f"      {'✅' if dmarc_status == 'verified' else '⚠️'} DMARC: {dmarc_status}")

        # Warmup Status
        print("\n   Warmup Status:")
        warmup_enabled = account.get("warmup_enabled", False)
        warmup_reputation = account.get("warmup_reputation", 0)
        daily_limit = account.get("daily_limit", 0)

        print(f"      {'✅' if warmup_enabled else '⚠️'} Warmup: {'ENABLED' if warmup_enabled else 'DISABLED'}")
        print(f"      Reputation: {warmup_reputation}%")
        print(f"      Daily limit: {daily_limit} emails/day")

        # Health Metrics
        print("\n   Account Health:")
        total_sent = account.get("total_sent", 0)
        bounces = account.get("bounces", 0)
        complaints = account.get("complaints", 0)

        bounce_rate = (bounces / total_sent * 100) if total_sent > 0 else 0
        complaint_rate = (complaints / total_sent * 100) if total_sent > 0 else 0

        print(f"      Total sent: {total_sent}")
        print(f"      {'✅' if bounce_rate < 2 else '❌'} Bounce rate: {bounce_rate:.2f}% {'(OK)' if bounce_rate < 2 else '(HIGH - should be <2%)'}")
        print(f"      {'✅' if complaint_rate < 0.1 else '❌'} Complaint rate: {complaint_rate:.2f}% {'(OK)' if complaint_rate < 0.1 else '(HIGH - should be <0.1%)'}")

        # Connection Status
        print("\n   Connection:")
        smtp_status = account.get("smtp_status", "unknown")
        last_used = account.get("last_used", "Never")

        print(f"      {'✅' if smtp_status == 'connected' else '❌'} SMTP: {smtp_status}")
        print(f"      Last used: {last_used}")

def check_send_settings():
    """Check campaign send settings for conservative approach"""
    print("\n" + "="*70)
    print("SEND VOLUME SETTINGS (SPAM PREVENTION)")
    print("="*70 + "\n")

    for campaign_id in CAMPAIGN_IDS:
        result = api_call("GET", f"/campaigns/{campaign_id}")

        if not result:
            print(f"❌ Could not retrieve campaign {campaign_id}")
            continue

        name = result.get("name", "Unknown")
        max_daily = result.get("max_leads_per_day", 0)
        min_gap = result.get("min_time_btwn_emails", 0)

        print(f"📊 {name}")
        print(f"   Max sends/day: {max_daily}")
        print(f"   Min gap between emails: {min_gap} minutes")

        # Check if conservative
        conservative = max_daily <= 10 and min_gap >= 2
        print(f"   {'✅' if conservative else '⚠️'} Settings: {'CONSERVATIVE (Good for cold accounts)' if conservative else 'AGGRESSIVE (Risk of spam)'}\n")

def check_content_safety():
    """Quick content safety check"""
    print("\n" + "="*70)
    print("CONTENT SAFETY CHECK")
    print("="*70 + "\n")

    spam_triggers = {
        "free": "❌ HIGH RISK",
        "guarantee": "⚠️ MEDIUM RISK",
        "limited time": "⚠️ MEDIUM RISK",
        "click here": "❌ HIGH RISK",
        "buy now": "❌ HIGH RISK"
    }

    print("Checking for spam trigger words in sequences...\n")

    issues_found = []

    for campaign_id in CAMPAIGN_IDS:
        sequences = api_call("GET", f"/campaigns/{campaign_id}/sequences")

        if not sequences:
            continue

        for seq in sequences:
            variants = seq.get("sequence_variants", [])
            if not variants:
                continue

            variant = variants[0]
            body = variant.get("email_body", "").lower()
            subject = variant.get("subject", "").lower()
            full_text = body + " " + subject

            for trigger, risk in spam_triggers.items():
                if trigger in full_text:
                    issues_found.append(f"{risk} Found '{trigger}' in campaign {campaign_id}, sequence {seq.get('seq_number')}")

    if issues_found:
        print("⚠️ ISSUES FOUND:\n")
        for issue in issues_found:
            print(f"   {issue}")
    else:
        print("✅ No high-risk spam triggers detected")

def deliverability_summary():
    """Print final summary and recommendations"""
    print("\n" + "="*70)
    print("DELIVERABILITY SUMMARY & RECOMMENDATIONS")
    print("="*70 + "\n")

    print("""
✅ CRITICAL CHECKS (Must be OK):
   □ All 3 email accounts have SPF + DKIM verified
   □ No spam trigger words in email content
   □ Conservative send limits (≤10/day per campaign)
   □ Min 2-minute gap between emails

⚠️ RECOMMENDED (Should be OK):
   □ DMARC configured (not critical but helpful)
   □ Email warmup enabled (if accounts are new)
   □ Bounce rate <2%
   □ Zero complaints

🚀 MONDAY LAUNCH CHECKLIST:
   1. Send test email to Gmail + Outlook (check spam placement)
   2. Verify DNS records in Smartlead UI (Settings → Email Accounts)
   3. Enable auto-reply detection (prevent reply-to-nobody issues)
   4. Start with A-Tier only (16 leads = lowest risk test)
   5. Monitor first hour of sends (check spam folder placement)

⚠️ SPAM RISK FACTORS TO WATCH:
   - New/cold email accounts (warm up first if possible)
   - No prior send history (start with <10/day)
   - Links in first email (Calendly links can trigger filters)
   - Generic "no-reply" sending domains

💡 IF EMAILS LAND IN SPAM:
   1. Pause campaigns immediately
   2. Check DNS records again
   3. Remove/shorten links
   4. Add plain text version
   5. Lower send volume to 5/day
   6. Manually reply to a few cold leads (boosts engagement signals)

    """)

def main():
    """Run complete deliverability check"""
    check_email_accounts()
    check_send_settings()
    check_content_safety()
    deliverability_summary()

    print("="*70 + "\n")

if __name__ == "__main__":
    main()
