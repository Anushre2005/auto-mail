"""Automatic follow-up engine.

For every first email you sent, it sends up to 3 follow-ups, 2 days apart, but only if nobody
from that company has replied. Each follow-up goes out on a weekday morning (8:00-10:30) in
the recipient's own time zone, as a reply in the same Gmail thread.

Run by Windows Task Scheduler every hour in the evening (India time):
    python followup_engine.py run            # check replies, send what is due
    python followup_engine.py run --dry-run  # show what would be sent, send nothing
    python followup_engine.py status         # print the state of every sequence
"""
import email
import email.header
import imaplib
import json
import os
import random
import re
import sys
import time
from datetime import date, datetime, timedelta
from email.utils import make_msgid, parseaddr
from pathlib import Path
from zoneinfo import ZoneInfo

import email_core as core

HERE = Path(__file__).resolve().parent
SEQ_PATH = HERE / "sequences.json"
IN_CLOUD = bool(os.environ.get("GITHUB_ACTIONS"))
# the cloud autopilot writes followup_engine.log; once the cloud is set up, the laptop keeps its own log
ENGINE_LOG = HERE / ("followup_engine.log" if IN_CLOUD or not (HERE / ".git").exists() else "followup_engine_local.log")
ENV_PATH = HERE / ".env"
IST = ZoneInfo("Asia/Kolkata")

GENERIC_LOCALPARTS = {"hello", "hi", "hey", "info", "contact", "support", "careers", "jobs", "admin", "hr",
                      "team", "data", "press", "hiring", "sales", "office", "help", "inquiries"}
EXACT_MATCH_DOMAINS = ("gmail.com", "outlook.com", "yahoo.com", "hotmail.com", ".edu")
DEFAULTS = {
    "interval_days": 2,          # days between steps
    "send_window": [8, 0, 10, 0],  # default: 8:00-10:00 AM their time (see SEND_WINDOWS for exceptions)
    "max_per_run": 12,
    "max_per_day": 25,
    "max_new_per_day": 10,      # brand-new first emails per day (follow-ups not counted)
    "paused": False,
}

# When an email may go out, in the person's own time: from 8:00 AM until the deadline for their region.
DEFAULT_WINDOW = (8, 0, 10, 0)          # USA, Europe and everywhere else: before 10 AM
SEND_WINDOWS = {
    "Asia/Kolkata": (8, 0, 11, 0),      # India: before 11 AM
}


def window_for(tz: str) -> tuple:
    return SEND_WINDOWS.get(tz, DEFAULT_WINDOW)


CITY_TZ = [  # keyword in company/city text -> time zone
    ("india", "Asia/Kolkata"), ("mumbai", "Asia/Kolkata"), ("bengaluru", "Asia/Kolkata"), ("bangalore", "Asia/Kolkata"),
    ("delhi", "Asia/Kolkata"), ("hyderabad", "Asia/Kolkata"), ("pune", "Asia/Kolkata"), ("chennai", "Asia/Kolkata"),
    ("kolkata", "Asia/Kolkata"), ("gurgaon", "Asia/Kolkata"), ("gurugram", "Asia/Kolkata"), ("noida", "Asia/Kolkata"),
    ("iit", "Asia/Kolkata"), ("iisc", "Asia/Kolkata"),
    ("london", "Europe/London"), ("berlin", "Europe/Berlin"), ("paris", "Europe/Paris"), ("amsterdam", "Europe/Amsterdam"),
    ("seattle", "America/Los_Angeles"), ("las vegas", "America/Los_Angeles"), ("stanford", "America/Los_Angeles"), ("washington.edu", "America/Los_Angeles"),
    ("utexas", "America/Chicago"),("san francisco", "America/Los_Angeles"), ("los angeles", "America/Los_Angeles"),
    ("denver", "America/Denver"), ("boulder", "America/Denver"),
    ("chicago", "America/Chicago"), ("austin", "America/Chicago"), ("illinois", "America/Chicago"),
    ("uiuc", "America/Chicago"), ("northwestern", "America/Chicago"), ("indiana", "America/Chicago"),
]


# ---------------------------------------------------------------- helpers
def log(msg: str) -> None:
    line = f"{datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')}  {msg}"
    print(line)
    with ENGINE_LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def read_env() -> dict:
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"')
    for k in ("GMAIL_ADDRESS", "GMAIL_APP_PASSWORD", "SENDER_NAME"):  # the cloud passes these as secrets
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


def guess_tz(text: str) -> str:
    t = text.lower()
    if re.search(r"@[\w.-]+\.in(?![\w.])", t):  # an Indian email address (.in, .co.in, .ac.in)
        return "Asia/Kolkata"
    for kw, tz in CITY_TZ:
        if kw in t:
            return tz
    return "America/New_York"


def is_generic(addr: str) -> bool:
    return addr.split("@")[0].lower() in GENERIC_LOCALPARTS


def load() -> dict:
    if SEQ_PATH.exists():
        data = json.loads(SEQ_PATH.read_text(encoding="utf-8"))
    else:
        data = {"settings": {}, "sequences": []}
    data["settings"] = {**DEFAULTS, **data.get("settings", {})}
    return data


def save(data: dict) -> None:
    tmp = SEQ_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(SEQ_PATH)


def next_weekday(d: date) -> date:
    while d.weekday() >= 5:  # Sat/Sun -> Monday
        d += timedelta(days=1)
    return d


def due_date(seq: dict, interval: int) -> date | None:
    """Local date on which the next follow-up becomes due (None when finished)."""
    n = len(seq["sent_steps"])
    if n >= len(seq["steps"]):
        return None
    if (seq.get("first_email") and n == 0) or not (seq["sent_steps"] or seq.get("first_sent")):
        return next_weekday(date.today())  # founder's first email: next weekday morning
    last = seq["sent_steps"][-1]["date"] if seq["sent_steps"] else seq["first_sent"]
    gap = seq.get("interval_days") or interval
    return next_weekday(date.fromisoformat(last) + timedelta(days=gap))


def current_recipient(seq: dict) -> str:
    return seq.get("person_email") or seq["to"]


# ---------------------------------------------------------------- Gmail (IMAP)
class Gmail:
    def __init__(self, user: str, app_password: str):
        self.user = user.lower()
        self.M = imaplib.IMAP4_SSL("imap.gmail.com")
        self.M.login(user, app_password.replace(" ", ""))

    def _search(self, folder: str, raw: str) -> list[bytes]:
        self.M.select(f'"{folder}"', readonly=True)
        typ, data = self.M.uid("SEARCH", "X-GM-RAW", f'"{raw}"')
        return data[0].split() if typ == "OK" and data and data[0] else []

    def _headers(self, uid: bytes) -> email.message.Message:
        typ, data = self.M.uid("FETCH", uid, "(BODY.PEEK[HEADER])")
        return email.message_from_bytes(data[0][1])

    def find_message_id(self, to: str, subject: str) -> str | None:
        for uid in reversed(self._search("[Gmail]/Sent Mail", f"to:{to}")):
            h = self._headers(uid)
            if (h.get("Subject") or "").strip().lower() == subject.strip().lower():
                return h.get("Message-ID")
        return None

    AUTO_PHRASES = ("received your", "support ticket", "ticket number", "ticket #", "we usually reply",
                    "we'll get back to you", "we will get back to you", "thanks for getting in touch",
                    "thanks for reaching out", "thank you for contacting", "thank you for reaching out",
                    "out of office", "out of the office", "automatic reply", "auto-reply", "autoreply",
                    "this inbox is not monitored", "do not reply", "no longer monitored")

    def _is_automatic(self, uid: bytes, h: email.message.Message) -> bool:
        """Helpdesk acknowledgements, out-of-office and other machine replies don't count as a reply."""
        if h.get("Auto-Submitted", "no").lower() != "no" or h.get("X-Autoreply") or h.get("X-Autorespond"):
            return True
        if (h.get("Precedence") or "").lower() in ("bulk", "auto_reply", "junk", "list"):
            return True
        subj = str(email.header.make_header(email.header.decode_header(h.get("Subject") or ""))).lower()
        typ, data = self.M.uid("FETCH", uid, "(BODY.PEEK[TEXT]<0.3000>)")
        raw = data[0][1] if typ == "OK" and data and data[0] and isinstance(data[0], tuple) else b""
        import quopri
        text = quopri.decodestring(raw).decode("utf-8", "replace").lower()
        text = re.sub(r"\s+", " ", text.replace("=\r\n", "").replace("=\n", ""))
        return any(p in subj or p in text for p in self.AUTO_PHRASES)

    def check_reply(self, seq: dict) -> str | None:
        """Return 'replied' / 'bounced' / None."""
        if not seq.get("first_sent") or not seq.get("to"):
            return None  # nothing sent yet
        since = date.fromisoformat(seq["first_sent"]).strftime("%Y/%m/%d")
        addrs = {seq["to"].lower()} | ({seq["person_email"].lower()} if seq.get("person_email") else set())
        domain = seq["to"].split("@")[1].lower()
        exact = any(domain.endswith(x) for x in EXACT_MATCH_DOMAINS)
        query = " OR ".join(f"from:{a}" for a in addrs) if exact else f"from:(@{domain})"
        if seq.get("person_email") and not exact:
            pd = seq["person_email"].split("@")[1].lower()
            if pd != domain:
                query += f" OR from:(@{pd})"
        for uid in self._search("[Gmail]/All Mail", f"({query}) after:{since}"):
            h = self._headers(uid)
            sender = parseaddr(h.get("From", ""))[1].lower()
            if sender == self.user:
                continue
            if not self._is_automatic(uid, h):
                return "replied"
        for a in addrs:
            if self._search("[Gmail]/All Mail", f"from:mailer-daemon \\\"{a}\\\" after:{since}"):
                return "bounced"
        return None

    def close(self):
        try:
            self.M.logout()
        except Exception:
            pass


# ---------------------------------------------------------------- core run
def build_followup(seq: dict, step_text: str, sender: str, sender_name: str):
    to = current_recipient(seq)
    switched = bool(seq.get("person_email")) and not seq.get("person_thread_id")
    if seq.get("first_email") and not seq["sent_steps"]:
        # brand-new first email to a founder: starts its own thread
        msg = core.build_message(sender, sender_name, to, seq["subject"], step_text, None)
        msg["Message-ID"] = make_msgid(domain=sender.split("@")[1])
        return msg, to, seq["subject"], False
    if switched and seq.get("bounced_original"):
        # the first email bounced, so this is the founder's first contact: send the original email
        subject = seq["subject"]
        body = re.sub(r"^Hi [^\n]*,", f"Hi {seq.get('person_first') or seq['first_name']},", step_text, count=1)
        msg = core.build_message(sender, sender_name, to, subject, body, None)
    elif switched:
        # first message to the founder directly: new thread, mention the earlier note
        subject = seq["subject"]
        intro = (f"Hi {seq.get('person_first') or seq['first_name']},\n\nI sent a note to your team inbox "
                 f"({seq['to']}) on {seq['first_sent']} and wanted to reach you directly.")
        step_text = step_text.replace("Just bumping this up in case it got buried. ", "")
        body = re.sub(r"^Hi [^\n]*,\n\n", intro + " ", step_text, count=1)
        if body == step_text:
            body = intro + "\n\n" + step_text
        msg = core.build_message(sender, sender_name, to, subject, body, None)
    else:
        subject = seq["subject"] if seq["subject"].lower().startswith("re:") else "Re: " + seq["subject"]
        msg = core.build_message(sender, sender_name, to, subject, step_text, None)
        parent = seq.get("person_thread_id") if seq.get("person_email") else seq.get("message_id")
        if parent:
            msg["In-Reply-To"] = parent
            msg["References"] = parent
    msg["Message-ID"] = make_msgid(domain=sender.split("@")[1])
    return msg, to, subject, switched


def activate_founder(data: dict, company: str, email_addr: str, person_name: str | None = None) -> dict:
    """A founder's address was found: queue their first email (sent next weekday morning, their time),
    and stop the old shared-inbox sequence for that company so nobody gets double follow-ups."""
    seq = next(s for s in data["sequences"] if s.get("kind") == "founder" and s["company"] == company)
    seq["to"] = email_addr.strip()
    if person_name and person_name != seq.get("person"):
        old_first, new_first = seq["first_name"], person_name.split()[0]
        seq["person"], seq["first_name"] = person_name, new_first
        seq["steps"] = [t.replace(f"Hi {old_first},", f"Hi {new_first},", 1) for t in seq["steps"]]
    seq["status"] = "active"
    for s in data["sequences"]:
        if s is not seq and s["company"] == company and s.get("kind") != "founder" and s["status"] in ("active", "bounced", "needs_person"):
            s["status"] = "moved"  # moved to founder
    return seq


def set_person_email(seq: dict, person_email: str, person_name: str, original_body: str | None = None) -> None:
    """Point a sequence at a real person. If the first email bounced, re-send the original to them first."""
    seq["person_email"] = person_email.strip()
    seq["person_first"] = person_name.split()[0] if person_name else seq["first_name"]
    seq["person_thread_id"] = None
    if seq["status"] == "bounced" and original_body and not seq.get("bounced_original"):
        seq["steps"] = [original_body] + seq["steps"]
        seq["bounced_original"] = True
        seq["sent_steps"] = []
        seq["first_sent"] = (date.today() - timedelta(days=2)).isoformat()  # makes step 1 due at the next morning
        seq["status"] = "active"


def personalize(text: str, seq: dict) -> str:
    first = seq.get("person_first") if seq.get("person_email") else None
    first = first or seq["first_name"]
    return text.replace("{first}", first).replace("{company}", seq["company"])


def record_sent(seq: dict, msg, to: str, subject: str, switched: bool, how: str) -> None:
    """Mark the next step of a sequence as sent (shared by the autopilot and the app's Send now button)."""
    now_local = datetime.now(ZoneInfo(seq["tz"]))
    is_first = bool(seq.get("first_email")) and not seq["sent_steps"]
    fu_no = len(seq["sent_steps"]) if seq.get("first_email") else len(seq["sent_steps"]) + 1
    if switched:
        seq["person_thread_id"] = msg["Message-ID"]
    if is_first:
        seq["message_id"] = msg["Message-ID"]
        seq["first_sent"] = now_local.date().isoformat()
    seq["sent_steps"].append({"date": now_local.date().isoformat(), "to": to,
                              "sent_at_ist": datetime.now(IST).isoformat(timespec="seconds")})
    core.append_log({"timestamp": datetime.now(IST).replace(tzinfo=None).isoformat(timespec="seconds"),
                     "source": f"{how} first email" if is_first else f"{how} follow-up {fu_no}",
                     "id": seq["id"], "company": seq["company"], "to": to, "subject": subject, "status": "sent"})
    log(f"Sent ({how}) {'FIRST EMAIL' if is_first else f'follow-up {fu_no}'} to {seq['company']} <{to}>")
    if len(seq["sent_steps"]) >= len(seq["steps"]):
        seq["status"] = "finished"


def send_now(data: dict, seq: dict, text: str | None = None) -> str:
    """Send the next email of one sequence right away (the app's Send now button).
    Checks for a reply first, so nobody who already answered gets a follow-up. Returns a message for the user."""
    env = read_env()
    sender, pw = env.get("GMAIL_ADDRESS"), env.get("GMAIL_APP_PASSWORD")
    if not (sender and pw):
        return "ERROR: connect your Gmail in Settings first."
    to_addr = current_recipient(seq) or ""
    if is_generic(to_addr):
        return f"ERROR: {to_addr} is a shared inbox. Add a person's email instead."
    k = len(seq["sent_steps"])
    if k >= len(seq["steps"]):
        return "ERROR: every email for this person has already been sent."
    gm = Gmail(sender, pw)
    try:
        if seq["sent_steps"] or seq.get("first_sent"):
            res = gm.check_reply(seq)
            if res:
                seq["status"] = res
                save(data)
                return f"ERROR: not sent, because they already {'replied' if res == 'replied' else 'bounced'}."
        if not seq.get("message_id") and not seq.get("person_email") and not seq.get("first_email"):
            seq["message_id"] = gm.find_message_id(seq["to"], seq["subject"])
    finally:
        gm.close()
    if text is not None:
        seq["steps"][k] = text
    body = personalize(seq["steps"][k], seq)
    msg, to, subject, switched = build_followup(seq, body, sender, env.get("SENDER_NAME", ""))
    smtp = core.connect(sender, pw)
    try:
        smtp.send_message(msg)
    finally:
        smtp.quit()
    record_sent(seq, msg, to, subject, switched, "manual")
    seq["status"] = "active" if len(seq["sent_steps"]) < len(seq["steps"]) else "finished"
    save(data)
    return f"Sent to {to}."


def run(dry_run: bool = False, force_window: bool = False) -> None:
    data = load()
    st = data["settings"]
    if st.get("paused") and not dry_run:  # a check-only run still reads replies while paused
        log("Paused: nothing sent. Unpause in the app's Auto follow-ups tab.")
        return
    env = read_env()
    sender, pw = env.get("GMAIL_ADDRESS"), env.get("GMAIL_APP_PASSWORD")
    if not (sender and pw):
        if IN_CLOUD:
            log("No Gmail login found. Add the GMAIL_ADDRESS and GMAIL_APP_PASSWORD secrets in the repo's "
                "Settings > Secrets and variables > Actions > Secrets tab.")
            sys.exit(1)  # show a red cross in GitHub so the problem is visible
        log("No Gmail login saved. Open the app, go to Settings and press Test and save.")
        return
    sender_name = env.get("SENDER_NAME", "")
    gm = Gmail(sender, pw)
    smtp = None
    sent_now = 0
    firsts_now = 0
    today_ist = datetime.now(IST).date().isoformat()
    new_today = sum(1 for r in core.load_log() if r.get("status") == "sent"
                    and r.get("source") == "auto first email" and r["timestamp"].startswith(today_ist))
    try:
        for seq in data["sequences"]:
            if seq["status"] != "active":
                continue
            # 0) only ever write to people, never to support/hello/careers-style shared inboxes
            if is_generic(current_recipient(seq) or ""):
                seq["status"] = "needs_person"
                log(f"{seq['company']}: {current_recipient(seq)} is a shared inbox, so nothing is sent. Waiting for a person's email.")
                continue
            # 1) stop if they replied or the address bounced
            res = gm.check_reply(seq)
            if res:
                seq["status"] = res
                log(f"{seq['company']}: {res.upper()}, sequence stopped.")
                continue
            # 2) is a follow-up due, and is it morning there?
            due = due_date(seq, st["interval_days"])
            if due is None:
                seq["status"] = "finished"
                continue
            now_local = datetime.now(ZoneInfo(seq["tz"]))
            h1, m1, h2, m2 = window_for(seq["tz"])
            in_window = now_local.weekday() < 5 and (h1, m1) <= (now_local.hour, now_local.minute) < (h2, m2)
            if now_local.date() < due or not (in_window or force_window):
                continue
            if sent_now >= st["max_per_run"]:
                log("Per-run limit reached; the rest go next run.")
                break
            if not dry_run and core.sent_today_count() >= st["max_per_day"]:
                log("Daily limit reached; the rest go tomorrow morning.")
                break
            is_first = bool(seq.get("first_email")) and not seq["sent_steps"]
            fu_no = len(seq["sent_steps"]) if seq.get("first_email") else len(seq["sent_steps"]) + 1
            if is_first and new_today + firsts_now >= st["max_new_per_day"]:
                continue  # today's quota of new first emails is used; this one goes next weekday morning
            if not seq.get("message_id") and not seq.get("person_email") and not seq.get("first_email"):
                seq["message_id"] = gm.find_message_id(seq["to"], seq["subject"])
            k = len(seq["sent_steps"])
            text = personalize(seq["steps"][k], seq)
            msg, to, subject, switched = build_followup(seq, text, sender, sender_name)
            if dry_run:
                firsts_now += is_first
                log(f"[DRY RUN] would send {'FIRST EMAIL' if is_first else f'follow-up {fu_no}'} to {seq['company']} <{to}> "
                    f"({now_local.strftime('%a %H:%M')} {seq['tz']})")
                sent_now += 1
                continue
            if smtp is None:
                smtp = core.connect(sender, pw)
            else:
                time.sleep(random.randint(40, 90))
                later = datetime.now(ZoneInfo(seq["tz"]))  # the wait may have pushed us past their deadline
                if not force_window and (later.hour, later.minute) >= (h2, m2):
                    continue
            try:
                smtp.send_message(msg)
            except Exception:
                smtp = core.connect(sender, pw)
                smtp.send_message(msg)
            record_sent(seq, msg, to, subject, switched, "auto")
            firsts_now += is_first
            sent_now += 1
            save(data)
    finally:
        gm.close()
        if smtp:
            try:
                smtp.quit()
            except Exception:
                pass
        save(data)  # dry runs only record replies/bounces; they never mark anything as sent
    log(f"Run done. {'Would send' if dry_run else 'Sent'} {sent_now}.")


def next_send_ist(seq: dict, settings: dict) -> datetime | None:
    """When the next email of this sequence is expected to go out, in India time (start of their morning window)."""
    if seq["status"] != "active":
        return None
    due = due_date(seq, settings["interval_days"])
    if due is None:
        return None
    tz = ZoneInfo(seq["tz"])
    h1, m1, h2, m2 = window_for(seq["tz"])
    now_local = datetime.now(tz)
    start = datetime(due.year, due.month, due.day, h1, m1, tzinfo=tz)
    end = datetime(due.year, due.month, due.day, h2, m2, tzinfo=tz)
    if now_local > end:  # today's window already passed: next weekday
        nd = next_weekday(now_local.date() + timedelta(days=1))
        start = datetime(nd.year, nd.month, nd.day, h1, m1, tzinfo=tz)
    elif now_local > start:
        start = now_local
    return start.astimezone(IST)


def status() -> None:
    data = load()
    for s in data["sequences"]:
        if s["status"] == "needs_email":
            continue
        due = due_date(s, data["settings"]["interval_days"])
        print(f"{s['status']:9} {len(s['sent_steps'])}/{len(s['steps'])}  next {due}  {s['company']:22} "
              f"{current_recipient(s)}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "run":
        if not IN_CLOUD and (HERE / ".git").exists():
            import cloud_sync
            if cloud_sync.enabled():  # the cloud autopilot does this now; running here too would double-send
                log("Laptop autopilot skipped: the cloud autopilot is on.")
                sys.exit(0)
        run(dry_run="--dry-run" in sys.argv, force_window="--any-time" in sys.argv)
    else:
        status()
