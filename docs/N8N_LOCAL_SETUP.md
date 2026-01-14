# n8n Local Setup Guide

**Why self-host?** Environment variables for secrets (not available on n8n Cloud free tier)

---

## Quick Start (5 Minutes)

### 1. **Create .env file with your secrets**

```bash
cp .env.example .env
```

Then edit `.env` and add your real API keys:

```bash
# .env
SUPABASE_URL=https://rlmuovkdvbxzyylbiunj.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.YOUR_REAL_KEY_HERE
SMARTLEAD_API_KEY=38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8

N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your-secure-password-here
```

### 2. **Start n8n**

```bash
./start-n8n.sh
```

Or manually:

```bash
docker-compose up -d
```

### 3. **Access n8n**

Open: http://localhost:5678

Login with credentials from your `.env` file.

---

## Import Your Workflow

1. **Copy workflow JSON** from `n8n/hvac_gtm_flywheel.json`
2. **In n8n UI:** Click "+" → "Import from File/URL"
3. **Paste JSON** and click "Import"
4. **Save workflow**

Your workflow will automatically use environment variables:
- `{{ $env.SUPABASE_URL }}`
- `{{ $env.SUPABASE_SERVICE_KEY }}`
- `{{ $env.SMARTLEAD_API_KEY }}`

---

## Webhooks (Clay → n8n)

### Production Webhook URLs

Once n8n is running, your webhook URLs will be:

**Clay Webhook (Lead Enriched):**
```
http://localhost:5678/webhook/clay-webhook
```

**Smartlead Events Webhook:**
```
http://localhost:5678/webhook/smartlead-events
```

### Making Webhooks Public (for Clay/Smartlead)

**Problem:** `localhost` only works on your machine. Clay/Smartlead can't reach it.

**Solutions:**

#### Option A: ngrok (Quick Testing)
```bash
# Install ngrok
brew install ngrok

# Expose n8n
ngrok http 5678

# Use the ngrok URL in Clay/Smartlead
https://abc123.ngrok.io/webhook/clay-webhook
```

#### Option B: Deploy to Cloud (Production)

**Railway (Recommended):**
1. Push this repo to GitHub
2. Create Railway project: https://railway.app
3. Add environment variables in Railway dashboard
4. Deploy
5. Use Railway URL: `https://your-app.railway.app/webhook/clay-webhook`

**Render/Fly.io:**
Similar process, just deploy the Docker container.

---

## Common Commands

### Start n8n
```bash
./start-n8n.sh
# OR
docker-compose up -d
```

### Stop n8n
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f n8n
```

### Restart n8n (after .env changes)
```bash
docker-compose restart
```

### Full reset (delete all workflows/data)
```bash
docker-compose down -v
rm -rf n8n_data/
docker-compose up -d
```

---

## Troubleshooting

### "Cannot connect to Supabase"
- Check `.env` file has correct `SUPABASE_SERVICE_KEY` (not anon key)
- Restart n8n: `docker-compose restart`
- Check logs: `docker-compose logs n8n`

### "Webhook not receiving data"
- Check webhook URL is correct in Clay/Smartlead
- If using localhost, use ngrok for external access
- Check n8n workflow is activated (toggle in UI)

### "Environment variable not found"
- Make sure `.env` file exists
- Restart n8n after changing `.env`
- Check variable name matches exactly (case-sensitive)

---

## Production Deployment Options

### Railway (Easiest)
✅ Free tier available
✅ Auto-deploys from GitHub
✅ Built-in HTTPS
✅ Environment variables in dashboard

**Setup:**
1. Create Railway account
2. "New Project" → "Deploy from GitHub"
3. Select this repo
4. Add environment variables in Settings
5. Done!

### Render
✅ Free tier (with sleep after inactivity)
✅ Auto-deploys from GitHub
✅ HTTPS included

**Setup:**
1. Create `render.yaml` config
2. Push to GitHub
3. Connect Render to repo
4. Deploy

### Fly.io
✅ Free tier available
✅ Global edge deployment
✅ Great performance

**Setup:**
```bash
flyctl launch
flyctl secrets set SUPABASE_URL=...
flyctl deploy
```

---

## Cost Comparison

| Option | Cost | Pros | Cons |
|--------|------|------|------|
| **Local Docker** | Free | Full control, fast | Need ngrok for webhooks, not 24/7 |
| **Railway** | Free tier → $5/mo | Easy, reliable, HTTPS | Paid after free tier |
| **Render** | Free (sleeps) → $7/mo | Simple setup | Free tier sleeps after 15min |
| **n8n Cloud** | $20/mo | Managed, no DevOps | No env vars on free tier |

**Recommendation:** Start with **local + ngrok** for testing, then deploy to **Railway** for production ($5/mo is worth it for 24/7 uptime).

---

## Next Steps

1. ✅ Start n8n locally
2. ✅ Import workflow from `n8n/hvac_gtm_flywheel.json`
3. ✅ Test with sample Clay webhook payload
4. ✅ Deploy to Railway for production webhooks
5. ✅ Update Clay/Smartlead with production webhook URLs

---

**Last Updated:** November 19, 2025
