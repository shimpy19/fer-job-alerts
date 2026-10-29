"""Check the FER careers job board and email new job posts."""

import json
import os
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

URL = "https://karijere.fer.hr/karijere/ponuda_poslova"
SEEN_FILE = Path(__file__).parent / "seen.json"
ENV_FILE = Path(__file__).parent / ".env"
HEADERS = {"User-Agent": "Mozilla/5.0 (fer-job-alerts personal job notifier)"}


def load_env_file():
    """Load KEY=value lines from .env into os.environ (for local runs)."""
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def fetch_page():
    response = requests.get(URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def parse_jobs(html):
    """Return a list of jobs: {"id", "title", "url", "summary"}."""
    soup = BeautifulSoup(html, "html.parser")
    jobs = {}
    for link in soup.select("h5 a[href]"):
        href = link["href"]
        # Each post's link looks like /karijere/ponuda_poslova?@=33w4u#news_171622
        job_id = parse_qs(urlparse(href).query).get("@", [None])[0]
        if not job_id:
            continue
        card = link.find_parent(class_="card") or link.parent
        lead = card.select_one(".card-content, .lead")
        jobs[job_id] = {
            "id": job_id,
            "title": link.get_text(strip=True),
            "url": urljoin(URL, href),
            "summary": lead.get_text(" ", strip=True) if lead else "",
        }
    return list(jobs.values())


def load_seen():
    if not SEEN_FILE.exists():
        return None
    return set(json.loads(SEEN_FILE.read_text()))


def save_seen(ids):
    SEEN_FILE.write_text(json.dumps(sorted(ids), indent=2) + "\n")


def matches_keywords(job, keywords):
    if not keywords:
        return True
    text = f"{job['title']} {job['summary']}".lower()
    return any(k in text for k in keywords)


def build_email(jobs, sender, recipient):
    msg = EmailMessage()
    noun = "novi posao" if len(jobs) == 1 else "nova posla" if len(jobs) < 5 else "novih poslova"
    msg["Subject"] = f"FER karijere: {len(jobs)} {noun}"
    msg["From"] = sender
    msg["To"] = recipient

    lines = []
    for job in jobs:
        summary = job["summary"]
        if len(summary) > 300:
            summary = summary[:300].rsplit(" ", 1)[0] + "…"
        lines += [job["title"], summary, job["url"], ""]
    lines.append(f"Sve ponude: {URL}")
    msg.set_content("\n".join(lines))
    return msg


def get_credentials():
    sender = os.environ.get("GMAIL_ADDRESS", "").strip()
    # App passwords are shown as "abcd efgh ijkl mnop"; Gmail wants them without spaces.
    password = "".join(os.environ.get("GMAIL_APP_PASSWORD", "").split())
    recipient = os.environ.get("EMAIL_TO", "").strip() or sender
    return sender, password, recipient


def send_email(msg, sender, password):
    if not sender or not password:
        sys.exit("GMAIL_ADDRESS and GMAIL_APP_PASSWORD must both be set.")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
    except (smtplib.SMTPAuthenticationError, smtplib.SMTPServerDisconnected) as e:
        # Gmail usually just drops the connection when the login is wrong.
        sys.exit(
            f"Gmail login failed ({type(e).__name__}). Check that GMAIL_ADDRESS is the Gmail "
            f"account the app password was created for, and that GMAIL_APP_PASSWORD is the "
            f"16-letter app password (not your normal password)."
        )


def send_test_email():
    sender, password, recipient = get_credentials()
    msg = EmailMessage()
    msg["Subject"] = "FER karijere: test email"
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(f"If you can read this, email alerts work.\n\n{URL}")
    send_email(msg, sender, password)
    print(f"Test email sent to {recipient}.")


def main():
    dry_run = "--dry-run" in sys.argv
    load_env_file()

    if "--test-email" in sys.argv:
        send_test_email()
        return

    jobs = parse_jobs(fetch_page())
    if not jobs:
        # Probably a site redesign; fail loudly so GitHub emails you about it.
        sys.exit("Found 0 jobs on the page - the HTML structure may have changed.")
    print(f"Found {len(jobs)} jobs on the page.")

    current_ids = {job["id"] for job in jobs}
    seen = load_seen()

    if seen is None:
        print("First run: saving current jobs without sending an email.")
        if not dry_run:
            save_seen(current_ids)
        return

    new_jobs = [job for job in jobs if job["id"] not in seen]
    keywords = [k.strip().lower() for k in os.environ.get("KEYWORDS", "").split(",") if k.strip()]
    to_notify = [job for job in new_jobs if matches_keywords(job, keywords)]
    print(f"{len(new_jobs)} new, {len(to_notify)} matching keywords.")

    if to_notify:
        sender, password, recipient = get_credentials()
        msg = build_email(to_notify, sender, recipient)
        if dry_run:
            print(f"--- Would send to {recipient}: {msg['Subject']}\n{msg.get_content()}")
        else:
            send_email(msg, sender, password)
            print(f"Email sent to {recipient}.")

    # Saved only after the email succeeds, so a failed send is retried next run.
    if new_jobs and not dry_run:
        save_seen(seen | current_ids)


if __name__ == "__main__":
    main()
