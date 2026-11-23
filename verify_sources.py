"""Read-only check of explicitly configured candidate employer feeds."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import radar
import sources


CANDIDATES = {
    'Datadog': 'datadog', 'Cloudflare': 'cloudflare', 'MongoDB': 'mongodb',
    'Snyk': 'snyk', 'Axonius': 'axonius', 'SentinelOne': 'sentinelone',
    'Tenable': 'tenable', 'Zscaler': 'zscaler', 'Okta': 'okta',
    'Robinhood': 'robinhood', 'Coinbase': 'coinbase', 'Affirm': 'affirm',
    'Point72': 'point72', 'Two Sigma': 'twosigma', 'SeatGeek': 'seatgeek',
    'Zocdoc': 'zocdoc', 'Yext': 'yext', 'Dropbox': 'dropbox',
    'Squarespace': 'squarespace',
}


def verify(pair):
    company, token = pair
    source = dict(name=company, company=company, type='greenhouse',
                  url=f'https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true')
    try:
        payload = radar.request(source['url'])
        data = json.loads(payload)
        jobs = data['jobs']
        if not isinstance(jobs, list):
            raise ValueError('Invalid jobs format')
        # Retain evidence for inspecting employer identity and parser behavior.
        Path(f'{token}-probe.json').write_bytes(payload)
        rows = sources.greenhouse(source, lambda _: payload)
        matches = radar.select(rows, radar.read_json('config.json')) if rows else []
        evidence = sorted({job.get('company_name', '') for job in jobs})
        print(f'{company}: {len(jobs)} jobs, {len(rows)} internships, {len(matches)} matches; employer={evidence}', flush=True)
        return dict(source=source, jobs=len(jobs), internships=len(rows), matches=len(matches),
                    employer_names=evidence, sample_urls=[job['absolute_url'] for job in jobs[:2]])
    except Exception as exc:
        print(f'{company}: FAILED {type(exc).__name__}', flush=True)
        return dict(source=source, error=type(exc).__name__)


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(verify, CANDIDATES.items()))
    Path('employers-probe.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
