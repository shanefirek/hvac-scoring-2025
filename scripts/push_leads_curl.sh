#!/bin/bash
# Push valid leads to 4 Smartlead test campaigns using curl
# API discovered to need lead_list wrapper

API_KEY="38ee964e-b100-4e2b-bfc1-a6ebf5ef48d3_4l5qyv8"

# Campaign 1: M&A Variant (2757801) - leads 1-125
echo "=== Pushing to M&A Variant (2757801) ==="
curl -s -X POST "https://server.smartlead.ai/api/v1/campaigns/2757801/leads?api_key=$API_KEY" \
  -H "Content-Type: application/json" \
  -d @/tmp/batch1.json | jq .

# Campaign 2: 35/100 Variant (2757802) - leads 126-250
echo "=== Pushing to 35/100 Variant (2757802) ==="
curl -s -X POST "https://server.smartlead.ai/api/v1/campaigns/2757802/leads?api_key=$API_KEY" \
  -H "Content-Type: application/json" \
  -d @/tmp/batch2.json | jq .

# Campaign 3: Social Proof Variant (2757804) - leads 251-375
echo "=== Pushing to Social Proof Variant (2757804) ==="
curl -s -X POST "https://server.smartlead.ai/api/v1/campaigns/2757804/leads?api_key=$API_KEY" \
  -H "Content-Type: application/json" \
  -d @/tmp/batch3.json | jq .

# Campaign 4: Direct Variant (2757805) - leads 376-498
echo "=== Pushing to Direct Variant (2757805) ==="
curl -s -X POST "https://server.smartlead.ai/api/v1/campaigns/2757805/leads?api_key=$API_KEY" \
  -H "Content-Type: application/json" \
  -d @/tmp/batch4.json | jq .

echo "=== Done ==="
