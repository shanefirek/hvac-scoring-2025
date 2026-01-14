#!/usr/bin/env python3
"""
Pull real-time campaign analytics (opens, clicks, replies, bookings)
"""

import requests
from datetime import datetime, timezone

API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
BASE_URL = "https://server.smartlead.ai/api/v1"

CAMPAIGNS = {
    "A": {"id": 2677089, "name": "A-Tier: Software & Scale"},
    "B": {"id": 2677090, "name": "B-Tier: Growth Signal"},
    "C": {"id": 2677091, "name": "C-Tier: Pain Focus"}
}

def api_call(method, endpoint):
    """Make API call"""
    url = f"{BASE_URL}{endpoint}"
    params = {"api_key": API_KEY}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

print("="*70)
print("📊 CAMPAIGN ANALYTICS - REAL-TIME DATA")
print("="*70)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %I:%M %p ET')}\n")

total_sent = 0
total_opened = 0
total_clicked = 0
total_replied = 0
total_booked = 0

for tier, config in CAMPAIGNS.items():
    campaign_id = config["id"]
    campaign_name = config["name"]

    print(f"\n{'='*70}")
    print(f"{tier}-TIER: {campaign_name}")
    print('='*70)

    # Get campaign analytics
    analytics = api_call("GET", f"/campaigns/{campaign_id}/analytics")

    if analytics:
        # Overall stats
        sent = analytics.get("sent", 0)
        delivered = analytics.get("delivered", 0)
        opened = analytics.get("opened", 0)
        clicked = analytics.get("clicked", 0)
        replied = analytics.get("replied", 0)
        bounced = analytics.get("bounced", 0)

        # Today's stats
        sent_today = analytics.get("sent_today", 0)
        opened_today = analytics.get("opened_today", 0)
        clicked_today = analytics.get("clicked_today", 0)
        replied_today = analytics.get("replied_today", 0)

        # Calculate rates
        open_rate = (opened / sent * 100) if sent > 0 else 0
        click_rate = (clicked / sent * 100) if sent > 0 else 0
        reply_rate = (replied / sent * 100) if sent > 0 else 0

        print(f"\n📈 ALL-TIME STATS:")
        print(f"   Sent: {sent}")
        print(f"   Delivered: {delivered}")
        print(f"   Opened: {opened} ({open_rate:.1f}%)")
        print(f"   Clicked: {clicked} ({click_rate:.1f}%)")
        print(f"   Replied: {replied} ({reply_rate:.1f}%)")
        print(f"   Bounced: {bounced}")

        print(f"\n📅 TODAY (Nov 18):")
        print(f"   Sent: {sent_today}")
        print(f"   Opened: {opened_today}")
        print(f"   Clicked: {clicked_today}")
        print(f"   Replied: {replied_today}")

        total_sent += sent
        total_opened += opened
        total_clicked += clicked
        total_replied += replied

    # Get leads with recent activity
    leads = api_call("GET", f"/campaigns/{campaign_id}/leads?limit=100")

    if leads and "data" in leads:
        lead_list = leads["data"]

        # Find leads with clicks
        clicked_leads = [l for l in lead_list if l.get("clicked", False)]
        replied_leads = [l for l in lead_list if l.get("replied", False)]

        if clicked_leads:
            print(f"\n🖱️  CLICKED LEADS ({len(clicked_leads)}):")
            for lead in clicked_leads[:10]:  # Show first 10
                email = lead.get("email", "unknown")
                company = lead.get("company_name", "unknown")
                last_clicked = lead.get("last_clicked_at", "")
                print(f"   • {email} ({company})")

        if replied_leads:
            print(f"\n✉️  REPLIED LEADS ({len(replied_leads)}):")
            for lead in replied_leads[:10]:
                email = lead.get("email", "unknown")
                company = lead.get("company_name", "unknown")
                print(f"   • {email} ({company})")

print(f"\n{'='*70}")
print("📊 TOTAL ACROSS ALL CAMPAIGNS")
print('='*70)
print(f"   Sent: {total_sent}")
print(f"   Opened: {total_opened} ({(total_opened/total_sent*100) if total_sent > 0 else 0:.1f}%)")
print(f"   Clicked: {total_clicked} ({(total_clicked/total_sent*100) if total_sent > 0 else 0:.1f}%)")
print(f"   Replied: {total_replied} ({(total_replied/total_sent*100) if total_sent > 0 else 0:.1f}%)")

print(f"\n{'='*70}")
print("💡 INTERPRETATION")
print('='*70)

if total_sent == 0:
    print("⚠️  No emails sent yet - campaigns may still be warming up")
elif total_sent < 50:
    print(f"📤 Early stage: Only {total_sent} emails sent so far")
    print("   → Too early for meaningful metrics")
    print("   → Give it 24-48 hours for more data")
elif total_replied > 0:
    print(f"🎉 {total_replied} REPLIES! Check Smartlead inbox for conversations")
    print("   → Look for booking intent (\"let's talk\", \"when can we chat\")")
    print("   → Manually follow up to close for Patrick meeting")
elif total_clicked > 0:
    print(f"🖱️  {total_clicked} clicks on Calendly link - HIGH INTEREST!")
    print("   → Check Patrick's Calendly for actual bookings")
    print("   → These are warm leads, follow up if they didn't book")
elif total_opened > 0:
    open_pct = total_opened / total_sent * 100
    if open_pct > 30:
        print(f"✅ {open_pct:.1f}% open rate is STRONG (above 20% avg)")
        print("   → Messaging is working, give it time for clicks/replies")
    else:
        print(f"⚠️  {open_pct:.1f}% open rate is below avg (20-30% expected)")
        print("   → Subject lines may need work")

print(f"\n🕐 Day 2 Reality Check:")
print("   Cold email typically takes 3-5 days to see first replies")
print("   Normal conversion timeline:")
print("      Day 1-2: Opens + clicks")
print("      Day 3-5: First replies")
print("      Day 7-14: Booked meetings")
print("   Your frustration is valid but this is normal pacing\n")

print('='*70 + "\n")
