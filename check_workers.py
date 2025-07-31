#!/usr/bin/env python3
import os
import requests
import smtplib
import datetime
from email.mime.text import MIMEText

# Configuration from environment
URL               = "https://solo.ckpool.org/users/bc1qjstetm3fsjnc0d9xuwqv3wlucm9slcm9l9gqxa"
THRESHOLD         = int(os.getenv("THRESHOLD", "3"))
SMTP_SERVER       = "smtp.gmail.com"
SMTP_PORT         = 587
FROM_EMAIL        = os.getenv("EMAIL_USER")
APP_PASSWORD      = os.getenv("EMAIL_PASS")
TO_EMAIL          = os.getenv("EMAIL_TO")
SHEET_WEBHOOK_URL = os.getenv("SHEET_WEBHOOK_URL")

def get_worker_count():
    resp = requests.get(URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return int(data.get("workers", 0))

def send_alert(count):
    body = f"⚠️ Only {count} workers online (threshold={THRESHOLD})"
    msg = MIMEText(body)
    msg["Subject"] = "Swarm ALPHA Worker Alert"
    msg["From"]    = FROM_EMAIL
    msg["To"]      = TO_EMAIL

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(FROM_EMAIL, APP_PASSWORD)
        server.send_message(msg)

def record_alert(count):
    """Post the alert to the Google Sheets Apps Script webhook."""
    now = datetime.datetime.now()
    payload = {
        "date":    now.strftime("%Y-%m-%d"),
        "time":    now.strftime("%H:%M:%S"),
        "workers": count
    }
    try:
        requests.post(SHEET_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        # If it fails, we simply log to stderr; it won't stop the script
        print(f"Failed to record to sheet: {e}")

def main():
    count = get_worker_count()
    if count < THRESHOLD:
        send_alert(count)
        record_alert(count)

if __name__ == "__main__":
    main()
