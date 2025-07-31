#!/usr/bin/env python3
import os, requests, smtplib, datetime
from email.mime.text import MIMEText

# ── CONFIG ─────────────────────────────────────────────────────────
URL   = "https://solo.ckpool.org/users/bc1qjstetm3fsjnc0d9xuwqv3wlucm9slcm9l9gqxa"
THRESHOLD = int(os.getenv("THRESHOLD", "3"))

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT   = 587
FROM_EMAIL  = os.getenv("EMAIL_USER")
APP_PASS    = os.getenv("EMAIL_PASS")
TO_EMAILS   = os.getenv("EMAIL_TO")          # comma-separated list
WEBHOOK     = os.getenv("SHEET_WEBHOOK_URL") # Apps-Script URL
# ───────────────────────────────────────────────────────────────────

def parse_hashrate(raw):
    """Return float hashrate in H/s (0 if missing)."""
    for key in ("hashrate1m", "hashrate_1m", "hashrate"):
        v = raw.get(key)
        if v not in (None, "", 0):
            try:
                return float(v)
            except ValueError:
                # string like "1.2T" – ignore
                pass
    return 0.0

def fetch_workers():
    r = requests.get(URL, timeout=10)
    r.raise_for_status()
    js = r.json()

    # Support array or object layouts
    objs = []
    for k in ("workers_info", "workers"):
        if isinstance(js.get(k), list):
            objs = js[k]
            break
        if isinstance(js.get(k), dict):
            objs = list(js[k].values())
            break

    active, offline = [], []
    for w in objs:
        full = w.get("worker") or w.get("name") or ""
        wid  = full.split(".")[-1] if "." in full else full
        hr   = parse_hashrate(w)
        (active if hr > 0 else offline).append(wid)

    return active, offline

def send_email(active, offline):
    body = (
        f"⚠️ ALPHA alert – {len(active)} active / {len(offline)} offline "
        f"(threshold={THRESHOLD})\n\n"
        f"Offline IDs: {', '.join(offline) or 'None'}\n\n"
        f"Active IDs : {', '.join(active)  or 'None'}"
    )
    msg = MIMEText(body)
    msg["Subject"] = "Swarm ALPHA Worker Alert"
    msg["From"]    = FROM_EMAIL
    msg["To"]      = TO_EMAILS

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
        s.starttls()
        s.login(FROM_EMAIL, APP_PASS)
        s.send_message(msg)

def log_to_sheet(active, offline):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "date_time": now,
        "workers"  : f"{len(active)} active / {len(offline)} offline",
        "offline"  : ", ".join(offline)
    }
    try:
        requests.post(WEBHOOK, json=payload, timeout=5)
    except Exception as e:
        print("Webhook error:", e)

def main():
    active, offline = fetch_workers()
    if len(active) < THRESHOLD or offline:       # trigger on count OR any 0-hash worker
        send_email(active, offline)
        log_to_sheet(active, offline)

if __name__ == "__main__":
    main()
