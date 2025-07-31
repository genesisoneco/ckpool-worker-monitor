#!/usr/bin/env python3
"""
Swarm-ALPHA worker monitor
Version 2025-07-31-B   ← check the Actions log for this banner
"""

import os, requests, smtplib, datetime
from email.mime.text import MIMEText

print("SCRIPT VERSION 2025-07-31-B")          # ← debug banner

# ── CONFIG (all via GitHub-Actions secrets) ───────────────────────
URL = "https://solo.ckpool.org/users/bc1qjstetm3fsjnc0d9xuwqv3wlucm9slcm9l9gqxa"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT   = 587
FROM_EMAIL  = os.getenv("EMAIL_USER")   # e.g. askgenesisone@gmail.com
APP_PASS    = os.getenv("EMAIL_PASS")   # 16-char Gmail App Password
TO_EMAILS   = os.getenv("EMAIL_TO")     # comma-separated list
# ───────────────────────────────────────────────────────────────────


def parse_hashrate(worker: dict) -> float:
    """Return hashrate in H/s (float). Accepts K/M/G/T suffixes."""
    units = {"k": 1e3, "m": 1e6, "g": 1e9, "t": 1e12}

    for key in ("hashrate1m", "hashrate_1m", "hashrate"):
        raw = str(worker.get(key, "")).strip().lower()
        if raw in ("", "0", "0.0"):
            continue

        # plain number?
        try:
            return float(raw)
        except ValueError:
            pass

        # number with unit suffix
        if raw[-1] in units:
            try:
                return float(raw[:-1]) * units[raw[-1]]
            except ValueError:
                pass
    return 0.0


def fetch_status():
    """Return (offline_ids, online_ids) using 1-minute hashrate."""
    js = requests.get(URL, timeout=10).json()

    # The pool may use workers_info, workers, or worker
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
        hr   = parse_hashrate(w)

        print("DEBUG", wid, "raw:", w.get("hashrate1m") or w.get("hashrate_1m") or w.get("hashrate"), "→", hr)  # ← per-worker debug

        (online if hr > 0 else offline).append(wid)

    return offline, online


def send_email(offline, online):
    now  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
    print("DEBUG offline:", offline, "online:", online)            # ← summary debug
    if offline:
        send_email(offline, online)


if __name__ == "__main__":
    main()
