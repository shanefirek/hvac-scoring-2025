#!/usr/bin/env python3
"""
Re-enrich leads with missing tech stack data

Queries Supabase for leads without service_software, calls the working
Railway tech stack API, and updates scores.
"""

import os
import sys
import requests
import time
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://rlmuovkdvbxzyylbiunj.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
TECH_STACK_API = os.getenv('TECH_STACK_API_URL')
SCORING_API = os.getenv('SCORING_API_URL')

def get_leads_missing_tech_stack(limit=None):
    """Query Supabase for leads without service_software"""
    url = f"{SUPABASE_URL}/rest/v1/leads"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
    }

    params = {
        'select': 'id,email,domain,company,reviews_count,linkedin_url',
        'service_software': 'is.null',
        'domain': 'not.is.null',  # Only leads with domains
    }

    if limit:
        params['limit'] = limit

    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()

def detect_tech_stack(domain):
    """Call Railway tech stack API"""
    if not domain:
        return None

    try:
        resp = requests.post(
            TECH_STACK_API,
            json={'domain': domain},
            timeout=30
        )
        result = resp.json()

        # Priority order: ServiceTitan > Jobber > Housecall Pro
        if result.get('uses_servicetitan'):
            return 'ServiceTitan'
        elif result.get('uses_jobber'):
            return 'Jobber'
        elif result.get('uses_housecallpro'):
            return 'Housecall Pro'

        return None
    except Exception as e:
        print(f"  Tech stack error for {domain}: {e}")
        return None

def recalculate_score(lead_data):
    """Call Railway scoring API"""
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

def update_lead(lead_id, updates):
    """Update lead in Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/leads"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }

    params = {'id': f'eq.{lead_id}'}

    resp = requests.patch(url, headers=headers, params=params, json=updates)
    resp.raise_for_status()
    return resp.json()

def main(dry_run=False, limit=None, delay=0.5):
    """
    Re-enrich leads missing tech stack

    Args:
        dry_run: Just print what would happen
        limit: Only process N leads (for testing)
        delay: Seconds to wait between API calls (rate limiting)
    """
    print("Fetching leads with missing tech stack...")
    leads = get_leads_missing_tech_stack(limit=limit)
    print(f"Found {len(leads)} leads without service_software\n")

    if not leads:
        print("No leads to enrich!")
        return

    success_count = 0
    tech_found_count = 0
    error_count = 0

    for idx, lead in enumerate(leads, 1):
        email = lead.get('email')
        domain = lead.get('domain')
        lead_id = lead.get('id')

        print(f"[{idx}/{len(leads)}] {email} ({domain})...")

        try:
            # Step 1: Detect tech stack
            service_software = detect_tech_stack(domain)

            if service_software:
                print(f"  ✅ Found: {service_software}")
                tech_found_count += 1
            else:
                print(f"  ⚪ No tech stack detected")

            # Step 2: Recalculate score with tech stack
            scoring_payload = {
                'company': lead.get('company') or '',
                'reviews_count': lead.get('reviews_count') or 0,
                'service_software': service_software or '',
                'linkedin_url': lead.get('linkedin_url') or '',
                'domain': domain or ''
            }

            score, tier, messaging_strategy, score_breakdown = recalculate_score(scoring_payload)

            if dry_run:
                print(f"  [DRY RUN] Would update: tech={service_software}, score={score}, tier={tier}")
            else:
                # Step 3: Update in Supabase
                updates = {
                    'service_software': service_software,
                    'score': score,
                    'tier': tier,
                    'messaging_strategy': messaging_strategy,
                    'score_breakdown': score_breakdown,
                    'updated_at': 'now()'
                }

                update_lead(lead_id, updates)
                print(f"  💾 Updated: score={score}, tier={tier}")

            success_count += 1

            # Rate limiting
            if delay > 0:
                time.sleep(delay)

        except Exception as e:
            print(f"  ❌ Error: {e}")
            error_count += 1
            continue

    print(f"\n{'='*60}")
    print(f"✅ Success: {success_count}/{len(leads)}")
    print(f"🔍 Tech stack found: {tech_found_count}/{len(leads)} ({tech_found_count/len(leads)*100:.1f}%)")
    print(f"❌ Errors: {error_count}")

    if dry_run:
        print(f"\n⚠️  DRY RUN - No changes made. Run without --dry-run to update.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Re-enrich leads with tech stack data')
    parser.add_argument('--dry-run', action='store_true', help='Print what would happen without doing it')
    parser.add_argument('--limit', type=int, help='Only process N leads (for testing)')
    parser.add_argument('--delay', type=float, default=0.5, help='Seconds between API calls (default 0.5)')

    args = parser.parse_args()

    main(
        dry_run=args.dry_run,
        limit=args.limit,
        delay=args.delay
    )
