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

Respond with ONLY a valid JSON array, no other text, no markdown formatting. Example format:
[{{"task": "...", "owner": "...", "deadline_text": "...", "priority": "..."}}]

Transcript:
{transcript}
"""

def parse_deadline(deadline_text):
    if not deadline_text or deadline_text.lower() == "no deadline specified":
        return None
    parsed = dateparser.parse(
        deadline_text,
        settings={"PREFER_DATES_FROM": "future", "RELATIVE_BASE": datetime.now()}
    )
    return parsed.isoformat() if parsed else None

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
        item["deadline_text"] = deadline_text
        item["deadline_date"] = parse_deadline(deadline_text)

    return items