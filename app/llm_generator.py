import os
import base64
import requests
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

# ========== AIpipe Config ==========
AIPIPE_TOKEN = os.getenv("AIPIPE_TOKEN")
AIPIPE_API_BASE = os.getenv("AIPIPE_API_BASE") or "https://openrouter.ai/api/v1"

if not AIPIPE_TOKEN:
    raise ValueError("❌ Missing AIPIPE_TOKEN. Please set it in your environment or .env file.")

# ========== Helper: Call AIpipe ==========
def ai_pipe_generate(prompt: str):
    url = f"{AIPIPE_API_BASE}/responses"
    headers = {"Authorization": f"Bearer {AIPIPE_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-5",
        "input": [
            {"role": "system", "content": "You are a helpful coding assistant that outputs runnable web apps."},
            {"role": "user", "content": prompt}
        ]
    }

    r = requests.post(url, json=payload, headers=headers, timeout=120)
    r.raise_for_status()
    data = r.json()

    # DEBUG: print entire raw response
    print("RAW AIpipe response:", data)

    text = ""

    # Extract from output_text if exists
    if data.get("output_text"):
        text = data["output_text"]

    # Extract from output array
    elif "output" in data:
        for item in data["output"]:
            for c in item.get("content", []):
                if isinstance(c, dict) and "text" in c:
                    text += c["text"]
                elif isinstance(c, str):
                    text += c

    # Extract from choices if exists
    elif "choices" in data:
        for ch in data["choices"]:
            msg = ch.get("message", {})
            content = msg.get("content", "")
            if content:
                text += content

    if not text:
        print("⚠ AIpipe did not return any text in expected fields.")

    return text


# ========== Attachment Handling ==========
TMP_DIR = Path("/tmp/llm_attachments")
TMP_DIR.mkdir(parents=True, exist_ok=True)

def decode_attachments(attachments):
    saved = []
    for att in attachments or []:
        name = att.get("name") or "attachment"
        url = att.get("url", "")
        if not url.startswith("data:"):
            continue
        try:
            header, b64data = url.split(",", 1)
            mime = header.split(";")[0].replace("data:", "")
            data = base64.b64decode(b64data)
            path = TMP_DIR / name
            with open(path, "wb") as f:
                f.write(data)
            saved.append({"name": name, "path": str(path), "mime": mime, "size": len(data)})
        except Exception as e:
            print("Failed to decode attachment", name, e)
    return saved

def summarize_attachment_meta(saved):
    summaries = []
    for s in saved:
        nm, p, mime = s["name"], s["path"], s.get("mime", "")
        try:
            if mime.startswith("text") or nm.endswith((".md", ".txt", ".json", ".csv")):
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    data = f.read(500)
                    preview = data.replace("\n", "\\n")[:500]
                summaries.append(f"- {nm} ({mime}): preview: {preview}")
            else:
                summaries.append(f"- {nm} ({mime}): {s['size']} bytes")
        except Exception as e:
            summaries.append(f"- {nm} ({mime}): (could not read preview: {e})")
    return "\n".join(summaries)

# ========== Utility Helpers ==========
def _strip_code_block(text: str) -> str:
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 2:
            return parts[1].strip()
    return text.strip()

def generate_readme_fallback(brief: str, checks=None, attachments_meta=None, round_num=1):
    checks_text = "\n".join(checks or [])
    att_text = attachments_meta or ""
    return f"""# Auto-generated README (Round {round_num})

**Project brief:** {brief}

**Attachments:**
{att_text}

**Checks to meet:**
{checks_text}

## Setup
1. Open `index.html` in a browser.
2. No build steps required.

## Notes
This README was generated as a fallback (AIpipe did not return an explicit README).
"""

# ========== Main Generation ==========
def generate_app_code(brief: str, attachments=None, checks=None, round_num=1, prev_readme=None):
    saved = decode_attachments(attachments or [])
    attachments_meta = summarize_attachment_meta(saved)

    context_note = ""
    if round_num == 2 and prev_readme:
        context_note = f"\n### Previous README.md:\n{prev_readme}\n\nRevise and enhance this project according to the new brief below.\n"

    base_prompt = f"""
You are a professional web developer assistant.

### Round
{round_num}

### Task
{brief}

{context_note}

### Attachments (if any)
{attachments_meta}

### Evaluation checks
{checks or []}

### Output format rules:
1. Produce a complete web app (HTML/JS/CSS inline if needed) satisfying the brief.
2. Output must contain **two parts only**:
   - index.html (main code)
   - README.md (starts after a line containing exactly: ---README.md---)
3. README.md must include:
   - Overview
   - Setup
   - Usage
   - If Round 2, describe improvements made from previous version.
4. Do not include any commentary outside code or README.
"""

    max_attempts = 2
    response_text = None
    for attempt in range(1, max_attempts + 1):
        print(f"🌐 Using proxy api_base={AIPIPE_API_BASE} with AIPIPE_TOKEN (attempt {attempt})", flush=True)
        text = ai_pipe_generate(base_prompt)

        if text and "---README.md---" in text:
            code_part, readme_part = text.split("---README.md---", 1)
            readme_candidate = _strip_code_block(readme_part)
            if len(readme_candidate.strip()) > 50 and ("# " in readme_candidate.splitlines()[0] or "Overview" in readme_candidate):
                response_text = text
                break
            else:
                print(f"⚠️ README from attempt {attempt} looks insufficient (length {len(readme_candidate)}).", flush=True)
                if attempt < max_attempts:
                    time.sleep(1)
                    continue
        else:
            print(f"⚠️ No README marker found in attempt {attempt}.", flush=True)
            if attempt < max_attempts:
                time.sleep(1)
                continue

    if not response_text:
        print("⚠️ Using fallback app and README because AIpipe did not return a valid response.", flush=True)
        response_text = f"""
<html>
  <head><title>Fallback App</title></head>
  <body>
    <h1>Hello (fallback)</h1>
    <p>This app was generated as a fallback because AIpipe failed. Brief: {brief}</p>
  </body>
</html>

---README.md---
{generate_readme_fallback(brief, checks, attachments_meta, round_num)}
"""

    # Parse final response
    if "---README.md---" in response_text:
        code_part, readme_part = response_text.split("---README.md---", 1)
        code_part = _strip_code_block(code_part)
        readme_part = _strip_code_block(readme_part)
        if len(readme_part.strip()) < 20:
            readme_part = generate_readme_fallback(brief, checks, attachments_meta, round_num)
    else:
        code_part = _strip_code_block(response_text)
        readme_part = generate_readme_fallback(brief, checks, attachments_meta, round_num)

    files = {"index.html": code_part, "README.md": readme_part}
    return {"files": files, "attachments": saved}
