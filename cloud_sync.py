"""Keeps the email queue in step between this laptop and the cloud autopilot (a private GitHub repo).

Both sides change the queue: the cloud sends follow-ups, the app sends emails by hand or edits them.
sync() fetches the other side's copy, merges the two person by person, and pushes the result, so neither
side ever overwrites the other.

    python cloud_sync.py        # sync once (used by the cloud workflow after each run)
"""
import csv
import io
import json
import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEQ = HERE / "sequences.json"
LOG = HERE / "sent_log.csv"
CLOUD_LOG = HERE / "followup_engine.log"
IN_CLOUD = bool(os.environ.get("GITHUB_ACTIONS"))
DONE = ("replied", "bounced", "finished", "needs_person", "moved", "stopped")


def git(*args, check=True, timeout=60) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(HERE), *args], capture_output=True, text=True,
                          encoding="utf-8", timeout=timeout, check=check)


GH_REPO = os.environ.get("GH_REPO", "Anushre2005/auto-mail")
BASE_FILE = HERE / ".sync_base.json"


def hosted() -> bool:
    """True when the app runs on Streamlit Cloud: it syncs through the GitHub API with the GH_TOKEN secret."""
    return bool(os.environ.get("GH_TOKEN"))


def _api(method: str, name: str, body: dict | None = None):
    import base64
    import urllib.error
    import urllib.request
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{name}" + ("?ref=main" if method == "GET" else "")
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body else None, headers={
        "Authorization": f"Bearer {os.environ['GH_TOKEN']}", "Accept": "application/vnd.github+json",
        "User-Agent": "email-app"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code in (404,) and method == "GET":
            return None, None
        raise
    if method == "GET":
        return base64.b64decode(data["content"]).decode("utf-8"), data["sha"]
    return data, None


def _put(name: str, text: str, sha: str | None, message: str) -> bool:
    import base64
    import urllib.error
    body = {"message": message, "branch": "main", "content": base64.b64encode(text.encode("utf-8")).decode()}
    if sha:
        body["sha"] = sha
    try:
        _api("PUT", name, body)
        return True
    except urllib.error.HTTPError as e:
        if e.code in (409, 422):  # someone (the autopilot) changed it in between
            return False
        raise


def sync_api(message: str, tries: int = 3) -> str:
    base = json.loads(BASE_FILE.read_text(encoding="utf-8")) if BASE_FILE.exists() else None
    my_seq_text = SEQ.read_text(encoding="utf-8")
    my_log_text = LOG.read_text(encoding="utf-8") if LOG.exists() else ""
    if base is None:  # first sync after start-up: the files on disk are the last known shared copy
        base = {"seq": my_seq_text}
    their_seq, seq_sha = _api("GET", "sequences.json")
    their_log, log_sha = _api("GET", "sent_log.csv")
    mine = json.loads(my_seq_text)
    merged = merge_sequences(json.loads(base["seq"]), mine, json.loads(their_seq)) if their_seq else mine
    seq_text = json.dumps(merged, indent=2, ensure_ascii=False)
    log_text = merge_logs(my_log_text, their_log or "")
    ok = True
    if seq_text != their_seq:
        ok = _put("sequences.json", seq_text, seq_sha, message)
    if ok and log_text != their_log:
        ok = _put("sent_log.csv", log_text, log_sha, message)
    if not ok:
        if tries <= 1:
            return "sync conflict, will retry next time"
        return sync_api(message, tries - 1)
    tmp = SEQ.with_suffix(".tmp")
    tmp.write_text(seq_text, encoding="utf-8")
    tmp.replace(SEQ)
    LOG.write_text(log_text, encoding="utf-8")
    BASE_FILE.write_text(json.dumps({"seq": seq_text}), encoding="utf-8")
    cloud_log, _ = _api("GET", "followup_engine.log")
    if cloud_log is not None:
        CLOUD_LOG.write_text(cloud_log, encoding="utf-8")
    return "synced"


def enabled() -> bool:
    """True once the cloud autopilot is set up: this folder is a git repo with a GitHub remote,
    or the app is hosted and has a GitHub token."""
    if hosted():
        return True
    if not (HERE / ".git").exists():
        return False
    try:
        return bool(git("remote", "get-url", "origin", check=False).stdout.strip())
    except Exception:
        return False


def _show(ref: str, name: str) -> str | None:
    r = git("show", f"{ref}:{name}", check=False)
    return r.stdout if r.returncode == 0 else None


def _pick(base, mine, theirs):
    """Three-way choice for one person's sequence."""
    if mine == theirs or theirs is None:
        return mine
    if mine is None:
        return theirs
    if base is not None and mine == base:
        return theirs          # only the other side changed it
    if base is not None and theirs == base:
        return mine            # only this side changed it
    # both changed: whoever has sent more wins; then a finished/replied state beats "active"
    if len(theirs["sent_steps"]) != len(mine["sent_steps"]):
        return theirs if len(theirs["sent_steps"]) > len(mine["sent_steps"]) else mine
    if theirs["status"] in DONE and mine["status"] == "active":
        return theirs
    return mine


def merge_sequences(base: dict | None, mine: dict, theirs: dict) -> dict:
    b = {s["id"]: s for s in (base or {}).get("sequences", [])}
    m = {s["id"]: s for s in mine["sequences"]}
    t = {s["id"]: s for s in theirs["sequences"]}
    order = list(m) + [i for i in t if i not in m]
    seqs = [x for i in order if (x := _pick(b.get(i), m.get(i), t.get(i))) is not None]
    # settings (pause switch, limits) are only changed in the app, so the laptop's copy wins
    settings = theirs["settings"] if IN_CLOUD else mine["settings"]
    return {**mine, "settings": settings, "sequences": seqs}


def merge_logs(mine: str, theirs: str) -> str:
    rows, seen = [], set()
    header = None
    for text in (theirs, mine):
        rd = csv.reader(io.StringIO(text))
        h = next(rd, None)
        header = header or h
        for r in rd:
            if r and tuple(r) not in seen:
                seen.add(tuple(r))
                rows.append(r)
    rows.sort(key=lambda r: r[0])
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    return out.getvalue()


def sync(message: str = "update queue", tries: int = 3) -> str:
    if not enabled():
        return "cloud not set up"
    if hosted() and not IN_CLOUD:
        return sync_api(message)
    git("fetch", "-q", "origin", "main")
    remote = "origin/main"
    base_seq = _show("HEAD", "sequences.json")
    their_seq, their_log = _show(remote, "sequences.json"), _show(remote, "sent_log.csv")
    mine = json.loads(SEQ.read_text(encoding="utf-8"))
    merged = merge_sequences(json.loads(base_seq) if base_seq else None, mine,
                             json.loads(their_seq)) if their_seq else mine
    log_text = merge_logs(LOG.read_text(encoding="utf-8") if LOG.exists() else "", their_log or "")
    # move onto the cloud's latest commit (keeps files on disk), then write the merged result
    git("reset", "-q", remote)
    if not IN_CLOUD:
        git("checkout", remote, "--", "followup_engine.log", check=False)  # the cloud's activity log
    tmp = SEQ.with_suffix(".tmp")
    tmp.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(SEQ)
    LOG.write_text(log_text, encoding="utf-8")
    git("add", "sequences.json", "sent_log.csv", *(["followup_engine.log"] if IN_CLOUD else []))
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        return "up to date"
    git("commit", "-q", "-m", message)
    r = git("push", "-q", "origin", "HEAD:main", check=False)
    if r.returncode != 0:  # someone pushed in between: merge again
        if tries <= 1:
            return "push failed: " + r.stderr.strip()[:200]
        return sync(message, tries - 1)
    return "synced"


if __name__ == "__main__":
    print(sync("autopilot run" if IN_CLOUD else "update from laptop"))
