# Manual Fixes Required - Smartlead Campaigns

**Generated:** November 14, 2025
**Campaigns:** 2677089 (A-Tier), 2677090 (B-Tier), 2677091 (C-Tier)

---

## ✅ What Was Fixed Automatically (Via API)

### Email Account Assignments
- ✅ **All 3 campaigns have correct email accounts assigned**
  - team@appletree-taxes.com (ID: 12664159)
  - team@appletree-advisors.com (ID: 12663958)
  - team@appletree-tax.com (ID: 12657708)
- **No action needed** - The "unknown" distribution in audit was a display issue, not an actual problem

---

## ❌ What Needs Manual Fixing (API Limitations)

### 1. Enable Open Tracking (All 3 Campaigns)

**Issue:** API endpoint `/campaigns/{id}/settings` rejects `track_settings: ["TRACK_OPENS", "TRACK_CLICKS"]`
**Error:** "Invalid track_settings value - TRACK_OPENS"

**Manual Fix in Smartlead UI:**
1. Go to each campaign (2677089, 2677090, 2677091)
2. Navigate to: Campaign Settings → Tracking
3. Enable:
   - ✅ Open tracking
   - ✅ Click tracking (if custom tracking domain is configured)
4. Save changes

**Impact:** Without open tracking, you won't see who opened emails (only replies)

---

### 2. Add Missing Calendly Links (3 Sequences)

**Issue:** API endpoint `PUT /campaigns/{id}/sequences/{seq_id}` does not exist
**Error:** "Cannot PUT /api/v1/campaigns/2677089/sequences/5154689"

**Sequences needing Calendly link:**

#### A-Tier Sequence 3 (Day 9 Email)
- **Campaign ID:** 2677089
- **Sequence ID:** 5154689
- **Subject:** "Your tech stack vs. your CPA"
- **Fix:** Add Calendly link before signature:
  ```
  Open to a quick call?

  https://calendly.com/appletreepd/30min

  Shane
  Appletree Business Services
  ```

#### B-Tier Sequence 1 (Day 0 Email)
- **Campaign ID:** 2677090
- **Sequence ID:** 5154692
- **Subject:** "Saw {{company}} on Google"
- **Fix:** Add Calendly link after "Worth a conversation?":
  ```
  Worth a conversation?

  https://calendly.com/appletreepd/30min

  Shane
  Appletree Business Services
  ```

#### C-Tier Sequence 1 (Day 0 Email)
- **Campaign ID:** 2677091
- **Sequence ID:** 5154697
- **Subject:** "Question about your CPA"
- **Fix:** Add Calendly link after "Worth 15 minutes to see if we're a fit?":
  ```
  Worth 15 minutes to see if we're a fit?

  https://calendly.com/appletreepd/30min

  Shane
  Appletree Business Services
  ```
- **Also fix spam word:** Replace "stress-free" with "low-stress"

**Manual Fix in Smartlead UI:**
1. Go to each campaign
2. Navigate to: Email Sequences
3. Click "Edit" on the specific sequence
4. Add Calendly link as shown above
5. For C-Tier Seq 1: Also replace "stress-free" → "low-stress"
6. Save changes

**Impact:** Without Calendly links, prospects can't book meetings directly (must reply to email)

---

### 3. Investigate Missing B-Tier Lead

**Issue:** B-Tier campaign has 28 leads, expected 29 (1 lead missing)

**Data:**
- CSV file: `smartlead_imports/leads_b_tier.csv` has 30 lines (29 leads + header)
- Smartlead campaign: Only 28 leads uploaded
- **1 lead was rejected during import**

**Possible Reasons:**
1. Email in global blocklist
2. Email invalid/bounced previously
3. Duplicate email in another campaign
4. Email format validation failure

**Manual Fix in Smartlead UI:**
1. Go to Campaign 2677090 (B-Tier)
2. Navigate to: Leads → View All
3. Export lead list as CSV
4. Compare against `smartlead_imports/leads_b_tier.csv` to identify missing lead
5. Check Smartlead: Blocklist → Global Blocklist for the missing email
6. If found in blocklist, determine if it should be removed
7. If not in blocklist, check lead import logs for rejection reason
8. Re-import the missing lead manually if appropriate

**Impact:** Low - Only 1 of 29 leads missing (3% reduction in B-Tier volume)

---

## 📋 Alternative: Sequences Update via API (Advanced)

**If you want to update sequences programmatically:**

The Smartlead API doesn't support `PUT /campaigns/{id}/sequences/{seq_id}`.
Instead, you must:

1. **Delete all sequences:**
   ```bash
   DELETE /campaigns/{id}/sequences
   ```

2. **Re-add all sequences** (including updated ones):
   ```bash
   POST /campaigns/{id}/sequences
   Body: {
     "sequences": [
       {
         "seq_number": 1,
         "subject": "...",
         "email_body": "...",
         "seq_delay_details": {"delay_in_days": 0}
       },
       // ... all other sequences
     ]
   }
   ```

**Risk:** This approach requires careful scripting to avoid data loss.
**Recommendation:** Use UI for one-time fixes, script for batch updates in future.

---

## 🔐 From instructions_before_launch.md (Still Needs Manual Verification)

These items cannot be addressed via API and require UI access:

### Account-Level Settings (All 3 Email Accounts)
- ⚠️ **Auto-reply detection:** Settings → Email Accounts → [Each Account] → Enable auto-reply detection
- ⚠️ **Reply forwarding:** Settings → Email Accounts → [Each Account] → Configure forwarding email
- ⚠️ **SPF/DKIM/DMARC health:** Settings → Email Accounts → Verify all GREEN
- ⚠️ **Warmup status:** Settings → Email Accounts → Check reputation scores

### Testing
- ⚠️ **Send test emails:** Send from each campaign to personal email
- ⚠️ **Test unsubscribe links:** Click unsubscribe in test emails
- ⚠️ **Test auto-reply detection:** Reply with out-of-office message
- ⚠️ **Test reply forwarding:** Verify replies arrive in configured inbox

### Pre-Launch
- ⚠️ **Campaign status:** Change from DRAFT → SCHEDULED or ACTIVE
- ⚠️ **Scheduled start time:** Set launch date/time (Monday 11/18, 8:30 AM ET)

---

## Summary

### ✅ Fixed Automatically
- Email account assignments verified (3 accounts on all campaigns)

### ❌ Needs Manual UI Fixes
- Enable open tracking (3 campaigns, ~2 min total)
- Add Calendly links to 3 sequences (~5 min total)
- Fix "stress-free" spam word in C-Tier Seq 1 (~1 min)
- Investigate missing B-Tier lead (~10 min)

### ⚠️ Needs Manual Verification (From Launch Instructions)
- Account health, auto-reply, forwarding, testing (~30 min total)

**Total Manual Work: ~50 minutes**

---

## Next Steps

1. **Complete manual fixes above** (sequences, tracking)
2. **Run audit again** to verify:
   ```bash
   python3 audit_smartlead_campaigns.py
   ```
3. **Complete launch checklist** from `instructions_before_launch.md`
4. **Launch Monday 11/18** after all verifications pass

---

**Last Updated:** November 14, 2025
**Maintained by:** Claude + Shane (Appletree HVAC project)
