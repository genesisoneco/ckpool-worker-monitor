#!/usr/bin/env python3
import os, requests, smtplib, datetime, json
from email.mime.text import MIMEText

# ─── CONFIG FROM ENV ──────────────────────────────────────────────────────────
URL               = "https://solo.ckpool.org/users/bc1qjstetm3fsjnc0d9xuwqv3wlucm9slcm9l9gqxa"
THRESHOLD         = int(os.getenv("THRESHOLD", "3"))
SMTP_SERVER       = "smtp.gmail.com"
SMTP_PORT         = 587
FROM_EMAIL        = os.getenv("EMAIL_USER")
APP_PASSWORD      = os.getenv("EMAIL_PASS")
TO_EMAIL          = os.getenv("EMAIL_TO")          # comma-separated list
SHEET_WEBHOOK_URL = os.getenv("SHEET_WEBHOOK_URL") # Google Apps Script URL
# ──────────────────────────────────────────────────────────────────────────────

def fetch_workers():
    """Return tuple: (active_ids, offline_ids)."""
    r = requests.get(URL, timeout=10)
    r.raise_for_status()
    js = r.json()

    # Support both array and object formats
    raw = []
    if isinstance(js.get("workers_info"), list):
        raw = js["workers_info"]
    elif isinstance(js.get("workers_info"), dict):
        raw = list(js["workers_info"].values())
    elif isinstance(js.get("workers"), list):
        raw = js["workers"]
    elif isinstance(js.get("workers"), dict):
        raw = list(js["workers"].values())

    active, offline = [], []
    for w in raw:
        full   = w.get("worker") or w.get("name") or ""
        wid    = full.split('.')[-1] if '.' in full else full
        hr1m   = w.get("hashrate1m") or w.get("hashrate", 0)
        if hr1m and hr1m > 0:
            active.append(wid)
        else:
            offline.append(wid)
    return active, offline

def send_alert(active, offline):
    body_lines = [
        f"⚠️ Worker alert – {len(active)} active / {len(offline)} offline (threshold={THRESHOLD})",
        "",
        "Offline IDs:",
        ", ".join(offline) if offline else "None",
        "",
        "Active IDs:",
        ", ".join(active) if active else "None"
    ]
    body = "\n".join(body_lines)

    msg = MIMEText(body)
    msg["Subject"] = "Swarm ALPHA Worker Alert"
    msg["From"]    = FROM_EMAIL
    msg["To"]      = TO_EMAIL

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
        s.starttls()
        s.login(FROM_EMAIL, APP_PASSWORD)
        s.send_message(msg)

def record_alert(active, offline):
    now = datetime.datetime.now()
    payload = {
        "date":    now.strftime("%Y-%m-%d"),
        "time":    now.strftime("%H:%M:%S"),
        "workers": f"{len(active)} active / {len(offline)} offline",
        "offline": ", ".join(offline)
    }
    try:
        requests.post(SHEET_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        print("Webhook error:", e)

def main():
    active, offline = fetch_workers()
    if len(active) < THRESHOLD or offline:     # trigger if below count OR any offline
        send_alert(active, offline)
        record_alert(active, offline)

if __name__ == "__main__":
    main()
