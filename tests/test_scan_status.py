import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import radar
from test_radar import listing


class ScanStatusTests(unittest.TestCase):
    def test_status_updates_when_nothing_new(self):
        self.check_run(seen=['1'], expected_delivered=0, expected_status='success')

    def test_delivery_failure_is_visible_and_not_marked_seen(self):
        self.check_run(seen=[], expected_delivered=0, expected_status='failed', fail=True)

    def test_new_job_is_delivered_and_reported(self):
        self.check_run(seen=[], expected_delivered=1, expected_status='success')

    def check_run(self, seen, expected_delivered, expected_status, fail=False):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            root = Path(folder)
            state = root / 'state.json'
            state.write_text(json.dumps({'seen': seen}), encoding='utf-8')
            args = argparse.Namespace(config=str(Path(__file__).resolve().parents[1] / 'config.json'),
                fixture=None, report=str(root/'matches.html'), state=str(state),
                scan_status=str(root/'scan-status.md'), matches_markdown=str(root/'matches.md'),
                test_notify=False, dry_run=False, list=False, baseline=False)
            with patch('radar.collect', return_value=([listing()], ['Test source: OK (1 listings)'], [])), \
                 patch('radar.notify', side_effect=OSError('offline') if fail else None) as notify, \
                 patch.dict(os.environ, {'NTFY_TOPIC': 'test-topic-12345', 'GITHUB_STEP_SUMMARY': ''}), \
                 contextlib.redirect_stdout(io.StringIO()):
                if fail:
                    with self.assertRaises(OSError):
                        radar.run(args)
                else:
                    radar.run(args)
            status = (root/'scan-status.md').read_text(encoding='utf-8')
            self.assertIn(f'Status: **{expected_status}**', status)
            self.assertIn(f'Alerts delivered: **{expected_delivered}**', status)
            self.assertIn('Test source: OK', status)
            self.assertIn('Checked:', status)
            self.assertIn('Cybersecurity Intern', (root/'matches.md').read_text())
            if seen:
                notify.assert_not_called()
            if fail:
                self.assertEqual(radar.read_json(state)['seen'], [])


if __name__ == '__main__':
    unittest.main()
