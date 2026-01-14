#!/bin/bash
# Trigger.dev Setup Helper Script
# Run this script to guide through Trigger.dev setup

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        Trigger.dev Automation Setup - Appletree HVAC          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found"
    echo "   Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
else
    echo "✅ .env file exists"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Check Environment Variables"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check required variables
check_env_var() {
    local var_name=$1
    local var_value=$(grep "^${var_name}=" .env | cut -d '=' -f2)

    if [ -z "$var_value" ] || [[ "$var_value" == *"your-"* ]] || [[ "$var_value" == *"here"* ]]; then
        echo "⚠️  ${var_name}: NOT CONFIGURED"
        return 1
    else
        echo "✅ ${var_name}: configured"
        return 0
    fi
}

all_configured=true

echo ""
echo "Supabase Configuration:"
check_env_var "SUPABASE_URL" || all_configured=false
check_env_var "SUPABASE_SERVICE_KEY" || all_configured=false

echo ""
echo "Smartlead Configuration:"
check_env_var "SMARTLEAD_API_KEY" || all_configured=false
check_env_var "SMARTLEAD_CAMPAIGN_A" || all_configured=false
check_env_var "SMARTLEAD_CAMPAIGN_B" || all_configured=false
check_env_var "SMARTLEAD_CAMPAIGN_C" || all_configured=false

echo ""
echo "Outscraper Configuration:"
check_env_var "OUTSCRAPER_API_KEY" || all_configured=false

echo ""
echo "Trigger.dev Configuration:"
check_env_var "TRIGGER_SECRET_KEY" || all_configured=false

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Get Missing API Keys"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if ! grep -q "OUTSCRAPER_API_KEY=.*[^here]" .env || grep -q "your-outscraper" .env; then
    echo "📝 Outscraper API Key:"
    echo "   1. Sign up at: https://outscraper.com"
    echo "   2. Go to: https://app.outscraper.com/api-key"
    echo "   3. Copy your API key"
    echo "   4. Update OUTSCRAPER_API_KEY in .env"
    echo ""
fi

if ! grep -q "TRIGGER_SECRET_KEY=.*[^here]" .env || grep -q "your-trigger" .env; then
    echo "📝 Trigger.dev Secret Key:"
    echo "   1. Login to Trigger.dev:"
    echo "      npx trigger.dev@latest login"
    echo ""
    echo "   2. Get your secret key from:"
    echo "      https://cloud.trigger.dev/projects/proj_anceawkgglmxzvyxdugw/apikeys"
    echo ""
    echo "   3. Update TRIGGER_SECRET_KEY in .env"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Install Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm packages..."
    npm install
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Next Actions"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$all_configured" = true ]; then
    echo "✅ All environment variables configured!"
    echo ""
    echo "Ready to test! Run:"
    echo ""
    echo "  npx trigger.dev@latest dev"
    echo ""
    echo "Then open: http://localhost:3030"
    echo ""
    echo "📖 Full guide: docs/TRIGGER_SETUP.md"
else
    echo "⚠️  Configuration incomplete"
    echo ""
    echo "Next steps:"
    echo "  1. Update missing API keys in .env"
    echo "  2. Run this script again to verify"
    echo "  3. Start testing with: npx trigger.dev@latest dev"
    echo ""
    echo "📖 Full guide: docs/TRIGGER_SETUP.md"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Implemented Tasks:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  1. weekly-scrape       - Scrape HVAC leads from Outscraper"
echo "  2. enrich-leads        - Detect FSM software from websites"
echo "  3. score-leads         - Apply scoring logic and assign tiers"
echo "  4. sync-to-smartlead   - Upload to Smartlead campaigns"
echo "  5. weekly-pipeline     - Orchestrator (scheduled Sundays 2 AM ET)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
