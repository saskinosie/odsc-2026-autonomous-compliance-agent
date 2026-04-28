"""
Custom Claw Agent — Teacher Licensure Compliance Monitor
~60 lines. A pydantic-ai agent with pluggable skills.

Add a new skill:
  1. Write a function in src/skills/
  2. Register it below with compliance_agent.tool_plain(your_function)
  3. That's it — the agent will use it when appropriate.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
from pydantic_ai import Agent

from compliance_urls import WATCH_LIST
from skills.check_change import check_for_change
from skills.discover_urls import discover_urls
from skills.fetch_page import fetch_compliance_page
from skills.send_alert import send_alert

load_dotenv()

compliance_agent = Agent(
    model="openai:gpt-4o-mini",
    instructions="""You are a teacher licensure compliance monitoring agent.

You monitor US state Department of Education websites for changes to teacher
certification and Praxis exam requirements.

Your skills:
- fetch_compliance_page(url): fetch a page and return its text
- check_for_change(state, subject, url, content): compare against stored snapshot
- send_alert(state, subject, url, summary): send a Telegram notification
- discover_urls(state): use Brave Search to find compliance pages for a state

When asked to run a compliance check:
1. For each relevant state/URL, fetch the page and check for changes
2. If status is 'changed', write a plain-English summary of what likely changed
   and why it matters for teachers, then call send_alert
3. Report what you found

When asked about a state not in the watch list, use discover_urls first.
Always cite the state, subject area, and URL in your response.""",
)

compliance_agent.tool_plain(fetch_compliance_page)
compliance_agent.tool_plain(check_for_change)
compliance_agent.tool_plain(send_alert)
compliance_agent.tool_plain(discover_urls)


WATCH_CONTEXT = "\n".join(
    f"- {state} | {subject}: {url}" for state, subject, url in WATCH_LIST
)


async def run(task: str) -> str:
    full_task = f"{task}\n\nMonitored URLs:\n{WATCH_CONTEXT}"
    result = await compliance_agent.run(full_task)
    return result.output


if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) or "Check all monitored states for compliance changes."
    print(asyncio.run(run(task)))
