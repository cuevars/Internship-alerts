import argparse
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import radar

CONFIG = radar.read_json(Path(__file__).resolve().parents[1] / 'config.json')


def listing(**updates):
    row = dict(id='1', title='Cybersecurity Intern', company_name='Example',
                locations=['Newark, NJ'], terms=['Summer 2027'], active=True,
                degrees=["Bachelor's"], url='https://example.com/job')
    row.update(updates)
    if 'url' not in updates:
        row['url'] = 'https://example.com/job/' + row['id']
    return row


class RadarTests(unittest.TestCase):
    def test_weighted_scoring_and_threshold(self):
        cases = [
            ('Cybersecurity Intern', ['NYC'], 5, True),
            ('Cybersecurity Intern', ['Remote'], 4, True),
            ('IT Intern', ['Remote'], 3, True),
            ('Software Intern', ['Remote'], 2, False),
            ('Data Analyst Intern', ['Philadelphia, PA'], 3, True),
        ]
        for title, locations, expected, accepted in cases:
            with self.subTest(title=title, locations=locations):
                row = listing(title=title, locations=locations)
                self.assertEqual(radar.score_listing(row, CONFIG)[0], expected)
                self.assertEqual(bool(radar.select([row], CONFIG)), accepted)

    def test_rules_count_once_case_insensitive(self):
        row = listing(title='CYBERSECURITY Security Intern', locations=['NYC', 'NYC', 'Remote'])
        self.assertEqual(radar.score_listing(row, CONFIG)[0], 6)

    def test_configurable_threshold_and_weights(self):
        config = copy.deepcopy(CONFIG)
        config['scoring']['minimum_score'] = 5
        self.assertEqual(radar.select([listing()], config), [])
        config['scoring']['rules'][0]['points'] = 5
        self.assertEqual(radar.select([listing()], config)[0]['score'], 6)

    def test_high_score_cannot_override_exclusions(self):
        for updates in [dict(active=False), dict(is_visible=False), dict(terms=['Summer 2026']),
                        dict(degrees=["Master's"]), dict(title='Senior Cybersecurity Intern'),
                        dict(url='javascript:alert(1)'), dict(locations=['Boston, MA'])]:
            self.assertEqual(radar.select([listing(**updates)], CONFIG), [])

    def test_remote_toggle(self):
        config = copy.deepcopy(CONFIG)
        config['include_remote'] = False
        self.assertEqual(radar.select([listing(locations=['Remote'])], config), [])

    def test_resume_recommendations(self):
        for title, resume in [('SOC Intern', 'Cybersecurity'), ('Cybersecurity Data Analyst', 'Cybersecurity'),
                              ('Data Analyst Intern', 'Data'), ('IT Intern', 'IT'), ('Software Intern', 'IT')]:
            self.assertEqual(radar.resume_for(title), resume)

    def test_notification_score_and_resume_at_top(self):
        row = radar.select([listing()], CONFIG)[0]
        title, body, url = radar.notification_payload(row)
        self.assertTrue(title.startswith('Score 4 |'))
        self.assertEqual(body.splitlines()[0], 'Score: 4 | Use resume: Cybersecurity')
        self.assertEqual(url, row['url'])

    def test_ranking_and_deduplication(self):
        lower = listing(id='low', locations=['Remote'], date_posted=999)
        higher = listing(id='high', locations=['NYC'], date_posted=1)
        self.assertEqual([r['id'] for r in radar.select([lower, higher, higher], CONFIG)], ['high', 'low'])

    def test_geography(self):
        for location in ['New York, NY', 'NYC', 'Philadelphia, PA', 'Pittsburgh, PA', 'Jersey City, NJ', 'Remote in USA']:
            row = listing()
            row['locations'] = [location]
            self.assertEqual(len(radar.select([row], CONFIG)), 1, location)
        row = listing()
        row['locations'] = ['Albany, NY', 'Los Angeles, CA']
        self.assertEqual(radar.select([row], CONFIG), [])

    def test_exclusions_and_it_boundary(self):
        for changes in [dict(active=False), dict(terms=['Summer 2026']), dict(degrees=["Master's"]),
                        dict(title='Facilities Intern'), dict(title='Senior Software Engineer')]:
            row = listing()
            row.update(changes)
            self.assertEqual(radar.select([row], CONFIG), [])
        row = listing()
        row['title'] = 'IT Intern'
        self.assertEqual(len(radar.select([row], CONFIG)), 1)

    def test_schema_failure(self):
        for raw in [[], {}, [{'unexpected': 'data'}]]:
            with self.assertRaises(ValueError):
                radar.select(raw, CONFIG)

    def test_partial_failure_retries_only_pending(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            root = Path(folder)
            feed = root / 'feed.json'
            second = listing()
            second['id'] = '2'
            second['url'] = 'https://example.com/job/2'
            feed.write_text(json.dumps([listing(), second]))
            args = argparse.Namespace(config=str(Path(__file__).resolve().parents[1] / 'config.json'),
                fixture=str(feed), report=str(root/'matches.html'), state=str(root/'state.json'),
                test_notify=False, dry_run=False, list=False, baseline=False)
            with patch.dict(os.environ, {'NTFY_TOPIC': 'test-topic-12345'}), patch('radar.notify', side_effect=[None, OSError('offline')]):
                with self.assertRaises(OSError):
                    radar.run(args)
            self.assertEqual(radar.read_json(root/'state.json')['seen'], ['1', 'url:https://example.com/job/1'])
            with patch.dict(os.environ, {'NTFY_TOPIC': 'test-topic-12345'}), patch('radar.notify') as notify:
                radar.run(args)
                self.assertEqual(notify.call_count, 1)
                radar.run(args)
                self.assertEqual(notify.call_count, 1)

    def test_report_escapes_feed_text(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            row = listing()
            row['title'] = '<script>alert(1)</script> Cybersecurity Intern'
            path = Path(folder)/'matches.html'
            radar.report(radar.select([row], CONFIG), path)
            self.assertNotIn('<script>', path.read_text())


if __name__ == '__main__':
    unittest.main()
