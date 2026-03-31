# 🤖 AI Job Tracker

Stop copying and pasting job descriptions into spreadsheets.  
Paste a link → the tracker reads the page → fills in your database automatically.

Built with **Gemini API** (URL context + structured output) and your choice of **Notion** or **Google Sheets**.

---

## What it does

| Step | What happens |
|------|-------------|
| 1 | You paste a job posting URL into your tracker |
| 2 | Gemini reads the public page using URL context grounding |
| 3 | Returns structured JSON: company, title, location, notes, PM/BA track |
| 4 | Fields are written back to your Notion database or Google Sheet |

Auto-filled fields:
- **Company** / **Position** / **Location**
- **Date Applied** (today)
- **Status** → `Applied`
- **Next Step** → `Follow up in 7 days` with auto-calculated date
- **Notes** → 1-sentence role summary
- **Track** → `PM` or `BA` (classified by Gemini)

---

## Versions

### 🗂️ Notion + Python [`/notion`](./notion/)

Best for: people who want a beautiful, filterable job tracker with full database features.

```
notion/
├── tracker.py          # main script
├── requirements.txt
└── .env.example        # copy to .env and fill in credentials
```

**Setup (5 minutes):**

```bash
# 1. Clone and install
git clone https://github.com/your-username/ai-job-tracker.git
cd ai-job-tracker/notion
pip install -r requirements.txt

# 2. Set up credentials
cp .env.example .env
# Edit .env with your Notion token, database ID, and Gemini API key

# 3. Run
python tracker.py
```

**Notion database columns you need:**

| Column name | Type |
|-------------|------|
| Job Link | URL |
| Company | Text |
| Position | Title |
| Location | Text |
| Date Applied | Date |
| Status | Select |
| Next Step | Text |
| Follow-up | Date |
| Notes | Text |
| Track | Select (`PM` / `BA`) |
| Processed | Checkbox ← script checks this |

> **Tip:** When you add a new job, leave **Processed** unchecked. Run the script and it will fill in everything else.

---

### 📊 Google Sheets + Apps Script [`/google-sheets`](./google-sheets/)

Best for: people who live in Google Workspace and want one-click filling without any local setup.

```
google-sheets/
└── tracker.gs          # paste into Apps Script
```

**Setup (3 minutes):**

1. Open your Google Sheet → **Extensions → Apps Script**
2. Paste the contents of `tracker.gs`
3. Replace `PASTE_YOUR_GEMINI_API_KEY_HERE` with your key
4. Save and refresh the sheet
5. A new **🤖 Job Tracker** menu will appear

**Column layout (A–I):**

```
A: Company | B: Date Applied | C: Job Link ← paste here
D: Next Step | E: Notes | F: Position | G: Status | H: Location | I: Track
```

**Usage:** Paste a link in column C → click **🤖 Job Tracker → Fill this row from link**  
Or use **Fill all empty rows** to batch-process everything at once.

---

## Getting your API keys

**Gemini API key** (free tier available):
→ [Google AI Studio](https://aistudio.google.com/app/apikey)

**Notion integration token:**
1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Create a new integration
3. Open your database in Notion → click `···` → **Add connections** → select your integration
4. Copy the database ID from the URL: `notion.so/workspace/`**`THIS_PART`**`?v=...`

---

## Known limitations

- **Login-gated pages** (some Workday, Greenhouse, Lever links) may fail if the page isn't publicly accessible. Gemini's URL context only works on public URLs.
- **Rate limits:** Gemini free tier allows ~15 requests/minute. The Notion script processes rows sequentially so this is rarely an issue.
- This tool does not store or log your job data anywhere — it's a direct Gemini ↔ Notion/Sheets pipeline.

---

## Why I built this

Job hunting involves a lot of copy-paste busywork. I wanted to focus on applications, not data entry. This took a weekend to build and has saved me hours since — hopefully it helps you too.

---

## Contributing

PRs welcome. Ideas for future versions:
- [ ] Sponsor/visa requirement detection
- [ ] Fit score based on resume keywords
- [ ] Automatic follow-up reminders via email
- [ ] Support for Airtable

---

## License

MIT
