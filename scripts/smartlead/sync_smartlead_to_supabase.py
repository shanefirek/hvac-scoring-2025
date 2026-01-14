#!/usr/bin/env python3
"""
Sync Smartlead Leads to Supabase
=================================

One-time script to consolidate Smartlead leads into Supabase.
Uses smart merge logic to fill missing names from Smartlead while preserving Clay scoring data.

Usage:
    python scripts/smartlead/sync_smartlead_to_supabase.py --dry-run  # Preview changes
    python scripts/smartlead/sync_smartlead_to_supabase.py            # Execute merge

Environment Variables:
    SMARTLEAD_API_KEY - Your Smartlead API key
    SUPABASE_URL - Your Supabase project URL
    SUPABASE_SERVICE_KEY - Your Supabase service role key
"""

import os
import sys
import argparse
import requests
from datetime import datetime
from typing import List, Dict, Any
import csv
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Campaign IDs to sync
CAMPAIGN_IDS = [2677089, 2677090, 2677091]  # A-Tier, B-Tier, C-Tier

# API endpoints
SMARTLEAD_API_BASE = "https://server.smartlead.ai/api/v1"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SMARTLEAD_API_KEY = os.getenv("SMARTLEAD_API_KEY")


class SmartleadToSupabaseSync:
    """Sync Smartlead leads to Supabase with smart merging"""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.stats = {
            'total_smartlead_leads': 0,
            'new_leads_inserted': 0,
            'existing_leads_updated': 0,
            'names_filled': 0,
            'campaigns_added': 0,
            'smartlead_ids_written': 0,
            'errors': 0
        }
        self.changes_log = []

        # Validate env vars
        if not all([SUPABASE_URL, SUPABASE_SERVICE_KEY, SMARTLEAD_API_KEY]):
            raise ValueError("Missing required environment variables. Check SUPABASE_URL, SUPABASE_SERVICE_KEY, SMARTLEAD_API_KEY")

    def fetch_smartlead_leads(self, campaign_id: int) -> List[Dict[str, Any]]:
        """Fetch all leads from a Smartlead campaign"""
        print(f"📥 Fetching leads from campaign {campaign_id}...")

        url = f"{SMARTLEAD_API_BASE}/campaigns/{campaign_id}/leads"
        headers = {}
        params = {"api_key": SMARTLEAD_API_KEY, "limit": 100, "offset": 0}

        all_leads = []

        while True:
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()

                # Get leads from 'data' array (Smartlead API format)
                campaign_leads = data.get('data', [])
                if not campaign_leads:
                    break

                # Extract the nested 'lead' object from each item
                leads = [item.get('lead', {}) for item in campaign_leads if 'lead' in item]
                all_leads.extend(leads)
                print(f"  ├─ Fetched {len(leads)} leads (total: {len(all_leads)})")

                # Check if there are more pages
                if len(leads) < params['limit']:
                    break

                params['offset'] += params['limit']

            except requests.RequestException as e:
                print(f"  └─ ❌ Error fetching leads from campaign {campaign_id}")
                print(f"     Error: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"     Status Code: {e.response.status_code}")
                    print(f"     Response Body: {e.response.text[:500]}")  # First 500 chars
                print(f"     URL: {url}")
                print(f"     API Key (last 4): ...{SMARTLEAD_API_KEY[-4:]}")
                self.stats['errors'] += 1
                break

        print(f"  └─ ✅ Total leads fetched: {len(all_leads)}")
        return all_leads

    def update_smartlead_lead_id(self, email: str, smartlead_lead_id: int) -> bool:
        """Update smartlead_lead_id for a lead by email"""
        url = f"{SUPABASE_URL}/rest/v1/leads"
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }

        params = {"email": f"eq.{email.lower()}"}
        payload = {
            "smartlead_lead_id": smartlead_lead_id,
            "in_smartlead": True,
            "last_smartlead_sync": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        try:
            response = requests.patch(url, headers=headers, params=params, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"    ❌ Error updating smartlead_lead_id for {email}: {e}")
            return False

    def merge_lead_to_supabase(self, email: str, first_name: str, last_name: str,
                                company: str, campaign_id: int, phone_number: str = None,
                                location: str = None, linkedin_url: str = None,
                                website: str = None) -> Dict[str, Any]:
        """Call Supabase merge_lead_data() function"""
        url = f"{SUPABASE_URL}/rest/v1/rpc/merge_lead_data"
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

        payload = {
            "p_email": email,
            "p_smartlead_first_name": first_name,
            "p_smartlead_last_name": last_name,
            "p_smartlead_company": company,
            "p_smartlead_campaign_id": campaign_id,
            "p_smartlead_data": {},
            "p_phone_number": phone_number,
            "p_location": location,
            "p_linkedin_url": linkedin_url,
            "p_website": website
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()

            if result and len(result) > 0:
                return result[0]
            else:
                return {"action": "error", "changes": {}}

        except requests.RequestException as e:
            print(f"    ❌ Error merging {email}: {e}")
            self.stats['errors'] += 1
            return {"action": "error", "changes": {}}

    def process_campaign(self, campaign_id: int):
        """Process all leads from a campaign"""
        leads = self.fetch_smartlead_leads(campaign_id)
        self.stats['total_smartlead_leads'] += len(leads)

        print(f"\n🔄 Processing {len(leads)} leads from campaign {campaign_id}...")

        for idx, lead in enumerate(leads, 1):
            email = (lead.get('email') or '').strip()
            smartlead_lead_id = lead.get('id')  # CRITICAL: Extract smartlead_lead_id
            first_name = (lead.get('first_name') or '').strip() or None
            last_name = (lead.get('last_name') or '').strip() or None
            company = (lead.get('company_name') or '').strip() or None
            phone_number = (lead.get('phone_number') or '').strip() or None
            location = (lead.get('location') or '').strip() or None
            linkedin_url = (lead.get('linkedin_profile') or '').strip() or None  # Smartlead uses 'linkedin_profile'
            website = (lead.get('website') or '').strip() or None

            if not email:
                print(f"  [{idx}/{len(leads)}] ⚠️  Skipping lead with no email")
                self.stats['errors'] += 1
                continue

            if not smartlead_lead_id:
                print(f"  [{idx}/{len(leads)}] ⚠️  Skipping {email} - no smartlead_lead_id")
                self.stats['errors'] += 1
                continue

            if self.dry_run:
                print(f"  [{idx}/{len(leads)}] 🔍 DRY-RUN: Would merge {email} + write smartlead_lead_id={smartlead_lead_id}")
                self.changes_log.append({
                    'email': email,
                    'smartlead_lead_id': smartlead_lead_id,
                    'first_name': first_name,
                    'last_name': last_name,
                    'company': company,
                    'phone_number': phone_number,
                    'location': location,
                    'linkedin_url': linkedin_url,
                    'website': website,
                    'campaign_id': campaign_id,
                    'action': 'dry_run'
                })
            else:
                result = self.merge_lead_to_supabase(
                    email, first_name, last_name, company, campaign_id,
                    phone_number, location, linkedin_url, website
                )
                action = result.get('action', 'unknown')
                changes = result.get('changes', {})

                # CRITICAL: Write back smartlead_lead_id to Supabase
                if action in ['inserted', 'updated']:
                    if self.update_smartlead_lead_id(email, smartlead_lead_id):
                        self.stats['smartlead_ids_written'] += 1
                    else:
                        self.stats['errors'] += 1

                if action == 'inserted':
                    self.stats['new_leads_inserted'] += 1
                    print(f"  [{idx}/{len(leads)}] ✨ NEW: {email} → {first_name} {last_name} [ID={smartlead_lead_id}]")
                elif action == 'updated':
                    self.stats['existing_leads_updated'] += 1

                    # Count what was updated
                    if changes.get('first_name_updated'):
                        self.stats['names_filled'] += 1
                    if changes.get('last_name_updated'):
                        self.stats['names_filled'] += 1
                    if changes.get('campaign_added'):
                        self.stats['campaigns_added'] += 1

                    updates = []
                    if changes.get('first_name_updated'):
                        updates.append('first_name')
                    if changes.get('last_name_updated'):
                        updates.append('last_name')
                    if changes.get('campaign_added'):
                        updates.append('campaign')
                    updates.append('smartlead_id')  # Always updated

                    update_str = ', '.join(updates)
                    print(f"  [{idx}/{len(leads)}] 🔄 MERGED: {email} ({update_str}) [ID={smartlead_lead_id}]")
                else:
                    print(f"  [{idx}/{len(leads)}] ❌ ERROR: {email}")

                self.changes_log.append({
                    'email': email,
                    'smartlead_lead_id': smartlead_lead_id,
                    'first_name': first_name,
                    'last_name': last_name,
                    'company': company,
                    'phone_number': phone_number,
                    'location': location,
                    'linkedin_url': linkedin_url,
                    'website': website,
                    'campaign_id': campaign_id,
                    'action': action,
                    'changes': changes
                })

    def save_report(self):
        """Save detailed report to CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/smartlead_sync_report_{timestamp}.csv"

        os.makedirs("data", exist_ok=True)

        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'email', 'smartlead_lead_id', 'first_name', 'last_name', 'company',
                'phone_number', 'location', 'linkedin_url', 'website',
                'campaign_id', 'action', 'changes'
            ])
            writer.writeheader()
            writer.writerows(self.changes_log)

        print(f"\n📄 Report saved: {filename}")

    def print_summary(self):
        """Print summary statistics"""
        print("\n" + "="*60)
        print("📊 SYNC SUMMARY")
        print("="*60)
        print(f"Total Smartlead leads processed: {self.stats['total_smartlead_leads']}")
        print(f"  ├─ New leads inserted: {self.stats['new_leads_inserted']}")
        print(f"  ├─ Existing leads updated: {self.stats['existing_leads_updated']}")
        print(f"  ├─ Names filled from Smartlead: {self.stats['names_filled']}")
        print(f"  ├─ Campaign trackings added: {self.stats['campaigns_added']}")
        print(f"  ├─ smartlead_lead_id written: {self.stats['smartlead_ids_written']} ✅")
        print(f"  └─ Errors: {self.stats['errors']}")
        print("="*60)

        if self.dry_run:
            print("\n⚠️  This was a DRY-RUN. No changes were made to Supabase.")
            print("   Run without --dry-run to execute the merge.")

    def run(self):
        """Main sync process"""
        mode = "DRY-RUN MODE" if self.dry_run else "LIVE MODE"
        print(f"\n🚀 Starting Smartlead → Supabase Sync ({mode})")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        for campaign_id in CAMPAIGN_IDS:
            self.process_campaign(campaign_id)

        self.save_report()
        self.print_summary()


def main():
    parser = argparse.ArgumentParser(
        description="Sync Smartlead leads to Supabase with smart merging"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without writing to Supabase'
    )

    args = parser.parse_args()

    try:
        syncer = SmartleadToSupabaseSync(dry_run=args.dry_run)
        syncer.run()

        if not args.dry_run:
            print("\n✅ Sync complete! Check Supabase to verify.")

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
