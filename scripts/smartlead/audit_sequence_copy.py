#!/usr/bin/env python3
"""
Audit All Sequence Copy for Spam Triggers

Analyzes every sequence across all 3 campaigns and flags:
- Spam trigger words
- Generic cold email phrases
- Fake threading (Re:, Fwd:)
- Missing personalization
- Overly salesy language

Usage:
    python audit_sequence_copy.py
"""

import requests
import json
from collections import defaultdict

API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
BASE_URL = "https://server.smartlead.ai/api/v1"

CAMPAIGNS = {
    "A-Tier": 2677089,
    "B-Tier": 2677090,
    "C-Tier": 2677091
}

# Spam trigger words and phrases
SPAM_TRIGGERS = {
    "HIGH RISK": [
        "click here", "buy now", "order now", "apply now",
        "sign up free", "risk free", "limited time", "act now",
        "100% free", "dear friend", "winner", "congratulations",
        "no obligation", "cancel anytime"
    ],
    "MEDIUM RISK": [
        "quick question", "just checking in", "following up",
        "touching base", "circling back", "wanted to reach out",
        "hope this email finds you well", "hope you're well",
        "i hope this email finds you", "per my last email"
    ],
    "GENERIC/SALESY": [
        "sound familiar", "does this resonate", "ring a bell",
        "worth a conversation", "worth 15 minutes", "worth a call",
        "are you the right person", "is this a good time",
        "let me know if you're interested", "hope to hear from you"
    ],
    "FAKE THREADING": [
        "re:", "fwd:", "fw:"
    ]
}

# Required personalization tokens
REQUIRED_TOKENS = ["{{first_name}}", "{{company_name}}"]

def api_call(method, endpoint):
    """Make API call to Smartlead"""
    url = f"{BASE_URL}{endpoint}"
    params = {"api_key": API_KEY}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ API Error: {e}")
        return None

def check_spam_triggers(text):
    """Check for spam trigger words/phrases"""
    text_lower = text.lower()
    found = defaultdict(list)

    for risk_level, triggers in SPAM_TRIGGERS.items():
        for trigger in triggers:
            if trigger in text_lower:
                found[risk_level].append(trigger)

    return dict(found)

def check_personalization(text):
    """Check for personalization tokens"""
    missing = []
    for token in REQUIRED_TOKENS:
        if token not in text:
            missing.append(token)
    return missing

def analyze_subject(subject):
    """Analyze subject line"""
    issues = []

    # Check length
    if len(subject) > 60:
        issues.append(f"⚠️ Too long ({len(subject)} chars, keep under 60)")
    if len(subject) < 20:
        issues.append(f"⚠️ Too short ({len(subject)} chars, aim for 30-50)")

    # Check for all caps
    if subject.isupper():
        issues.append("❌ ALL CAPS (major spam flag)")

    # Check for excessive punctuation
    if subject.count('!') > 1:
        issues.append(f"❌ Too many exclamation marks ({subject.count('!')})")
    if '!!' in subject or '???' in subject:
        issues.append("❌ Multiple punctuation (!!!, ???)")

    # Check for spam triggers
    spam = check_spam_triggers(subject)
    if spam:
        for risk, triggers in spam.items():
            issues.append(f"❌ {risk}: {', '.join(triggers)}")

    return issues

def analyze_body(body):
    """Analyze email body"""
    issues = []

    # Check length
    word_count = len(body.split())
    if word_count > 150:
        issues.append(f"⚠️ Too long ({word_count} words, aim for 75-125)")
    if word_count < 50:
        issues.append(f"⚠️ Too short ({word_count} words)")

    # Check for links
    calendly_link = "calendly.com/appletreepd/30min"
    has_calendly = calendly_link in body

    link_count = body.count('http://') + body.count('https://')

    if not has_calendly:
        issues.append("❌ Missing Calendly link")
    if link_count > 2:
        issues.append(f"⚠️ Too many links ({link_count}, keep to 1-2)")

    # Check for spam triggers
    spam = check_spam_triggers(body)
    if spam:
        for risk, triggers in spam.items():
            issues.append(f"❌ {risk}: {', '.join(triggers)}")

    # Check personalization
    missing_tokens = check_personalization(body)
    if missing_tokens:
        issues.append(f"⚠️ Missing tokens: {', '.join(missing_tokens)}")

    # Check for bullet points (can look promotional)
    bullet_count = body.count('→') + body.count('•') + body.count('-')
    if bullet_count > 5:
        issues.append(f"⚠️ Too many bullets ({bullet_count}, looks promotional)")

    return issues

def audit_campaign(tier, campaign_id):
    """Audit all sequences in a campaign"""
    print(f"\n{'='*70}")
    print(f"{tier} CAMPAIGN (ID: {campaign_id})")
    print(f"{'='*70}\n")

    sequences = api_call("GET", f"/campaigns/{campaign_id}/sequences")

    if not sequences:
        print("❌ Could not retrieve sequences")
        return

    for seq in sequences:
        seq_num = seq.get("seq_number", "?")
        delay = seq.get("seq_delay_details", {}).get("delayInDays", 0)

        # Get content from variants
        variants = seq.get("sequence_variants", [])
        if not variants:
            print(f"⚠️ Sequence {seq_num}: No variants found")
            continue

        variant = variants[0]
        subject = variant.get("subject", "")
        body = variant.get("email_body", "")

        print(f"📧 SEQUENCE {seq_num} (Day {delay})")
        print(f"{'─'*70}\n")

        # Show subject
        print(f"Subject: \"{subject}\"")
        subject_issues = analyze_subject(subject)
        if subject_issues:
            print("  Issues:")
            for issue in subject_issues:
                print(f"    {issue}")
        else:
            print("  ✅ Subject looks good")

        print()

        # Show body preview
        body_preview = body[:100].replace('\n', ' ') + "..." if len(body) > 100 else body
        print(f"Body: \"{body_preview}\"")
        print(f"Length: {len(body.split())} words")

        body_issues = analyze_body(body)
        if body_issues:
            print("  Issues:")
            for issue in body_issues:
                print(f"    {issue}")
        else:
            print("  ✅ Body looks good")

        print("\n")

def main():
    """Run audit on all campaigns"""
    print("\n" + "="*70)
    print("SEQUENCE COPY AUDIT - SPAM & DELIVERABILITY CHECK")
    print("="*70)

    for tier, campaign_id in CAMPAIGNS.items():
        audit_campaign(tier, campaign_id)

    print("="*70)
    print("AUDIT COMPLETE")
    print("="*70 + "\n")

    print("RECOMMENDATIONS:")
    print("  • Remove 'Re:' from subject lines (fake threading)")
    print("  • Replace generic phrases: 'quick question', 'sound familiar'")
    print("  • Keep subjects 30-50 characters")
    print("  • Keep body 75-125 words")
    print("  • Ensure all sequences have Calendly link")
    print("  • Use {{first_name}} and {{company_name}} tokens")
    print("  • Avoid exclamation marks and ALL CAPS")
    print()

if __name__ == "__main__":
    main()
