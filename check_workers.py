#!/usr/bin/env python3
import os, requests, smtplib, datetime
from email.mime.text import MIMEText

# ── CONFIG ─────────────────────────────────────────────────────────
URL = "https://solo.ckpool.org/users/bc1qjstetm3fsjnc0d9xuwqv3wlucm9slcm9l9gqxa"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT   = 587
FROM_EMAIL  = os.getenv("EMAIL_USER")   # e.g. askgenesisone@gmail.com
APP_PASS    = os.getenv("EMAIL_PASS")   # 16-char App Password
TO_EMAILS   = os.getenv("EMAIL_TO")     # comma-separated list
# ───────────────────────────────────────────────────────────────────

def parse_hashrate(w):
    """Return hashrate in H/s as float, 0.0 if missing/zero."""
    for k in ("hashrate1m", "hashrate_1m", "hashrate"):
        v = w.get(k)
        if v not in (None, "", 0, "0"):
            try:
                return float(v)
            except ValueError:
                # values like "1.26T" aren't needed here
                pass
    return 0.0

def fetch_status():
    """Return (offline_ids, online_ids) based on 1-minute hashrate."""
    js = requests.get(URL, timeout=10).json()

    # Accept workers_info, workers, or worker
    objs = []
    for key in ("workers_info", "workers", "worker"):
        if isinstance(js.get(key), list):
            objs = js[key]
            break
        if isinstance(js.get(key), dict):
            objs = list(js[key].values())
            break

    offline, online = [], []
    for w in objs:
        full = w.get("workername") or w.get("worker") or w.get("name") or ""
        wid  = full.split(".")[-1] if "." in full else full
        (online if parse_hashrate(w) > 0 else offline).append(wid)

    return offline, online

def send_email(offline, online):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = (
        f"⚠️ Swarm ALPHA alert – {now}\n\n"
        f"Offline workers ({len(offline)}): {', '.join(offline) or 'None'}\n"
        f"Online  workers ({len(online )}): {', '.join(online ) or 'None'}"
    )
    msg = MIMEText(body)
    msg["Subject"] = "Swarm ALPHA – Offline Worker Alert"
    msg["From"]    = FROM_EMAIL
    msg["To"]      = TO_EMAILS

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
        s.starttls()
        s.login(FROM_EMAIL, APP_PASS)
        s.send_message(msg)

def main():
    offline, online = fetch_status()
    if offline:                 # trigger when at least one worker is 0 H/s
        send_email(offline, online)

if __name__ == "__main__":
    main()
