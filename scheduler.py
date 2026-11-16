"""Queue unsent drafts so the engine sends them automatically on the recipient's next weekday morning,
then follows up in the same thread (startups: 3 follow-ups, 2 days apart; professors: 2, 4 days apart)."""
import re

import followup_engine as fe
from founder_data import FU1 as STARTUP_FU1, FU2, FU3, SIG, PROF_FU1, PROF_FU2


def is_scheduled(data: dict, to: str, subject: str) -> bool:
    return any(s.get("kind") == "scheduled" and s["to"].lower() == to.lower()
               and s["subject"].lower() == subject.lower() for s in data["sequences"])


def schedule_draft(data: dict, d: dict) -> dict | None:
    """d is a parsed draft {source, id, company, to, subject, body}. Returns the new sequence, or None if
    it was already scheduled."""
    if not d["to"] or is_scheduled(data, d["to"], d["subject"]):
        return None
    prof = d["source"] == "professor_emails.md" or d["company"].lower().startswith(("prof", "dr."))
    greet_m = re.match(r"((?:Hi|Dear) ([^\n]*),)", d["body"])
    greeting, first = (greet_m.group(1), greet_m.group(2)) if greet_m else ("Hi,", "there")
    company = re.sub(r"\s*[\(\[].*$|:.*$", "", d["company"]).strip()
    if prof:
        steps = [d["body"], PROF_FU1.format(greeting=greeting), PROF_FU2.replace("{first}", first)]
    else:
        fill = dict(first=first, company=company, sig=SIG)
        steps = [d["body"], STARTUP_FU1.format(**fill), FU2.format(**fill), FU3.format(**fill)]
    seq = {
        "id": f"scheduled#{d['source']}#{d['id']}",
        "kind": "scheduled",
        "first_email": True,
        "company": company,
        "first_name": first,
        "to": d["to"],
        "subject": d["subject"],
        "first_sent": None,
        "tz": fe.guess_tz(d["company"] + " " + d["to"]),
        "generic_inbox": fe.is_generic(d["to"]),
        "suggested_person": "",
        "person_email": "",
        "message_id": None,
        "steps": steps,
        "sent_steps": [],
        "status": "active",
    }
    if prof:
        seq["interval_days"] = 4
    if d["source"] == "biotech_emails.md":  # biotech emails carry the resume
        seq["attach"] = "Anushree_Revankar_Resume.pdf"
    data["sequences"].append(seq)
    return seq
