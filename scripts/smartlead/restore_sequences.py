#!/usr/bin/env python3
"""
Restore all sequences to campaigns (with Calendly links + spam word fix)

This restores all 4+3+2=9 sequences that were accidentally deleted
when trying to update individual sequences.
"""

import requests
import json

API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
BASE_URL = "https://server.smartlead.ai/api/v1"
CALENDLY_LINK = "https://calendly.com/appletreepd/30min"

def api_call(method, endpoint, data=None):
    """Make API call to Smartlead"""
    url = f"{BASE_URL}{endpoint}"
    params = {"api_key": API_KEY}
    headers = {"Content-Type": "application/json"}

    try:
        if method == "POST":
            response = requests.post(url, params=params, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                print(f"   {e.response.json()}")
            except:
                print(f"   {e.response.text[:500]}")
        return None

def restore_a_tier_sequences():
    """Restore all 4 A-Tier sequences"""
    print("\n📝 Restoring A-Tier Sequences...")

    sequences = [
        {
            "seq_number": 1,
            "seq_delay_details": {"delay_in_days": 0},
            "seq_variants": [{
                "subject": "{{first_name}} - tax season question",
                "email_body": f"""{{{{first_name}}}},<div><br></div>How responsive is your CPA during busy season?<div><br></div>Most HVAC owners running {{{{service_software}}}} tell us the same thing: They can't get their accountant on the phone during tax season, then April hits and there's a surprise $15k bill.<div><br></div>You're clearly running a tight operation at {{{{company}}}} ({{{{review_count}}}} reviews doesn't happen by accident). But if your accounting feels like a black hole, we should talk.<div><br></div>We're Appletree Business Services. We specialize in trades at your scale — monthly books, proactive tax planning, fixed pricing. No surprises.<div><br></div>Worth a conversation? {CALENDLY_LINK}<div><br></div>Shane<br>Appletree Business Services""",
                "variant_label": "A"
            }]
        },
        {
            "seq_number": 2,
            "seq_delay_details": {"delay_in_days": 4},
            "seq_variants": [{
                "subject": "Re: Quick question about {{company}}'s accounting",
                "email_body": f"""{{{{first_name}}}},<div><br></div>Following up about {{{{company}}}}'s accounting.<div><br></div>You're running {{{{service_software}}}}, so you clearly have your operations dialed in. But here's the pattern we see constantly with HVAC companies at your scale:<div><br></div>→ CPA goes MIA during busy season<div><br></div>→ Books are 3 months behind<div><br></div>→ April brings surprise tax bills<div><br></div>Sound familiar?<div><br></div>We handle bookkeeping, payroll, and strategic tax planning for growing HVAC companies. Fixed monthly price, proactive communication, 24-hour response time.<div><br></div>If your current CPA setup isn't working, let's talk: {CALENDLY_LINK}<div><br></div>Shane<br>Appletree Business Services""",
                "variant_label": "A"
            }]
        },
        {
            "seq_number": 3,
            "seq_delay_details": {"delay_in_days": 9},
            "seq_variants": [{
                "subject": "Your tech stack vs. your CPA",
                "email_body": f"""{{{{first_name}}}},<div><br></div>You're running {{{{service_software}}}}. That's a $10k+/year investment in doing things right.<div><br></div>But let me guess — your CPA still wants to chat "once things calm down" and sends you a bill you weren't expecting.<div><br></div>We work with HVAC companies that have outgrown the local accountant who only shows up in March.<div><br></div>What we do differently:<div><br></div>→ Monthly books (not once-a-year scrambles)<div><br></div>→ Proactive tax planning (not surprise bills)<div><br></div>→ Fixed pricing (no hourly billing mysteries)<div><br></div>→ 24-hour response time (not radio silence)<div><br></div>Companies like {{{{company}}}} deserve financial systems as dialed in as their operations.<div><br></div>Open to a quick call?<div><br></div>{CALENDLY_LINK}<div><br></div>Shane<br>Appletree Business Services""",
                "variant_label": "A"
            }]
        },
        {
            "seq_number": 4,
            "seq_delay_details": {"delay_in_days": 14},
            "seq_variants": [{
                "subject": "Last note about {{company}}",
                "email_body": f"""{{{{first_name}}}},<div><br></div>Last email, I promise.<div><br></div>{{{{company}}}} has {{{{review_count}}}} reviews and you're running {{{{service_software}}}}. You're clearly doing things right.<div><br></div>If your accounting is the only part of your business that still feels chaotic — unresponsive CPA, messy books, tax surprises — we should talk.<div><br></div>We're Appletree. We clean up the financial side so you can focus on running jobs.<div><br></div>If now's not the time, no worries. But if it is, here's my calendar: {CALENDLY_LINK}<div><br></div>Shane<br>Appletree Business Services""",
                "variant_label": "A"
            }]
        }
    ]

    result = api_call("POST", "/campaigns/2677089/sequences", {"sequences": sequences})
    if result and result.get("ok"):
        print("   ✅ A-Tier sequences restored (4 sequences)")
        return True
    else:
        print("   ❌ Failed to restore A-Tier sequences")
        return False

def restore_b_tier_sequences():
    """Restore all 3 B-Tier sequences"""
    print("\n📝 Restoring B-Tier Sequences...")

    sequences = [
        {
            "seq_number": 1,
            "seq_delay_details": {"delay_in_days": 0},
            "seq_variants": [{
                "subject": "Saw {{company}} on Google",
                "email_body": f"""{{{{first_name}}}},<div><br></div>Came across {{{{company}}}} and saw your {{{{review_count}}}} reviews. Clearly you're doing something right.<div><br></div>Quick question: How responsive is your CPA during tax season?<div><br></div>Most HVAC owners at your scale tell us they can't get their accountant on the phone for weeks. Then April hits and there's a $12k surprise bill they weren't planning for.<div><br></div>We're Appletree Business Services. We work with a lot of HVAC, plumbing, and home service businesses. Monthly books, proactive tax planning, fixed monthly pricing.<div><br></div>Worth a conversation?<div><br></div>{CALENDLY_LINK}<div><br></div>Shane<br>Appletree Business Services""",
                "variant_label": "A"
            }]
        },
        {
            "seq_number": 2,
            "seq_delay_details": {"delay_in_days": 5},
            "seq_variants": [{
                "subject": "Re: Saw {{company}} on Google",
                "email_body": f"""{{{{first_name}}}},<div><br></div>Following up about {{{{company}}}}'s accounting.<div><br></div>**Common pattern with HVAC companies at your scale:**<div><br></div>→ CPA disappears during busy season<div><br></div>→ Books are months behind<div><br></div>→ Tax bills are always a surprise<div><br></div>→ You're running the business blind on financials<div><br></div>Sound familiar?<div><br></div>We help HVAC companies get out of that chaos and into clarity.<div><br></div>What we do:<div><br></div>- Monthly bookkeeping & cleanup<div><br></div>- Strategic tax planning (not just filing)<div><br></div>- Fixed monthly price, no surprises<div><br></div>If that's what {{{{company}}}} needs, let's talk: {CALENDLY_LINK}<div><br></div>Shane<br>Appletree Business Services""",
                "variant_label": "A"
            }]
        },
        {
            "seq_number": 3,
            "seq_delay_details": {"delay_in_days": 12},
            "seq_variants": [{
                "subject": "One last thing about {{company}}",
                "email_body": f"""{{{{first_name}}}},<div><br></div>Last email from me.<div><br></div>{{{{company}}}} has {{{{review_count}}}} Google reviews — your reputation is spotless. Your books should be too.<div><br></div>If you're tired of:<div><br></div>- Playing phone tag with your CPA<div><br></div>- Getting surprise tax bills<div><br></div>- Never knowing where you actually stand financially<div><br></div>We should talk.<div><br></div>We're Appletree. We simplify the financial side so you can focus on getting jobs done.<div><br></div>Here's my calendar if you want to chat: {CALENDLY_LINK}<div><br></div>Shane<br>Appletree Business Services""",
                "variant_label": "A"
            }]
        }
    ]

    result = api_call("POST", "/campaigns/2677090/sequences", {"sequences": sequences})
    if result and result.get("ok"):
        print("   ✅ B-Tier sequences restored (3 sequences)")
        return True
    else:
        print("   ❌ Failed to restore B-Tier sequences")
        return False

def restore_c_tier_sequences():
    """Restore all 2 C-Tier sequences (with spam word fix)"""
    print("\n📝 Restoring C-Tier Sequences...")

    sequences = [
        {
            "seq_number": 1,
            "seq_delay_details": {"delay_in_days": 0},
            "seq_variants": [{
                "subject": "Question about your CPA",
                # Fixed "stress-free" -> "low-stress"
                "email_body": f"""{{{{first_name}}}},<div><br></div>Quick question about {{{{company}}}}: How responsive is your accountant during tax season?<div><br></div>Most HVAC owners tell us the same story — they can't get their CPA on the phone for weeks, books are always behind, and April brings a surprise tax bill they weren't ready for.<div><br></div>Sound familiar?<div><br></div>We're Appletree Business Services. We work with a lot of HVAC, plumbing, and home service businesses.<div><br></div>We keep your books simple, your taxes predictable, and your weekends low-stress.<div><br></div>Worth 15 minutes to see if we're a fit?<div><br></div>{CALENDLY_LINK}<div><br></div>Shane<br>Appletree Business Services""",
                "variant_label": "A"
            }]
        },
        {
            "seq_number": 2,
            "seq_delay_details": {"delay_in_days": 10},
            "seq_variants": [{
                "subject": "Re: Question about your CPA",
                "email_body": f"""{{{{first_name}}}},<div><br></div>Last email from me about {{{{company}}}}'s accounting.<div><br></div>If you're dealing with:<div><br></div>→ An unresponsive CPA who disappears during busy season<div><br></div>→ Books that are months behind<div><br></div>→ Surprise tax bills every April<div><br></div>We can help.<div><br></div>We're Appletree — we work with a lot of trades and home service businesses. Monthly bookkeeping, proactive tax planning, fixed pricing. No surprises.<div><br></div>You handle the calls. We handle the numbers.<div><br></div>If you want to talk, here's my calendar: {CALENDLY_LINK}<div><br></div>Shane<br>Appletree Business Services""",
                "variant_label": "A"
            }]
        }
    ]

    result = api_call("POST", "/campaigns/2677091/sequences", {"sequences": sequences})
    if result and result.get("ok"):
        print("   ✅ C-Tier sequences restored (2 sequences, spam word fixed)")
        return True
    else:
        print("   ❌ Failed to restore C-Tier sequences")
        return False

def main():
    print("="*70)
    print("RESTORING ALL SEQUENCES WITH CALENDLY LINKS + SPAM FIX")
    print("="*70)

    restore_a_tier_sequences()
    restore_b_tier_sequences()
    restore_c_tier_sequences()

    print("\n" + "="*70)
    print("RESTORATION COMPLETE")
    print("="*70)
    print("\nRun audit to verify:")
    print("   python3 audit_smartlead_campaigns.py\n")

if __name__ == "__main__":
    main()
