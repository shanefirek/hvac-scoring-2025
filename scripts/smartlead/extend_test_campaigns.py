#!/usr/bin/env python3
"""Extend A/B test campaign sequences with urgency follow-ups"""

import requests

API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
BASE_URL = "https://server.smartlead.ai/api/v1"

# Each campaign's original Email 1 (keeping their unique angles)
CAMPAIGN_EMAIL1 = {
    2757801: {  # M&A Variant
        "subject": "Your accountant files taxes. Do they know what {{company_name}} is worth?",
        "email_body": """{{#if first_name}}{{first_name}},{{else}}Hey there,{{/if}}<br><div><br></div><div>Most accountants can't tell you what your business would sell for. They've never bought or sold one.</div><div><br></div><div>Our team has done 10+ deals. We built a scorecard that covers the full picture - books, taxes, wealth, and exit readiness.</div><div><br></div><div>Most HVAC owners score 35 out of 100.</div><div><br></div><div>Free until Jan 15 (normally $500).</div><div><br></div><div>Reply "score" and I'll send the details.</div><div><br></div><div>--</div><div><br></div><div>Patrick Dichter</div><div>Owner, Business Consultant</div>Appletree Business Services"""
    },
    2757802: {  # 35/100 Variant
        "subject": "Most HVAC owners score 35/100 on this",
        "email_body": """<div>{{#if first_name}}{{first_name}},{{else}}Hey there,{{/if}}<br><br></div><div>Quick question - do you know if {{company_name}} made money last month? Like, actually know?</div><div><br></div><div>We built a scorecard that shows where you stand across books, taxes, and financial health. Most contractors score way lower than they expect.</div><div><br></div><div>30 minutes. Free until Jan 15 (normally $500).</div><div><br></div><div>Reply "score" if you want in.</div><div><br></div><div>--</div><div><br></div><div>Patrick Dichter</div><div>Owner, Business Consultant</div>Appletree Business Services"""
    },
    2757804: {  # Social Proof Variant
        "subject": "You guys help me sleep",
        "email_body": """{{#if first_name}}{{first_name}},{{else}}So,{{/if}}<br><br><div>That's what an HVAC owner told us after 6 months working together.</div><div><br></div><div>We do bookkeeping, tax, and payroll in one place - but we also think about where your business is headed. Most accountants don't.</div><div><br></div><div>Built a scorecard that shows where you stand. Only takes 30 mins, free until Jan 15 (normally $500).</div><div><br></div><div>Reply "score" if you're curious.</div><div><br></div><div>--</div><div><br></div><div>Patrick Dichter</div><div>Owner, Business Consultant</div>Appletree Business Services"""
    },
    2757805: {  # Direct Variant
        "subject": "Ready for your exit?",
        "email_body": """{{#if first_name}}{{first_name}},{{else}}Hey there,{{/if}}<br><br><div>Does your accountant think about your business beyond tax season?</div><div><br></div><div>We do. Built a 100-point scorecard that covers books, taxes, wealth building, and exit readiness.</div><div><br></div><div>Free until Jan 15 (normally $500).</div><div><br></div><div>Reply "score" if you want it.</div><div><br></div><div>--</div><div><br></div><div>Patrick Dichter</div><div>Owner, Business Consultant</div>Appletree Business Services"""
    }
}

# Follow-up emails (same for all campaigns)
FOLLOWUP_EMAILS = [
    {
        "seq_number": 2,
        "seq_delay_details": {"delay_in_days": 3},
        "seq_variants": [{
            "subject": "Re: Quick follow-up",
            "email_body": """{{#if first_name}}{{first_name}}{{else}}Hey there{{/if}} - bumping this up.<div><br></div>The free scorecard offer expires Jan 15. After that it's $500.<div><br></div>Takes 15 min. You'll know exactly where your business stands - books, taxes, and exit readiness.<div><br></div>Reply "score" if you want in.<div><br></div>Patrick""",
            "variant_label": "A"
        }]
    },
    {
        "seq_number": 3,
        "seq_delay_details": {"delay_in_days": 3},
        "seq_variants": [{
            "subject": "10 days left",
            "email_body": """{{#if first_name}}{{first_name}},{{else}}Hey there,{{/if}}<div><br></div>Just a heads up - the free scorecard closes Jan 15.<div><br></div>Most HVAC owners we run it for find $15-30k in missed tax savings. Worth 15 minutes to find out.<div><br></div>Reply "score" and I'll send you the link.<div><br></div>Patrick""",
            "variant_label": "A"
        }]
    },
    {
        "seq_number": 4,
        "seq_delay_details": {"delay_in_days": 4},
        "seq_variants": [{
            "subject": "Closing your file",
            "email_body": """{{#if first_name}}{{first_name}},{{else}}Hey there,{{/if}}<div><br></div>Haven't heard back, so I'll assume the timing isn't right.<div><br></div>If you change your mind before Jan 15, the free scorecard offer still stands. After that it goes back to $500.<div><br></div>Patrick""",
            "variant_label": "A"
        }]
    }
]

def update_campaign(campaign_id, name):
    print(f"\nUpdating {name} (ID: {campaign_id})...")

    # Build full sequence: original Email 1 + follow-ups
    email1 = CAMPAIGN_EMAIL1[campaign_id]
    sequences = [
        {
            "seq_number": 1,
            "seq_delay_details": {"delay_in_days": 0},
            "seq_variants": [{
                "subject": email1["subject"],
                "email_body": email1["email_body"],
                "variant_label": "A"
            }]
        }
    ] + FOLLOWUP_EMAILS

    url = f"{BASE_URL}/campaigns/{campaign_id}/sequences"
    params = {"api_key": API_KEY}
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, params=params, json={"sequences": sequences}, headers=headers)

    if response.status_code == 200:
        print(f"  Sequences updated (4 emails)")
        return True
    else:
        print(f"  FAILED: {response.status_code} - {response.text[:200]}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("EXTENDING A/B TEST CAMPAIGN SEQUENCES")
    print("Adding urgency follow-ups (Jan 15 deadline)")
    print("=" * 50)

    campaigns = [
        (2757801, "M&A Variant"),
        (2757802, "35/100 Variant"),
        (2757804, "Social Proof"),
        (2757805, "Direct Variant"),
    ]

    success = 0
    for campaign_id, name in campaigns:
        if update_campaign(campaign_id, name):
            success += 1

    print("\n" + "=" * 50)
    print(f"DONE - {success}/4 campaigns updated")
    print("=" * 50)
