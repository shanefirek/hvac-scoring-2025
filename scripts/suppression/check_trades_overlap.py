#!/usr/bin/env python3
"""
Canopy Trades-Only Suppression Check

Filters Canopy client list to trades-related businesses only,
then does exact name matching against HVAC leads.
"""

import csv
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
CANOPY_LIST = BASE_DIR / "canopy_client_list_appletree.csv"
LEADS_A = BASE_DIR / "data" / "processed" / "leads_a_tier.csv"
LEADS_B = BASE_DIR / "data" / "processed" / "leads_b_tier.csv"
LEADS_C = BASE_DIR / "data" / "processed" / "leads_c_tier.csv"

# Trades-related keywords
TRADES_KEYWORDS = [
    'hvac', 'heating', 'cooling', 'mechanical', 'plumbing', 'plumber',
    'air conditioning', 'a/c', ' ac ', 'furnace', 'heat pump', 'boiler',
    'refrigeration', 'ductwork', 'ventilation', 'climate control',
    'thermal', 'temperature', 'comfort systems'
]


def normalize(name: str) -> str:
    """Normalize for exact matching."""
    if not name:
        return ""
    name = name.lower().strip()
    # Remove leading numbers (Canopy format: "1234 Company Name")
    name = re.sub(r'^\d+\s*', '', name)
    # Remove common suffixes
    name = re.sub(r'\b(llc|inc|corp|co|ltd|limited|services?|company)\b\.?', '', name)
    # Remove punctuation
    name = re.sub(r'[^\w\s]', '', name)
    # Collapse whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def is_trades_business(company: str) -> bool:
    """Check if company name contains trades keywords."""
    lower = company.lower()
    return any(kw in lower for kw in TRADES_KEYWORDS)


def load_canopy_trades() -> list[dict]:
    """Load only trades-related Canopy clients."""
    trades = []
    with open(CANOPY_LIST, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            company = row.get('Name', '') or row.get('Display Name', '')
            if company and is_trades_business(company):
                trades.append({
                    'company': company,
                    'normalized': normalize(company),
                    'city': row.get('City', ''),
                    'state': row.get('State', ''),
                    'owner': row.get('Client Owner', ''),
                    'contact': row.get('Contact Person', '')
                })
    return trades


def load_leads() -> list[dict]:
    """Load all HVAC leads."""
    leads = []
    for tier_file, tier in [(LEADS_A, 'A'), (LEADS_B, 'B'), (LEADS_C, 'C')]:
        if not tier_file.exists():
            continue
        with open(tier_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('email'):
                    leads.append({
                        'email': row['email'],
                        'company': row.get('company', ''),
                        'normalized': normalize(row.get('company', '')),
                        'tier': tier
                    })
    return leads


def main():
    print("=" * 60)
    print("CANOPY TRADES-ONLY SUPPRESSION CHECK")
    print("=" * 60)

    # Step 1: Filter Canopy to trades only
    print("\n[1] Filtering Canopy list to trades businesses...")
    trades = load_canopy_trades()
    print(f"    Found {len(trades)} trades-related Canopy clients")

    if trades:
        print("\n    Trades clients found:")
        for t in trades:
            loc = f"{t['city']}, {t['state']}" if t['city'] else "(no location)"
            print(f"    - {t['company']} | {loc}")

    # Step 2: Load leads
    print("\n[2] Loading HVAC leads...")
    leads = load_leads()
    print(f"    Loaded {len(leads)} leads")

    # Step 3: Exact match
    print("\n[3] Checking for exact matches...")
    matches = []

    # Create lookup sets
    canopy_normalized = {t['normalized']: t for t in trades}

    for lead in leads:
        if lead['normalized'] in canopy_normalized:
            canopy = canopy_normalized[lead['normalized']]
            matches.append({
                'lead_email': lead['email'],
                'lead_company': lead['company'],
                'lead_tier': lead['tier'],
                'canopy_company': canopy['company'],
                'canopy_location': f"{canopy['city']}, {canopy['state']}"
            })

    # Results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    if not matches:
        print("\n✅ NO EXACT MATCHES FOUND")
        print("   None of your HVAC leads are existing Canopy clients.")
        print("   Safe to proceed - no suppression needed.")
    else:
        print(f"\n🚨 FOUND {len(matches)} EXACT MATCHES - SUPPRESS THESE:")
        for m in matches:
            print(f"\n   Email: {m['lead_email']}")
            print(f"   Lead: {m['lead_company']} (Tier {m['lead_tier']})")
            print(f"   Canopy: {m['canopy_company']}")
            print(f"   Location: {m['canopy_location']}")

        # Save suppression list
        suppress_file = BASE_DIR / "data" / "final_suppression_emails.txt"
        with open(suppress_file, 'w') as f:
            for m in matches:
                f.write(m['lead_email'] + '\n')
        print(f"\n   📄 Suppression list saved: {suppress_file}")

    print("\n" + "=" * 60)
    print(f"Summary: {len(trades)} trades clients in Canopy, {len(matches)} overlap with leads")
    print("=" * 60)


if __name__ == "__main__":
    main()
