# Appletree HVAC Lead Scoring System

**Date:** November 12, 2025
**Session:** Initial build and deployment

---

## Project Context

Building a lead management system for Appletree Business (bookkeeping/tax services for HVAC contractors). Client: Patrick at appletreebusiness.com.

**Timeline:** 3 months to deliver leads + outbound campaigns
**Week 1 Goal:** 175+ scored leads ready to send by Monday
**Current Status:** 160 verified leads, scored and tiered, ready for Smartlead

---

## What We Built

### FastAPI Lead Scoring System

**Repository:** `appletree-data-pipeline`
**Deployed:** Railway at `https://hvac-scoring-2025-production.up.railway.app`

**Key Files:**
- `main.py` - FastAPI app with `/score-lead` endpoint
- `requirements.txt` - Dependencies (fastapi, uvicorn, pydantic)
- `README.md` - Deployment and Clay integration docs
- `HVAC Nov 2025 Appletree - HVAC_draft_appletree_112025.csv` - Source data (202 leads)

---

## Architecture Decision: Why FastAPI Over Clay Formulas

**Problem:** Needed to score 200+ HVAC leads based on sophistication signals, assign tiers, and route to appropriate messaging sequences.

**Why we built an API instead of Clay formulas:**

1. **Iteration speed** - Change scoring weights with one variable, not 5 nested formulas
2. **Version control** - Git history of scoring logic changes
3. **Reusability** - Same API works for future batches, other clients
4. **Testing** - Can curl test locally before deploying
5. **Professional positioning** - "I built a scoring API" > "I made Clay formulas"
6. **Not locked into Clay** - Can switch CRMs/tools without rebuilding logic

**Architecture:**
```
Clay Table (source of truth)
    ↓
HTTP API Column → POST to Railway
    ↓
FastAPI calculates: score, tier, messaging
    ↓
Returns JSON → Clay stores in column
    ↓
Export to Smartlead (A/B/C campaigns)
```

---

## Scoring Logic

**Total possible: 30 points**

### Point System
- **Service Software** (+15): ServiceTitan, Jobber, or Housecall Pro
- **Franchise** (+10): Company name matches franchise list
- **Reviews** (non-franchise only):
  - 500+ reviews: +10
  - 100-499 reviews: +7
  - 25-99 reviews: +4
  - 10-24 reviews: +2
- **LinkedIn URL** (+3): Profile exists
- **Domain** (+2): Website exists

### Tier Classification
- **A-Tier (20-30 points)**: High sophistication - Software users, franchises, or high-volume operations
- **B-Tier (10-19 points)**: Medium sophistication - Good reviews OR tech signals
- **C-Tier (0-9 points)**: Lower sophistication - Smaller operations

### Messaging Strategies

**A-Tier:**
- Franchise: "Multi-unit operations + franchise fee complexity"
- Software + Scale: "Tech-forward operator with systems"
- Scale: "High-volume operation with complex tax needs"

**B-Tier:**
- Tech Signal: "Has systems, needs better accounting integration"
- Growth Signal: "Established business, room for tax optimization"

**C-Tier:**
- Pain Focus: "Direct CPA pain points and tax surprises"

### Franchise Detection
Company name matches: ARS, Rescue Rooter, One Hour, Benjamin Franklin, Roto-Rooter, Mr. Rooter, Aire Serv, Goettl

---

## Data Pipeline

### Source Data
- **202 leads** initially scraped from New England HVAC businesses
- Enriched via FastAPI scraper (built previously, separate from this scoring system)
- Email validation completed (99.9% accuracy)

### Data Quality Issues Found & Fixed
1. **Duplicate franchises** - Same location, multiple "owners" listed (Aire Serv, ARS)
2. **Invalid emails** - ~30-40 rows with `Verified: FALSE`
3. **Supplier contamination** - Johnstone Supply, Ferguson (not contractors)
4. **Broken email fields** - Empty strings, formula text, multiple emails in one field

### Final Clean Dataset
- **160 verified leads** ready to send
- All emails validated and verified
- Duplicates removed
- Suppliers filtered out

### Distribution (Estimated)
- **A-Tier:** ~25-30 leads (15-20%)
- **B-Tier:** ~60-70 leads (35-40%)
- **C-Tier:** ~70-80 leads (45-50%)

---

## Key Insights from Data Analysis

### Service Software Coverage (Sparse)
- Only **~9% of leads** have FSM software detected (ServiceTitan, Jobber, Housecall Pro)
- **Why:** New England geography-first approach, not tech-first
- **Decision:** Week 1 proceeds with current list, Week 2+ pivots to tech-first sourcing

### Geographic Focus
- **New England heavy:** NH, VT, ME, MA, CT
- Intentional for initial testing
- **Next phase:** Expand to CST (TX, CO, AZ) with tech-first targeting

### Franchise Representation
- **~2-3% are franchises** after deduping
- Low representation due to geography-first approach
- Franchise review counts roll up to parent brand (e.g., 4k reviews for brand, not individual location)

### Review Count Distribution
- **0-25 reviews:** ~40 leads
- **25-100 reviews:** ~80 leads
- **100-500 reviews:** ~50 leads
- **500+ reviews:** ~30 leads
- **Outliers:** Joyce Cooling (4,814), Fire & Ice (3,936), Central Cooling (2,992)

---

## Clay Integration

### HTTP API Column Setup

**Endpoint:** `https://hvac-scoring-2025-production.up.railway.app/score-lead`
**Method:** POST
**Headers:** `Content-Type: application/json`

**Request Body:**
```json
{
  "company": "{{Company}}",
  "reviews_count": {{Reviews Count}},
  "service_software": "{{Field Service Tech}}",
  "linkedin_url": "{{Linkedin Url}}",
  "domain": "{{Domain}}"
}
```

**Response Stored in Clay:**
```json
{
  "is_franchise": "NO",
  "score": 27,
  "tier": "A",
  "messaging_strategy": "Software + Scale: Tech-forward operator with systems",
  "breakdown": {
    "service_software": 15,
    "franchise_or_reviews": 10,
    "linkedin": 3,
    "domain": 2
  }
}
```

### Handling Missing Data
- API accepts optional fields (reviews_count, service_software, linkedin_url, domain)
- Empty fields default to `""` or `0`
- Scoring handles missing data gracefully (0 points for missing signals)

### Clay Column Visibility
**Hidden columns:**
- Email waterfall logic (30+ intermediate enrichment columns)
- Failed enrichment attempts
- Debugging/testing columns

**Visible columns for Patrick demo:**
- Company
- Name
- Final Email
- Domain
- Reviews Count
- Service Software
- **Score** (from API)
- **Tier** (from API)
- **Messaging Strategy** (from API)

---

## Smartlead Campaign Structure

### 3 Separate Campaigns

**1. "HVAC A-Tier - Software & Scale"**
- 25-30 leads
- 4 touchpoints over 2 weeks
- 2-3 days between emails
- Aggressive follow-up (high-value prospects)

**2. "HVAC B-Tier - Growth Signal"**
- 60-70 leads
- 3 touchpoints over 3 weeks
- 4-5 days between emails
- Normal cadence

**3. "HVAC C-Tier - Pain Focus"**
- 70-80 leads
- 2 touchpoints over 4 weeks
- 5-7 days between emails
- Conservative approach

### Send Capacity
- **3 email domains** configured in Smartlead
- **10 sends/day per domain** = 30 sends/day total
- **450 total sends** (160 leads × avg 2.8 emails) over 4 weeks
- **~20-25 sends/day average** (well under 30/day limit)

### Launch Timeline
- **Monday Week 1:** A-Tier campaign (test highest value first)
- **Tuesday Week 1:** B-Tier campaign
- **Wednesday Week 1:** C-Tier campaign (optional delay)

---

## Next Steps

### Week 1 (This Week)
- [x] Build FastAPI scoring system
- [x] Deploy to Railway
- [x] Integrate with Clay
- [x] Clean and score 160 leads
- [ ] Draft email sequences (A/B/C tiers)
- [ ] Load leads into Smartlead campaigns
- [ ] Demo to Patrick (Thursday)
- [ ] Launch campaigns (Monday)

### Week 2-3 (Tech-First Pivot)
- [ ] Build tech-first scraping strategy (ServiceTitan/Jobber/HCP users)
- [ ] Source methods:
  - Jobber public directory scraping
  - ServiceTitan LinkedIn employee detection
  - Housecall Pro booking widget detection
- [ ] Target: 500-1k leads with FSM software
- [ ] Expand geography to CST states (TX, CO, AZ)

### Week 4+ (Scale & Optimize)
- [ ] Analyze Week 1 response rates by tier
- [ ] Adjust scoring weights based on conversion data
- [ ] A/B test messaging strategies
- [ ] Scale to 10k+ lead database

---

## Technical Notes

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python main.py

# Test endpoint
curl -X POST http://localhost:8000/score-lead \
  -H "Content-Type: application/json" \
  -d '{"company": "Test", "reviews_count": 100, "service_software": "ServiceTitan", "linkedin_url": "https://linkedin.com/in/test", "domain": "test.com"}'
```

### Deployment
```bash
# Push to GitHub
git add .
git commit -m "Update scoring logic"
git push

# Railway auto-deploys from main branch
# URL: https://hvac-scoring-2025-production.up.railway.app
```

### Updating Scoring Logic
Edit `main.py` and change weight constants:
```python
# Service software points
if has_software:
    score += 15  # Change this value

# Franchise points
if is_franchise:
    score += 10  # Change this value
```

Commit → Push → Railway auto-redeploys → Clay automatically uses new logic

---

## Key Decisions & Rationale

### Why FastAPI Over Alternatives
- **Not Clay formulas:** Too rigid, no version control, hard to debug
- **Not Python script + CSV export:** Need real-time scoring in Clay for iteration
- **Not serverless (Lambda/Cloud Functions):** Railway simpler for MVP, can migrate later
- **FastAPI specifically:** Fast to build, auto-generates docs, modern Python stack

### Why 3 Tiers Instead of 5
- **Simplicity:** Easier to manage 3 messaging strategies than 5
- **Clear differentiation:** A (high sophistication), B (medium), C (low)
- **Smartlead limitation:** More campaigns = more complexity in small team
- **Messaging clarity:** Each tier has distinct angle (software/growth/pain)

### Why New England First
- **Testing ground:** Smaller market, lower risk
- **Client proximity:** Patrick's network may be here
- **Proof of concept:** Validate system before scaling nationally
- **Accept tradeoffs:** Lower software signals, fewer franchises (known limitation)

### Why Tech-First for Week 2+
- **Better ICP fit:** Software users = budget + complexity
- **Stronger messaging:** Can reference specific tools (ServiceTitan, Jobber)
- **Higher scoring leads:** More A-tier prospects
- **Differentiation:** Competitors scrape by geography, we scrape by sophistication

---

## Patrick Demo Script (Thursday)

**Opening:**
"Here's where we're at for Week 1..."

**1. Show the leads (Clay table)**
- 160 qualified HVAC contractors
- All emails verified (99.9% deliverability)
- Scored 0-30 points based on sophistication signals
- Tiered A/B/C for targeted messaging

**2. Show the system (API)**
- "I built a scoring API that runs on every lead"
- Show Railway dashboard (it's deployed and running)
- Explain scoring logic (software, reviews, franchises)
- "This is reusable for every future batch"

**3. Show the campaigns (Smartlead)**
- 3 campaigns ready to launch Monday
- A-Tier: Software/scale messaging (25-30 leads)
- B-Tier: Growth messaging (60-70 leads)
- C-Tier: Pain-focused messaging (70-80 leads)
- Staggered launch over 4 weeks

**4. Set expectations**
- Week 1: Testing messaging with current list
- Week 2: Pivoting to tech-first sourcing (ServiceTitan/Jobber users nationwide)
- Goal: Build 10k+ lead database over 3 months

**Positioning:**
"We started geography-first to test the system. Now we're pivoting to tech-first for higher quality leads and tighter messaging."

---

## Lessons Learned

### What Worked Well
1. **Building API first** - Saved hours of Clay formula debugging
2. **Testing locally before deploying** - Caught issues immediately
3. **Handling optional fields in API** - Clay integration much smoother
4. **Clear tier thresholds** - Easy to explain to client

### What to Improve
1. **Data sourcing** - Tech-first from the start would've given better signals
2. **Franchise detection** - Need better logic for PE-backed vs owner-operator
3. **Review count normalization** - Franchises skew high, need separate scoring

### Technical Debt
- **No authentication on API** - Fine for MVP, add API keys later if needed
- **No rate limiting** - Clay won't abuse it, but good practice for scale
- **No database** - Scoring is stateless, consider logging for analytics
- **Hardcoded franchise list** - Should move to config file or database

---

## Questions for Future Sessions

1. **Should we A/B test scoring models?** (e.g., software = 20 pts vs 15 pts)
2. **Do we need separate scoring for franchises vs independents?**
3. **Should we build a dashboard for Patrick to see lead quality metrics?**
4. **How do we handle re-scoring leads when enrichment improves?**
5. **Should we track which tier converts best and adjust weights?**

---

## Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com
- **Railway Deployment:** https://docs.railway.app
- **Clay HTTP API:** https://clay.com/university/http-api
- **Smartlead:** https://smartlead.ai

---

**Last Updated:** November 12, 2025
**Next Review:** After Week 1 campaign results (Nov 18-19, 2025)
