#!/bin/bash
# Teacher Licensure Compliance Checker
# Usage:
#   ./check.sh "Ohio" "Mathematics 7-12"   — check specific state/subject
#   ./check.sh "all"                        — check all monitored states
#   ./check.sh "log"                        — show recent change log

TARGET="${1:-all}"
SUBJECT="${2:-}"
DB="/home/user/data/compliance.db"

# Ensure data directory and database exist
mkdir -p "$(dirname "$DB")"
sqlite3 "$DB" "
CREATE TABLE IF NOT EXISTS snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  state TEXT NOT NULL,
  subject TEXT,
  url TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  content_excerpt TEXT,
  checked_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS changes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  state TEXT NOT NULL,
  subject TEXT,
  url TEXT NOT NULL,
  old_hash TEXT,
  new_hash TEXT NOT NULL,
  content_excerpt TEXT,
  detected_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"

# Show change log
if [ "$TARGET" = "log" ]; then
  echo "=== Recent Compliance Changes ==="
  sqlite3 -column -header "$DB" "
    SELECT state, subject, detected_at, url
    FROM changes
    ORDER BY detected_at DESC
    LIMIT 20;
  "
  exit 0
fi

# State DOE compliance pages to monitor
# Format: "STATE|SUBJECT|URL"
declare -a WATCH_LIST=(
  "Ohio|General Licensure|https://education.ohio.gov/Topics/Teaching/Licensure"
  "Texas|General Licensure|https://tea.texas.gov/texas-educators/certification/educator-certification"
  "California|General Licensure|https://www.ctc.ca.gov/educator-prep/program-accred/accreditation-overview"
  "Florida|General Licensure|https://www.fldoe.org/teaching/certification/"
  "New York|General Licensure|https://www.nysed.gov/teaching-certification"
  "Pennsylvania|General Licensure|https://www.education.pa.gov/Educators/Certification/Pages/default.aspx"
  "Illinois|General Licensure|https://www.isbe.net/Pages/Licensure.aspx"
  "Georgia|General Licensure|https://www.gapsc.com/Commission/GetCertified/certification_routes.aspx"
  "North Carolina|General Licensure|https://www.dpi.nc.gov/educators/licensure"
  "Virginia|General Licensure|https://www.doe.virginia.gov/teaching-learning-assessment/teaching-in-virginia"
)

check_url() {
  local state="$1"
  local subject="$2"
  local url="$3"

  # Fetch page content
  local content
  content=$(curl -sL --max-time 15 --user-agent "Mozilla/5.0 (compatible; compliance-monitor/1.0)" "$url" 2>/dev/null)
  if [ -z "$content" ]; then
    echo "  ⚠️  Could not fetch: $url"
    return
  fi

  # Strip HTML tags and hash the meaningful text content
  local text
  text=$(echo "$content" | python3 -c "
import sys, re, hashlib
html = sys.stdin.read()
text = re.sub(r'<[^>]+>', ' ', html)
text = re.sub(r'\s+', ' ', text).strip()
print(text[:2000])
" 2>/dev/null)

  local new_hash
  new_hash=$(echo "$text" | python3 -c "import sys, hashlib; print(hashlib.sha256(sys.stdin.read().encode()).hexdigest())")
  local excerpt="${text:0:300}"

  # Look up stored hash
  local old_hash
  old_hash=$(sqlite3 "$DB" "SELECT content_hash FROM snapshots WHERE state='$state' AND url='$url' ORDER BY checked_at DESC LIMIT 1;")

  if [ -z "$old_hash" ]; then
    # First time seeing this URL — store baseline
    sqlite3 "$DB" "INSERT INTO snapshots (state, subject, url, content_hash, content_excerpt) VALUES ('$state', '$subject', '$url', '$new_hash', '$excerpt');"
    echo "  📌 Baseline captured: $state — $url"
  elif [ "$old_hash" != "$new_hash" ]; then
    # Content changed — record it
    sqlite3 "$DB" "INSERT INTO snapshots (state, subject, url, content_hash, content_excerpt) VALUES ('$state', '$subject', '$url', '$new_hash', '$excerpt');"
    sqlite3 "$DB" "INSERT INTO changes (state, subject, url, old_hash, new_hash, content_excerpt) VALUES ('$state', '$subject', '$url', '$old_hash', '$new_hash', '$excerpt');"
    echo "  🚨 CHANGE DETECTED: $state ($subject)"
    echo "     URL: $url"
    echo "     Excerpt: ${excerpt:0:200}"
  else
    echo "  ✅ No change: $state — $url"
  fi
}

echo "=== Teacher Licensure Compliance Monitor ==="
echo "Started: $(date)"
echo ""

if [ "$TARGET" = "all" ]; then
  for entry in "${WATCH_LIST[@]}"; do
    IFS='|' read -r state subject url <<< "$entry"
    echo "Checking $state..."
    check_url "$state" "$subject" "$url"
  done
else
  # Check specific state
  for entry in "${WATCH_LIST[@]}"; do
    IFS='|' read -r state subject url <<< "$entry"
    if [[ "${state,,}" == *"${TARGET,,}"* ]]; then
      echo "Checking $state..."
      check_url "$state" "$subject" "$url"
    fi
  done
fi

echo ""
echo "=== Summary ==="
sqlite3 -column -header "$DB" "
  SELECT COUNT(*) as total_changes, MAX(detected_at) as last_change
  FROM changes;
"
