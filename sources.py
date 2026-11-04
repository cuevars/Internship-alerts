"""Adapters for public, employer-owned career listings; standard library only."""
import html
from html.parser import HTMLParser
import json
import re
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode


def canonical_url(url):
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query) if not k.lower().startswith('utm_')
             and k.lower() not in ('source', 'src', 'gh_src', 'gh_jid')]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip('/'), urlencode(sorted(query)), ''))


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain(value):
    parser = Text()
    parser.feed(html.unescape(value))
    return ' '.join(' '.join(parser.parts).split())


def terms_for(title, description=''):
    # Never invent Summer 2027 from the current date or a board's category.
    # Description dates often mean graduation windows, not internship dates.
    terms = re.findall(r'\b(Spring|Summer|Fall|Winter)\s*[-–]?\s*(20\d{2})\b', title, re.I)
    if terms:
        return sorted({f'{season.title()} {year}' for season, year in terms})
    return [f'Unspecified season {year}' for year in sorted(set(re.findall(r'\b20\d{2}\b', title)))]


def normalize(source, job_id, title, url, locations, description=''):
    return dict(id=f'{source["name"]}:{job_id}', company_name=source['company'], title=title,
                url=url, locations=locations, terms=terms_for(title, description), active=True,
                degrees=[], source=source['name'], direct_employer=True, date_posted=0)


def greenhouse(source, fetch):
    data = json.loads(fetch(source['url']))
    if not isinstance(data, dict) or not isinstance(data.get('jobs'), list):
        raise ValueError('Greenhouse response schema changed')
    rows = []
    for job in data['jobs']:
        title = job['title']
        if not re.search(r'\b(intern\w*|co[ -]?op)\b', title, re.I):
            continue
        location = job['location']['name']
        rows.append(normalize(source, job['id'], title, job['absolute_url'],
                              [location], plain(job.get('content', ''))))
    return rows


class HersheyPage(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = None
        self.capture = None
        self.depth = 0
        self.total = None
        self.text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get('class', '').split()
        if tag == 'tr':
            self.row = dict(title='', location='', url='')
        if self.capture:
            self.depth += 1
        elif self.row is not None:
            if tag == 'a' and 'jobTitle-link' in classes and not self.row['title']:
                self.row['url'] = attrs['href']
                self.capture, self.depth = 'title', 1
            elif tag == 'span' and 'jobLocation' in classes and not self.row['location'].strip():
                self.capture, self.depth = 'location', 1

    def handle_data(self, data):
        self.text.append(data)
        if self.capture and self.row is not None:
            self.row[self.capture] += data

    def handle_endtag(self, tag):
        if self.capture:
            self.depth -= 1
            if self.depth == 0:
                self.capture = None
        if tag == 'tr' and self.row is not None:
            if self.row['url']:
                # Responsive desktop/mobile markup repeats titles and locations.
                self.rows.append(self.row)
            self.row = None


def hershey(source, fetch):
    rows = {}
    offset = 0
    for _ in range(source.get('max_pages', 20)):
        separator = '&' if '?' in source['url'] else '?'
        page = HersheyPage()
        page.feed(fetch(source['url'] + separator + f'startrow={offset}').decode('utf-8'))
        count = re.search(r'Results\s+(\d+)\s*[–-]\s*(\d+)\s+of\s+(\d+)', ' '.join(' '.join(page.text).split()))
        if not count:
            raise ValueError('Hershey results/pagination markup changed')
        start, end, total = map(int, count.groups())
        if total == 0:
            return []
        if not page.rows or end <= offset:
            raise ValueError('Hershey pagination did not advance')
        for row in page.rows:
            url = urljoin(source['url'], row['url'])
            if urlsplit(url).netloc != urlsplit(source['url']).netloc:
                raise ValueError('Unexpected employer link host')
            title = ' '.join(row['title'].split())
            location = ' '.join(row['location'].split())
            key = url.rstrip('/').split('/')[-1]
            rows[key] = normalize(source, key, title, url, [location])
        if end >= total:
            return list(rows.values())
        offset = end
    raise ValueError('Hershey page limit reached before all results were read')


def collect(config, fetch):
    rows, statuses, failures = [], [], []
    sources = [dict(name='Simplify', type='simplify', url=config['feed_url'])] + config.get('employer_sources', [])
    for source in sources:
        if not source.get('enabled', True):
            continue
        try:
            if source['type'] == 'simplify':
                result = json.loads(fetch(source['url']))
                if not isinstance(result, list) or not result:
                    raise ValueError('Invalid aggregate feed')
            else:
                adapter = {'greenhouse': greenhouse, 'hershey': hershey}[source['type']]
                result = adapter(source, fetch)
            rows.extend(result)
            statuses.append(f'{source["name"]}: OK ({len(result)} listings)')
        except Exception as exc:
            failures.append(source['name'])
            statuses.append(f'{source["name"]}: FAILED ({type(exc).__name__}); retry next run')
    if len(failures) == len(sources):
        raise ValueError('All sources failed')
    return rows, statuses, failures
