import argparse
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import radar

CONFIG = radar.read_json(Path(__file__).resolve().parents[1] / 'config.json')


def listing(**updates):
    return dict(id='1', title='Cybersecurity Intern', company_name='Example',
                locations=['Newark, NJ'], terms=['Summer 2027'], active=True,
                degrees=["Bachelor's"], url='https://example.com/job', **updates)


class RadarTests(unittest.TestCase):
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
            feed.write_text(json.dumps([listing(), second]))
            args = argparse.Namespace(config=str(Path(__file__).resolve().parents[1] / 'config.json'),
                fixture=str(feed), report=str(root/'matches.html'), state=str(root/'state.json'),
                test_notify=False, dry_run=False, list=False, baseline=False)
            with patch.dict(os.environ, {'NTFY_TOPIC': 'test-topic-12345'}), patch('radar.notify', side_effect=[None, OSError('offline')]):
                with self.assertRaises(OSError):
                    radar.run(args)
            self.assertEqual(radar.read_json(root/'state.json')['seen'], ['1'])
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
