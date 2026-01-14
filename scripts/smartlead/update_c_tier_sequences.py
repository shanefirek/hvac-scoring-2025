#!/usr/bin/env python3
"""Update C-Tier sequences with new copy"""

import requests

API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
BASE_URL = "https://server.smartlead.ai/api/v1"
CALENDLY_LINK = "https://calendly.com/appletreepd/30min"

def update_sequences():
    print("Updating C-Tier sequences...")

    sequences = [
        {
            "seq_number": 1,
            "seq_delay_details": {"delay_in_days": 0},
            "seq_variants": [{
                "subject": "Quick question about {{company_name}}",
                "email_body": """{{#if first_name}}{{first_name}},{{else}}Hey there,{{/if}}<div><br></div>Do you handle your own books or have someone doing it for you?<div><br></div>Just curious - we work with a lot of HVAC companies and I'm always surprised how many owners are still doing it themselves.<div><br></div>Patrick<div><br></div><div>--</div><div>Patrick Dichter</div><div>Appletree Business Services</div>""",
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

    url = f"{BASE_URL}/campaigns/2677091/sequences"
    params = {"api_key": API_KEY}
    headers = {"Content-Type": "application/json"}

    response = requests.post(url, params=params, json={"sequences": sequences}, headers=headers)

    if response.status_code == 200:
        print("✅ C-Tier sequences updated!")
        print(response.json())
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    update_sequences()
