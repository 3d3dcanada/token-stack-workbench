"""Offline negative controls for the real-host evidence validator."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('host_probe', Path(__file__).resolve().parents[1] / 'tools/host_probe.py')
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)


def fixture():
    cases = []
    for mode, deny in ((True, False), (False, False), (True, True)):
        output = ('Command blocked by PreToolUse hook: RTK adapter BLOCKED: '
                  '3D3D guard BLOCKED: force/mirror push') if deny else 'token-stack-canary.txt'
        event = {'item': {'type': 'command_execution', 'status': 'completed',
                         'exit_code': 0, 'command': "/bin/bash -lc 'rtk git status'"}}
        cases.append({'code_mode': mode, 'deny': deny, 'exit': 0,
                      'stdout': '' if deny else json.dumps(event),
                      'requests': [{}, {'input': [{'type': 'custom_tool_call_output',
                          'call_id': 'call_probe', 'output': output}]}]})
    return cases


class HostValidationTests(unittest.TestCase):
    def test_complete_evidence(self):
        host.validate(fixture())

    def test_missing_rewrite_denial_execution_and_case(self):
        good = fixture()
        bad = copy.deepcopy(good)
        bad[0]['stdout'] = bad[0]['stdout'].replace('rtk git status', 'git status')
        with self.assertRaisesRegex(ValueError, 'rewrite'):
            host.validate(bad)
        bad = copy.deepcopy(good)
        bad[2]['requests'][1]['input'] = []
        with self.assertRaisesRegex(ValueError, 'guard denial'):
            host.validate(bad)
        bad = copy.deepcopy(good)
        bad[2]['stdout'] = good[0]['stdout']
        with self.assertRaisesRegex(ValueError, 'guard denial'):
            host.validate(bad)
        with self.assertRaisesRegex(ValueError, 'missing or duplicate'):
            host.validate(good[:2])


if __name__ == '__main__':
    unittest.main()
