# Verification and limits

Source workstation observations, September 12, 2026:

| Check | Result |
|---|---|
| Original doctor | Exit 0; registration/direct tests only |
| Guard denial in active Codex code mode | Blocked by the installed RTK adapter and guard |
| Real host, nested plain git status | Executed `rtk git status`, exit 0, fixture filename returned |
| Real host, plain exec_command | Same successful rewrite |
| Real host, inert nested canary | Denied before execution; rejection returned to code mode |
| Adapter tests | 16 tests passed |
| Broken rewrite saved fixture | Exit 1 |
| Broken guard saved fixture | Exit 1 |
| Updated machine doctor | Exit 0, no warnings |
| Installed guard and adapter | Byte hashes unchanged |
| Claude settings and memory | Byte hashes unchanged |
| Codex config | Only fixture-created project entries removed; other bytes match by hash reconstruction |

Representative host output:

```text
command: /bin/bash -lc 'rtk git status'
exit_code: 0
* No commits yet on master
?? token-stack-canary.txt

PASS: Codex host executes RTK rewrites in nested and plain tools;
guard blocks inert nested canary before execution (LIVE LOCAL HOST)
```

The local fixture uses the real CLI, hook configuration, trusted adapter and shell
execution, but a scripted loopback model endpoint. It proves the host boundary, not
production-model behavior or universal safety. No raw request logs are published:
they can contain private instruction and session metadata even in a local test.

The existing guard intentionally uses pattern checks and is fail-open when parsing
fails. It can block harmless quoted examples, and it is not guaranteed to catch every
indirect, encoded or dynamically constructed command. The adapter's fail-closed error
handling does not turn this heuristic into a complete security sandbox. Those limits
were retained and disclosed, not silently weakened or claimed fixed.

The public source has portable path handling and must be tested separately on a new
host. The supplied host probe checks whatever hook is actually installed, while
`tests/test_adapter.py` checks the source copy in this repository.

Remaining gates:
- matched context-cap/effort quality and cost experiments;
- approved, fact-preserving memory reduction under verified loader limits;
- general code-mode schema/batching savings under a real provider workload;
- review after client, RTK, hook or configuration upgrades;

The original private evidence and backups remain on the owner's machine. Aggregate
numbers and representative outputs here are sanitized summaries. They are not a
replacement for independently running the checks on the recipient's machine.
