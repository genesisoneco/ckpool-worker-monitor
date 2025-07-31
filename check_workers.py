#!/usr/bin/env python3
"""
Swarm-ALPHA worker monitor
Version 2025-07-31-D   – HTML mail, bold red offline IDs
"""

import os, requests, smtplib, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ── CONFIG (GitHub-Actions secrets) ───────────────────────────────
URL = "https://solo.ckpool.org/users/bc1qjstetm3fsjnc0d9xuwqv3wlucm9slcm9l9gqxa"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT   = 587
FROM_EMAIL  = os.getenv("EMAIL_USER")     # gmail address
APP_PASS    = os.getenv("EMAIL_PASS")     # 16-char App Password
TO_EMAILS   = os.getenv("EMAIL_TO")       # comma-separated list
SUPPORT_EMAIL = "askgenesisone@gmail.com"
# ──────────────────────────────────────────────────────────────────


def parse_hashrate(w: dict) -> float:
    """Return hashrate in H/s (handles K/M/G/T suffix)."""
    units = {"k": 1e3, "m": 1e6, "g": 1e9, "t": 1e12}
    for key in ("hashrate1m", "hashrate_1m", "hashrate"):
        raw = str(w.get(key, "")).strip().lower()
        if raw in ("", "0", "0.0"):
            continue
        try:
            return float(raw)
        except ValueError:
            if raw[-1] in units:
                try:
                    return float(raw[:-1]) * units[raw[-1]]
                except ValueError:
                    pass
    return 0.0


def fetch_status():
    js = requests.get(URL, timeout=10).json()
    objs = []
    for key in ("workers_info", "workers", "worker"):
        val = js.get(key)
        if isinstance(val, list):
            objs = val; break
        if isinstance(val, dict):
            objs = list(val.values()); break

    offline, online = [], []
    for w in objs:
        name = (w.get("workername") or w.get("worker") or
                w.get("name") or "")
        wid  = name.split(".")[-1] if "." in name else name
        (online if parse_hashrate(w) > 0 else offline).append(wid)
    return offline, online


def send_email(offline, online):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Plain text (fallback) ─────────────────────────────────────
    text_body = (
        f"⚠️ Swarm ALPHA alert — {now}\n\n"
        f"Offline workers ({len(offline)}): {', '.join(offline) or 'None'}\n"
        f"Online  workers ({len(online )}): {', '.join(online ) or 'None'}\n\n"
        "ACTION REQUIRED:\n"
        "• Check plugs and network cables.\n"
        "• Verify ASIC miner temperature.\n"
        f"• For help, e-mail {SUPPORT_EMAIL}."
    )

    # ── HTML body ────────────────────────────────────────────────
    html_offline = ", ".join(
        f'<span style="font-weight:bold;color:#e00;">{wid}</span>'
        for wid in offline
    ) or "None"

    html_online = ", ".join(online) or "None"

    html_body = f"""
    <html><body style="font-family:Arial,Helvetica,sans-serif;color:#fff;
                       background:#000;padding:1rem;">
      <h2 style="margin-top:0;">⚠️ Swarm ALPHA alert — {now}</h2>

      <p style="font-size:1.25rem;">
        <strong>Offline workers ({len(offline)}):</strong> {html_offline}<br>
        <strong>Online  workers ({len(online )}):</strong> {html_online}
      </p>

      <p style="font-size:1.1rem;margin-top:1.5rem;">
        🚨 <strong>Action required:</strong><br>
        • Check that power plugs and network cables are secure.<br>
        • Verify the ASIC miner hasn’t overheated.<br>
        • If over-temperature is suspected, e-mail
          <a href="mailto:{SUPPORT_EMAIL}" style="color:#0af;">
            {SUPPORT_EMAIL}
          </a> for immediate assistance.
      </p>
    </body></html>
    """

    msg           = MIMEMultipart("alternative")
    msg["Subject"]= "Swarm ALPHA – Offline Worker Alert"
    msg["From"]   = FROM_EMAIL
    msg["To"]     = TO_EMAILS
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
        s.starttls()
        s.login(FROM_EMAIL, APP_PASS)
        s.send_message(msg)


def main():
    offline, online = fetch_status()
    if offline:                   # send mail only if something is offline
        send_email(offline, online)


if __name__ == "__main__":
    main()
