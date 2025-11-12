# Appletree HVAC Lead Scoring API

FastAPI service that scores HVAC leads based on sophistication signals for Appletree's outbound campaigns.

## Scoring Logic

**Total possible: 30 points**

- **Service Software** (+15): ServiceTitan, Jobber, or Housecall Pro
- **Franchise** (+10): Company name matches franchise list
- **Reviews** (non-franchise only):
  - 500+ reviews: +10
  - 100-499 reviews: +7
  - 25-99 reviews: +4
  - 10-24 reviews: +2
- **LinkedIn URL** (+3): Profile exists
- **Domain** (+2): Website exists

## Tier Classification

- **A-Tier (20-30 points)**: High sophistication - Software users, franchises, or high-volume operations
- **B-Tier (10-19 points)**: Medium sophistication - Good reviews OR tech signals
- **C-Tier (0-9 points)**: Lower sophistication - Smaller operations, pain-focused messaging

## Quick Start (Local)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

Server runs at `http://localhost:8000`

Test it:
```bash
curl http://localhost:8000/
```

## API Endpoints

### `POST /score-lead`

Score a single lead.

**Request Body:**
```json
{
  "company": "Glasco Heating & Air Conditioning",
  "reviews_count": 973,
  "service_software": "ServiceTitan",
  "linkedin_url": "https://linkedin.com/in/...",
  "domain": "glascohvac.com"
}
```

**Response:**
```json
{
  "is_franchise": "NO",
  "score": 30,
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

### `GET /` or `/health`

Health check endpoint.

## Deploy to Railway

### 1. Push to GitHub

```bash
git add .
git commit -m "Add lead scoring API"
git push
```

### 2. Deploy on Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select this repository
4. Railway auto-detects Python and deploys

### 3. Get Your Production URL

After deployment, Railway gives you a URL like:
```
https://appletree-data-pipeline-production.up.railway.app
```

Test it:
```bash
curl https://your-app.railway.app/
```

## Clay Integration

### Add HTTP API Column in Clay

1. **In your Clay table**, add a new column
2. Select **"HTTP API"**
3. Configure the request:

**Method:** `POST`

**URL:** `https://your-app.railway.app/score-lead`

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Body (JSON):**
```json
{
  "company": "{{Company}}",
  "reviews_count": {{Reviews Count}},
  "service_software": "{{Field Service Tech}}",
  "linkedin_url": "{{Linkedin Url}}",
  "domain": "{{Domain}}"
}
```

**Response Mapping:**

Clay will store the entire JSON response. You can then reference in other columns:

- `{{HTTP_API_Column.tier}}` → A, B, or C
- `{{HTTP_API_Column.score}}` → 0-30
- `{{HTTP_API_Column.messaging_strategy}}` → Strategy description
- `{{HTTP_API_Column.is_franchise}}` → YES or NO

### Example Clay Setup

**Columns to send to API:**
- Company (text)
- Reviews Count (number)
- Field Service Tech (text)
- Linkedin Url (text)
- Domain (text)

**New columns to create:**
- **Scoring Data** (HTTP API column) → stores full JSON response
- **Tier** (formula) → `{{Scoring Data.tier}}`
- **Score** (formula) → `{{Scoring Data.score}}`
- **Messaging** (formula) → `{{Scoring Data.messaging_strategy}}`

### Hide Janky Enrichment Columns

Once scoring is working, hide these columns:
- All the email waterfall columns
- Failed enrichment attempts
- Intermediate calculation columns

**Show Patrick:**
- Company
- Name
- Final Email
- Domain
- Reviews
- Software
- **Score** ⭐
- **Tier** ⭐
- **Messaging** ⭐

## Messaging Strategies

The API returns messaging strategies based on tier + signals:

### A-Tier Strategies
- **Franchise**: "Multi-unit operations + franchise fee complexity"
- **Software + Scale**: "Tech-forward operator with systems"
- **Scale**: "High-volume operation with complex tax needs"

### B-Tier Strategies
- **Tech Signal**: "Has systems, needs better accounting integration"
- **Growth Signal**: "Established business, room for tax optimization"

### C-Tier Strategy
- **Pain Focus**: "Direct CPA pain points and tax surprises"

## Updating Scoring Logic

To change scoring weights, edit `main.py`:

```python
# Service software points
if has_software:
    score += 15  # Change this value

# Franchise points
if is_franchise:
    score += 10  # Change this value
```

After changes:
1. Commit to git
2. Railway auto-redeploys
3. Clay automatically uses new logic (no changes needed)

## Testing

Test the API locally before deploying:

```bash
# Start server
python main.py

# Test with curl
curl -X POST http://localhost:8000/score-lead \
  -H "Content-Type: application/json" \
  -d '{
    "company": "Aire Serv of Portland",
    "reviews_count": 450,
    "service_software": "Housecall Pro",
    "linkedin_url": "https://linkedin.com/in/test",
    "domain": "aireserv.com"
  }'
```

Expected response:
```json
{
  "is_franchise": "YES",
  "score": 28,
  "tier": "A",
  "messaging_strategy": "Franchise: Multi-unit operations + franchise fee complexity",
  "breakdown": {
    "service_software": 15,
    "franchise_or_reviews": 10,
    "linkedin": 3,
    "domain": 0
  }
}
```

## Architecture

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

## Next Steps

1. ✅ Deploy to Railway
2. ✅ Test the endpoint
3. ✅ Add HTTP API column in Clay
4. ✅ Map response fields
5. ✅ Hide janky columns
6. ✅ Show Patrick the clean table
7. 🚀 Export to Smartlead (Monday)

## Troubleshooting

**Clay returns error:**
- Check Railway logs for errors
- Verify your URL is correct
- Test endpoint with curl first

**Scoring looks wrong:**
- Check column mappings in Clay (e.g., Reviews Count is a number, not text)
- Test with sample data locally
- Check the `breakdown` field to see how points were assigned

**Railway deployment failed:**
- Check `requirements.txt` is in repo
- Verify `main.py` has no syntax errors
- Check Railway build logs

## Support

Questions? Check the Railway logs or test locally first.
