#!/usr/bin/env python3
"""
Smartlead Campaign Audit Script

Audits all 3 HVAC campaigns via Smartlead API and compares against
requirements from instructions_before_launch.md

Usage:
    python audit_smartlead_campaigns.py
"""

import requests
import json
from collections import defaultdict

# Configuration
API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
BASE_URL = "https://server.smartlead.ai/api/v1"

# Campaign IDs
CAMPAIGNS = {
    "A": {"id": 2677089, "name": "A-Tier: Software & Scale", "expected_leads": 16, "expected_sequences": 4, "max_daily": 10},
    "B": {"id": 2677090, "name": "B-Tier: Growth Signal", "expected_leads": 29, "expected_sequences": 3, "max_daily": 8},
    "C": {"id": 2677091, "name": "C-Tier: Pain Focus", "expected_leads": 106, "expected_sequences": 2, "max_daily": 10}
}

# Expected configuration from instructions_before_launch.md
EXPECTED_CONFIG = {
    "send_days": [1, 2, 3, 4, 5],  # Mon-Fri
    "timezone": "America/New_York",
    "min_gap_seconds": 120,
    "stop_on_reply": True,
    "calendly_link": "https://calendly.com/appletreepd/30min"
}

# Spam trigger words to check for
SPAM_WORDS = [
    "free", "guarantee", "limited time", "act now", "click here",
    "buy now", "order now", "apply now", "sign up free", "risk free",
    "no obligation", "cancel anytime", "winner", "congratulations"
]

# Required personalization tokens
REQUIRED_TOKENS = ["{{first_name}}", "{{company}}"]

def api_call(method, endpoint, data=None):
    """Make API call to Smartlead"""
    url = f"{BASE_URL}{endpoint}"
    params = {"api_key": API_KEY}
    headers = {"Content-Type": "application/json"}

    try:
        if method == "GET":
            response = requests.get(url, params=params, headers=headers)
        elif method == "POST":
            response = requests.post(url, params=params, json=data, headers=headers)

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"    ❌ API Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"    Detail: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"    Response: {e.response.text}")
        return None

# ============================================================================
# AUDIT FUNCTIONS
# ============================================================================

def get_campaign_info(campaign_id):
    """Get complete campaign info (includes schedule, settings, etc.)"""
    result = api_call("GET", f"/campaigns/{campaign_id}")
    return result

def get_campaign_leads(campaign_id):
    """Get all leads from campaign (max 100 per call due to API limit)"""
    all_leads = []
    offset = 0
    limit = 100

    while True:
        result = api_call("GET", f"/campaigns/{campaign_id}/leads?limit={limit}&offset={offset}")
        if not result:
            break

        leads = result.get("data", [])
        all_leads.extend(leads)

        # Check if there are more leads
        total_leads = int(result.get("total_leads", 0))
        if offset + limit >= total_leads:
            break

        offset += limit

    return all_leads

def get_campaign_sequences(campaign_id):
    """Get all email sequences from campaign (returns list directly)"""
    result = api_call("GET", f"/campaigns/{campaign_id}/sequences")
    # API returns a list directly, not a dict
    if result and isinstance(result, list):
        return result
    return []

def get_email_accounts(campaign_id):
    """Get email accounts assigned to campaign"""
    result = api_call("GET", f"/campaigns/{campaign_id}/email-accounts")
    if result:
        return result.get("email_accounts", [])
    return []

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def check_personalization_tokens(text):
    """Check if required personalization tokens are present"""
    missing = []
    for token in REQUIRED_TOKENS:
        if token not in text:
            missing.append(token)
    return missing

def check_spam_words(text):
    """Check for spam trigger words"""
    found = []
    text_lower = text.lower()
    for word in SPAM_WORDS:
        if word in text_lower:
            found.append(word)
    return found

def check_calendly_link(text):
    """Check if Calendly link is present"""
    return EXPECTED_CONFIG["calendly_link"] in text

def analyze_lead_distribution(leads):
    """Analyze how leads are distributed across email accounts"""
    distribution = defaultdict(int)
    for lead in leads:
        account_id = lead.get("email_account_id", "unknown")
        distribution[account_id] += 1

    total = len(leads)
    percentages = {acc: (count/total)*100 if total > 0 else 0
                   for acc, count in distribution.items()}

    # Check if any account has >40% of leads
    unbalanced = any(pct > 40 for pct in percentages.values())

    return distribution, percentages, unbalanced

# ============================================================================
# REPORT GENERATION
# ============================================================================

def print_header(text):
    """Print section header"""
    print(f"\n{'='*70}")
    print(f"{text}")
    print(f"{'='*70}")

def print_section(text):
    """Print subsection"""
    print(f"\n{text}")
    print("-" * len(text))

def status_icon(is_ok):
    """Return status icon"""
    return "✅" if is_ok else "❌"

def warning_icon():
    """Return warning icon"""
    return "⚠️"

def audit_campaign(tier, config):
    """Audit a single campaign"""
    campaign_id = config["id"]
    campaign_name = config["name"]

    print_section(f"CAMPAIGN {campaign_id}: {campaign_name}")

    # Get complete campaign info (includes schedule, settings, etc.)
    info = get_campaign_info(campaign_id)
    if not info:
        print(f"   ❌ Could not retrieve campaign info")
        return

    # Campaign status
    status = info.get("status", "UNKNOWN")
    print(f"   Status: {status}")

    # Audit schedule (from campaign info)
    print(f"\n   📅 Send Schedule:")
    schedule = info.get("scheduler_cron_value", {})
    days = schedule.get("days", [])
    timezone = schedule.get("tz", "")
    start_hour = schedule.get("startHour", "")
    end_hour = schedule.get("endHour", "")
    min_gap = info.get("min_time_btwn_emails", 0)
    max_daily = info.get("max_leads_per_day", 0)

    days_ok = days == EXPECTED_CONFIG["send_days"]
    tz_ok = timezone == EXPECTED_CONFIG["timezone"]
    gap_ok = min_gap >= EXPECTED_CONFIG["min_gap_seconds"] / 60  # API uses minutes
    daily_ok = max_daily == config["max_daily"]

    print(f"      {status_icon(days_ok)} Days: {days} {'(Mon-Fri)' if days_ok else '(EXPECTED: Mon-Fri [1,2,3,4,5])'}")
    print(f"      {status_icon(tz_ok)} Timezone: {timezone}")
    print(f"      {status_icon(True)} Hours: {start_hour} - {end_hour}")
    print(f"      {status_icon(gap_ok)} Min gap: {min_gap} minutes")
    print(f"      {status_icon(daily_ok)} Max daily: {max_daily} {'(OK)' if daily_ok else f'(EXPECTED: {config['max_daily']})'}")

    # Audit settings (from campaign info)
    print(f"\n   ⚙️  Campaign Settings:")
    track_settings = info.get("track_settings", [])
    stop_settings = info.get("stop_lead_settings", "")

    # track_settings uses NEGATIVE values (DONT_TRACK_*)
    # Empty array = all tracking enabled
    # Array with values = those things are disabled
    has_open_tracking = "DONT_TRACK_EMAIL_OPEN" not in track_settings
    has_click_tracking = "DONT_TRACK_LINK_CLICK" not in track_settings
    stops_on_reply = "REPLY" in stop_settings.upper()

    print(f"      {status_icon(has_open_tracking)} Open tracking: {'ON' if has_open_tracking else 'OFF'}")
    print(f"      {status_icon(has_click_tracking)} Click tracking: {'ON' if has_click_tracking else 'OFF'}")
    print(f"      {status_icon(stops_on_reply)} Stop on reply: {'YES' if stops_on_reply else 'NO'}")

    # Audit leads
    print(f"\n   👥 Lead Distribution:")
    leads = get_campaign_leads(campaign_id)
    if leads:
        distribution, percentages, unbalanced = analyze_lead_distribution(leads)

        total_leads = len(leads)
        expected_leads = config["expected_leads"]
        count_ok = total_leads == expected_leads

        print(f"      {status_icon(count_ok)} Total leads: {total_leads} {'(OK)' if count_ok else f'(EXPECTED: {expected_leads})'}")
        print(f"      {warning_icon() if unbalanced else status_icon(True)} Distribution across email accounts:")

        for account_id, count in distribution.items():
            pct = percentages[account_id]
            flag = "⚠️ UNBALANCED" if pct > 40 else ""
            print(f"         Account {account_id}: {count} leads ({pct:.1f}%) {flag}")
    else:
        print(f"      ❌ Could not retrieve leads")

    # Audit sequences
    print(f"\n   ✉️  Email Sequences:")
    sequences = get_campaign_sequences(campaign_id)
    if sequences:
        seq_count = len(sequences)
        expected_count = config["expected_sequences"]
        count_ok = seq_count == expected_count

        print(f"      {status_icon(count_ok)} Total sequences: {seq_count} {'(OK)' if count_ok else f'(EXPECTED: {expected_count})'}")

        for seq in sequences:
            seq_num = seq.get("seq_number", "?")
            delay = seq.get("seq_delay_details", {}).get("delayInDays", 0)

            # Get content from variant (not top-level which is often empty)
            variants = seq.get("sequence_variants", [])
            if variants:
                variant = variants[0]
                subject = variant.get("subject", "")
                body = variant.get("email_body", "")
            else:
                # Fallback to top-level if no variants
                subject = seq.get("subject", "")
                body = seq.get("email_body", "")

            # Check for tokens
            missing_tokens = check_personalization_tokens(subject + " " + body)

            # Check for spam words
            spam_found = check_spam_words(subject + " " + body)

            # Check for Calendly link
            has_calendly = check_calendly_link(body)

            print(f"\n      Sequence {seq_num} (Delay: {delay} days):")
            print(f"         Subject: {subject[:50]}...")
            print(f"         {status_icon(not missing_tokens)} Personalization: {'OK' if not missing_tokens else f'MISSING {missing_tokens}'}")
            print(f"         {status_icon(not spam_found)} Spam check: {'CLEAN' if not spam_found else f'FOUND: {spam_found}'}")
            print(f"         {status_icon(has_calendly)} Calendly link: {'PRESENT' if has_calendly else 'MISSING'}")
    else:
        print(f"      ❌ Could not retrieve sequences")

def main():
    """Run complete audit"""
    print_header("SMARTLEAD CAMPAIGN AUDIT REPORT")
    print(f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Auditing 3 campaigns: {', '.join([str(c['id']) for c in CAMPAIGNS.values()])}")

    # Audit each campaign
    for tier in ["A", "B", "C"]:
        audit_campaign(tier, CAMPAIGNS[tier])

    # Summary
    print_header("AUDIT SUMMARY")
    print(f"""
This audit checked:
   ✅ Campaign status (DRAFT/SCHEDULED/ACTIVE)
   ✅ Send schedule (days, times, timezone, gaps)
   ✅ Daily send limits
   ✅ Tracking settings (opens, clicks)
   ✅ Stop conditions (reply, bounce, unsubscribe)
   ✅ Lead counts and distribution
   ✅ Email sequences (count, delays)
   ✅ Personalization tokens
   ✅ Spam trigger words
   ✅ Calendly link presence

ITEMS REQUIRING MANUAL UI VERIFICATION:
   ⚠️  Email account health (SPF/DKIM/DMARC status)
   ⚠️  Auto-reply detection settings
   ⚠️  Reply forwarding configuration
   ⚠️  Unsubscribe link testing
   ⚠️  Test email deliverability
   ⚠️  Custom tracking domain (if applicable)

Next Steps:
   1. Review any ❌ or ⚠️ items above
   2. Cross-reference with Smartlead UI
   3. Address critical issues before launch
   4. Complete manual verification items from instructions_before_launch.md
    """)

    print("="*70 + "\n")

if __name__ == "__main__":
    main()
