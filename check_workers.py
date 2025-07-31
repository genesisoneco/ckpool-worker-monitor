#!/usr/bin/env python3
import os, requests, smtplib, datetime
from email.mime.text import MIMEText

# ── CONFIG from GitHub-Actions / env vars ──────────────────────────
URL   = "https://solo.ckpool.org/users/bc1qjstetm3fsjnc0d9xuwqv3wlucm9slcm9l9gqxa"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT   = 587
FROM_EMAIL  = os.getenv("EMAIL_USER")        # gmail addr
APP_PASS    = os.getenv("EMAIL_PASS")        # 16-char app-password
TO_EMAILS   = os.getenv("EMAIL_TO")          # comma-separated list
WEBHOOK     = os.getenv("SHEET_WEBHOOK_URL") # Apps-Script URL
# ───────────────────────────────────────────────────────────────────

def parse_hashrate(w):
    """Return float hash-rate in H/s (0 if missing)."""
    for k in ("hashrate1m", "hashrate_1m", "hashrate"):
        v = w.get(k)
        if v not in (None, "", 0):
            try:
                return float(v)
            except ValueError:
                pass            # string like "1.3T", ignore
    return 0.0

def fetch_status():
    """Return (offline_ids, online_ids) based on hashrate1m == 0."""
    js = requests.get(URL, timeout=10).json()

    # Flatten possible layouts
    objs = []
    for key in ("workers_info", "workers"):
        if isinstance(js.get(key), list):
            objs = js[key]
            break
        if isinstance(js.get(key), dict):
            objs = list(js[key].values())
            break

    offline, online = [], []
    for w in objs:
        full  = w.get("worker") or w.get("name") or ""
        wid   = full.split('.')[-1] if '.' in full else full
        hr    = parse_hashrate(w)
        (online if hr > 0 else offline).append(wid)

    return offline, online

def send_email(offline, online):
    body = (
        "⚠️ Swarm ALPHA alert\n\n"
        f"Offline workers ({len(offline)}): {', '.join(offline) or 'None'}\n"
        f"Online  workers ({len(online )}): {', '.join(online ) or 'None'}"
    )
    msg = MIMEText(body)
    msg["Subject"] = "Swarm ALPHA - Offline Worker Alert"
    msg["From"]    = FROM_EMAIL
    msg["To"]      = TO_EMAILS

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
        s.starttls()
        s.login(FROM_EMAIL, APP_PASS)
        s.send_message(msg)

def log_to_sheet(offline, online):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "date_time": now,
        "offline"  : ", ".join(offline),
        "online"   : ", ".join(online)
    }
    try:
        requests.post(WEBHOOK, json=payload, timeout=5)
    except Exception as e:
        print("Webhook error:", e)

def main():
    offline, online = fetch_status()
    if offline:                          # alert ONLY if 1+ workers at 0 H/s
        send_email(offline, online)
        log_to_sheet(offline, online)

if __name__ == "__main__":
    main()
