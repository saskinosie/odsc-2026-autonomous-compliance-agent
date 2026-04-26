# 🛡️ Dual-Agent Harness Protocol (Claude + Codex)

1. **The Audit:** Every file write triggers the `codex review` harness automatically.
2. **The Feedback:** If the terminal shows "🛑 CODEX REVIEW FINDINGS," treat those as mandatory blockers — not suggestions.
3. **The Loop:** Apply fixes immediately. Each fix triggers a new Codex review.
4. **The Circuit Breaker:** If you and Codex have disagreed on the same code for **3 consecutive turns**, STOP. Summarize the disagreement and ask the user for a tie-breaker.
5. **The Completion:** Do not declare a task complete until Codex returns a PASS.
6. **The Badge:** Sign off with "✅ Vetted by Codex (gpt-5.2)".
