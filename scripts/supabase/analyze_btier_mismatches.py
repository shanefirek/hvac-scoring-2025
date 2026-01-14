#!/usr/bin/env python3
"""
Analyze B-tier campaign data for tier mismatches.
Quick analysis from MCP data retrieval.
"""

import json

# B-tier campaign data from MCP call
b_tier_data = """[B-tier JSON data will be inserted here]"""

# For now, let's manually count from the data we saw
print("\n" + "="*70)
print("B-TIER CAMPAIGN ANALYSIS (ID: 2677090)")
print("="*70)

# Manual analysis from the visible data:
correct_b = []
wrong_tier_c = []
missing_tier = []
other_tier = []

# Sample leads we can see from the output
leads = [
    {"email": "office@coastalphc.com", "tier": "B", "score": "15"},
    {"email": "info@bigalsservices.com", "tier": "B", "score": "15"},
    {"email": "support@walleys.com", "tier": None, "score": "770"},  # Missing tier
    {"email": "lincoln@balancedhvac.com", "tier": "B", "score": "15"},
    {"email": "paul.russo@glascohvac.com", "tier": "B", "score": "15"},
    {"email": "office@eastcoastairnh.com", "tier": "B", "score": "15"},
    {"email": "peter@calllloyd.com", "tier": None, "score": "898"},  # Missing tier
    {"email": "info@greenheatvt.com", "tier": None, "score": "447"},  # Missing tier
    {"email": "gary@wilsonph.com", "tier": None, "score": "108"},  # Missing tier
    {"email": "info@brocksheating.com", "tier": None, "score": "444"},  # Missing tier
    # ... continues
    {"email": "office@excelmechanical.com", "tier": "C", "score": "6"},  # WRONG
    {"email": "info@americanairinc.com", "tier": "C", "score": "9"},  # WRONG
    {"email": "service@northeasthc.com", "tier": "C", "score": "9"},  # WRONG
    {"email": "lundefined@meta.com", "tier": "C", "score": "5"},  # WRONG
]

print("\nFrom B-tier campaign (71 total leads):")
print("\nTier Distribution:")
print("  ✓ Correct (B-tier): ~28 leads")
print("  ❌ Wrong tier (C-tier in B campaign): ~28 leads (39%)")
print("  ⚠️  Missing tier field: ~15 leads (21%)")
print("\nSuspicious emails found:")
print("  - lundefined@meta.com (C-tier, score 5)")
print("  - support@fb.com (mentioned in summary)")
print("  - press@fb.com (mentioned in summary)")
print("  - himher@hotmail.no (mentioned in summary)")

print("\n" + "="*70)
print("NEXT STEPS")
print("="*70)
print("\n1. Need to get A-tier and C-tier campaign data (MCP calls failing)")
print("2. Complete full reconciliation across all 3 campaigns")
print("3. Create script to move ~28 C-tier leads from B-tier campaign")
print("4. Import orphan leads to Supabase")
print("5. Fix missing tier fields")

print("\n⚠️  MCP API Issue: A-tier and C-tier calls returning 400 errors")
print("   May need to use alternative method to retrieve campaign data")
print()
