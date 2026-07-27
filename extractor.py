import os
import json
import dateparser
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-flash-latest")

EXTRACTION_PROMPT = """You are an assistant that extracts action items from meeting transcripts.

Read the transcript below and extract every decision and action item mentioned.

For each one, identify:
- task: a clear, concise description of what needs to be done
- owner: the person responsible (use their name as mentioned in the transcript; if unclear, use "Unassigned")
- deadline_text: the deadline exactly as mentioned in the transcript (e.g. "Friday", "next week", "by Aug 5"). If none mentioned, use "No deadline specified"
- priority: "high", "medium", or "low" based on urgency language used
- category: classify as "meeting" (a task tied to a scheduled meeting/call), "email" (something that needs to be sent/communicated to someone), or "todo" (a general task with no communication or meeting component)

Respond with ONLY a valid JSON array, no other text, no markdown formatting.

Example:
[
  {
    "task": "...",
    "owner": "...",
    "deadline_text": "...",
    "priority": "...",
    "category": "..."
  }
]

Transcript:
{transcript}
"""


def parse_deadline(deadline_text):
    if not deadline_text or deadline_text.lower() == "no deadline specified":
        return None

    parsed = dateparser.parse(
        deadline_text,
        settings={
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": datetime.now()
        }
    )

    return parsed.isoformat() if parsed else None


def compute_confidence(owner, deadline_text, priority):
    score = 55

    if owner != "Unassigned":
        score += 20

    if deadline_text != "No deadline specified":
        score += 20

    if priority in ("high", "low"):
        score += 5

    return min(score, 99)


def extract_action_items(transcript):
    prompt = EXTRACTION_PROMPT.format(transcript=transcript)

    response = model.generate_content(prompt)

    raw_text = response.text.strip()
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        items = json.loads(raw_text)
    except json.JSONDecodeError:
        return []

    for item in items:
        deadline_text = item.get("deadline_text", "No deadline specified")
        owner = item.get("owner", "Unassigned")
        priority = item.get("priority", "medium")

        item["deadline_text"] = deadline_text
        item["deadline_date"] = parse_deadline(deadline_text)

        if item.get("category") not in ["meeting", "email", "todo"]:
            item["category"] = "todo"

        item["confidence"] = compute_confidence(
            owner,
            deadline_text,
            priority
        )

    return items