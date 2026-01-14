#!/usr/bin/env python3
"""Export unsent leads to CSV files by tier for Smartlead import."""

import os
import csv
from dotenv import load_dotenv
from supabase import create_client

# Load .env file
load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_KEY")
)

def export_leads():
    """Export unsent leads by SCORE to CSV files for correct campaign routing."""

    # Query all unsent leads
    result = supabase.table("leads").select(
        "email, first_name, last_name, company, domain, linkedin_url, "
        "reviews_count, service_software, phone_number, city, state, tier, score"
    ).or_("in_smartlead.eq.false,in_smartlead.is.null").or_("suppressed.eq.false,suppressed.is.null").execute()

    leads = result.data
    print(f"Total unsent leads: {len(leads)}")

    # Separate by SCORE (not tier field - score is source of truth)
    # A-Tier: 20-30 pts → Campaign 2677089
    # B-Tier: 10-19 pts → Campaign 2677090
    # C-Tier: 0-9 pts  → Campaign 2677091
    a_tier = [l for l in leads if (l.get('score') or 0) >= 20]
    b_tier = [l for l in leads if 10 <= (l.get('score') or 0) < 20]
    c_tier = [l for l in leads if (l.get('score') or 0) < 10]

    print(f"\nBy SCORE (source of truth):")
    print(f"  A-tier (20-30 pts): {len(a_tier)} → Campaign 2677089")
    print(f"  B-tier (10-19 pts): {len(b_tier)} → Campaign 2677090")
    print(f"  C-tier (0-9 pts):   {len(c_tier)} → Campaign 2677091")

    # CSV headers matching Smartlead import format
    headers = [
        'email', 'first_name', 'last_name', 'company_name', 'website',
        'linkedin_url', 'reviews_count', 'service_software', 'phone',
        'city', 'state'
    ]

    output_dir = "/Users/shanefirek/projects/appletree-outbound-2025/appletree-data-pipeline/data/exports"
    os.makedirs(output_dir, exist_ok=True)

    def write_csv(leads, filename):
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for lead in leads:
                writer.writerow([
                    lead.get('email', ''),
                    lead.get('first_name', 'there') or 'there',
                    lead.get('last_name', '') or '',
                    lead.get('company', '') or '',
                    lead.get('domain', '') or '',
                    lead.get('linkedin_url', '') or '',
                    lead.get('reviews_count', 0) or 0,
                    lead.get('service_software', '') or '',
                    lead.get('phone_number', '') or '',
                    lead.get('city', '') or '',
                    lead.get('state', '') or ''
                ])
        print(f"Wrote {len(leads)} leads to {filepath}")

    write_csv(a_tier, 'unsent_a_tier_full.csv')
    write_csv(b_tier, 'unsent_b_tier_full.csv')
    write_csv(c_tier, 'unsent_c_tier_full.csv')

    print("\nDone! Import these CSVs to Smartlead campaigns:")
    print("  A-tier → Campaign 2677089")
    print("  B-tier → Campaign 2677090")
    print("  C-tier → Campaign 2677091")

if __name__ == "__main__":
    export_leads()
