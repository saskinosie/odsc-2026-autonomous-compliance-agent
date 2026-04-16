#!/bin/bash
# Search the web using Brave Search API
# Usage: ./search.sh "your search query"

QUERY="${1:-SEC filing news}"

curl -s "https://api.search.brave.com/res/v1/web/search?q=$(echo "$QUERY" | sed 's/ /+/g')&count=5" \
  -H "Accept: application/json" \
  -H "X-Subscription-Token: ${BRAVE_API_KEY}" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
for r in data.get('web', {}).get('results', []):
    print(f\"**{r.get('title', '')}**\")
    print(f\"{r.get('description', '')}\")
    print(f\"URL: {r.get('url', '')}\")
    print()
" 2>/dev/null || echo "Error searching Brave"
