// AI Job Tracker — Google Sheets Version
// Paste this into Extensions → Apps Script in your Google Sheet.
//
// Column layout (configure below if yours differs):
//   A: Company | B: Date Applied | C: Job Link | D: Next Step
//   E: Notes   | F: Position     | G: Status   | H: Location | I: Track

const GEMINI_API_KEY = 'PASTE_YOUR_GEMINI_API_KEY_HERE';

// ── Column indices (1-based) ───────────────────────────────────────────────────
const COL = {
  COMPANY:      1,  // A
  DATE_APPLIED: 2,  // B
  JOB_LINK:     3,  // C
  NEXT_STEP:    4,  // D
  NOTES:        5,  // E
  POSITION:     6,  // F
  STATUS:       7,  // G
  LOCATION:     8,  // H
  TRACK:        9,  // I
};

// ── Menu setup ────────────────────────────────────────────────────────────────
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('🤖 Job Tracker')
    .addItem('Fill this row from link', 'fillCurrentRow')
    .addItem('Fill all empty rows',     'fillAllRows')
    .addToUi();
}

// ── Fill a single row ──────────────────────────────────────────────────────────
function fillCurrentRow() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const row   = sheet.getActiveCell().getRow();
  _processRow(sheet, row);
}

// ── Fill all rows that have a link but no Company yet ─────────────────────────
function fillAllRows() {
  const sheet    = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const lastRow  = sheet.getLastRow();
  let   count    = 0;

  for (let row = 2; row <= lastRow; row++) {
    const link    = sheet.getRange(row, COL.JOB_LINK).getValue();
    const company = sheet.getRange(row, COL.COMPANY).getValue();
    if (link && !company) {
      _processRow(sheet, row);
      count++;
    }
  }

  SpreadsheetApp.getUi().alert(`Done! Processed ${count} row(s).`);
}

// ── Core: call Gemini and write fields ─────────────────────────────────────────
function _processRow(sheet, row) {
  const url = sheet.getRange(row, COL.JOB_LINK).getValue();

  if (!url) {
    SpreadsheetApp.getUi().alert('No link found in column C for this row.');
    return;
  }

  const today    = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'MMMM d, yyyy');
  const followup = _addDays(new Date(), 7);
  const followupStr = Utilities.formatDate(followup, Session.getScriptTimeZone(), 'MMMM d, yyyy');

  const prompt = `
Read the public job posting at the URL below and extract the following fields.
Return ONLY valid JSON — no markdown, no explanation.

{
  "company":   "string",
  "position":  "string",
  "location":  "string",
  "notes":     "string — 1 sentence summary",
  "track":     "PM or BA"
}

Rules:
- "track" = "PM" if product/strategy focused; "BA" if analytics/data focused.
- Use empty string "" for fields you cannot find.

URL: ${url}
`;

  const payload = {
    contents: [{ parts: [{ text: prompt }] }],
    tools: [{ url_context: {} }],
    generationConfig: { responseMimeType: 'application/json' },
  };

  const endpoint =
    'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent';

  let response;
  try {
    response = UrlFetchApp.fetch(endpoint, {
      method:          'post',
      contentType:     'application/json',
      headers:         { 'x-goog-api-key': GEMINI_API_KEY },
      payload:         JSON.stringify(payload),
      muteHttpExceptions: true,
    });
  } catch (e) {
    SpreadsheetApp.getUi().alert('Network error: ' + e.message);
    return;
  }

  const json = JSON.parse(response.getContentText());

  if (!json.candidates || !json.candidates.length) {
    SpreadsheetApp.getUi().alert('Gemini returned no result. Check the link and try again.');
    return;
  }

  let data;
  try {
    data = JSON.parse(json.candidates[0].content.parts[0].text);
  } catch (e) {
    SpreadsheetApp.getUi().alert('Could not parse Gemini response as JSON.');
    return;
  }

  // Write to sheet
  sheet.getRange(row, COL.COMPANY).setValue(data.company   || '');
  sheet.getRange(row, COL.POSITION).setValue(data.position || '');
  sheet.getRange(row, COL.LOCATION).setValue(data.location || '');
  sheet.getRange(row, COL.NOTES).setValue(data.notes       || '');
  sheet.getRange(row, COL.TRACK).setValue(data.track       || '');
  sheet.getRange(row, COL.DATE_APPLIED).setValue(today);
  sheet.getRange(row, COL.STATUS).setValue('Applied');
  sheet.getRange(row, COL.NEXT_STEP).setValue('Follow up by ' + followupStr);
}

// ── Utility ───────────────────────────────────────────────────────────────────
function _addDays(date, days) {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}
