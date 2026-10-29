# FER job alerts

Checks the [FER careers job board](https://karijere.fer.hr/karijere/ponuda_poslova) every 30 minutes
and emails you any new job posts. Runs for free on GitHub Actions.

## How it works

1. Downloads the job board page and pulls out every post (title, summary, link, unique ID).
2. Compares the IDs with `seen.json`, the list of posts it has already seen.
3. Emails you the new ones via Gmail, then adds them to `seen.json`.

The first run (no `seen.json` yet) only saves the current posts and sends no email.

## Gmail app password (required)

> **Your normal Gmail password will not work.** Gmail only accepts an *app password* here,
> and a wrong password just shows up as `Connection unexpectedly closed`.

1. Turn on [2-Step Verification](https://myaccount.google.com/signinoptions/twosv) for your Google account
   (app passwords don't exist without it).
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords), signed in as
   **the same Gmail account** you'll use as `GMAIL_ADDRESS`.
3. Create an app password (any name, e.g. `fer-job-alerts`) and copy the 16 letters. Spaces don't matter.
4. Test it locally with `python main.py --test-email` (see below) before adding it to GitHub.

## Set up on GitHub

1. Fork or push this repo to GitHub (public repos get unlimited free Actions minutes).
2. Go to **Settings → Secrets and variables → Actions** and add the secrets from the table below.
   If your `.env` works locally, `gh secret set -f .env` copies it over.
3. Go to **Actions → Check for new jobs → Run workflow** to test it. After that it runs by itself
   every 30 minutes; scheduled runs appear in the Actions tab marked *Scheduled*.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your Gmail address and app password
python main.py --test-email   # sends one test email, to check your Gmail login
python main.py --dry-run      # prints the alert email instead of sending it
python main.py
```

## Configuration

| Name | Where (GitHub) | Required | Meaning |
|---|---|---|---|
| `GMAIL_ADDRESS` | Secret | yes | Gmail account that sends the email |
| `GMAIL_APP_PASSWORD` | Secret | yes | [App password](https://myaccount.google.com/apppasswords) for that account |
| `EMAIL_TO` | Variable | no | Where to send alerts (defaults to `GMAIL_ADDRESS`) |
| `KEYWORDS` | Variable | no | Comma-separated words; only matching posts are emailed, e.g. `junior,student,python,praksa` |
