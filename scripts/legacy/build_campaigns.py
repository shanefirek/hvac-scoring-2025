#!/usr/bin/env env python3
"""
Smartlead Campaign Builder - Appletree HVAC Outbound Nov 2025

This script creates 3 tiered campaigns in Smartlead with email sequences.
Campaigns are left in DRAFT mode for manual review before launch.

Usage:
    python build_campaigns.py

Requirements:
    - Smartlead MCP server configured in Claude Desktop
    - Email account IDs from Smartlead
    - Calendly link for Patrick
"""

# ============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================================================

# Your Smartlead email account IDs (comma-separated list)
EMAIL_ACCOUNT_IDS = []  # e.g., [12345, 12346, 12347]

# Sender information
SENDER_NAME = "Patrick"  # Or "Patrick from Appletree"
SENDER_EMAIL = "patrick@appletreebusiness.com"  # Your sending domain
REPLY_TO_EMAIL = "patrick@appletreebusiness.com"

# Calendly booking link (replace [Calendly link] in sequences)
CALENDLY_LINK = "https://calendly.com/patrick/15min"  # UPDATE THIS

# Campaign settings
TIMEZONE = "America/New_York"
SEND_START_HOUR = "09:00"
SEND_END_HOUR = "17:00"
SEND_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# Daily sending limits (10 leads/day per campaign = 30/day total)
MAX_LEADS_PER_DAY = {
    "A": 10,
    "B": 8,
    "C": 10
}

# ============================================================================
# EMAIL SEQUENCES DATA
# ============================================================================

CAMPAIGNS = {
    "A": {
        "name": "HVAC A-Tier - Software & Scale",
        "description": "ServiceTitan/Jobber/HCP users + high reviews (20-30 points)",
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

Worth a conversation? {calendly_link}

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

If your current CPA setup isn't working, let's talk: {calendly_link}

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

If now's not the time, no worries. But if it is, here's my calendar: {calendly_link}

Shane
Appletree Business Services"""
            }
        ]
    },
    "B": {
        "name": "HVAC B-Tier - Growth Signal",
        "description": "Good reviews OR service software (10-19 points)",
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

If that's what {{company}} needs, let's talk: {calendly_link}

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

Here's my calendar if you want to chat: {calendly_link}

Shane
Appletree Business Services"""
            }
        ]
    },
    "C": {
        "name": "HVAC C-Tier - Pain Focus",
        "description": "Lower reviews, no service software (0-9 points)",
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

If you want to talk, here's my calendar: {calendly_link}

Shane
Appletree Business Services"""
            }
        ]
    }
}

# ============================================================================
# SCRIPT LOGIC
# ============================================================================

def inject_calendly_link(body: str) -> str:
    """Replace {calendly_link} placeholder with actual link"""
    return body.replace("{calendly_link}", CALENDLY_LINK)

def print_campaign_config():
    """Display configuration summary before running"""
    print("\n" + "="*70)
    print("SMARTLEAD CAMPAIGN BUILDER - APPLETREE HVAC NOV 2025")
    print("="*70)
    print(f"\nSender: {SENDER_NAME} <{SENDER_EMAIL}>")
    print(f"Email Accounts: {EMAIL_ACCOUNT_IDS}")
    print(f"Calendly Link: {CALENDLY_LINK}")
    print(f"Timezone: {TIMEZONE}")
    print(f"Send Window: {SEND_START_HOUR} - {SEND_END_HOUR}")
    print(f"Send Days: {', '.join(SEND_DAYS)}")
    print("\nCampaigns to create:")
    print(f"  A-Tier: {CAMPAIGNS['A']['name']} ({len(CAMPAIGNS['A']['sequences'])} emails)")
    print(f"  B-Tier: {CAMPAIGNS['B']['name']} ({len(CAMPAIGNS['B']['sequences'])} emails)")
    print(f"  C-Tier: {CAMPAIGNS['C']['name']} ({len(CAMPAIGNS['C']['sequences'])} emails)")
    print("\n" + "="*70 + "\n")

def main():
    """
    Main execution flow:
    1. Validate configuration
    2. Display summary
    3. Provide manual MCP commands to run
    """

    # Validate config
    if not EMAIL_ACCOUNT_IDS:
        print("❌ ERROR: EMAIL_ACCOUNT_IDS not configured")
        print("   Get your email account IDs from Smartlead and update build_campaigns.py")
        return

    if CALENDLY_LINK == "https://calendly.com/patrick/15min":
        print("⚠️  WARNING: Using default Calendly link. Update CALENDLY_LINK in script.")

    # Display config
    print_campaign_config()

    # Generate instructions
    print("📋 MANUAL SETUP INSTRUCTIONS")
    print("="*70)
    print("\nThis script provides the campaign data structure.")
    print("To create campaigns, you'll need to use the Smartlead MCP tools via Claude.\n")

    print("STEP 1: Create each campaign")
    print("-" * 70)

    for tier, config in CAMPAIGNS.items():
        print(f"\n{tier}-TIER CAMPAIGN:")
        print(f"  Name: {config['name']}")
        print(f"  Sequences: {len(config['sequences'])} emails")
        print(f"  Delays: {', '.join([f'Day {seq['delay_days']}' for seq in config['sequences']])}")

    print("\n\nSTEP 2: After campaigns are created")
    print("-" * 70)
    print("1. Import leads from Clay CSV (filtered by tier column)")
    print("2. Verify merge tags are working: {{first_name}}, {{company}}, etc.")
    print("3. Send test email to yourself")
    print("4. Activate campaigns on Monday 11/18")

    print("\n✅ Script ready. Use Claude with MCP tools to create campaigns.")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
