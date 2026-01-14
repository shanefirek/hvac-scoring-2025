#!/usr/bin/env python3
"""
Canopy Client Suppression List Checker

Compares HVAC leads against Patrick's Canopy client list to identify
any existing clients that should be excluded from outreach.

Uses fuzzy matching since the Canopy list has no emails - only company names.
"""

import csv
import os
from pathlib import Path
from difflib import SequenceMatcher
import re

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
CANOPY_LIST = BASE_DIR / "canopy_client_list_appletree.csv"
LEADS_A = BASE_DIR / "data" / "processed" / "leads_a_tier.csv"
LEADS_B = BASE_DIR / "data" / "processed" / "leads_b_tier.csv"
LEADS_C = BASE_DIR / "data" / "processed" / "leads_c_tier.csv"

# Fuzzy match threshold (0.0 to 1.0)
# 0.7 = 70% similar - catches variations like "ABC Heating" vs "ABC Heating & Cooling"
MATCH_THRESHOLD = 0.65


def normalize_company_name(name: str) -> str:
    """Normalize company name for comparison."""
    if not name:
        return ""

    # Lowercase
    name = name.lower().strip()

    # Remove common suffixes
    suffixes = [
        "llc", "inc", "inc.", "corp", "corporation", "co", "co.",
        "company", "services", "service", "ltd", "limited"
    ]
    for suffix in suffixes:
        name = re.sub(rf'\b{suffix}\b\.?', '', name)

    # Remove punctuation except spaces
    name = re.sub(r'[^\w\s]', '', name)

    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name).strip()

    # Remove leading numbers (Canopy uses "1234 Company Name" format)
    name = re.sub(r'^\d+\s*', '', name)

    return name


def similarity_score(name1: str, name2: str) -> float:
    """Calculate similarity between two normalized names."""
    n1 = normalize_company_name(name1)
    n2 = normalize_company_name(name2)

    if not n1 or not n2:
        return 0.0

    # Exact match after normalization
    if n1 == n2:
        return 1.0

    # One contains the other
    if n1 in n2 or n2 in n1:
        return 0.9

    # Sequence matcher for fuzzy matching
    return SequenceMatcher(None, n1, n2).ratio()


def load_canopy_clients() -> list[dict]:
    """Load Canopy client list."""
    clients = []
    with open(CANOPY_LIST, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Use "Name" column for company name, or "Display Name" as fallback
            company = row.get('Name', '') or row.get('Display Name', '')
            if company:
                clients.append({
                    'company': company,
                    'normalized': normalize_company_name(company),
                    'city': row.get('City', ''),
                    'state': row.get('State', ''),
                    'owner': row.get('Client Owner', ''),
                    'contact': row.get('Contact Person', '')
                })
    return clients


def load_leads() -> list[dict]:
    """Load all HVAC leads from tier files."""
    leads = []

    for tier_file, tier in [(LEADS_A, 'A'), (LEADS_B, 'B'), (LEADS_C, 'C')]:
        if not tier_file.exists():
            print(f"Warning: {tier_file} not found")
            continue

        with open(tier_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('email'):
                    leads.append({
                        'email': row['email'],
                        'company': row.get('company', ''),
                        'normalized': normalize_company_name(row.get('company', '')),
                        'first_name': row.get('first_name', ''),
                        'last_name': row.get('last_name', ''),
                        'tier': tier
                    })
    return leads


def find_matches(leads: list[dict], clients: list[dict]) -> list[dict]:
    """Find leads that match Canopy clients."""
    matches = []

    for lead in leads:
        best_match = None
        best_score = 0.0

        for client in clients:
            score = similarity_score(lead['company'], client['company'])
            if score > best_score:
                best_score = score
                best_match = client

        if best_score >= MATCH_THRESHOLD:
            matches.append({
                'lead_email': lead['email'],
                'lead_company': lead['company'],
                'lead_tier': lead['tier'],
                'canopy_company': best_match['company'],
                'canopy_city': best_match['city'],
                'canopy_state': best_match['state'],
                'canopy_owner': best_match['owner'],
                'match_score': round(best_score, 2)
            })

    return matches


def main():
    print("=" * 70)
    print("CANOPY CLIENT SUPPRESSION CHECK")
    print("=" * 70)

    # Load data
    print("\n[1] Loading data...")
    clients = load_canopy_clients()
    leads = load_leads()

    print(f"    Canopy clients: {len(clients)}")
    print(f"    HVAC leads: {len(leads)}")

    # Find matches
    print(f"\n[2] Checking for matches (threshold: {MATCH_THRESHOLD * 100:.0f}% similarity)...")
    matches = find_matches(leads, clients)

    # Report results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    if not matches:
        print("\n✅ NO MATCHES FOUND")
        print("   None of your HVAC leads appear to be existing Canopy clients.")
        print("   Safe to proceed with outreach campaigns.")
    else:
        print(f"\n⚠️  FOUND {len(matches)} POTENTIAL MATCHES")
        print("   These leads may already be Canopy clients:\n")

        # Group by tier
        for tier in ['A', 'B', 'C']:
            tier_matches = [m for m in matches if m['lead_tier'] == tier]
            if tier_matches:
                print(f"\n   --- {tier}-Tier ({len(tier_matches)} matches) ---")
                for m in tier_matches:
                    print(f"\n   Lead: {m['lead_company']}")
                    print(f"   Email: {m['lead_email']}")
                    print(f"   Canopy: {m['canopy_company']}")
                    print(f"   Location: {m['canopy_city']}, {m['canopy_state']}")
                    print(f"   Match: {m['match_score'] * 100:.0f}%")

        # Save to file
        output_file = BASE_DIR / "data" / "suppression_matches.csv"
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=matches[0].keys())
            writer.writeheader()
            writer.writerows(matches)

        print(f"\n   📄 Full report saved to: {output_file}")

        # Generate suppression list
        suppression_file = BASE_DIR / "data" / "suppression_emails.txt"
        with open(suppression_file, 'w') as f:
            for m in matches:
                f.write(m['lead_email'] + '\n')

        print(f"   📄 Email suppression list: {suppression_file}")
        print("\n   ACTION: Review matches and add emails to Smartlead global block list")

    print("\n" + "=" * 70)

    # Summary stats
    print("\nSUMMARY:")
    print(f"  Total HVAC leads checked: {len(leads)}")
    print(f"  Total Canopy clients: {len(clients)}")
    print(f"  Potential overlaps: {len(matches)}")
    print(f"  Safe to send: {len(leads) - len(matches)}")

    return matches


if __name__ == "__main__":
    main()
