"""Core logic: parse draft files, send via Gmail SMTP, keep a sent log."""
import csv
import mimetypes
import re
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
HERE = Path(__file__).resolve().parent
LOG_PATH = HERE / "sent_log.csv"
LOG_FIELDS = ["timestamp", "source", "id", "company", "to", "subject", "status", "error"]


def parse_drafts(path: Path) -> list[dict]:
    """Parse a markdown file of drafts.

    Each draft looks like:
        ## 3. Company name
        **To:** someone@company.com
        **Subject:** ...
        ```text
        body...
        ```
    """
    text = Path(path).read_text(encoding="utf-8")
    chunks = re.split(r"^## (\d+)\.\s*(.+)$", text, flags=re.M)
    drafts = []
    # re.split with 2 groups -> [pre, num, title, body, num, title, body, ...]
    for i in range(1, len(chunks) - 2, 3):
        num, title, block = chunks[i], chunks[i + 1].strip(), chunks[i + 2]
        to_m = re.search(r"^\*\*To:\*\*\s*(.+)$", block, flags=re.M)
        subj_m = re.search(r"^\*\*Subject:\*\*\s*(.+)$", block, flags=re.M)
        body_m = re.search(r"```text\n(.*?)\n```", block, flags=re.S)
        if not (to_m and subj_m and body_m):
            continue
        to_raw = to_m.group(1).strip()
        to_addr = to_raw.split()[0] if to_raw else ""
        drafts.append({
            "source": Path(path).name,
            "id": int(num),
            "company": title,
            "to": to_addr if EMAIL_RE.match(to_addr) else "",
            "to_raw": to_raw,
            "subject": subj_m.group(1).strip(),
            "body": body_m.group(1).strip(),
        })
    return drafts


def load_log() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    with LOG_PATH.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def sent_key(to: str, subject: str) -> str:
    return f"{to.strip().lower()}|{subject.strip().lower()}"


def already_sent() -> set[str]:
    """(recipient, subject) pairs sent successfully. A follow-up ("Re: ...") is a different
    subject, so it is allowed; the same email is never sent twice."""
    return {sent_key(r["to"], r["subject"]) for r in load_log() if r.get("status") == "sent"}


def first_sent_dates() -> dict[str, str]:
    """recipient -> date of the first successful email (YYYY-MM-DD)."""
    out = {}
    for r in load_log():
        if r.get("status") == "sent":
            out.setdefault(r["to"].strip().lower(), r["timestamp"][:10])
    return out


def sent_today_count() -> int:
    today = datetime.now().date().isoformat()
    return sum(1 for r in load_log() if r.get("status") == "sent" and r["timestamp"].startswith(today))


def append_log(row: dict) -> None:
    new = not LOG_PATH.exists()
    with LOG_PATH.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in LOG_FIELDS})


def build_message(sender: str, sender_name: str, to: str, subject: str, body: str,
                  attachment: Path | None) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = f"{sender_name} <{sender}>" if sender_name else sender
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    if attachment:
        attachment = Path(attachment)
        ctype, _ = mimetypes.guess_type(attachment.name)
        maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
        msg.add_attachment(attachment.read_bytes(), maintype=maintype, subtype=subtype,
                           filename=attachment.name)
    return msg


def connect(sender: str, app_password: str) -> smtplib.SMTP_SSL:
    """Log in to Gmail over SSL. Raises smtplib.SMTPAuthenticationError on bad credentials."""
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context(), timeout=30)
    server.login(sender, app_password.replace(" ", ""))
    return server
