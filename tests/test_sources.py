import copy
import json
import unittest
from unittest.mock import Mock
import radar
import sources
from test_radar import CONFIG, listing


class SourceTests(unittest.TestCase):
    def test_distinct_query_job_ids_are_not_collapsed(self):
        first = listing(id='one', url='https://www.mongodb.com/careers/job/?gh_jid=111')
        second = listing(id='two', url='https://www.mongodb.com/careers/job/?gh_jid=222')
        self.assertEqual(len(radar.select([first, second], CONFIG)), 2)
        self.assertEqual(sources.canonical_url('https://example.com/jobs/111?gh_jid=111'), 'https://example.com/jobs/111')

    def test_employer_https_upgrade_is_opt_in(self):
        source = dict(name='Example', company='Example', url='https://example.com/api', force_https=True)
        data = {'jobs': [dict(id=1, title='IT Intern', absolute_url='http://example.com/careers?gh_jid=1', location={'name': 'NYC'})]}
        rows = sources.greenhouse(source, lambda _: json.dumps(data).encode())
        self.assertEqual(rows[0]['url'], 'https://example.com/careers?gh_jid=1')

    def test_graduation_dates_are_not_internship_dates(self):
        self.assertEqual(sources.terms_for('Data Intern', 'Graduation between Fall 2027 and Summer 2028'), [])
        self.assertEqual(sources.terms_for('IT Intern 2026'), ['Unspecified season 2026'])
        self.assertEqual(radar.select([listing(direct_employer=True, terms=['Unspecified season 2026'])], CONFIG), [])

    def test_greenhouse_only_internships_and_explicit_terms(self):
        source = dict(name='Employer', company='Example', url='https://example.com/api')
        jobs = [dict(id=1, title='Data Intern - Summer 2027', absolute_url='https://example.com/job/1',
                     location={'name': 'New York, NY'}, content='<p>SQL</p>'),
                dict(id=2, title='Data Engineer', absolute_url='https://example.com/job/2',
                     location={'name': 'NYC'}, content='')]
        rows = sources.greenhouse(source, lambda url: json.dumps({'jobs': jobs}).encode())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['terms'], ['Summer 2027'])
        self.assertEqual(rows[0]['id'], 'Employer:1')
        self.assertEqual(len(radar.select(rows, CONFIG)), 1)

    def test_unspecified_is_configurable_and_other_season_excluded(self):
        row = listing(direct_employer=True, terms=[])
        self.assertEqual(len(radar.select([row], CONFIG)), 1)
        config = copy.deepcopy(CONFIG)
        config['include_unspecified_employer_terms'] = False
        self.assertEqual(radar.select([row], config), [])
        row['terms'] = ['Spring 2027']
        self.assertEqual(radar.select([row], CONFIG), [])

    def test_cross_source_url_dedup(self):
        first = listing(url='https://example.com/job/1?utm_source=list')
        second = listing(id='Employer:1', direct_employer=True, url='https://example.com/job/1')
        result = radar.select([first, second], CONFIG)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['aliases'], ['1', 'Employer:1'])

    def test_hershey_pagination_and_responsive_duplicates(self):
        source = dict(name='Hershey', company='The Hershey Company', url='https://example.com/interns')
        def page(number):
            return (f'Results {number} – {number} of 2<table><tr><td>'
                    f'<a class="jobTitle-link" href="/job/{number}">IT Intern Summer 2027</a>'
                    f'<a class="jobTitle-link" href="/job/{number}">IT Intern Summer 2027</a>'
                    '<span class="jobLocation"><span class="jobLocation">Hershey, PA, US</span></span>'
                    '</td></tr></table>').encode()
        fetch = Mock(side_effect=[page(1), page(2)])
        rows = sources.hershey(source, fetch)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['title'], 'IT Intern Summer 2027')
        self.assertEqual(rows[0]['locations'], ['Hershey, PA, US'])
        self.assertTrue(fetch.call_args_list[1].args[0].endswith('startrow=1'))

    def test_markup_changes_are_failures_not_empty_results(self):
        with self.assertRaises(ValueError):
            sources.hershey(dict(name='Hershey', company='Hershey', url='https://example.com'), lambda _: b'Access denied')
        with self.assertRaises(ValueError):
            sources.greenhouse(dict(url='https://example.com'), lambda _: b'{}')

    def test_failed_source_does_not_discard_other_sources(self):
        config = dict(feed_url='https://example.com/feed', employer_sources=[dict(name='Broken', type='greenhouse', url='https://example.com/broken')])
        fetch = Mock(side_effect=[json.dumps([listing()]).encode(), OSError('offline')])
        rows, statuses, failures = sources.collect(config, fetch)
        self.assertEqual(len(rows), 1)
        self.assertEqual(failures, ['Broken'])
        self.assertIn('FAILED', statuses[-1])

    def test_valid_empty_employer_feed(self):
        self.assertEqual(sources.greenhouse(dict(url='https://example.com'), lambda _: b'{"jobs": []}'), [])


if __name__ == '__main__':
    unittest.main()
