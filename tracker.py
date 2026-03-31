"""
AI Job Tracker — Notion Version
Reads unprocessed job links from a Notion database,
extracts structured info via Gemini API, and writes back to Notion.

Requirements:
    pip install requests python-dotenv

Setup:
    1. Copy .env.example to .env and fill in your credentials
    2. Create a Notion integration and connect it to your database
    3. Add a "Job Link" (URL) and "Processed" (Checkbox) column to your DB
    4. Run: python tracker.py
"""

import os
import json
import requests
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
NOTION_TOKEN        = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID  = os.environ["NOTION_DATABASE_ID"]
GEMINI_API_KEY      = os.environ["GEMINI_API_KEY"]

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent"
)

# ── Notion helpers ─────────────────────────────────────────────────────────────

def get_unprocessed_rows() -> list[dict]:
    """Return all Notion DB rows where Processed = false."""
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    payload = {
        "filter": {
            "property": "Processed",
            "checkbox": {"equals": False},
        }
    }
    resp = requests.post(url, headers=NOTION_HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json().get("results", [])


def update_notion_page(page_id: str, job: dict) -> None:
    """Write extracted job fields back to a Notion page."""
    followup = (date.today() + timedelta(days=7)).isoformat()

    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "Company":      {"rich_text": [{"text": {"content": job.get("company", "")}}]},
            "Position":     {"title":     [{"text": {"content": job.get("position", "")}}]},
            "Location":     {"rich_text": [{"text": {"content": job.get("location", "")}}]},
            "Date Applied": {"date":      {"start": date.today().isoformat()}},
            "Status":       {"select":    {"name": job.get("status", "Applied")}},
            "Next Step":    {"rich_text": [{"text": {"content": job.get("next_step", "")}}]},
            "Follow-up":    {"date":      {"start": followup}},
            "Notes":        {"rich_text": [{"text": {"content": job.get("notes", "")}}]},
            "Track":        {"select":    {"name": job.get("track", "PM")}},
            "Processed":    {"checkbox":  True},
        }
    }
    resp = requests.patch(url, headers=NOTION_HEADERS, json=payload)
    resp.raise_for_status()
    print(f"  ✓ Updated: {job.get('company', '?')} — {job.get('position', '?')}")


# ── Gemini extraction ──────────────────────────────────────────────────────────

def extract_job_info(job_url: str) -> dict:
    """
    Ask Gemini to read the public job page and return structured JSON.
    Uses URL context grounding + structured output (application/json).
    """
    today = date.today().strftime("%B %-d, %Y")

    prompt = f"""
Read the public job posting at the URL below and extract the following fields.
Return ONLY valid JSON — no markdown, no explanation.

Schema:
{{
  "company":    "string — company name",
  "position":   "string — exact job title",
  "location":   "string — city/remote/hybrid, empty string if not found",
  "status":     "Applied",
  "next_step":  "Wait for response / follow up in 7 days",
  "notes":      "string — 1-sentence summary of the role",
  "track":      "PM or BA"
}}

Rules:
- "track" = "PM" if product management / product strategy focused;
            "BA" if data / business analysis / analytics focused.
- Keep "notes" to one concise sentence.
- Use empty string "" for any field you cannot find.

URL: {job_url}
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"url_context": {}}],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    resp = requests.post(
        GEMINI_ENDPOINT,
        headers={"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError(f"Gemini returned no candidates. Raw response: {data}")

    raw = candidates[0]["content"]["parts"][0]["text"]
    return json.loads(raw)


# ── Main loop ──────────────────────────────────────────────────────────────────

def main():
    print("🔍 Fetching unprocessed rows from Notion...")
    rows = get_unprocessed_rows()

    if not rows:
        print("✅ Nothing to process.")
        return

    print(f"📋 Found {len(rows)} row(s) to process.\n")

    for row in rows:
        props    = row["properties"]
        page_id  = row["id"]
        job_link = props.get("Job Link", {}).get("url")

        if not job_link:
            print(f"  ⚠ Skipping row {page_id[:8]}… — no Job Link found.")
            continue

        print(f"  → Processing: {job_link[:60]}...")

        try:
            job_info = extract_job_info(job_link)
            update_notion_page(page_id, job_info)
        except json.JSONDecodeError as e:
            print(f"  ✗ JSON parse error: {e}")
        except requests.HTTPError as e:
            print(f"  ✗ HTTP error: {e}")
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")

    print("\n🎉 Done.")


if __name__ == "__main__":
    main()
