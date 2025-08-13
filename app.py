import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx

# Twilio
from twilio.twiml.messaging_response import MessagingResponse

# ---- Load env ----
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")  # optional: for signature validation
BROWSERBASE_API_KEY = os.getenv("BROWSERBASE_API_KEY")          # needed if using browser automation
BROWSERBASE_PROJECT_ID = os.getenv("BROWSERBASE_PROJECT_ID")    # optional, if your account uses projects
USE_BROWSERBASE = os.getenv("USE_BROWSERBASE", "true").lower() == "true"

# Canvas (fast path if you can get a token)
CANVAS_BASE_URL = os.getenv("CANVAS_BASE_URL")     # e.g. "https://canvas.instructure.com"
CANVAS_TOKEN = os.getenv("CANVAS_TOKEN")           # user-scoped access token

# Gmail (placeholder for later)
GMAIL_ACCESS_TOKEN = os.getenv("GMAIL_ACCESS_TOKEN")  # demo token if you wire it

app = FastAPI()


# -----------------------
# Simple in-memory store (demo)
# -----------------------
REMINDERS = []  # [{text, when_iso, phone}]
ASSIGNMENT_CACHE = {}  # phone -> list[Assignment]


class Assignment(BaseModel):
    title: str
    course: Optional[str] = None
    due: Optional[str] = None  # ISO8601 or human string
    url: Optional[str] = None


# -----------------------
# OpenAI helpers
# -----------------------
async def ai_intent_and_slots(user_text: str) -> dict:
    """
    Very small router using GPT to detect what the user wants.
    Returns a dict with: intent in {"CHECK_ASSIGNMENTS","SET_REMINDER","CHECK_EMAIL","HELP"}
    and extracted slots.
    """
    prompt = f"""
You are an intent router for a student assistant over SMS.
Return strict JSON. Fields:
- intent: one of ["CHECK_ASSIGNMENTS","SET_REMINDER","CHECK_EMAIL","HELP"]
- when: ISO8601 or human phrase (optional)
- subject: short text (optional)

User: "{user_text}"
JSON:
"""
    # Using OpenAI Responses API-style call (works with gpt-4o-mini)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Return only valid JSON. No extra text."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
            },
        )
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"]
    try:
        data = json.loads(content)
    except Exception:
        data = {"intent": "HELP"}
    return data


async def ai_nice_reply(summary_bullets: List[str]) -> str:
    """Turn bullet facts into a friendly, short SMS response."""
    text = "• " + "\n• ".join(summary_bullets)
    prompt = f"Rewrite these bullets into a concise, friendly SMS (<= 600 chars):\n{text}"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You write concise, friendly SMS replies."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.4,
            },
        )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


# -----------------------
# Canvas REST API path (fastest if available)
# -----------------------
async def fetch_canvas_assignments() -> List[Assignment]:
    """Fetch upcoming assignments via Canvas API if token/base URL provided."""
    if not (CANVAS_BASE_URL and CANVAS_TOKEN):
        return []

    # Example: list courses then upcoming assignments per course
    headers = {"Authorization": f"Bearer {CANVAS_TOKEN}"}
    out: List[Assignment] = []

    async with httpx.AsyncClient(timeout=30) as client:
        # get courses
        cr = await client.get(f"{CANVAS_BASE_URL}/api/v1/courses?enrollment_state=active", headers=headers)
        cr.raise_for_status()
        courses = cr.json()

        # for each course, fetch assignments due soon
        for c in courses[:10]:
            course_name = c.get("name")
            course_id = c.get("id")
            ar = await client.get(f"{CANVAS_BASE_URL}/api/v1/courses/{course_id}/assignments", headers=headers)
            if ar.status_code != 200:
                continue
            for a in ar.json():
                due_at = a.get("due_at")  # ISO date string or None
                if due_at:
                    out.append(
                        Assignment(
                            title=a.get("name"),
                            course=course_name,
                            due=due_at,
                            url=a.get("html_url"),
                        )
                    )
    return out


# -----------------------
# Browserbase automation path (works with any LMS UI)
# -----------------------
BB_RUN_ENDPOINT = "https://api.browserbase.com/v1/automation/run"

PLAYWRIGHT_JS_TEMPLATE = """
const { chromium } = require('playwright');

module.exports = async ({ context }) => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // 1) Go to login page
  await page.goto(process.env.LMS_LOGIN_URL, { waitUntil: 'domcontentloaded' });

  // 2) Fill credentials (for demo; use OAuth if your LMS supports it)
  await page.fill(process.env.LMS_USER_SELECTOR, process.env.LMS_USERNAME);
  await page.fill(process.env.LMS_PASS_SELECTOR, process.env.LMS_PASSWORD);
  await page.click(process.env.LMS_SUBMIT_SELECTOR);

  // 3) Wait for navigation and go to assignments page
  await page.waitForLoadState('networkidle', { timeout: 30000 });
  await page.goto(process.env.LMS_ASSIGNMENTS_URL, { waitUntil: 'domcontentloaded' });

  // 4) Scrape assignments (adjust selectors to your LMS)
  const items = await page.$$eval(process.env.LMS_ASSIGNMENT_ITEM_SEL, (els) => {
    const getText = (el, sel) => {
      const n = el.querySelector(sel);
      return n ? n.textContent.trim() : null;
    };
    const getHref = (el, sel) => {
      const n = el.querySelector(sel);
      return n && n.getAttribute('href') ? n.getAttribute('href') : null;
    };
    return els.map(el => ({
      title: getText(el, process.env.LMS_ASSIGNMENT_TITLE_SEL),
      due: getText(el, process.env.LMS_ASSIGNMENT_DUE_SEL),
      url: getHref(el, process.env.LMS_ASSIGNMENT_LINK_SEL),
      course: getText(el, process.env.LMS_ASSIGNMENT_COURSE_SEL)
    }));
  });

  return { assignments: items };
};
"""

async def fetch_assignments_via_browserbase(lms_env: dict) -> List[Assignment]:
    """
    Calls Browserbase 'automation/run' with a JS Playwright script.
    lms_env: environment variables/values for selectors & URLs.
    """
    if not BROWSERBASE_API_KEY:
        return []

    payload = {
        "projectId": BROWSERBASE_PROJECT_ID,  # optional if your account requires it
        "language": "javascript",
        "script": PLAYWRIGHT_JS_TEMPLATE,
        "env": lms_env,  # sent as process.env.* to the script
        # You can also set timeouts, region, or proxy settings if needed.
    }

    headers = {
        "Authorization": f"Bearer {BROWSERBASE_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(BB_RUN_ENDPOINT, headers=headers, json=payload)
        if resp.status_code != 200:
            return []
        data = resp.json()
        # Expecting { result: { assignments: [...] } }  — adjust if your account returns { logs, result, ... }
        result = (data.get("result") or {}).get("assignments") or []
        return [Assignment(**a) for a in result if a.get("title")]


# -----------------------
# Email summarization (stub for later)
# -----------------------
async def summarize_recent_email() -> str:
    # For a 2–3 day MVP, you can hard-wire a demo response
    # or implement Gmail API quickstart and replace this.
    if not GMAIL_ACCESS_TOKEN:
        return "Email integration not connected yet. (Demo: 2 unread emails from Prof. Smith re: lab report; Career Center newsletter.)"
    # TODO: implement Gmail read + summarize with OpenAI
    return "Summarized your latest emails. (Replace stub with Gmail Graph calls.)"


# -----------------------
# Reminder scheduling (demo)
# -----------------------
def parse_when_to_iso(when_str: Optional[str]) -> Optional[str]:
    if not when_str:
        return None
    # naive: 'tonight 8pm' -> now date w/ 20:00
    lower = when_str.lower()
    now = datetime.utcnow()
    if "tonight" in lower:
        return (now.replace(hour=20, minute=0, second=0, microsecond=0)).isoformat()
    if "tomorrow" in lower:
        t = now + timedelta(days=1)
        return t.replace(hour=9, minute=0, second=0, microsecond=0).isoformat()
    # fallback: just store the phrase
    return when_str

def add_reminder(phone: str, subject: str, when_str: Optional[str]) -> str:
    when_iso = parse_when_to_iso(when_str)
    REMINDERS.append({"text": subject or "Study session", "when_iso": when_iso, "phone": phone})
    return f"Okay, I'll remind you: '{subject or 'Study'}' at {when_iso or when_str or 'the set time'}."


# -----------------------
# Twilio webhook
# -----------------------
@app.post("/sms", response_class=PlainTextResponse)
async def sms_webhook(request: Request):
    form = await request.form()
    body = (form.get("Body") or "").strip()
    from_phone = form.get("From") or "unknown"

    # Route with AI
    intent = await ai_intent_and_slots(body)
    action = intent.get("intent", "HELP")

    if action == "SET_REMINDER":
        reply = add_reminder(from_phone, intent.get("subject"), intent.get("when"))
        twiml = MessagingResponse()
        twiml.message(reply)
        return PlainTextResponse(str(twiml))

    elif action == "CHECK_EMAIL":
        summary = await summarize_recent_email()
        twiml = MessagingResponse()
        twiml.message(summary)
        return PlainTextResponse(str(twiml))

    elif action == "CHECK_ASSIGNMENTS":
        bullets: List[str] = []
        assignments: List[Assignment] = []

        # 1) Try Canvas API first (fast & reliable)
        assignments = await fetch_canvas_assignments()

        # 2) If not available, fall back to Browserbase scraping
        if not assignments and USE_BROWSERBASE:
            # Replace these with your LMS URLs & selectors (see .env template below)
            lms_env = {
                "LMS_LOGIN_URL": os.getenv("LMS_LOGIN_URL"),
                "LMS_ASSIGNMENTS_URL": os.getenv("LMS_ASSIGNMENTS_URL"),
                "LMS_USER_SELECTOR": os.getenv("LMS_USER_SELECTOR"),
                "LMS_PASS_SELECTOR": os.getenv("LMS_PASS_SELECTOR"),
                "LMS_SUBMIT_SELECTOR": os.getenv("LMS_SUBMIT_SELECTOR"),
                "LMS_USERNAME": os.getenv("LMS_USERNAME"),
                "LMS_PASSWORD": os.getenv("LMS_PASSWORD"),

                # Scraping selectors (per-assignment item and sub-elements)
                "LMS_ASSIGNMENT_ITEM_SEL": os.getenv("LMS_ASSIGNMENT_ITEM_SEL"),
                "LMS_ASSIGNMENT_TITLE_SEL": os.getenv("LMS_ASSIGNMENT_TITLE_SEL"),
                "LMS_ASSIGNMENT_DUE_SEL": os.getenv("LMS_ASSIGNMENT_DUE_SEL"),
                "LMS_ASSIGNMENT_LINK_SEL": os.getenv("LMS_ASSIGNMENT_LINK_SEL"),
                "LMS_ASSIGNMENT_COURSE_SEL": os.getenv("LMS_ASSIGNMENT_COURSE_SEL", ""),
            }
            assignments = await fetch_assignments_via_browserbase(lms_env)

        if not assignments:
            twiml = MessagingResponse()
            twiml.message("I couldn't find upcoming assignments yet. Try connecting Canvas (token) or set LMS selectors.")
            return PlainTextResponse(str(twiml))

        # cache & format
        ASSIGNMENT_CACHE[from_phone] = assignments
        for a in assignments[:6]:
            due_txt = a.due or "no due date"
            course = f" · {a.course}" if a.course else ""
            bullets.append(f"{a.title}{course} — due {due_txt}")

        nice = await ai_nice_reply(bullets)
        twiml = MessagingResponse()
        twiml.message(nice)
        return PlainTextResponse(str(twiml))

    # HELP or fallback
    twiml = MessagingResponse()
    twiml.message("Try: 'what's due this week', 'set reminder to study calc at 8pm', or 'summarize my email'.")
    return PlainTextResponse(str(twiml))


@app.get("/")
def health():
    return {"ok": True}
