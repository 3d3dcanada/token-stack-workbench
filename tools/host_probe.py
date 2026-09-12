"""Exercise real Codex hooks with a loopback scripted Responses endpoint; no model/API spend.

Only fixed git-status and inert printf commands are offered to the host. No command
received from an external service or test payload is executed by this harness.
"""
import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import tempfile
import threading
import tomllib


def probe(code_mode=True, deny=False):
    requests = []
    command = "printf '%s\\n' 'git push --force TOKEN_STACK_INERT_CANARY'" if deny else 'git status'

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            body = b'{"models":[]}'
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            request = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append(request)
            if len(requests) == 1:
                args = {'cmd': command, 'workdir': workspace, 'max_output_tokens': 2000}
                if code_mode:
                    item = {'type': 'custom_tool_call', 'id': 'fc_probe', 'call_id': 'call_probe',
                            'name': 'exec', 'input': 'text(await tools.exec_command(' + json.dumps(args) + '));'}
                else:
                    item = {'type': 'function_call', 'id': 'fc_probe', 'call_id': 'call_probe',
                            'name': 'exec_command', 'arguments': json.dumps(args)}
            else:
                item = {'type': 'message', 'id': 'msg_done', 'role': 'assistant',
                        'content': [{'type': 'output_text', 'text': 'Local probe complete.'}]}
            events = [
                {'type': 'response.created', 'response': {'id': 'resp_probe'}},
                {'type': 'response.output_item.done', 'output_index': 0, 'item': item},
                {'type': 'response.completed', 'response': {'id': 'resp_probe', 'status': 'completed',
                    'output': [item], 'usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}}},
            ]
            body = ''.join('event: ' + x['type'] + '\ndata: ' + json.dumps(x) + '\n\n' for x in events).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    config = tomllib.loads((Path.home() / '.codex/config.toml').read_text())
    if config.get('projects', {}).get(str(Path.home()), {}).get('trust_level') != 'trusted':
        raise RuntimeError('Home must already be a trusted Codex project; this probe never grants trust')
    with tempfile.TemporaryDirectory(prefix='token-stack-host-') as workspace:
        subprocess.run(['git', 'init', '-q', workspace], check=True, capture_output=True)
        Path(workspace, 'token-stack-canary.txt').write_text('Local harmless fixture\n')
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        argv = ['codex', 'exec', '--json', '--ephemeral', '--skip-git-repo-check',
                '-C', str(Path.home()), '-s', 'danger-full-access',
                '-c', 'model_provider="token_stack_fixture"',
                '-c', 'model_providers.token_stack_fixture={name="Local token-stack fixture",base_url="http://127.0.0.1:' + str(server.server_port) + '/v1",wire_api="responses",requires_openai_auth=false}',
                '-c', 'features.code_mode_host=' + str(code_mode).lower()]
        for name in config.get('mcp_servers', {}):
            argv += ['-c', 'mcp_servers.' + name + '.enabled=false']
        argv += ['Run the single harmless local diagnostic tool call supplied by the fixture.']
        try:
            result = subprocess.run(argv, input='', text=True, capture_output=True, timeout=45)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
    return {'code_mode': code_mode, 'deny': deny, 'argv': argv, 'exit': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr, 'requests': requests}


def validate(results):
    """Check execution and model-visible denial, never a hook-registration message."""
    expected = {(True, False), (False, False), (True, True)}
    if {(r['code_mode'], r['deny']) for r in results} != expected or len(results) != 3:
        raise ValueError('missing or duplicate host probe cases')
    for result in results:
        if result['exit'] != 0 or len(result['requests']) != 2:
            raise ValueError('host did not complete the tool round trip')
        events = [json.loads(line) for line in result['stdout'].splitlines() if line.strip()]
        executions = [e['item'] for e in events if e.get('item', {}).get('type') == 'command_execution']
        outputs = [i for i in result['requests'][1].get('input', [])
                   if i.get('call_id') == 'call_probe' and i.get('type', '').endswith('_output')]
        returned = json.dumps(outputs, ensure_ascii=False)
        if result['deny']:
            if executions or 'Command blocked by PreToolUse hook: RTK adapter BLOCKED:' not in returned or '3D3D guard BLOCKED: force/mirror push' not in returned:
                raise ValueError('guard denial did not stop nested execution and reach code mode')
        else:
            completed = [e for e in executions if e.get('status') == 'completed']
            if len(completed) != 1 or completed[0].get('exit_code') != 0 or completed[0].get('command') != "/bin/bash -lc 'rtk git status'" or 'token-stack-canary.txt' not in returned:
                raise ValueError('RTK rewrite did not reach successful execution and tool output')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--plain', action='store_true')
    parser.add_argument('--deny', action='store_true')
    parser.add_argument('--output')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--fixture', help='Validate saved host evidence only; never executes its commands')
    args = parser.parse_args()
    if args.check:
        try:
            results = json.loads(Path(args.fixture).read_text()) if args.fixture else [probe(), probe(False), probe(deny=True)]
            validate(results)
        except Exception as exc:
            print('FAIL: Codex host behavior: ' + str(exc))
            sys.exit(1)
        if args.output:
            Path(args.output).write_text(json.dumps(results, indent=2) + '\n')
        print('PASS: Codex host executes RTK rewrites in nested and plain tools; guard blocks inert nested canary before execution' + (' (SAVED FIXTURE ONLY)' if args.fixture else ' (LIVE LOCAL HOST)'))
        sys.exit(0)
    if not args.output:
        parser.error('--output is required without --check')
    result = probe(not args.plain, args.deny)
    Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('requests', 'argv')}, indent=2))
