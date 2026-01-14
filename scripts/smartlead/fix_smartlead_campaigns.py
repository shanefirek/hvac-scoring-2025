#!/usr/bin/env python3
"""
Fix Smartlead Campaign Issues

Programmatically fixes issues found in audit:
1. Enable open tracking (all 3 campaigns)
2. Add missing Calendly links (3 sequences)
3. Fix spam word "free" in C-Tier Sequence 1
4. Verify email account assignments

Usage:
    python fix_smartlead_campaigns.py [--dry-run]
"""

import requests
import json
import sys
import argparse

# Configuration
API_KEY = "38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"
BASE_URL = "https://server.smartlead.ai/api/v1"
CALENDLY_LINK = "https://calendly.com/appletreepd/30min"

# Campaign IDs
CAMPAIGNS = {
    "A": 2677089,
    "B": 2677090,
    "C": 2677091
}

# Email account IDs (from build_smartlead_campaigns.py)
EMAIL_ACCOUNT_IDS = [12664159, 12663958, 12657708]

def api_call(method, endpoint, data=None):
    """Make API call to Smartlead"""
    url = f"{BASE_URL}{endpoint}"
    params = {"api_key": API_KEY}
    headers = {"Content-Type": "application/json"}

    try:
        if method == "GET":
            response = requests.get(url, params=params, headers=headers)
        elif method == "POST":
            response = requests.post(url, params=params, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, params=params, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, params=params, json=data, headers=headers)

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"      ❌ API Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"         {json.dumps(error_detail, indent=2)}")
            except:
                print(f"         {e.response.text[:200]}")
        return None

def print_section(text):
    """Print section header"""
    print(f"\n{'='*70}")
    print(f"{text}")
    print(f"{'='*70}\n")

# ============================================================================
# FIX 1: ENABLE OPEN TRACKING
# ============================================================================

def enable_open_tracking(campaign_id, campaign_name, dry_run=False):
    """Enable open and click tracking for a campaign"""
    print(f"📊 {campaign_name} (ID: {campaign_id})")

    if dry_run:
        print(f"   [DRY RUN] Would enable open & click tracking")
        return True

    # Correct API format: Empty array = enable tracking
    # track_settings uses NEGATIVE values (DONT_TRACK_*), so empty = track everything
    data = {
        "track_settings": [],  # Empty array enables all tracking
        "stop_lead_settings": "REPLY_TO_AN_EMAIL",
        "follow_up_percentage": 100,
        "enable_ai_esp_matching": True,
        "send_as_plain_text": False
    }

    result = api_call("POST", f"/campaigns/{campaign_id}/settings", data)

    if result and result.get("ok"):
        print(f"   ✅ Open & click tracking enabled")
        return True
    else:
        print(f"   ❌ Failed to enable tracking")
        return False

# ============================================================================
# FIX 2: UPDATE SEQUENCES (ADD CALENDLY + FIX SPAM)
# ============================================================================

def get_sequences(campaign_id):
    """Get all sequences for a campaign"""
    result = api_call("GET", f"/campaigns/{campaign_id}/sequences")
    if result and isinstance(result, list):
        return result
    return []

def update_sequence(campaign_id, sequence_obj, updated_body, dry_run=False):
    """Update a sequence using correct API format with seq_variants"""
    if dry_run:
        return True

    # GET returns flat structure (subject/email_body at top level)
    # But POST expects nested seq_variants structure
    # Build the nested structure from flat GET response

    original_subject = sequence_obj.get("subject", "")
    seq_id = sequence_obj.get("id")

    # Extract delay - GET returns camelCase, POST wants snake_case
    delay_details = sequence_obj.get("seq_delay_details", {})
    delay_days = delay_details.get("delayInDays", delay_details.get("delay_in_days", 0))

    # Build update payload with correct nested structure
    data = {
        "sequences": [
            {
                "id": seq_id,
                "seq_number": sequence_obj.get("seq_number"),
                "seq_delay_details": {
                    "delay_in_days": delay_days  # POST requires snake_case
                },
                "seq_variants": [
                    {
                        # Don't include variant ID for simplicity (API should handle it)
                        "subject": original_subject,  # Keep original subject
                        "email_body": updated_body,    # Update body
                        "variant_label": "A"
                    }
                ]
            }
        ]
    }

    # Use POST to same endpoint (with sequence ID = update, without = create)
    result = api_call("POST", f"/campaigns/{campaign_id}/sequences", data)

    if result and result.get("ok"):
        return True
    return False

def fix_sequences(dry_run=False):
    """Fix missing Calendly links and spam words"""
    print_section("FIX 2: UPDATE EMAIL SEQUENCES")

    fixes = [
        {
            "campaign": "A",
            "campaign_id": CAMPAIGNS["A"],
            "seq_number": 3,
            "issue": "Missing Calendly link",
            "action": "Add Calendly link to end of email"
        },
        {
            "campaign": "B",
            "campaign_id": CAMPAIGNS["B"],
            "seq_number": 1,
            "issue": "Missing Calendly link",
            "action": "Add Calendly link to end of email"
        },
        {
            "campaign": "C",
            "campaign_id": CAMPAIGNS["C"],
            "seq_number": 1,
            "issue": "Missing Calendly link + spam word 'free'",
            "action": "Add Calendly link, replace 'stress-free' with 'low-stress'"
        }
    ]

    for fix in fixes:
        print(f"\n📝 {fix['campaign']}-Tier Sequence {fix['seq_number']}")
        print(f"   Issue: {fix['issue']}")
        print(f"   Action: {fix['action']}")

        # Get current sequences
        sequences = get_sequences(fix['campaign_id'])
        if not sequences:
            print(f"   ❌ Could not retrieve sequences")
            continue

        # Find the sequence to update
        target_seq = None
        for seq in sequences:
            if seq.get("seq_number") == fix['seq_number']:
                target_seq = seq
                break

        if not target_seq:
            print(f"   ❌ Sequence {fix['seq_number']} not found")
            continue

        # GET returns flat structure with subject/email_body at top level
        body = target_seq.get("email_body", "")
        seq_id = target_seq.get("id")

        if not body:
            print(f"   ❌ No email body found in sequence")
            continue

        # Apply fixes
        updated_body = body

        # Fix C-Tier spam word
        if fix['campaign'] == "C" and fix['seq_number'] == 1:
            updated_body = updated_body.replace("stress-free", "low-stress")
            updated_body = updated_body.replace("weekends stress-free", "weekends low-stress")

        # Add Calendly link if missing
        if CALENDLY_LINK not in updated_body:
            # Try to add before signature (handle both HTML and plain text)
            if "Shane<br>Appletree Business Services" in updated_body:
                # HTML format
                updated_body = updated_body.replace(
                    "Shane<br>Appletree Business Services",
                    f"{CALENDLY_LINK}<div><br></div><div><br></div>Shane<br>Appletree Business Services"
                )
            elif "Shane\nAppletree Business Services" in updated_body:
                # Plain text format
                updated_body = updated_body.replace(
                    "Shane\nAppletree Business Services",
                    f"{CALENDLY_LINK}\n\nShane\nAppletree Business Services"
                )
            else:
                # Fallback: add at end
                updated_body += f"<div><br></div><div><br></div>{CALENDLY_LINK}"

        if dry_run:
            print(f"   [DRY RUN] Would update sequence {seq_id}")
            print(f"      Old length: {len(body)} chars")
            print(f"      New length: {len(updated_body)} chars")
            print(f"      Has Calendly: {CALENDLY_LINK in updated_body}")
        else:
            success = update_sequence(fix['campaign_id'], target_seq, updated_body, dry_run)
            if success:
                print(f"   ✅ Sequence updated successfully")
            else:
                print(f"   ❌ Failed to update sequence")

# ============================================================================
# FIX 3: VERIFY EMAIL ACCOUNT ASSIGNMENTS
# ============================================================================

def verify_email_accounts(dry_run=False):
    """Verify email accounts are assigned to campaigns"""
    print_section("FIX 3: VERIFY EMAIL ACCOUNT ASSIGNMENTS")

    for tier, campaign_id in CAMPAIGNS.items():
        print(f"\n📧 {tier}-Tier Campaign (ID: {campaign_id})")

        # Get current email accounts
        result = api_call("GET", f"/campaigns/{campaign_id}/email-accounts")

        if result and isinstance(result, list):
            current_accounts = result
            account_ids = [acc.get("id") for acc in current_accounts]

            print(f"   Current accounts: {len(current_accounts)}")
            for acc in current_accounts:
                print(f"      - {acc.get('from_email', 'unknown')} (ID: {acc.get('id')})")

            # Check if all expected accounts are assigned
            missing = [acc_id for acc_id in EMAIL_ACCOUNT_IDS if acc_id not in account_ids]

            if missing:
                print(f"   ⚠️  Missing {len(missing)} email accounts")

                if dry_run:
                    print(f"   [DRY RUN] Would add email accounts: {missing}")
                else:
                    # Add missing accounts
                    data = {"email_account_ids": missing}
                    add_result = api_call("POST", f"/campaigns/{campaign_id}/email-accounts", data)

                    if add_result and add_result.get("ok"):
                        print(f"   ✅ Added {len(missing)} email accounts")
                    else:
                        print(f"   ❌ Failed to add email accounts")
            else:
                print(f"   ✅ All email accounts assigned")
        else:
            print(f"   ❌ Could not retrieve email accounts")

# ============================================================================
# FIX 4: INVESTIGATE MISSING B-TIER LEAD
# ============================================================================

def investigate_missing_lead(dry_run=False):
    """Check why B-Tier has 28 leads instead of 29"""
    print_section("FIX 4: INVESTIGATE MISSING B-TIER LEAD")

    campaign_id = CAMPAIGNS["B"]

    # Get current leads
    result = api_call("GET", f"/campaigns/{campaign_id}/leads?limit=100&offset=0")

    if result:
        total = int(result.get("total_leads", 0))
        leads = result.get("data", [])

        print(f"   Total leads in campaign: {total}")
        print(f"   Expected: 29")
        print(f"   Difference: {29 - total}")

        if total == 29:
            print(f"   ✅ Lead count is now correct!")
        elif total == 28:
            print(f"   ⚠️  Still missing 1 lead")
            print(f"   💡 Check data/processed/leads_b_tier.csv for rejected lead")
            print(f"   Possible reasons:")
            print(f"      - Email in global blocklist")
            print(f"      - Email invalid/bounced")
            print(f"      - Duplicate email in another campaign")
        else:
            print(f"   ⚠️  Unexpected lead count: {total}")
    else:
        print(f"   ❌ Could not retrieve leads")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run all fixes"""
    parser = argparse.ArgumentParser(description='Fix Smartlead campaign issues')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying them')
    args = parser.parse_args()

    dry_run = args.dry_run

    print("\n" + "="*70)
    print("SMARTLEAD CAMPAIGN FIX SCRIPT")
    print("="*70)

    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made\n")
    else:
        print("\n⚠️  LIVE MODE - Changes will be applied\n")

    # Fix 1: Enable open tracking
    print_section("FIX 1: ENABLE OPEN TRACKING")
    for tier, campaign_id in CAMPAIGNS.items():
        enable_open_tracking(campaign_id, f"{tier}-Tier", dry_run)

    # Fix 2: Update sequences
    fix_sequences(dry_run)

    # Fix 3: Verify email accounts
    verify_email_accounts(dry_run)

    # Fix 4: Investigate missing lead
    investigate_missing_lead(dry_run)

    # Summary
    print_section("FIXES COMPLETE")

    if dry_run:
        print("This was a DRY RUN. Run without --dry-run to apply changes.")
    else:
        print("All fixes applied! Re-run audit to verify:")
        print("   python3 audit_smartlead_campaigns.py")

    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
