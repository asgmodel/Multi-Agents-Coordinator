import json
from pathlib import Path
import shutil
import tempfile
import unittest

from multi_agents import core


class CoordinatorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'agents').mkdir()
        shutil.copyfile(core.ROOT / 'agents' / 'team.json', self.root / 'agents' / 'team.json')
        core.init('demo', 'asgmodel/example', root=self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_register_has_one_json(self):
        self.assertEqual(len(list((self.root / 'tasks' / 'demo').glob('*.json'))), 1)
        with self.assertRaises(core.Invalid):
            core.init('demo', 'other/repo', root=self.root)

    def test_blocks_traversal(self):
        with self.assertRaises(core.Invalid):
            core.init('../other', 'asgmodel/example', root=self.root)

    def test_unique_ids_and_dependencies(self):
        core.add('demo', 'B01', 'Backend API', root=self.root)
        with self.assertRaises(core.Invalid):
            core.add('demo', 'B01', 'Again', root=self.root)
        with self.assertRaises(core.Invalid):
            core.add('demo', 'B02', 'Test', depends=['B01', 'B01'], root=self.root)
        core.add('demo', 'B02', 'Frontend React', depends=['B01'], root=self.root)
        self.assertFalse(core.ready(core.get_task(core.load('demo', self.root), 'B02'), core.load('demo', self.root)))

    def test_bad_owner_rejected(self):
        with self.assertRaises(core.Invalid):
            core.add('demo', 'T1', 'Safe', owner='UNKNOWN', root=self.root)
        self.assertEqual(core.load('demo', self.root)['tasks'], [])

    def test_cycle_validation(self):
        core.add('demo', 'A', 'API', root=self.root)
        core.add('demo', 'B', 'Frontend', depends=['A'], root=self.root)
        data = core.load('demo', self.root)
        data['tasks'][0]['depends_on'] = ['B']
        self.assertTrue(any('cycle' in msg for msg in core.validate(data, self.root)))

    def test_done_needs_evidence_and_approval(self):
        core.add('demo', 'A', 'API', owner='AI-01', root=self.root)
        with self.assertRaises(core.Invalid):
            core.update('demo', 'A', status='DONE', root=self.root)
        self.assertEqual(core.load('demo', self.root)['tasks'][0]['status'], 'PLANNED')
        core.update('demo', 'A', status='DONE', owner_approved=True, tests_passed=True,
                    reviewer='AI-04', evidence='PR #1 checks', root=self.root)
        self.assertEqual(core.load('demo', self.root)['tasks'][0]['status'], 'DONE')

    def test_self_review_blocked(self):
        core.add('demo', 'A', 'API', owner='AI-01', root=self.root)
        with self.assertRaises(core.Invalid):
            core.update('demo', 'A', status='DONE', owner_approved=True, tests_passed=True,
                        reviewer='AI-01', evidence='PR #1', root=self.root)

    def test_dependency_gate(self):
        core.add('demo', 'A', 'Backend', owner='AI-01', root=self.root)
        core.add('demo', 'B', 'Frontend', owner='AI-02', depends=['A'], root=self.root)
        with self.assertRaises(core.Invalid):
            core.update('demo', 'B', status='DONE', owner_approved=True, tests_passed=True,
                        reviewer='AI-04', evidence='CI', root=self.root)
        core.update('demo', 'A', status='DONE', owner_approved=True, tests_passed=True,
                    reviewer='AI-04', evidence='CI', root=self.root)
        self.assertTrue(core.ready(core.get_task(core.load('demo', self.root), 'B'), core.load('demo', self.root)))

    def test_blocker_prevents_done(self):
        core.add('demo', 'A', 'API', owner='AI-01', root=self.root)
        core.update('demo', 'A', blocker='Missing contract', root=self.root)
        with self.assertRaises(core.Invalid):
            core.update('demo', 'A', status='DONE', root=self.root)

    def test_dispatch_dry_run_and_apply(self):
        core.add('demo', 'A', 'Frontend React screen', root=self.root)
        core.add('demo', 'B', 'Backend SQL query', root=self.root)
        proposed = core.dispatch('demo', root=self.root)
        self.assertEqual({x['task']: x['owner'] for x in proposed}, {'A': 'AI-02', 'B': 'AI-01'})
        self.assertTrue(all(t['owner'] is None for t in core.load('demo', self.root)['tasks']))
        core.dispatch('demo', apply=True, root=self.root)
        self.assertEqual([x['owner'] for x in core.load('demo', self.root)['tasks']], ['AI-02', 'AI-01'])

    def test_unknown_work_goes_to_triage(self):
        core.add('demo', 'X', 'Something entirely new', root=self.root)
        self.assertEqual(core.dispatch('demo', root=self.root)[0]['owner'], 'AI-04')

    def test_global_parallel_limit(self):
        for i in range(9):
            core.add('demo', f'T{i}', f'Backend API work {i}', root=self.root)
        self.assertEqual(len(core.dispatch('demo', root=self.root)), 4)

    def test_dedupe_artifact_and_evidence(self):
        core.add('demo', 'A', 'Backend', owner='AI-01', root=self.root)
        core.update('demo', 'A', artifact='PR #1', evidence='CI #2', root=self.root)
        core.update('demo', 'A', artifact='PR #1', evidence='CI #2', root=self.root)
        task = core.load('demo', self.root)['tasks'][0]
        self.assertEqual(task['artifacts'], ['PR #1'])
        self.assertEqual(task['verification']['evidence'], ['CI #2'])

    def test_validate_all(self):
        self.assertEqual(core.validate_all(self.root), {})


if __name__ == '__main__':
    unittest.main()
