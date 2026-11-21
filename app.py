"""Cold Email Sender: pick an email, read it, press Send. The autopilot handles the rest.

Run:  streamlit run app.py   (or double-click "Start Email Sender.bat")
"""
import importlib
import smtplib
import subprocess
import time
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

import os
try:  # hosted on Streamlit Cloud: passwords and tokens come from the app's Secrets settings
    for _k, _v in st.secrets.items():
        if isinstance(_v, str):
            os.environ.setdefault(_k, _v)
except Exception:
    pass  # running on the laptop: no secrets file, the .env file is used instead
HOSTED = bool(os.environ.get("GH_TOKEN"))

import email_core as core
import followup_engine as fe
import people_finder
import scheduler

import cloud_sync

fe = importlib.reload(fe)            # always use the latest engine code, even if the app stays open for days
scheduler = importlib.reload(scheduler)
CLOUD = cloud_sync.enabled()
if CLOUD:
    _save = fe.save

    def _save_and_sync(d):           # every change made in the app goes to the cloud autopilot straight away
        _save(d)
        try:
            cloud_sync.sync("update from app")
        except Exception:
            pass                     # offline: it syncs next time
    fe.save = _save_and_sync
    scheduler.fe.save = _save_and_sync

HERE = Path(__file__).resolve().parent
DRAFT_DIR = HERE / "drafts" if (HERE / "drafts").exists() else HERE.parent
ENV_PATH = HERE / ".env"
DRAFT_FILES = ["READY_TO_SEND.md", "professor_emails.md", "biotech_emails.md"]


def read_env() -> dict:
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"')
    for k in ("GMAIL_ADDRESS", "GMAIL_APP_PASSWORD", "SENDER_NAME", "HUNTER_API_KEY"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


def write_env(updates: dict) -> None:
    """Save keys to .env, keeping every other key that is already there."""
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    keep = [l for l in lines if l.split("=", 1)[0].strip() not in updates]
    new = [f'{k}="{v}"' if " " in str(v) else f"{k}={v}" for k, v in updates.items()]
    ENV_PATH.write_text("\n".join(new + keep) + "\n", encoding="utf-8")


def fmt(dt) -> str:
    return dt.strftime("%a %d %b, %I:%M %p") if dt else ""


def step_name(s: dict, i: int) -> str:
    if s.get("first_email"):
        return "first email" if i == 0 else f"follow-up {i}"
    return f"follow-up {i + 1}"


def icon(s: dict) -> str:
    if s.get("kind") == "professor" or "professor_emails" in s.get("id", "") or s["company"].startswith(("Prof", "Dr.")):
        return "🎓"
    return "👤" if s.get("kind") == "founder" else "🏢"


def plain_status(s: dict) -> str:
    done, total = len(s["sent_steps"]), len(s["steps"])
    if s["status"] == "active":
        return "Waiting to send first email" if s.get("first_email") and done == 0 else f"Following up ({done} of {total} sent)"
    return {"replied": "💬 REPLIED", "bounced": "❌ Bounced", "finished": "Done, no reply yet",
            "needs_email": "Need their email", "needs_person": "Need a person's email (only a shared inbox)",
            "moved": "Moved to founder", "stopped": "Stopped"}.get(s["status"], s["status"])


def their_time(tz: str) -> str:
    now = datetime.now(ZoneInfo(tz))
    h1, m1, h2, m2 = fe.window_for(tz)
    good = now.weekday() < 5 and (h1, m1) <= (now.hour, now.minute) < (h2, m2)
    return f"It's {now.strftime('%a %I:%M %p')} for them now" + (
        " (a good time) ✅" if good else f" (best is {h1}:{m1:02d}–{h2}:{m2:02d} AM their time on a weekday)")


def flash(msg: str) -> None:
    st.session_state.flash = msg


def due_now_list(seqs: list, sts: dict) -> list:
    """Everyone whose next email is due today or earlier (in their own time zone), whatever the hour."""
    out = []
    for s in seqs:
        if s["status"] != "active" or fe.is_generic(fe.current_recipient(s) or ""):
            continue
        if fe.manual_due(s, sts["interval_days"], datetime.now(ZoneInfo(s["tz"])).date()):
            out.append(s)
    return out


def send_all_due_button(key: str) -> None:
    due = due_now_list(seqs, sts)
    firsts = sum(1 for s in due if s.get("first_email") and not s["sent_steps"])
    room_all = max(0, sts["max_per_day"] - sent_today)
    if not due:
        st.caption("Nothing in the queue is due today.")
        return
    mins = max(1, round(len(due) * 65 / 60))
    if st.button(f"📤 Send all {len(due)} due emails now (any time of day)", type="primary", key=key,
                 disabled=not creds_ok, use_container_width=True,
                 help="Sends everyone in the queue whose email is due today, right now, ignoring their morning "
                      "time slot. It waits about a minute between emails so Gmail doesn't flag you."):
        before = len(core.load_log())
        with st.spinner(f"Sending {len(due)} emails, about {mins} minutes. Keep this page open…"):
            fe.run(manual=True)
        n = sum(1 for r in core.load_log()[before:] if r.get("status") == "sent")
        left = len(due_now_list(fe.load()["sequences"], sts))
        flash(f"✅ {n} emails sent." + (f" {left} were held back by your daily limits (change them in ⚙️ "
                                        "Settings) and go next time." if left else ""))
        st.rerun()
    note = f"{len(due)} due ({firsts} first emails, {len(due) - firsts} follow-ups) · takes about {mins} min."
    if len(due) > room_all or firsts > sts["max_new_per_day"]:
        note += (f" ⚠️ Your daily limits ({sts['max_new_per_day']} new first emails, {sts['max_per_day']} emails "
                 "in total) will hold some back. Raise them in ⚙️ Settings to send all today.")
    st.caption(note)


st.set_page_config(page_title="Cold Email Sender", page_icon="✉️", layout="wide")

if CLOUD and time.time() - st.session_state.get("last_sync", 0) > 60:  # get the cloud's latest sends
    try:
        cloud_sync.sync("update from app")
    except Exception:
        pass
    st.session_state.last_sync = time.time()

env = read_env()
data = fe.load()
sts = data["settings"]
seqs = data["sequences"]
log_rows = core.load_log()
creds_ok = bool(env.get("GMAIL_ADDRESS") and env.get("GMAIL_APP_PASSWORD"))
today_iso = datetime.now().date().isoformat()
sent_today = sum(1 for r in log_rows if r.get("status") == "sent" and r.get("timestamp", "").startswith(today_iso))

# ---------------- Header ----------------
st.title("✉️ Cold Email Sender")

try:
    task = subprocess.run(["schtasks", "/Query", "/TN", "ColdEmailFollowUps", "/V", "/FO", "LIST"],
                          capture_output=True, text=True)
except Exception:  # not on Windows (hosted)
    task = subprocess.CompletedProcess([], 1, "", "")
last_result = next((l.split(":", 1)[1].strip() for l in task.stdout.splitlines() if l.startswith("Last Result")), "0")
cloud_log = HERE / "followup_engine.log"
last_cloud = (cloud_log.read_text(encoding="utf-8").strip().splitlines() or [""])[-1][:16] if cloud_log.exists() else ""
if not creds_ok:
    st.error("First, connect your Gmail in **⚙️ Settings**." if not HOSTED else
             "Gmail isn't connected: add GMAIL_ADDRESS and GMAIL_APP_PASSWORD in the app's Secrets on Streamlit.")
elif CLOUD and sts["paused"]:
    st.info("🤖 Autopilot is **OFF**. Emails only go out when you press **Send now**. (Turn it on in ⚙️ Settings.)")
elif CLOUD:
    st.success("☁️ Autopilot is **ON in the cloud**: follow-ups go out by themselves every weekday US morning, "
               f"**even when your laptop is off**. Last cloud check: {last_cloud or 'not yet'} (India time).")
elif task.returncode != 0:
    st.info("🤖 Autopilot is not set up. You can still send everything by hand.")
elif sts["paused"]:
    st.info("🤖 Autopilot is **OFF**. Emails only go out when you press **Send now**. (Turn it on in ⚙️ Settings.)")
elif last_result not in ("0", "267009", "267011"):
    st.warning("🤖 Autopilot is ON, but Windows blocked its last run (usually because the laptop was on battery). "
               "Keep the laptop plugged in during the evening, or send by hand below.")
else:
    st.success("🤖 Autopilot is **ON**: follow-ups go out by themselves 5:30–11:30 PM India time while the laptop is "
               "on. You can also send anything yourself, any time.")

replied = [s for s in seqs if s["status"] == "replied"]
queued = [s for s in seqs if s["status"] == "active"]
st.markdown(f"**💬 {len(replied)} replies** &nbsp;·&nbsp; **✉️ {sent_today} sent today** &nbsp;·&nbsp; "
            f"**⏰ {len(queued)} people in the queue**")
if replied:
    st.success("💬 **Replies from:** " + ", ".join(s["company"] for s in replied) + ". Answer them in Gmail.")

if "flash" in st.session_state:
    m = st.session_state.pop("flash")
    (st.error if m.startswith("ERROR") else st.success)(m.replace("ERROR: ", ""))

tab_send, tab_track, tab_people, tab_settings = st.tabs(
    ["✉️ Send emails", "📋 Sent & to send", "👥 People", "⚙️ Settings"])

# ---------------- Send emails ----------------
with tab_send:
    mode = st.radio("What do you want to do?", ["Send a prepared email", "Write a new email"],
                    horizontal=True, label_visibility="collapsed")

    if mode == "Send a prepared email":
        send_all_due_button("send_all_top")
        st.divider()
        # 1) everyone whose next email is ready (follow-ups, founders' first emails, scheduled drafts)
        items = []
        for s in seqs:
            k = len(s["sent_steps"])
            if s["status"] != "active" or k >= len(s["steps"]) or fe.is_generic(fe.current_recipient(s) or ""):
                continue
            due_day = fe.due_date(s, sts["interval_days"])
            due_now = due_day is not None and datetime.now(ZoneInfo(s["tz"])).date() >= due_day
            when = fe.next_send_ist(s, sts)
            note = "due now" if due_now else f"due {due_day.strftime('%a %d %b')}"
            items.append({"kind": "seq", "s": s, "sort": (0 if due_now else 1, when.timestamp() if when else 9e12),
                          "label": f"{icon(s)} {s['company']}  ·  {step_name(s, k)}  ·  {note}"})
        # 2) drafts in your files that haven't been sent or scheduled yet
        sent_set = core.already_sent()
        for f in DRAFT_FILES:
            if not (DRAFT_DIR / f).exists():
                continue
            for d in core.parse_drafts(DRAFT_DIR / f):
                if (not d["to"] or fe.is_generic(d["to"]) or core.sent_key(d["to"], d["subject"]) in sent_set
                        or scheduler.is_scheduled(data, d["to"], d["subject"])):
                    continue
                items.append({"kind": "draft", "d": d, "sort": (0, 0),
                              "label": f"🆕 {d['company'][:60]}  ·  first email  ·  not sent yet"})
        items.sort(key=lambda x: x["sort"])

        if not items:
            st.info("Nothing to send right now. 🎉 Write a new email, or add founders' emails in 👥 People.")
        else:
            n_due = sum(1 for it in items if it["sort"][0] == 0)
            st.caption(f"{len(items)} emails ready ({n_due} due now). Pick one, read it, and press **Send now**.")
            i = st.selectbox("Pick an email", range(len(items)), format_func=lambda j: items[j]["label"])
            it = items[i]

            if it["kind"] == "seq":
                s = it["s"]
                k = len(s["sent_steps"])
                uid = f"{s['id']}_{k}"
                to = fe.current_recipient(s)
                tz = s["tz"]
                first = bool(s.get("first_email")) and k == 0
                subject = s["subject"] if first or s["subject"].lower().startswith("re:") else "Re: " + s["subject"]
                body = fe.personalize(s["steps"][k], s)
                extra = "" if first else f" · this is {step_name(s, k)} of {len(s['steps']) - (1 if s.get('first_email') else 0)}, sent as a reply in the same thread"
            else:
                d = it["d"]
                uid = f"draft_{d['source']}_{d['id']}"
                to, subject, body, first = d["to"], d["subject"], d["body"], True
                tz = fe.guess_tz(d["company"] + " " + d["to"])
                extra = ""

            st.markdown(f"**To:** {to}  \n<small>{their_time(tz)}{extra}</small>", unsafe_allow_html=True)
            subj_v = st.text_input("Subject", subject, key=f"subj_{uid}", disabled=not first)
            body_v = st.text_area("Message", body, height=340, key=f"body_{uid}")

            b1, b2, b3 = st.columns([1, 1.4, 1])
            send = b1.button("🚀 Send now", type="primary", use_container_width=True, disabled=not creds_ok)
            later_label = "⏰ Let autopilot send it" if it["kind"] == "draft" else "💾 Save my changes"
            later = b2.button(later_label, use_container_width=True,
                              help="Autopilot sends it on their next weekday morning, then follows up until they reply.")
            test = b3.button("📨 Send me a test", use_container_width=True, disabled=not creds_ok)
            if sent_today >= sts["max_per_day"]:
                st.caption(f"⚠️ You've sent {sent_today} today. More than ~25 a day can get a new Gmail flagged.")

            if send or later:
                if it["kind"] == "draft":  # turn the draft into a sequence so follow-ups happen automatically
                    s = scheduler.schedule_draft(data, {**d, "subject": subj_v, "body": body_v})
                    k = 0
                if first:
                    s["subject"] = subj_v
                s["steps"][k] = body_v
                fe.save(data)
                if send:
                    with st.spinner("Sending…"):
                        try:
                            msg = fe.send_now(data, s)
                        except Exception as e:
                            msg = f"ERROR: could not send: {e}"
                    flash(msg if msg.startswith("ERROR") else
                          f"✅ {msg} Follow-ups will continue automatically until they reply.")
                else:
                    flash("Saved. The autopilot will send it on their next weekday morning.")
                st.rerun()
            if test:
                try:
                    srv = core.connect(env["GMAIL_ADDRESS"], env["GMAIL_APP_PASSWORD"])
                    srv.send_message(core.build_message(env["GMAIL_ADDRESS"], env.get("SENDER_NAME", ""),
                                                        env["GMAIL_ADDRESS"], "[TEST] " + subj_v, body_v, None))
                    srv.quit()
                    st.success("Test sent to your own inbox.")
                except Exception as e:
                    st.error(f"Test failed: {e}")

    else:  # Write a new email
        n1, n2 = st.columns(2)
        who = n1.text_input("Who is it for? (name or company, for your records)")
        to = n2.text_input("Their email")
        subj = st.text_input("Subject")
        body = st.text_area("Message", height=340,
                            placeholder="Hi …,\n\n…\n\nWarm regards,\nAnushree Revankar\n"
                                        "github.com/Anushre2005 | linkedin.com/in/anushree-revankar")
        follow = st.checkbox("If they don't reply, follow up automatically (up to 3 short follow-ups, 2 days apart)",
                             value=True)
        ok = bool(core.EMAIL_RE.match(to.strip()) and subj.strip() and body.strip())
        c1, c2 = st.columns(2)
        if c1.button("🚀 Send now", type="primary", use_container_width=True, disabled=not (ok and creds_ok)):
            d = {"source": "manual", "id": int(datetime.now().timestamp()), "company": who or to,
                 "to": to.strip(), "subject": subj, "body": body}
            try:
                if follow:
                    s = scheduler.schedule_draft(data, d)
                    fe.save(data)
                    msg = fe.send_now(data, s)
                else:
                    srv = core.connect(env["GMAIL_ADDRESS"], env["GMAIL_APP_PASSWORD"])
                    srv.send_message(core.build_message(env["GMAIL_ADDRESS"], env.get("SENDER_NAME", ""),
                                                        d["to"], subj, body, None))
                    srv.quit()
                    core.append_log({"timestamp": datetime.now().isoformat(timespec="seconds"), "source": "manual",
                                     "id": d["id"], "company": d["company"], "to": d["to"], "subject": subj,
                                     "status": "sent"})
                    msg = f"Sent to {d['to']}."
            except Exception as e:
                msg = f"ERROR: could not send: {e}"
            flash(msg)
            st.rerun()
        if c2.button("📨 Send me a test", use_container_width=True, disabled=not (ok and creds_ok)):
            try:
                srv = core.connect(env["GMAIL_ADDRESS"], env["GMAIL_APP_PASSWORD"])
                srv.send_message(core.build_message(env["GMAIL_ADDRESS"], env.get("SENDER_NAME", ""),
                                                    env["GMAIL_ADDRESS"], "[TEST] " + subj, body, None))
                srv.quit()
                st.success("Test sent to your own inbox.")
            except Exception as e:
                st.error(f"Test failed: {e}")
        if to and not core.EMAIL_RE.match(to.strip()):
            st.caption("⚠️ That email address doesn't look right.")

# ---------------- Sent & to send ----------------
def which_email(source: str) -> str:
    src = (source or "").lower()
    if "follow-up" in src:
        return "Follow-up " + src.rsplit("follow-up", 1)[1].strip()
    return "First email"


def when_label(dt: datetime) -> str:
    d = (dt.date() - datetime.now().date()).days
    day = {0: "Today", -1: "Yesterday", 1: "Tomorrow"}.get(d, dt.strftime("%a %d %b"))
    return f"{day}, {dt.strftime('%I:%M %p').lstrip('0')}"


with tab_track:
    sent_rows = [r for r in log_rows if r.get("status") in ("sent", "failed")]
    upcoming = []
    for s in seqs:
        if s["status"] != "active":
            continue
        k, total = len(s["sent_steps"]), len(s["steps"])
        nxt = fe.next_send_ist(s, sts)
        gap = s.get("interval_days", sts["interval_days"])
        for j, step in enumerate(range(k, total)):
            if sts["paused"]:
                plan = "Autopilot off: press Send now"
            elif nxt is None:
                plan = "Waiting"
            elif j == 0:
                plan = when_label(nxt)
            else:
                plan = f"Around {(nxt + pd.Timedelta(days=gap * j)).strftime('%a %d %b')}, if no reply"
            upcoming.append({"sort": (nxt.timestamp() if nxt else 9e12) + j * 86400 * gap,
                             "When (India time)": plan, "Name": f"{icon(s)} {s['company']}",
                             "Email": fe.current_recipient(s), "Which email": step_name(s, step).capitalize()})
    sent_set = core.already_sent()
    for f in DRAFT_FILES:
        if not (DRAFT_DIR / f).exists():
            continue
        for d in core.parse_drafts(DRAFT_DIR / f):
            if (d["to"] and not fe.is_generic(d["to"]) and core.sent_key(d["to"], d["subject"]) not in sent_set
                    and not scheduler.is_scheduled(data, d["to"], d["subject"])):
                upcoming.append({"sort": 9.9e12, "When (India time)": "Not scheduled: send it from ✉️ Send emails",
                                 "Name": f"🆕 {d['company'][:60]}", "Email": d["to"], "Which email": "First email"})
    upcoming.sort(key=lambda x: x["sort"])

    c1, c2, c3 = st.columns(3)
    c1.metric("✅ Sent so far", sum(1 for r in sent_rows if r["status"] == "sent"))
    c2.metric("⏳ Still to send", len(upcoming))
    c3.metric("💬 Replies", len(replied))
    view = st.radio("Show", ["⏳ Still to send", "✅ Already sent"], horizontal=True, label_visibility="collapsed")
    find = st.text_input("Search by name or email", placeholder="e.g. Ferguson or uchicago",
                         label_visibility="collapsed").strip().lower()

    if view == "✅ Already sent":
        table = [{"When (India time)": when_label(datetime.fromisoformat(r["timestamp"])),
                  "Name": r["company"], "Email": r["to"], "Which email": which_email(r["source"]),
                  "Subject": r["subject"], "Result": "✅ Sent" if r["status"] == "sent" else "❌ Failed"}
                 for r in sorted(sent_rows, key=lambda r: r["timestamp"], reverse=True)]
        tip = "Newest first. Follow-ups are sent as replies in the same Gmail thread as the first email."
    else:
        table = [{k: v for k, v in u.items() if k != "sort"} for u in upcoming]
        tip = ("Follow-ups stop by themselves as soon as someone replies. "
               "Want to send one earlier? Pick it in ✉️ Send emails and press Send now.")
    if find:
        table = [t for t in table if find in (t["Name"] + " " + t["Email"]).lower()]
    if table:
        st.dataframe(pd.DataFrame(table), hide_index=True, use_container_width=True, height=480)
        st.caption(tip)
    else:
        st.caption("Nothing here.")

# ---------------- People ----------------
with tab_people:
    show = st.radio("Show", ["In the queue", "Replied", "Need an email", "Finished", "Everyone"], horizontal=True)
    keep = {"In the queue": lambda s: s["status"] == "active",
            "Replied": lambda s: s["status"] == "replied",
            "Need an email": lambda s: s["status"] in ("needs_email", "needs_person"),
            "Finished": lambda s: s["status"] in ("finished", "bounced", "stopped"),
            "Everyone": lambda s: s["status"] != "moved"}[show]
    rows = [s for s in seqs if keep(s)]
    if rows:
        st.dataframe(pd.DataFrame([{
            "Name": f"{icon(s)} {s['company']}",
            "Status": plain_status(s),
            "Email": fe.current_recipient(s) if s["status"] != "needs_email" else "",
            "Autopilot sends next": fmt(fe.next_send_ist(s, sts)) if not sts["paused"] else "(autopilot off)",
        } for s in rows]), hide_index=True, use_container_width=True, height=420)
    else:
        st.caption("Nobody here.")

    waiting = [s for s in seqs if s.get("kind") == "founder" and s["status"] == "needs_email"]
    with st.expander(f"➕ Add a founder's email ({len(waiting)} founders have an email written but no address)"):
        no_first_yet = [s for s in seqs if s.get("kind") == "founder" and s["status"] in ("needs_email", "active")
                        and not s["sent_steps"]]
        if no_first_yet:
            a1, a2, a3 = st.columns(3)
            comp = a1.selectbox("Company", [s["company"] for s in no_first_yet], key="manual_comp")
            s = next(x for x in no_first_yet if x["company"] == comp)
            pname = a2.text_input("Founder's full name", value=s.get("person", ""), key=f"mn_{comp}")
            pmail = a3.text_input("Their email", value=s.get("to", ""), key=f"mm_{comp}")
            if st.button("Add"):
                if core.EMAIL_RE.match(pmail.strip()):
                    fe.activate_founder(data, comp, pmail.strip(), pname)
                    fe.save(data)
                    flash(f"{comp} added. Their email is now in ✉️ Send emails.")
                    st.rerun()
                else:
                    st.error("That doesn't look like an email address.")

        st.divider()
        st.write("**Or look them up with Hunter.io** (free plan: 25 searches a month)")
        hkey = read_env().get("HUNTER_API_KEY", "")
        if not hkey and HOSTED:
            st.caption("Add HUNTER_API_KEY to this app's Secrets on Streamlit to use this.")
        elif not hkey:
            new_key = st.text_input("Paste your Hunter.io API key", type="password")
            if st.button("Save key") and new_key:
                write_env({"HUNTER_API_KEY": new_key})
                st.rerun()
        elif waiting:
            n_look = st.number_input("How many to look up", 1, len(waiting), min(10, len(waiting)))
            if st.button("🔎 Look up"):
                found, bar = [], st.progress(0.0)
                for j, s in enumerate(waiting[:int(n_look)], 1):
                    r = people_finder.find_email(hkey, s["domain"], s["person"])
                    found.append({"Use": bool(r["email"]) and (r["status"] == "valid" or r["score"] >= 85),
                                  "Company": s["company"], "Founder": s["person"], "Email": r["email"],
                                  "Confidence": r["score"], "Note": r["error"]})
                    bar.progress(j / int(n_look))
                    err = (r["error"] or "").lower()
                    if any(w in err for w in ("restricted", "limit", "unauthorized", "invalid api key")):
                        st.error(f"Hunter says: {r['error']}")
                        break
                st.session_state.hunter = found
        if st.session_state.get("hunter"):
            got = st.data_editor(pd.DataFrame(st.session_state.hunter), hide_index=True, use_container_width=True,
                                 disabled=["Company", "Founder", "Email", "Confidence", "Note"])
            if st.button("Add the ticked founders", type="primary"):
                n = 0
                for _, r in got[got["Use"]].iterrows():
                    if r["Email"]:
                        fe.activate_founder(data, r["Company"], r["Email"], r["Founder"])
                        n += 1
                fe.save(data)
                st.session_state.pop("hunter")
                flash(f"{n} founders added. Their emails are now in ✉️ Send emails.")
                st.rerun()

# ---------------- Settings ----------------
with tab_settings:
    st.subheader("🤖 Autopilot")
    on = st.toggle("Send follow-ups automatically every evening (5:30–11:30 PM India time = US morning)",
                   value=not sts["paused"])
    if on == sts["paused"]:
        sts["paused"] = not on
        fe.save(data)
        st.rerun()
    st.caption("Needs the laptop on, plugged in and awake in the evening. When it's off, nothing is sent "
               "unless you press Send now.")
    c1, c2 = st.columns(2)
    if c1.button("🔄 Check Gmail for replies", help="Only reads your inbox. Sends nothing."):
        with st.spinner("Reading your Gmail…"):
            fe.run(dry_run=True)
        st.rerun()
    with c2:
        send_all_due_button("send_all_settings")
    l1, l2, l3 = st.columns(3)
    max_new = l1.number_input("New first emails a day", 1, 30, int(sts["max_new_per_day"]))
    max_day = l2.number_input("All emails a day", 1, 60, int(sts["max_per_day"]))
    max_run = l3.number_input("Emails per hourly run", 1, 30, int(sts["max_per_run"]))
    if (max_new, max_day, max_run) != (sts["max_new_per_day"], sts["max_per_day"], sts["max_per_run"]):
        sts.update(max_new_per_day=int(max_new), max_per_day=int(max_day), max_per_run=int(max_run))
        fe.save(data)
        st.toast("Saved")

    st.divider()
    st.subheader("📧 Gmail account")
    if HOSTED:
        st.caption(f"Sending as {env.get('GMAIL_ADDRESS', '(not set)')}. The login is kept in this app's Secrets "
                   "on Streamlit (Settings → Secrets), not in the app itself.")
    if HOSTED:  # never show the password on the web: it stays in Streamlit's Secrets
        sender, sender_name, app_pw = env.get("GMAIL_ADDRESS", ""), env.get("SENDER_NAME", ""), env.get("GMAIL_APP_PASSWORD", "")
    else:
        g1, g2, g3 = st.columns(3)
        sender = g1.text_input("Gmail address", value=env.get("GMAIL_ADDRESS", ""))
        sender_name = g2.text_input("Your name", value=env.get("SENDER_NAME", "Anushree Revankar"))
        app_pw = g3.text_input("App Password (not your normal password)", value=env.get("GMAIL_APP_PASSWORD", ""),
                               type="password")
    if not HOSTED and st.button("Test and save"):
        try:
            core.connect(sender, app_pw).quit()
            write_env({"GMAIL_ADDRESS": sender, "SENDER_NAME": sender_name, "GMAIL_APP_PASSWORD": app_pw})
            st.success("Connected and saved ✔")
        except smtplib.SMTPAuthenticationError:
            st.error("Login failed. Use an App Password from myaccount.google.com/apppasswords.")
        except Exception as e:
            st.error(f"Could not connect: {e}")

    st.divider()
    st.subheader("📜 History")
    with st.expander("Every email sent"):
        st.dataframe(pd.DataFrame(log_rows)[::-1] if log_rows else pd.DataFrame(), hide_index=True,
                     use_container_width=True)
    with st.expander("Autopilot activity log"):
        if fe.ENGINE_LOG.exists():
            st.code("\n".join(fe.ENGINE_LOG.read_text(encoding="utf-8").splitlines()[-40:]))
