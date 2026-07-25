import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

EXTRACTION_PROMPT = """You are an assistant that extracts action items from meeting transcripts.

Read the transcript below and extract every decision and action item mentioned.
For each one, identify:
- task: a clear, concise description of what needs to be done
- owner: the person responsible (use their name as mentioned in the transcript; if unclear, use "Unassigned")
- deadline: any date or timeframe mentioned (if none mentioned, use "No deadline specified")
- priority: "high", "medium", or "low" based on urgency language used

Respond with ONLY a valid JSON array, no other text, no markdown formatting. Example format:
[{{"task": "...", "owner": "...", "deadline": "...", "priority": "..."}}]

Transcript:
{transcript}
"""

def extract_action_items(transcript):
    prompt = EXTRACTION_PROMPT.format(transcript=transcript)
    response = model.generate_content(prompt)
    raw_text = response.text.strip()
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()
    try:
        items = json.loads(raw_text)
        return items
    except json.JSONDecodeError:
        return []