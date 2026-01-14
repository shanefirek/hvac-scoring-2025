#!/usr/bin/env python3
"""
Build Smartlead campaigns via direct API calls

Creates 3 tiered HVAC campaigns with sequences, leads, and configuration.
Bypasses MCP tools by hitting Smartlead API directly.

Usage:
    python build_smartlead_campaigns.py
"""

import requests
import csv
import json
import time

# Configuration
API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
BASE_URL = "https://server.smartlead.ai/api/v1"

# Email accounts to use for sending
EMAIL_ACCOUNT_IDS = [12664159, 12663958, 12657708]

# Calendly link
CALENDLY_LINK = "https://calendly.com/appletreepd/30min"

# Campaign configurations
CAMPAIGNS = {
    "A": {
        "name": "HVAC A-Tier - Software & Scale",
        "leads_file": "data/processed/leads_a_tier.csv",
        "max_leads_per_day": 10,
        "sequences": [
            {
                "seq_number": 1,
                "delay_days": 0,
                "subject": "{{first_name}} - tax season question",
                "body": """{{first_name}},

How responsive is your CPA during busy season?

Most HVAC owners running {{service_software}} tell us the same thing: They can't get their accountant on the phone during tax season, then April hits and there's a surprise $15k bill.

You're clearly running a tight operation at {{company}} ({{review_count}} reviews doesn't happen by accident). But if your accounting feels like a black hole, we should talk.

We're Appletree Business Services. We specialize in trades at your scale — monthly books, proactive tax planning, fixed pricing. No surprises.

Worth a conversation? """ + CALENDLY_LINK + """

Shane
Appletree Business Services"""
            },
            {
                "seq_number": 2,
                "delay_days": 4,
                "subject": "Re: Quick question about {{company}}'s accounting",
                "body": """{{first_name}},

Following up about {{company}}'s accounting.

You're running {{service_software}}, so you clearly have your operations dialed in. But here's the pattern we see constantly with HVAC companies at your scale:

→ CPA goes MIA during busy season
→ Books are 3 months behind
→ April brings surprise tax bills

Sound familiar?

We handle bookkeeping, payroll, and strategic tax planning for growing HVAC companies. Fixed monthly price, proactive communication, 24-hour response time.

If your current CPA setup isn't working, let's talk: """ + CALENDLY_LINK + """

Shane
Appletree Business Services"""
            },
            {
                "seq_number": 3,
                "delay_days": 9,
                "subject": "Your tech stack vs. your CPA",
                "body": """{{first_name}},

You're running {{service_software}}. That's a $10k+/year investment in doing things right.

But let me guess — your CPA still wants to chat "once things calm down" and sends you a bill you weren't expecting.

We work with HVAC companies that have outgrown the local accountant who only shows up in March.

What we do differently:
→ Monthly books (not once-a-year scrambles)
→ Proactive tax planning (not surprise bills)
→ Fixed pricing (no hourly billing mysteries)
→ 24-hour response time (not radio silence)

Companies like {{company}} deserve financial systems as dialed in as their operations.

Open to a quick call?

Shane
Appletree Business Services"""
            },
            {
                "seq_number": 4,
                "delay_days": 14,
                "subject": "Last note about {{company}}",
                "body": """{{first_name}},

Last email, I promise.

{{company}} has {{review_count}} reviews and you're running {{service_software}}. You're clearly doing things right.

If your accounting is the only part of your business that still feels chaotic — unresponsive CPA, messy books, tax surprises — we should talk.

We're Appletree. We clean up the financial side so you can focus on running jobs.

If now's not the time, no worries. But if it is, here's my calendar: """ + CALENDLY_LINK + """

Shane
Appletree Business Services"""
            }
        ]
    },
    "B": {
        "name": "HVAC B-Tier - Growth Signal",
        "leads_file": "data/processed/leads_b_tier.csv",
        "max_leads_per_day": 8,
        "sequences": [
            {
                "seq_number": 1,
                "delay_days": 0,
                "subject": "Saw {{company}} on Google",
                "body": """{{first_name}},

Came across {{company}} and saw your {{review_count}} reviews. Clearly you're doing something right.

Quick question: How responsive is your CPA during tax season?

Most HVAC owners at your scale tell us they can't get their accountant on the phone for weeks. Then April hits and there's a $12k surprise bill they weren't planning for.

We're Appletree Business Services. We work with a lot of HVAC, plumbing, and home service businesses. Monthly books, proactive tax planning, fixed monthly pricing.

Worth a conversation?

Shane
Appletree Business Services"""
            },
            {
                "seq_number": 2,
                "delay_days": 5,
                "subject": "Re: Saw {{company}} on Google",
                "body": """{{first_name}},

Following up about {{company}}'s accounting.

**Common pattern with HVAC companies at your scale:**
→ CPA disappears during busy season
→ Books are months behind
→ Tax bills are always a surprise
→ You're running the business blind on financials

Sound familiar?

We help HVAC companies get out of that chaos and into clarity.

What we do:
- Monthly bookkeeping & cleanup
- Strategic tax planning (not just filing)
- Fixed monthly price, no surprises

If that's what {{company}} needs, let's talk: """ + CALENDLY_LINK + """

Shane
Appletree Business Services"""
            },
            {
                "seq_number": 3,
                "delay_days": 12,
                "subject": "One last thing about {{company}}",
                "body": """{{first_name}},

Last email from me.

{{company}} has {{review_count}} Google reviews — your reputation is spotless. Your books should be too.

If you're tired of:
- Playing phone tag with your CPA
- Getting surprise tax bills
- Never knowing where you actually stand financially

We should talk.

We're Appletree. We simplify the financial side so you can focus on getting jobs done.

Here's my calendar if you want to chat: """ + CALENDLY_LINK + """

Shane
Appletree Business Services"""
            }
        ]
    },
    "C": {
        "name": "HVAC C-Tier - Pain Focus",
        "leads_file": "data/processed/leads_c_tier.csv",
        "max_leads_per_day": 10,
        "sequences": [
            {
                "seq_number": 1,
                "delay_days": 0,
                "subject": "Question about your CPA",
                "body": """{{first_name}},

Quick question about {{company}}: How responsive is your accountant during tax season?

Most HVAC owners tell us the same story — they can't get their CPA on the phone for weeks, books are always behind, and April brings a surprise tax bill they weren't ready for.

Sound familiar?

We're Appletree Business Services. We work with a lot of HVAC, plumbing, and home service businesses.

We keep your books simple, your taxes predictable, and your weekends stress-free.

Worth 15 minutes to see if we're a fit?

Shane
Appletree Business Services"""
            },
            {
                "seq_number": 2,
                "delay_days": 10,
                "subject": "Re: Question about your CPA",
                "body": """{{first_name}},

Last email from me about {{company}}'s accounting.

If you're dealing with:
→ An unresponsive CPA who disappears during busy season
→ Books that are months behind
→ Surprise tax bills every April

We can help.

We're Appletree — we work with a lot of trades and home service businesses. Monthly bookkeeping, proactive tax planning, fixed pricing. No surprises.

You handle the calls. We handle the numbers.

If you want to talk, here's my calendar: """ + CALENDLY_LINK + """

Shane
Appletree Business Services"""
            }
        ]
    }
}

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
        elif method == "PUT":
            response = requests.put(url, params=params, json=data, headers=headers)

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None

def create_campaign(name):
    """Create a new campaign"""
    print(f"\n📝 Creating campaign: {name}")

    data = {"name": name}
    result = api_call("POST", "/campaigns/create", data)

    if result and result.get("ok"):
        campaign_id = result.get("id")
        print(f"   ✅ Created: ID {campaign_id}")
        return campaign_id
    else:
        print(f"   ❌ Failed to create campaign")
        return None

def load_leads_from_csv(filename):
    """Load leads from CSV file"""
    leads = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lead = {
                "email": row['email'],
                "first_name": row['first_name'],
                "last_name": row['last_name'],
                "company_name": row['company'],
                "custom_fields": {
                    "service_software": row['service_software'],
                    "review_count": row['review_count']
                }
            }
            leads.append(lead)
    return leads

def add_leads_to_campaign(campaign_id, leads):
    """Add leads to campaign"""
    print(f"   📋 Adding {len(leads)} leads...")

    # Split into batches of 100 (API limit)
    batch_size = 100
    total_uploaded = 0

    for i in range(0, len(leads), batch_size):
        batch = leads[i:i+batch_size]

        data = {
            "lead_list": batch,
            "settings": {
                "ignore_global_block_list": False,
                "ignore_unsubscribe_list": False,
                "ignore_duplicate_leads_in_other_campaign": True
            }
        }

        result = api_call("POST", f"/campaigns/{campaign_id}/leads", data)

        if result and result.get("ok"):
            uploaded = result.get("upload_count", 0)
            total_uploaded += uploaded
            print(f"      Batch {i//batch_size + 1}: {uploaded} leads uploaded")
        else:
            print(f"      ❌ Batch {i//batch_size + 1} failed")

    print(f"   ✅ Total uploaded: {total_uploaded}/{len(leads)} leads")
    return total_uploaded

def add_email_accounts(campaign_id):
    """Add email accounts to campaign"""
    print(f"   📧 Adding email accounts...")

    data = {"email_account_ids": EMAIL_ACCOUNT_IDS}
    result = api_call("POST", f"/campaigns/{campaign_id}/email-accounts", data)

    if result and result.get("ok"):
        print(f"   ✅ Added {len(EMAIL_ACCOUNT_IDS)} email accounts")
        return True
    else:
        print(f"   ❌ Failed to add email accounts")
        return False

def add_sequences(campaign_id, sequences):
    """Add email sequences to campaign"""
    print(f"   ✉️  Adding {len(sequences)} sequences...")

    # Convert sequences to API format
    sequence_data = []
    for seq in sequences:
        sequence_data.append({
            "seq_number": seq["seq_number"],
            "subject": seq["subject"],
            "email_body": seq["body"],
            "seq_delay_details": {
                "delay_in_days": seq["delay_days"]
            }
        })

    data = {"sequences": sequence_data}
    result = api_call("POST", f"/campaigns/{campaign_id}/sequences", data)

    if result and result.get("ok"):
        print(f"   ✅ Added {len(sequences)} sequences")
        return True
    else:
        print(f"   ❌ Failed to add sequences")
        return False

def configure_schedule(campaign_id, max_leads_per_day):
    """Configure campaign schedule"""
    print(f"   ⏰ Configuring schedule...")

    data = {
        "timezone": "America/New_York",
        "days_of_the_week": [1, 2, 3, 4, 5],  # Mon-Fri
        "start_hour": "09:00",
        "end_hour": "17:00",
        "min_time_btw_emails": 3,  # 3 minutes
        "max_new_leads_per_day": max_leads_per_day
    }

    result = api_call("POST", f"/campaigns/{campaign_id}/schedule", data)

    if result and result.get("ok"):
        print(f"   ✅ Schedule configured ({max_leads_per_day} leads/day max)")
        return True
    else:
        print(f"   ❌ Failed to configure schedule")
        return False

def configure_settings(campaign_id):
    """Configure campaign settings"""
    print(f"   ⚙️  Configuring settings...")

    data = {
        "track_settings": ["TRACK_OPENS", "TRACK_CLICKS"],
        "stop_lead_settings": "REPLY_TO_AN_EMAIL",
        "follow_up_percentage": 100,
        "enable_ai_esp_matching": True,
        "send_as_plain_text": False
    }

    result = api_call("POST", f"/campaigns/{campaign_id}/settings", data)

    if result and result.get("ok"):
        print(f"   ✅ Settings configured")
        return True
    else:
        print(f"   ❌ Failed to configure settings")
        return False

def build_campaign(tier, config):
    """Build complete campaign for a tier"""
    print(f"\n{'='*70}")
    print(f"Building {tier}-TIER Campaign: {config['name']}")
    print(f"{'='*70}")

    # Create campaign
    campaign_id = create_campaign(config['name'])
    if not campaign_id:
        return None

    time.sleep(1)  # Rate limiting

    # Load and add leads
    leads = load_leads_from_csv(config['leads_file'])
    add_leads_to_campaign(campaign_id, leads)
    time.sleep(1)

    # Add email accounts
    add_email_accounts(campaign_id)
    time.sleep(1)

    # Add sequences
    add_sequences(campaign_id, config['sequences'])
    time.sleep(1)

    # Configure schedule
    configure_schedule(campaign_id, config['max_leads_per_day'])
    time.sleep(1)

    # Configure settings
    configure_settings(campaign_id)

    print(f"\n✅ {tier}-Tier campaign complete! ID: {campaign_id}")
    return campaign_id

def main():
    """Build all 3 campaigns"""
    print("\n" + "="*70)
    print("SMARTLEAD CAMPAIGN BUILDER - APPLETREE HVAC NOV 2025")
    print("="*70)
    print(f"\nAPI Key: {API_KEY[:20]}...")
    print(f"Email Accounts: {EMAIL_ACCOUNT_IDS}")
    print(f"Calendly: {CALENDLY_LINK}")

    campaign_ids = {}

    # Build each campaign
    for tier in ["A", "B", "C"]:
        campaign_id = build_campaign(tier, CAMPAIGNS[tier])
        if campaign_id:
            campaign_ids[tier] = campaign_id
        time.sleep(2)  # Pause between campaigns

    # Summary
    print("\n" + "="*70)
    print("CAMPAIGN BUILD COMPLETE")
    print("="*70)

    for tier, campaign_id in campaign_ids.items():
        print(f"\n{tier}-Tier: {CAMPAIGNS[tier]['name']}")
        print(f"   Campaign ID: {campaign_id}")
        print(f"   Leads: {len(load_leads_from_csv(CAMPAIGNS[tier]['leads_file']))}")
        print(f"   Sequences: {len(CAMPAIGNS[tier]['sequences'])}")
        print(f"   Max sends/day: {CAMPAIGNS[tier]['max_leads_per_day']}")

    print(f"\n✅ All campaigns created in DRAFT mode")
    print(f"✅ Ready to review in Smartlead UI")
    print(f"✅ Activate on Monday 11/18 to launch")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
