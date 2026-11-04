"""Personal internship radar. Python 3.11+, no third-party dependencies."""
import argparse
import html
import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from sources import collect, canonical_url


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def request(url, data=None, headers=None):
    if urlsplit(url).scheme != "https":
        raise ValueError("Only HTTPS endpoints are supported")
    req = Request(url, data=data, headers={"User-Agent": "InternshipRadar/1.0", **(headers or {})})
    with urlopen(req, timeout=60) as response:
        return response.read()


def track(title):
    if re.search(r"cyber|secur|infosec|threat|SOC\b", title, re.I):
        return "Cybersecurity"
    if re.search(r"data|analy|business intelligence|machine learning", title, re.I):
        return "Data"
    if re.search(r"software|developer|programmer|QA\b", title, re.I):
        return "Software"
    return "IT / Technology"


GUIDANCE = {
    "Cybersecurity": "Emphasize relevant security labs, networking, Linux, scripting and CTF work you actually did.",
    "Data": "Emphasize SQL, Python, Excel, data cleaning, dashboards and measurable project results you can explain.",
    "Software": "Emphasize relevant programming languages, Git, testing and projects with clear outcomes.",
    "IT / Technology": "Emphasize troubleshooting, networking, operating systems, scripting and customer support experience.",
}


def score_listing(row, config):
    """Each configured rule contributes at most once, regardless of repetitions."""
    score = 0
    reasons = []
    for rule in config['scoring']['rules']:
        field = rule['field']
        if field not in ('title', 'locations'):
            raise ValueError('Scoring field must be title or locations')
        text = row['title'] if field == 'title' else '; '.join(map(str, row['locations']))
        if re.search(rule['pattern'], text, re.I):
            score += rule['points']
            reasons.append(rule['name'])
    return score, reasons


def resume_for(title):
    category = track(title)
    return category if category in ('Cybersecurity', 'Data') else 'IT'


def notification_payload(row):
    title = f'Score {row["score"]} | New {row["track"]} internship'
    body = (f'Score: {row["score"]} | Use resume: {row["resume"]}\n'
            f'{row["company_name"]} — {row["title"]}\n'
            f'{"; ".join(row["locations"])}\n'
            f'Source: {row.get("source", "Simplify")} | Term: {", ".join(row["terms"]) or "Unspecified - verify dates"}\n'
            f'Matched: {", ".join(row["score_reasons"])}\n'
            f'{GUIDANCE[row["track"]]}\nSophomore eligibility: check posting.\n{row["url"]}')
    return title, body, row['url']


def select(raw, config):
    if not isinstance(raw, list) or not raw:
        raise ValueError("Feed must be a nonempty list; refusing to replace the current shortlist")
    required = {"id", "company_name", "title", "url", "locations", "terms"}
    if not any(isinstance(row, dict) and required <= row.keys() for row in raw):
        raise ValueError("Feed schema changed: no recognizable listings")
    matches = {}
    for row in raw:
        if not isinstance(row, dict) or not required <= row.keys():
            continue
        if row.get("active") is not True or row.get("is_visible", True) is False:
            continue
        if not isinstance(row["title"], str) or not isinstance(row["locations"], list) or not isinstance(row["terms"], list):
            continue
        unspecified = (row.get('direct_employer') and (not row['terms'] or
                       any(term == 'Unspecified season ' + target.split()[-1]
                           for term in row['terms'] for target in config['terms']))
                       and config.get('include_unspecified_employer_terms', False))
        if not unspecified and not set(config["terms"]) & set(row["terms"]):
            continue
        degrees = row.get("degrees", [])
        if degrees and not any("bachelor" in str(d).lower() or "undergrad" in str(d).lower() for d in degrees):
            continue
        title = row["title"]
        if not re.search(config["role_pattern"], title, re.I) or re.search(config["exclude_pattern"], title, re.I):
            continue
        locations = "; ".join(str(x) for x in row["locations"])
        local = re.search(config["location_pattern"], locations, re.I)
        remote = config["include_remote"] and re.search(r"\bremote\b", locations, re.I)
        if not (local or remote) or urlsplit(str(row["url"])).scheme != "https":
            continue
        score, reasons = score_listing(row, config)
        if score < config['scoring']['minimum_score']:
            continue
        item = dict(row, track=track(title), score=score, score_reasons=reasons, resume=resume_for(title))
        key = canonical_url(row['url'])
        if key in matches:
            matches[key]['aliases'].append(str(row['id']))
            continue
        item['aliases'] = [str(row['id'])]
        matches[key] = item
    return sorted(matches.values(), key=lambda r: (r['score'], str(r.get("date_posted", 0))), reverse=True)


def report(rows, path, statuses=()):
    esc = lambda value: html.escape(str(value), quote=True)
    cards = []
    for row in rows:
        cards.append(f'<article><small>Score {esc(row["score"])} · Use resume: {esc(row["resume"])} · {esc(row["track"])}</small><h2>{esc(row["title"])}</h2>'
                     f'<p>{esc(row["company_name"])} · {esc("; ".join(row["locations"]))}</p>'
                     f'<p>Source: {esc(row.get("source", "Simplify"))} · Term: {esc(", ".join(row["terms"]) or "Unspecified — verify dates")}</p>'
                     f'<p>{esc(GUIDANCE[row["track"]])}</p><p>Check graduation year, work authorization, dates and location restrictions in the posting.</p>'
                     f'<a href="{esc(row["url"])}" rel="noopener noreferrer">View posting / apply →</a></article>')
    content = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    content += '<title>Internship Radar</title><style>body{font:16px system-ui;background:#eef3f8;color:#18283c;max-width:850px;margin:32px auto;padding:16px}article{background:white;padding:24px;border-radius:16px;margin:18px 0}h1{font-size:36px}h2{font-size:21px}small,a{color:#075eaa}p{line-height:1.6}</style>'
    content += f'<h1>Internship Radar</h1><p>NYIT CS · NYC / NJ / PA / Remote · Summer 2027</p><p>{len(rows)} matches. Updated {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}.</p>'
    content += '<p>' + '<br>'.join(esc(status) for status in statuses) + '</p>'
    content += '<p>Keep Cybersecurity, IT and Data résumé versions in your phone’s Files or cloud drive. Duplicate the closest version for each application; use the posting’s keywords only where truthful. Save the final PDF with the company name.</p>'
    content += ''.join(cards) or '<p>No matching roles right now.</p>'
    Path(path).write_text(content + '</html>', encoding="utf-8")


def notify(title, body, url=""):
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{10,128}", topic):
        raise ValueError("Set NTFY_TOPIC to a random topic of 10–128 letters, digits, underscores or hyphens")
    headers = {"Title": title.encode("ascii", "replace").decode(), "Tags": "briefcase"}
    if url:
        headers["Click"] = url
    token = os.environ.get("NTFY_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    server = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
    request(server + '/' + topic, body.encode("utf-8"), headers)


def run(args):
    config = read_json(args.config)
    if args.test_notify:
        notify("Internship Radar test", "Your phone is connected to Internship Radar.")
        print("Test delivered to notification service; confirm it appears on your phone.")
        return
    if args.fixture:
        raw, statuses, failures = read_json(args.fixture), [], []
    else:
        raw, statuses, failures = collect(config, request)
    for status in statuses:
        print(status)
    rows = select(raw, config) if raw else []
    for row in rows:
        print(f'Score {row["score"]} | Resume: {row["resume"]} | {row["company_name"]} | {row["title"]} | {"; ".join(row["locations"])}\n{row["url"]}')
    print(f"{len(rows)} current matches")
    if args.dry_run:
        if failures:
            raise RuntimeError('Some sources failed')
        return
    report(rows, args.report, statuses)
    if args.list:
        if failures:
            raise RuntimeError('Some sources failed')
        return
    state_path = Path(args.state)
    state = read_json(state_path) if state_path.exists() else {"seen": []}
    if not isinstance(state, dict) or not isinstance(state.get("seen"), list):
        raise ValueError("Invalid state file; restore it before resuming alerts")
    seen = set(state["seen"])
    if args.baseline:
        for row in rows:
            seen.update(row['aliases'])
            seen.add('url:' + canonical_url(row['url']))
    else:
        # Send separately so every listing has its own tappable application link.
        # Persist after each successful send so a later failure retries only pending jobs.
        if not os.environ.get("NTFY_TOPIC"):
            raise ValueError("No NTFY_TOPIC configured. Use --list to preview or --baseline to skip existing jobs")
        limit = int(config["max_alerts_per_run"])
        if limit < 1:
            raise ValueError("max_alerts_per_run must be positive")
        for row in [r for r in rows if not (set(r['aliases']) & seen)
                    and 'url:' + canonical_url(r['url']) not in seen][:limit]:
            notify(*notification_payload(row))
            seen.update(row['aliases'])
            seen.add('url:' + canonical_url(row['url']))
            save_state(state_path, seen)
    save_state(state_path, seen)
    if failures:
        raise RuntimeError('Some sources failed; successful sources were processed')


def save_state(path, seen):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps({"seen": sorted(seen)}, indent=2), encoding="utf-8")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='config.json')
    parser.add_argument('--state', default='state.json')
    parser.add_argument('--report', default='matches.html')
    parser.add_argument('--fixture')
    mode = parser.add_mutually_exclusive_group()
    for flag in ['list', 'dry-run', 'baseline', 'test-notify']:
        mode.add_argument('--' + flag, action='store_true')
    try:
        run(parser.parse_args())
    except Exception as exc:
        # Avoid exposing notification endpoints or credentials in workflow logs.
        print(f'Radar failed ({type(exc).__name__}). Check configuration, network and feed format. State retains successful sends.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
