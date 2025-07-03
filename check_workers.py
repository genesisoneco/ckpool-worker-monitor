#!/usr/bin/env python3
import os, requests, smtplib
from email.mime.text import MIMEText

URL         = "https://solo.ckpool.org/users/bc1qj77y5emr5xv6jrqn940wn0uk58afya82je7uu5"
THRESHOLD   = int(os.getenv("THRESHOLD", "10"))
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT   = 587
FROM_EMAIL  = os.getenv("EMAIL_USER")
APP_PASSWORD= os.getenv("EMAIL_PASS")
TO_EMAIL    = os.getenv("EMAIL_TO")

def get_worker_count():
    resp = requests.get(URL, timeout=10)
    return int(resp.json().get("workers", 0))

def send_alert(cnt):
    body = f"⚠️ Only {cnt} workers online (threshold={THRESHOLD})"
    msg = MIMEText(body)
    msg["Subject"] = "Swarm ALPHA Worker Alert"
    msg["From"]    = FROM_EMAIL
    msg["To"]      = TO_EMAIL
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
        s.starttls()
        s.login(FROM_EMAIL, APP_PASSWORD)
        s.send_message(msg)

if __name__=="__main__":
    c = get_worker_count()
    if c < THRESHOLD:
        send_alert(c)
