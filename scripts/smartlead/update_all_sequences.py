#!/usr/bin/env python3
"""Update all tier sequences with new copy"""

import requests

API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
BASE_URL = "https://server.smartlead.ai/api/v1"
CALENDLY_LINK = "https://calendly.com/appletreepd/30min"

def update_campaign(campaign_id, name, sequences):
    print(f"\nUpdating {name}...")
    url = f"{BASE_URL}/campaigns/{campaign_id}/sequences"
    params = {"api_key": API_KEY}
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, params=params, json={"sequences": sequences}, headers=headers)

    if response.status_code == 200:
        print(f"✅ {name} updated!")
        return True
    else:
        print(f"❌ Failed: {response.status_code} - {response.text[:200]}")
        return False

# A-Tier sequences (software users - mention their tech stack)
a_tier_sequences = [
    {
        "seq_number": 1,
        "seq_delay_details": {"delay_in_days": 0},
        "seq_variants": [{
            "subject": "Quick question about {{company_name}}",
            "email_body": """{{#if first_name}}{{first_name}},{{else}}Hey there,{{/if}}<div><br></div>Saw you're running {{service_software}} - you clearly take operations seriously.<div><br></div>Quick question: who handles your books? In-house or outsourced?<div><br></div>Just curious - we work with a lot of HVAC companies at your size and most are still piecing it together.<div><br></div>Patrick<div><br></div><div>--</div><div>Patrick Dichter</div><div>Appletree Business Services</div>""",
            "variant_label": "A"
        }]
    },
    {
        "seq_number": 2,
        "seq_delay_details": {"delay_in_days": 3},
        "seq_variants": [{
            "subject": "Re: Quick question",
            "email_body": f"""{{{{#if first_name}}}}{{{{first_name}}}}{{{{else}}}}Hey there{{{{/if}}}} - bumping this up.<div><br></div>If books/taxes are a headache, I have 15 min this week to see if we can help.<div><br></div>If not, no worries.<div><br></div><a href="{CALENDLY_LINK}">calendly.com/appletreepd/30min</a><div><br></div>Patrick""",
            "variant_label": "A"
        }]
    },
    {
        "seq_number": 3,
        "seq_delay_details": {"delay_in_days": 3},
        "seq_variants": [{
            "subject": "What most HVAC owners miss",
            "email_body": f"""{{{{#if first_name}}}}{{{{first_name}}}},{{{{else}}}}Hey there,{{{{/if}}}}<div><br></div>Most HVAC owners we talk to are leaving $15-30k/year on the table in tax savings.<div><br></div>Usually it's entity structure, retirement accounts, or equipment depreciation that's not set up right.<div><br></div>Worth a 15 min call to see if that's you?<div><br></div><a href="{CALENDLY_LINK}">calendly.com/appletreepd/30min</a><div><br></div>Patrick""",
            "variant_label": "A"
        }]
    },
    {
        "seq_number": 4,
        "seq_delay_details": {"delay_in_days": 4},
        "seq_variants": [{
            "subject": "Should I close your file?",
            "email_body": """{{#if first_name}}{{first_name}},{{else}}Hey there,{{/if}}<div><br></div>Haven't heard back so I'll assume timing isn't right.<div><br></div>If anything changes with your accounting situation, I'm here.<div><br></div>Patrick""",
            "variant_label": "A"
        }]
    }
]

# B-Tier sequences (high reviews - DO NOT use review_count variable, data is inconsistent)
b_tier_sequences = [
    {
        "seq_number": 1,
        "seq_delay_details": {"delay_in_days": 0},
        "seq_variants": [{
            "subject": "Quick question about {{company_name}}",
            "email_body": """{{#if first_name}}{{first_name}},{{else}}Hey there,{{/if}}<div><br></div>Quick question: who handles your books? In-house or outsourced?<div><br></div>Just curious - we work with a lot of HVAC companies and most are still piecing it together.<div><br></div>Patrick<div><br></div><div>--</div><div>Patrick Dichter</div><div>Appletree Business Services</div>""",
            "variant_label": "A"
        }]
    },
    {
        "seq_number": 2,
        "seq_delay_details": {"delay_in_days": 3},
        "seq_variants": [{
            "subject": "Re: Quick question",
            "email_body": f"""{{{{#if first_name}}}}{{{{first_name}}}}{{{{else}}}}Hey there{{{{/if}}}} - bumping this up.<div><br></div>If books/taxes are a headache, I have 15 min this week to see if we can help.<div><br></div>If not, no worries.<div><br></div><a href="{CALENDLY_LINK}">calendly.com/appletreepd/30min</a><div><br></div>Patrick""",
            "variant_label": "A"
        }]
    },
    {
        "seq_number": 3,
        "seq_delay_details": {"delay_in_days": 3},
        "seq_variants": [{
            "subject": "What most HVAC owners miss",
            "email_body": f"""{{{{#if first_name}}}}{{{{first_name}}}},{{{{else}}}}Hey there,{{{{/if}}}}<div><br></div>Most HVAC owners we talk to are leaving $15-30k/year on the table in tax savings.<div><br></div>Usually it's entity structure, retirement accounts, or equipment depreciation that's not set up right.<div><br></div>Worth a 15 min call to see if that's you?<div><br></div><a href="{CALENDLY_LINK}">calendly.com/appletreepd/30min</a><div><br></div>Patrick""",
            "variant_label": "A"
        }]
    },
    {
        "seq_number": 4,
        "seq_delay_details": {"delay_in_days": 4},
        "seq_variants": [{
            "subject": "Should I close your file?",
            "email_body": """{{#if first_name}}{{first_name}},{{else}}Hey there,{{/if}}<div><br></div>Haven't heard back so I'll assume timing isn't right.<div><br></div>If anything changes with your accounting situation, I'm here.<div><br></div>Patrick""",
            "variant_label": "A"
        }]
    }
]

if __name__ == "__main__":
    print("="*50)
    print("UPDATING ALL SEQUENCES")
    print("="*50)

    update_campaign(2677089, "A-Tier", a_tier_sequences)
    update_campaign(2677090, "B-Tier", b_tier_sequences)

    print("\n" + "="*50)
    print("DONE - C-Tier already updated separately")
    print("="*50)
