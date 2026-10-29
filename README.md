# FER job alerts

Checks the [FER careers job board](https://karijere.fer.hr/karijere/ponuda_poslova) every 30 minutes
and emails you any new job posts. Runs for free on GitHub Actions.

## How it works

1. Downloads the job board page and pulls out every post (title, summary, link, unique ID).
2. Compares the IDs with `seen.json`, the list of posts it has already seen.
3. Emails you the new ones via Gmail, then adds them to `seen.json`.

The first run (no `seen.json` yet) only saves the current posts and sends no email.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your Gmail address and app password
python main.py --dry-run   # prints the email instead of sending it
python main.py
```

## Configuration

| Name | Where (GitHub) | Required | Meaning |
|---|---|---|---|
| `GMAIL_ADDRESS` | Secret | yes | Gmail account that sends the email |
| `GMAIL_APP_PASSWORD` | Secret | yes | [App password](https://myaccount.google.com/apppasswords) for that account |
| `EMAIL_TO` | Variable | no | Where to send alerts (defaults to `GMAIL_ADDRESS`) |
| `KEYWORDS` | Variable | no | Comma-separated words; only matching posts are emailed, e.g. `junior,student,python,praksa` |
