#!/usr/bin/env python3
import os, requests, smtplib, datetime
from email.mime.text import MIMEText

# ── CONFIG (from GitHub-Actions secrets / env vars) ────────────────
URL = "https://solo.ckpool.org/users/bc1qjstetm3fsjnc0d9xuwqv3wlucm9slcm9l9gqxa"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT   = 587
FROM_EMAIL  = os.getenv("EMAIL_USER")   # e.g. askgenesisone@gmail.com
APP_PASS    = os.getenv("EMAIL_PASS")   # 16-char Gmail App Password
TO_EMAILS   = os.getenv("EMAIL_TO")     # comma-separated list
# ───────────────────────────────────────────────────────────────────

def parse_hashrate(worker: dict) -> float:
    """
    Return hashrate in H/s as float.
    Accepts numeric, string numbers, or strings with K/M/G/T suffix.
    """
    unit = {"k": 1e3, "m": 1e6, "g": 1e9, "t": 1e12}

    for key in ("hashrate1m", "hashrate_1m", "hashrate"):
        raw = str(worker.get(key, "")).strip().lower()
        if raw in ("", "0", "0.0"):
            continue

        # plain number?
        try:
            return float(raw)
        except ValueError:
            pass

        # number with unit suffix (e.g. 1.26t, 821g)
        if raw[-1] in unit:
            try:
                return float(raw[:-1]) * unit[raw[-1]]
            except ValueError:
                pass
    return 0.0  # default if nothing parsed

def fetch_status():
    """Return (offline_ids, online_ids) by examining 1-minute hashrate."""
    js = requests.get(URL, timeout=10).json()

    # Accept workers_info, workers, or worker
    objs = []
    for key in ("workers_info", "workers", "worker"):
        val = js.get(key)
        if isinstance(val, list):
            objs = val
            break
        if isinstance(val, dict):
            objs = list(val.values())
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
    if offline:                     # alert only if ≥1 workers at 0 H/s
        send_email(offline, online)

if __name__ == "__main__":
    main()
