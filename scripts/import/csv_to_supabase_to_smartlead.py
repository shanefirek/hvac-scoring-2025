#!/usr/bin/env python3
"""
Direct import: CSV → Supabase → Smartlead

Replaces Clay + n8n entirely. Just runs the whole pipeline locally.
"""

import os
import sys
import pandas as pd
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://rlmuovkdvbxzyylbiunj.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')  # Need service role key
SMARTLEAD_API_KEY = os.getenv('SMARTLEAD_API_KEY', '38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8')

# Railway endpoints (optional - if you want to enrich in the script)
TECH_STACK_API = os.getenv('TECH_STACK_API_URL')  # Your Railway endpoint
SCORING_API = os.getenv('SCORING_API_URL')  # Your Railway endpoint

def enrich_tech_stack(domain):
    """Call Railway tech stack detector to check for FSM software"""
    if not TECH_STACK_API or not domain:
        return None

    try:
        # Single API call checks all 3 platforms
        resp = requests.post(
            TECH_STACK_API,
            json={'domain': domain},
            timeout=30  # Increased from 10s
        )
        result = resp.json()

        # Priority order: ServiceTitan > Jobber > Housecall Pro
        if result.get('uses_servicetitan'):
            return 'ServiceTitan'
        elif result.get('uses_jobber'):
            return 'Jobber'
        elif result.get('uses_housecallpro'):
            return 'Housecall Pro'

        # No matches found
        return None
    except Exception as e:
        print(f"  Tech stack detection error for {domain}: {e}")
        return None

def calculate_score(lead_data):
    """Call Railway scoring endpoint and return enriched fields"""
    if not SCORING_API:
        return None, None, None, None

    try:
        resp = requests.post(SCORING_API, json=lead_data, timeout=10)
        data = resp.json()
        return (
            data.get('score'),
            data.get('tier'),
            data.get('messaging_strategy'),
            data.get('breakdown', {})
        )
    except Exception as e:
        print(f"  Scoring error: {e}")
        return None, None, None, None

def upsert_to_supabase(lead):
    """Upsert lead to Supabase via sync_lead_from_clay function"""

    url = f"{SUPABASE_URL}/rest/v1/rpc/sync_lead_from_clay"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        'p_clay_id': None,  # No Clay ID for direct imports
        'p_email': lead.get('email'),
        'p_first_name': lead.get('first_name'),
        'p_last_name': lead.get('last_name'),
        'p_company': lead.get('name'),  # Company name
        'p_domain': lead.get('domain'),
        'p_linkedin_url': lead.get('company_linkedin'),
        'p_reviews_count': int(lead.get('reviews', 0) or 0),
        'p_service_software': lead.get('service_software'),
        'p_score': int(lead.get('score', 0) or 0),
        'p_tier': lead.get('tier'),
        'p_messaging_strategy': lead.get('messaging_strategy'),
        'p_score_breakdown': lead.get('score_breakdown', {}),
        'p_clay_data': {},  # Empty for direct imports
        'p_phone_number': lead.get('phone'),
        'p_city': lead.get('city'),
        'p_state': lead.get('state'),
        'p_postal_code': lead.get('postal_code')
    }

    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()  # Returns lead UUID

def add_to_smartlead_campaign(email, first_name, last_name, company, campaign_id, custom_fields=None):
    """Add lead to Smartlead campaign"""

    url = f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/leads"
    params = {'api_key': SMARTLEAD_API_KEY}

    lead_data = {
        'email': email,
        'first_name': first_name or '',
        'last_name': last_name or '',
        'company_name': company or '',
        'custom_fields': custom_fields or {}
    }

    payload = {'lead_list': [lead_data]}

    resp = requests.post(url, params=params, json=payload)
    resp.raise_for_status()
    return resp.json()

def main(
    csv_path,
    enrich=False,
    push_to_smartlead=False,
    campaign_mapping=None,
    dry_run=False
):
    """
    Main import pipeline

    Args:
        csv_path: Path to cleaned CSV
        enrich: Whether to call Railway endpoints for enrichment
        push_to_smartlead: Whether to push to Smartlead after Supabase
        campaign_mapping: Dict of tier -> campaign_id (e.g., {'A': 2677089, 'B': 2677090, 'C': 2677091})
        dry_run: Just print what would happen, don't actually do it
    """

    # Load CSV
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} leads from {csv_path}")

    success_count = 0
    error_count = 0

    for idx, row in df.iterrows():
        lead = row.to_dict()

        # Convert NaN to None for JSON serialization
        lead = {k: (None if pd.isna(v) else v) for k, v in lead.items()}

        email = lead.get('email')

        if not email:
            print(f"Row {idx}: No email, skipping")
            continue

        try:
            # Optional: Enrich with Railway endpoints
            if enrich:
                print(f"Enriching {email}...")

                # Step 1: Detect FSM software
                service_software = enrich_tech_stack(lead.get('domain'))

                # Step 2: Calculate score with detected tech stack
                scoring_payload = {
                    'company': lead.get('name'),
                    'reviews_count': int(lead.get('reviews', 0) or 0),
                    'service_software': service_software or '',
                    'linkedin_url': lead.get('company_linkedin') or '',
                    'domain': lead.get('domain') or ''
                }
                score, tier, messaging_strategy, score_breakdown = calculate_score(scoring_payload)

                # Step 3: Add enriched fields to lead
                lead['service_software'] = service_software
                lead['score'] = score
                lead['tier'] = tier
                lead['messaging_strategy'] = messaging_strategy
                lead['score_breakdown'] = score_breakdown

            if dry_run:
                print(f"[DRY RUN] Would upsert {email} to Supabase")
            else:
                # Upsert to Supabase
                lead_id = upsert_to_supabase(lead)
                print(f"✅ {email} → Supabase (ID: {lead_id})")

            # Optional: Push to Smartlead
            if push_to_smartlead and campaign_mapping:
                tier = lead.get('tier')
                campaign_id = campaign_mapping.get(tier)

                if campaign_id:
                    if dry_run:
                        print(f"[DRY RUN] Would add {email} to Smartlead campaign {campaign_id}")
                    else:
                        add_to_smartlead_campaign(
                            email=email,
                            first_name=lead.get('first_name'),
                            last_name=lead.get('last_name'),
                            company=lead.get('name'),
                            campaign_id=campaign_id,
                            custom_fields={
                                'score': str(lead.get('score', 0)),
                                'tier': tier,
                                'city': lead.get('city', ''),
                                'state': lead.get('state', '')
                            }
                        )
                        print(f"  → Smartlead campaign {campaign_id}")

            success_count += 1

        except Exception as e:
            print(f"❌ {email}: {e}")
            error_count += 1

    print(f"\n✅ Done: {success_count} success, {error_count} errors")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Import leads: CSV → Supabase → Smartlead')
    parser.add_argument('csv_path', help='Path to cleaned CSV file')
    parser.add_argument('--enrich', action='store_true', help='Enrich with Railway endpoints')
    parser.add_argument('--smartlead', action='store_true', help='Push to Smartlead campaigns')
    parser.add_argument('--dry-run', action='store_true', help='Print what would happen without doing it')

    args = parser.parse_args()

    # Campaign mapping (A/B/C tier → campaign IDs)
    campaign_mapping = {
        'A': 2677089,
        'B': 2677090,
        'C': 2677091
    }

    main(
        csv_path=args.csv_path,
        enrich=args.enrich,
        push_to_smartlead=args.smartlead,
        campaign_mapping=campaign_mapping,
        dry_run=args.dry_run
    )
