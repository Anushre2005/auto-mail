"""Find a founder's direct work email with the Hunter.io API (free plan: 25 searches/month).

Get a free API key at https://hunter.io/api-keys after signing up, and paste it in the app.
"""
import json
import urllib.error
import urllib.parse
import urllib.request


def find_email(api_key: str, domain: str, full_name: str) -> dict:
    """Return {"email", "score", "status", "error"} for a person at a company domain."""
    parts = full_name.split()
    params = {"domain": domain, "first_name": parts[0], "last_name": " ".join(parts[1:]) or parts[0],
              "api_key": api_key}
    url = "https://api.hunter.io/v2/email-finder?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "cold-email-sender"}),
                                    timeout=30) as r:
            data = json.load(r).get("data") or {}
        return {"email": data.get("email") or "", "score": data.get("score") or 0,
                "status": (data.get("verification") or {}).get("status") or "", "error": ""}
    except urllib.error.HTTPError as e:
        try:
            msg = json.load(e).get("errors", [{}])[0].get("details", str(e))
        except Exception:
            msg = str(e)
        return {"email": "", "score": 0, "status": "", "error": msg}
    except Exception as e:
        return {"email": "", "score": 0, "status": "", "error": str(e)}
