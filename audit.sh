#!/bin/bash
# audit.sh - Bridges Claude Code to the Codex Review Harness

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path')

if [ ! -f "$FILE_PATH" ]; then exit 0; fi

# Walk up the directory tree — skip audit if any ancestor contains .noaudit
DIR=$(dirname "$FILE_PATH")
while [ "$DIR" != "/" ]; do
  if [ -f "$DIR/.noaudit" ]; then exit 0; fi
  DIR=$(dirname "$DIR")
done

if ! command -v codex &> /dev/null; then
    echo '{"decision":"block","reason":"Codex CLI not found. Run: npm install -g @openai/codex"}'
    exit 0
fi

if ! command -v jq &> /dev/null; then
    echo '{"decision":"block","reason":"jq not found. Run: brew install jq"}'
    exit 0
fi

FILE_CONTENT=$(cat "$FILE_PATH")
PROMPT="Review this code file ($FILE_PATH) for security vulnerabilities, bugs, and logic errors. If everything looks good, respond with just the word LGTM. Otherwise list the critical issues concisely.

$FILE_CONTENT"

FULL_OUTPUT=$(echo "$PROMPT" | codex review - 2>&1)

# Extract only the codex response section (after the "codex" marker line)
CRITIQUE=$(echo "$FULL_OUTPUT" | awk '/^codex$/{found=1; next} found{print}')

if [[ "$CRITIQUE" == *"LGTM"* ]] || \
   [[ "$CRITIQUE" == *"no issues"* ]] || \
   [[ "$CRITIQUE" == *"no security"* ]] || \
   [[ "$CRITIQUE" == *"no executable"* ]] || \
   [[ "$CRITIQUE" == *"no apparent"* ]] || \
   [[ "$CRITIQUE" == *"does not contain"* ]] || \
   [[ "$CRITIQUE" == *"does not introduce"* ]]; then
    exit 0
else
    jq -n --arg reason "🛑 CODEX REVIEW FINDINGS:\n$CRITIQUE" '{"decision":"block","reason":$reason}'
fi
