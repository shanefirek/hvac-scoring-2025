#!/usr/bin/env python3
"""
Backfill Scoring for Unscored Leads in Supabase
================================================

This script:
1. Loads enrichment data from data/processed/*.csv files
2. Calculates scores using the original FastAPI scoring logic
3. Updates Supabase with missing score/tier/enrichment data

Usage:
    python scripts/supabase/backfill_unscored_leads.py --dry-run  # Preview changes
    python scripts/supabase/backfill_unscored_leads.py            # Execute updates
"""

import os
import sys
import csv
import argparse
import requests
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Franchise detection list (from scoring API)
FRANCHISES = [
    "ARS", "Rescue Rooter", "One Hour", "Benjamin Franklin",
    "Roto-Rooter", "Mr. Rooter", "Aire Serv", "Goettl"
]

# Service software keywords (from scoring API)
SERVICE_SOFTWARE = ["ServiceTitan", "Jobber", "Housecall Pro"]


class LeadScorer:
    """Calculate lead scores using original FastAPI logic"""

    @staticmethod
    def detect_franchise(company_name: str) -> bool:
        """Check if company name contains franchise keywords"""
        if not company_name:
            return False
        company_upper = company_name.upper()
        return any(franchise.upper() in company_upper for franchise in FRANCHISES)

    @staticmethod
    def calculate_review_score(review_count: int) -> int:
        """Calculate score based on review count (for non-franchises)"""
        if review_count >= 500:
            return 10
        elif review_count >= 100:
            return 7
        elif review_count >= 25:
            return 4
        elif review_count >= 10:
            return 2
        return 0

    @staticmethod
    def has_service_software(software: str) -> bool:
        """Check if lead uses recognized service software"""
        if not software:
            return False
        return any(sw.lower() in software.lower() for sw in SERVICE_SOFTWARE)

    @staticmethod
    def determine_messaging_strategy(tier: str, has_software: bool, is_franchise: bool) -> str:
        """Determine messaging strategy based on tier and signals"""
        if tier == "A":
            if is_franchise:
                return "Franchise: Multi-unit operations + franchise fee complexity"
            elif has_software:
                return "Software + Scale: Tech-forward operator with systems"
            else:
                return "Scale: High-volume operation with complex tax needs"
        elif tier == "B":
            if has_software:
                return "Tech Signal: Has systems, needs better accounting integration"
            else:
                return "Growth Signal: Established business, room for tax optimization"
        else:
            return "Pain Focus: Direct CPA pain points and tax surprises"

    @classmethod
    def score_lead(cls, company: str, reviews_count: int, service_software: str,
                   linkedin_url: str, domain: str) -> Dict:
        """
        Score a lead using the original API logic

        Returns dict with: score, tier, messaging_strategy, breakdown
        """
        score = 0
        breakdown = {
            "service_software": 0,
            "franchise_or_reviews": 0,
            "linkedin": 0,
            "domain": 0
        }

        # Service software (+15)
        has_software = cls.has_service_software(service_software or "")
        if has_software:
            score += 15
            breakdown["service_software"] = 15

        # Franchise vs reviews
        is_franchise = cls.detect_franchise(company or "")
        if is_franchise:
            score += 10
            breakdown["franchise_or_reviews"] = 10
        else:
            review_score = cls.calculate_review_score(reviews_count or 0)
            score += review_score
            breakdown["franchise_or_reviews"] = review_score

        # LinkedIn URL (+3)
        if linkedin_url and len(linkedin_url) > 0:
            score += 3
            breakdown["linkedin"] = 3

        # Domain (+2)
        if domain and len(domain) > 0:
            score += 2
            breakdown["domain"] = 2

        # Determine tier
        if score >= 20:
            tier = "A"
        elif score >= 10:
            tier = "B"
        else:
            tier = "C"

        # Messaging strategy
        messaging = cls.determine_messaging_strategy(tier, has_software, is_franchise)

        return {
            "score": score,
            "tier": tier,
            "messaging_strategy": messaging,
            "score_breakdown": breakdown,
            "is_franchise": is_franchise
        }


class SupabaseBackfiller:
    """Backfill unscored leads with enrichment data from processed CSVs"""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        self.stats = {
            "leads_processed": 0,
            "leads_updated": 0,
            "errors": 0
        }

    def fetch_unscored_leads(self) -> List[Dict]:
        """Fetch leads from Supabase that are missing scores"""
        url = f"{SUPABASE_URL}/rest/v1/leads?select=email,company,score,tier,in_smartlead"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        all_leads = response.json()
        unscored = [l for l in all_leads if l.get('score') is None or l.get('tier') is None]

        print(f"📊 Found {len(unscored)} leads missing score/tier in Supabase")
        print(f"   (Total leads in database: {len(all_leads)})")
        print()

        return unscored

    def load_processed_csvs(self) -> Dict[str, Dict]:
        """Load all leads from data/processed/*.csv files"""
        csv_files = [
            'data/processed/leads_a_tier.csv',
            'data/processed/leads_b_tier.csv',
            'data/processed/leads_c_tier.csv'
        ]

        leads_data = {}

        for csv_file in csv_files:
            if not os.path.exists(csv_file):
                print(f"⚠️  Warning: {csv_file} not found, skipping...")
                continue

            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    email = row.get('email', '').strip().lower()
                    if email:
                        leads_data[email] = {
                            'email': row.get('email', '').strip(),
                            'first_name': row.get('first_name', '').strip(),
                            'last_name': row.get('last_name', '').strip(),
                            'company': row.get('company', '').strip(),
                            'tier': row.get('tier', '').strip(),
                            'service_software': row.get('service_software', '').strip(),
                            'review_count': int(row.get('review_count', 0) or 0)
                        }

        print(f"📁 Loaded {len(leads_data)} leads from processed CSV files")
        print()

        return leads_data

    def parse_domain_from_email(self, email: str) -> str:
        """Extract domain from email address"""
        if '@' in email:
            return email.split('@')[1]
        return ""

    def update_lead_in_supabase(self, email: str, update_data: Dict) -> bool:
        """Update a single lead in Supabase"""
        url = f"{SUPABASE_URL}/rest/v1/leads?email=eq.{email}"

        try:
            response = requests.patch(url, headers=self.headers, json=update_data)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"   ❌ Error updating {email}: {e}")
            self.stats['errors'] += 1
            return False

    def backfill(self):
        """Main backfill process"""
        print(f"\n🚀 Starting Backfill Process {'(DRY-RUN)' if self.dry_run else '(LIVE)'}")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Step 1: Fetch unscored leads from Supabase
        unscored_leads = self.fetch_unscored_leads()

        if not unscored_leads:
            print("✅ No unscored leads found! All leads are already scored.")
            return

        # Step 2: Load enrichment data from CSVs
        csv_data = self.load_processed_csvs()

        # Step 3: Match and update
        print(f"🔄 Processing {len(unscored_leads)} unscored leads...\n")

        for idx, lead in enumerate(unscored_leads, 1):
            email = lead.get('email', '').strip().lower()

            # Look up enrichment data
            enrichment = csv_data.get(email)

            if not enrichment:
                print(f"  [{idx}/{len(unscored_leads)}] ⚠️  No CSV data for {email} - skipping")
                self.stats['errors'] += 1
                continue

            # Extract domain from email if not in CSV
            domain = self.parse_domain_from_email(email)

            # Calculate score
            score_result = LeadScorer.score_lead(
                company=enrichment['company'],
                reviews_count=enrichment['review_count'],
                service_software=enrichment['service_software'],
                linkedin_url="",  # Not in CSV, will be 0pts
                domain=domain
            )

            # Prepare update
            update_data = {
                "score": score_result['score'],
                "tier": score_result['tier'],
                "messaging_strategy": score_result['messaging_strategy'],
                "score_breakdown": score_result['score_breakdown'],
                "reviews_count": enrichment['review_count'],
                "service_software": enrichment['service_software'] if enrichment['service_software'] else None,
                "domain": domain,
                "company": enrichment['company'],
                "first_name": enrichment['first_name'] if enrichment['first_name'] else None,
                "last_name": enrichment['last_name'] if enrichment['last_name'] else None
            }

            # Display
            tier_emoji = "🥇" if score_result['tier'] == "A" else "🥈" if score_result['tier'] == "B" else "🥉"
            print(f"  [{idx}/{len(unscored_leads)}] {tier_emoji} {email}")
            print(f"       Score: {score_result['score']} | Tier: {score_result['tier']} | Company: {enrichment['company']}")
            print(f"       Reviews: {enrichment['review_count']} | Software: {enrichment['service_software'] or 'None'}")

            if self.dry_run:
                print(f"       🔍 DRY-RUN: Would update with {update_data}")
                self.stats['leads_processed'] += 1
            else:
                if self.update_lead_in_supabase(email, update_data):
                    print(f"       ✅ Updated successfully")
                    self.stats['leads_updated'] += 1
                else:
                    print(f"       ❌ Update failed")

            self.stats['leads_processed'] += 1
            print()

        # Summary
        self.print_summary()

    def print_summary(self):
        """Print summary statistics"""
        print("\n" + "="*60)
        print("📊 BACKFILL SUMMARY")
        print("="*60)
        print(f"Leads processed: {self.stats['leads_processed']}")
        print(f"  ├─ Successfully updated: {self.stats['leads_updated']}")
        print(f"  └─ Errors: {self.stats['errors']}")
        print("="*60)

        if self.dry_run:
            print("\n⚠️  This was a DRY-RUN. No changes were made to Supabase.")
            print("   Run without --dry-run to execute the updates.")


def main():
    parser = argparse.ArgumentParser(
        description="Backfill scoring for unscored leads in Supabase"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without updating Supabase'
    )

    args = parser.parse_args()

    try:
        backfiller = SupabaseBackfiller(dry_run=args.dry_run)
        backfiller.backfill()

        if not args.dry_run:
            print("\n✅ Backfill complete! Run data quality audit to verify.")

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
