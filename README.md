# Appletree HVAC GTM Flywheel

**Automated lead management system:** Clay → n8n → Supabase → Smartlead

Complete lead scoring, enrichment, and campaign automation system for Appletree Business (bookkeeping/tax services targeting HVAC contractors).

**Client:** Patrick at appletreebusiness.com
**Timeline:** 3 months to deliver leads + outbound campaigns
**Current Status:** 🚀 LIVE - 150 leads sending, 60% open rates, 90%+ inbox delivery

---

## 🔄 Flywheel Architecture (NEW - Nov 19, 2025)

```
Clay (enrichment)
  ↓ webhook trigger
n8n (orchestration)
  ↓ score via Railway API
Supabase (data warehouse)
  ↓ campaign sync
Smartlead (outbound)
  ↓ engagement webhooks
n8n → Supabase (analytics)
```

**Key Benefits:**
- ✅ **No manual CSV exports** - Clay triggers n8n automatically
- ✅ **Single source of truth** - All data in Supabase
- ✅ **Real-time analytics** - Smartlead events → Supabase
- ✅ **Version-controlled sequences** - Email copy in database

**Quick Start:**
1. Supabase schema already deployed (3 migrations applied)
2. Import `n8n/hvac_gtm_flywheel.json` to your n8n instance
3. Configure Clay webhook (see `docs/CLAY_WEBHOOK_SETUP.md`)
4. Done! Leads auto-sync to Supabase, campaigns managed via n8n

**Setup Guides:**
- **Full Flywheel:** [docs/FLYWHEEL_SETUP.md](docs/FLYWHEEL_SETUP.md)
- **Clay Webhook:** [docs/CLAY_WEBHOOK_SETUP.md](docs/CLAY_WEBHOOK_SETUP.md)
- **Quick Start (30 min):** [docs/FLYWHEEL_QUICKSTART.md](docs/FLYWHEEL_QUICKSTART.md)

**Technical Notes:**
- Workflow built using n8n MCP tools (not manual JSON)
- All Supabase operations use REST API (`/rest/v1/rpc/` for functions)
- Clay handles all scoring (no Railway API in workflow)

---

## 📁 Repository Structure

```
appletree-data-pipeline/
├── README.md                    # This file
├── claude.md                    # Project context & instructions (for AI agents)
├── requirements.txt             # Python dependencies
│
├── scripts/                     # All automation scripts
│   ├── scoring/
│   │   └── main.py             # FastAPI lead scoring service (deployed to Railway)
│   ├── clay/
│   │   └── clean_clay_export.py # Transform Clay CSV → tier-specific CSVs
│   ├── smartlead/
│   │   ├── build_smartlead_campaigns.py    # Create 3 campaigns via API
│   │   ├── audit_smartlead_campaigns.py    # Audit campaign configuration
│   │   ├── fix_smartlead_campaigns.py      # Auto-fix campaign issues
│   │   ├── restore_sequences.py            # Restore all sequences w/ fixes
│   │   └── update_company_names.py         # Bulk update lead company names
│   └── legacy/
│       ├── build_campaigns.py   # [DEPRECATED] Old campaign builder
│       └── create_campaigns.py  # [DEPRECATED] Old campaign creator
│
├── data/                        # All data files
│   ├── raw/                     # Original exports from Clay/scrapers
│   │   ├── HVAC Nov 2025 Appletree - HVAC_draft_appletree_112025.csv
│   │   └── Clay_HVAC_export_11132025.csv
│   └── processed/               # Clean CSVs ready for Smartlead import
│       ├── leads_a_tier.csv    # 16 A-Tier leads (20-30 points)
│       ├── leads_b_tier.csv    # 28 B-Tier leads (10-19 points)
│       └── leads_c_tier.csv    # 106 C-Tier leads (0-9 points)
│
├── sequences/                   # Email sequence copy
│   └── sequences_11_2025_appletree.txt  # All 9 email sequences (A/B/C tiers)
│
├── docs/                        # Documentation
│   ├── FLYWHEEL_SETUP.md       # 🆕 GTM flywheel setup guide (Nov 19)
│   ├── CLAY_WEBHOOK_SETUP.md   # 🆕 Clay webhook configuration (Nov 19)
│   ├── FLYWHEEL_QUICKSTART.md  # 30-minute quick start guide
│   ├── SUPABASE_SCHEMA.md      # Database schema reference
│   ├── SMARTLEAD_SETUP.md      # Complete campaign setup guide (Nov 13)
│   ├── LAUNCH_GUIDE.md         # Quick launch instructions
│   ├── FIXES_COMPLETED.md      # ✅ What was fixed via API automation
│   ├── MANUAL_FIXES_NEEDED.md  # ⚠️ What requires manual UI work
│   └── instructions_before_launch.md  # Pre-launch checklist
│
├── n8n/                         # 🆕 n8n workflow automation
│   └── hvac_gtm_flywheel.json  # Single workflow: Clay → Supabase → Smartlead
│
└── archive/                     # Old/reference files
    ├── context_from_claude_desktop.md
    └── test.json
```

---

## 🚀 Quick Start

### 1. Score Leads (FastAPI)

```bash
# Install dependencies
pip install -r requirements.txt

# Run scoring API locally
python scripts/scoring/main.py

# Test it
curl http://localhost:8000/score-lead \
  -H "Content-Type: application/json" \
  -d '{"company": "Test HVAC", "reviews_count": 100, "service_software": "ServiceTitan"}'
```

**Production:** Deployed at `https://hvac-scoring-2025-production.up.railway.app`

### 2. Tech Stack Detection (FastAPI)

```bash
# Test tech stack detection API
curl -X POST https://fastapi-production-85b6.up.railway.app/classify \
  -H "Content-Type: application/json" \
  -d '{"domain": "isaacheating.com"}'
```

**Production:** `https://fastapi-production-85b6.up.railway.app/classify`

**Response:**
```json
{
  "domain": "isaacheating.com",
  "uses_servicetitan": true,
  "uses_housecallpro": false,
  "uses_jobber": false,
  "confidence": 0.95,
  "matches": {"servicetitan": "servicetitan.com"}
}
```

**Performance:**
- ✅ **Fast**: ~0.4-0.5 seconds per domain
- ✅ **Accurate**: Regex-based pattern matching
- ✅ **No AI calls**: Pure pattern detection
- ✅ **All 3 platforms**: ServiceTitan, Jobber, Housecall Pro in one call

### 3. Process Clay Export

```bash
# Clean and tier leads from Clay export
python scripts/clay/clean_clay_export.py

# Output: 3 CSV files in data/processed/ (A/B/C tiers)
```

### 3. Build Smartlead Campaigns

```bash
# Create all 3 campaigns via Smartlead API
python scripts/smartlead/build_smartlead_campaigns.py

# Output: 3 campaign IDs (2677089, 2677090, 2677091)
```

### 4. Audit Campaigns

```bash
# Check campaign configuration
python scripts/smartlead/audit_smartlead_campaigns.py

# Output: Color-coded report (✅ ❌ ⚠️)
```

---

## 📊 Lead Scoring System

**Total possible: 30 points**

| Signal | Points |
|--------|--------|
| **Service Software** (ServiceTitan, Jobber, Housecall Pro) | +15 |
| **Franchise** (ARS, Rescue Rooter, One Hour, etc.) | +10 |
| **Reviews** (500+) | +10 |
| **Reviews** (100-499) | +7 |
| **Reviews** (25-99) | +4 |
| **Reviews** (10-24) | +2 |
| **LinkedIn URL** | +3 |
| **Domain** | +2 |

### Tier Classification

- **A-Tier (20-30 points):** High sophistication - Software users, franchises, high-volume
- **B-Tier (10-19 points):** Medium sophistication - Good reviews OR tech signals
- **C-Tier (0-9 points):** Lower sophistication - Smaller operations, pain-focused messaging

---

## 📧 Campaign Structure

### A-Tier: Software & Scale (16 leads)
- **4 emails** over 14 days (Days 0, 4, 9, 14)
- **Max:** 10 sends/day
- **Messaging:** Tech-forward, systems-focused

### B-Tier: Growth Signal (28 leads)
- **3 emails** over 12 days (Days 0, 5, 12)
- **Max:** 8 sends/day
- **Messaging:** Growth phase, optimization opportunities

### C-Tier: Pain Focus (106 leads)
- **2 emails** over 10 days (Days 0, 10)
- **Max:** 10 sends/day
- **Messaging:** CPA pain points, direct value prop

**Total:** 150 leads, 363 sends over 14 days (28 sends/day average)

---

## 🛠️ Key Scripts

### Scoring

**`scripts/scoring/main.py`**
- FastAPI service for lead scoring
- Deployed to Railway
- Used by Clay HTTP API column

### Clay Processing

**`scripts/clay/clean_clay_export.py`**
- Transforms Clay CSV into tier-specific CSVs
- Validates emails, extracts names
- Outputs to `data/processed/`

### Smartlead Automation

**`scripts/smartlead/build_smartlead_campaigns.py`**
- Creates 3 campaigns via Smartlead API
- Imports leads, adds sequences, configures settings
- **Usage:** Run once per batch

**`scripts/smartlead/audit_smartlead_campaigns.py`**
- Comprehensive campaign health check
- Validates schedule, tracking, sequences, leads
- **Usage:** Run before launch and periodically

**`scripts/smartlead/fix_smartlead_campaigns.py`**
- Automated fixes for common issues
- Enables tracking, updates sequences
- **Usage:** `--dry-run` to preview, then live mode

**`scripts/smartlead/restore_sequences.py`**
- Restores all 9 sequences with Calendly links
- Fixes spam words ("stress-free" → "low-stress")
- **Usage:** Emergency restore after accidental deletions

---

## 📖 Documentation

### Getting Started
- **`README.md`** (this file) - Repo overview and quick start
- **`claude.md`** - Complete project context (for AI agents)
- **`docs/FLYWHEEL_SETUP.md`** - 🆕 **GTM Flywheel automation setup** (Nov 19)

### Campaign Setup
- **`docs/SMARTLEAD_SETUP.md`** - Full campaign setup guide (authoritative, Nov 13)
- **`docs/LAUNCH_GUIDE.md`** - Quick launch checklist

### Current State
- **`docs/FIXES_COMPLETED.md`** - ✅ What was fixed via automation (Nov 14)
- **`docs/MANUAL_FIXES_NEEDED.md`** - ⚠️ Remaining manual tasks (~35 min)
- **`docs/instructions_before_launch.md`** - Pre-launch verification checklist

### Automation
- **`n8n/hvac_gtm_flywheel.json`** - 🆕 n8n workflow for complete automation
- **Supabase migrations** - Applied via MCP tools (schema, views, functions, seeds)

---

## 🎯 Launch Checklist

### ✅ Completed (Automated via API)
- [x] 150 leads scored and tiered
- [x] 3 campaigns created (IDs: 2677089, 2677090, 2677091)
- [x] All 9 sequences loaded with Calendly links
- [x] Personalization tokens working
- [x] Open & click tracking enabled
- [x] Stop on reply configured
- [x] Send schedule set (Mon-Fri, 9-5pm ET)
- [x] Daily send limits configured
- [x] Email accounts assigned (3 accounts rotating)
- [x] Spam words removed

### ⏳ Manual Tasks Remaining (~35 min)
- [ ] Verify SPF/DKIM/DMARC status (Settings → Email Accounts)
- [ ] Enable auto-reply detection (all 3 accounts)
- [ ] Configure reply forwarding
- [ ] Send test emails from each campaign
- [ ] Test unsubscribe links
- [ ] Change campaign status DRAFT → ACTIVE
- [ ] Set launch time (Monday 11/18, 8:30 AM ET)

**See `docs/MANUAL_FIXES_NEEDED.md` for detailed instructions**

---

## 🔧 Troubleshooting

### Scripts fail with "No such file" errors
- **Solution:** Scripts expect to run from repo root: `python scripts/smartlead/audit_smartlead_campaigns.py`

### Smartlead API returns 400 errors
- **Check:** API docs at https://helpcenter.smartlead.ai/en/articles/125-full-api-documentation
- **Note:** MCP tools have known issues, use direct API calls instead

### Clay export has wrong column names
- **Update:** `scripts/clay/clean_clay_export.py` input column mappings (lines 30-50)

### Campaign sequences missing personalization
- **Run:** `python scripts/smartlead/audit_smartlead_campaigns.py` to identify issues
- **Fix:** Check that sequences have `{{first_name}}`, `{{company}}`, etc.

---

## 📈 Next Steps

### Week 1 (Current - Nov 18 Launch)
- [x] Score 160 leads
- [x] Build campaigns
- [ ] Complete manual verifications
- [ ] Launch Monday 11/18

### Week 2-3 (Tech-First Pivot)
- [ ] Build ServiceTitan/Jobber/HCP user targeting
- [ ] Scrape 500-1k leads with FSM software
- [ ] Expand to CST states (TX, CO, AZ)

### Week 4+ (Scale & Optimize)
- [ ] Analyze response rates by tier
- [ ] A/B test messaging strategies
- [ ] Adjust scoring weights based on conversions
- [ ] Scale to 10k+ lead database

---

## 🔑 Key Learnings

### What Worked
1. **API-first approach** - 100% of fixable issues resolved via automation
2. **Audit → Fix → Verify pipeline** - Systematic, traceable
3. **Reading API docs carefully** - Saved hours of trial/error
4. **Dry-run mode** - Prevented costly mistakes

### What Didn't Work
1. **MCP tools** - Still buggy, direct API more reliable
2. **Individual sequence updates** - API replaces all, can't update one
3. **Geography-first sourcing** - Low software signal rate, pivoting to tech-first

### For Next Batch
1. Always dry-run first
2. Backup sequences before updates
3. Target tech-first (ServiceTitan users) for higher ICP fit
4. Use audit script before every launch

---

## 🤝 Support

**Questions?**
- Check `docs/` folder for detailed guides
- Run audit script to diagnose issues
- Review `claude.md` for full project context

**Updates:**
- All changes documented in `docs/FIXES_COMPLETED.md`
- Git history tracks all modifications

---

**Last Updated:** November 17, 2025 - LAUNCHED
**Next Review:** After Week 1 results (Nov 24, 2025)
**Maintained by:** Claude + Shane (Appletree HVAC project)

---

## 🚀 LAUNCH STATUS (Nov 17, 2025)

### Live Campaign Performance:
- **A-Tier:** 16 emails sent, 62.5% open rate
- **B-Tier:** Launches Nov 18 (tomorrow)
- **C-Tier:** 30 emails sent, 60% open rate
- **Total:** 46 sends, 28 opens (60.9%)
- **Deliverability:** 0 bounces, 0 blocks, 90%+ inbox

### Recent Changes (Nov 16-17):
✅ Fixed SPF/DNS issues (65% → 90%+ inbox rate)
✅ Increased send limits to 85/day (was 28/day)
✅ Re-enabled click tracking via API
✅ All 3 campaigns active and sending

### Known Issues:
⚠️ ~50% of "opens" are Apple MPP inflated (real rate ~26-30%)
⚠️ C-Tier missing Calendly in Seq 1 (intentional, testing)
⚠️ Smartlead UI can't update active campaigns (use API scripts)
