# Review this token stack

You are reviewing a sanitized handoff of a real Claude Code/Codex token-efficiency
setup. Read README.md, docs/HANDOFF.md, docs/MEASUREMENTS.md, docs/SETUP.md and
docs/VERIFICATION.md, in that order, then read every source/test file you will run.

First explain what is installed, what each part does, what was corrected, and which
results were measured versus modeled. Do not assume this machine matches the source
workstation. Check current official documentation for the installed client versions.

Then review the code and optionally run local checks within the owner's authorization:

1. Run `python3 tests/test_adapter.py` if the documented prerequisites exist.
2. Inspect the owner's actual hook configuration without printing credentials. Never
   replace it wholesale or copy a trust hash from elsewhere. Preserve the existing
   catastrophe guard and its order. Owner trust/approval is a real gate.
3. If the hook is already installed and trusted, run `python3 tools/host_probe.py --check`.
   It uses a local fixture, no provider model. Confirm the executed RTK rewrite, the
   successful result reaching the next request, and denial before nested execution.
   An invented outer `exec` hook payload is not proof of a deployed guard gap.
4. Review edge cases: malformed input, processor/guard errors, idempotence, multi-command
   strings, heredocs and quoted command examples. Do not execute dangerous commands.
   The source guard is a limited pattern filter; identify actual limits without silently
   broadening or weakening its policy.
5. Run the usage census self-test. With permission to read local transcripts, obtain
   deduplicated aggregate counts. Keep raw transcripts and personal configs private.
6. Cost context caps, effective effort, memory-index size, targeted reads and instruction
   overhead. Include summary/cache-rebuild/recovery costs and acceptance quality in any
   proposed A/B. Never translate local RTK estimates into subscription savings.
7. Keep Headroom off unless separately approved. Do not install rejected alternatives,
   prune MCP servers for speculative token savings, load a GPU model, modify memory,
   change model defaults, publish, spend, commit or push without authorization.

Return a short verdict and a review file with:
- confirmed working behavior and exact test output;
- reproducible defects ranked by severity, with file/line references;
- portability problems and anything you could not verify;
- the smallest justified repair and the checks that would prove it;
- open decisions for the owner, with numerical tradeoffs rather than promises.

Do not call the work complete merely because config parsing or offline tests pass.
Do not re-report superseded historical claims as current defects. If implementation is
requested later, back up first, use focused work orders, verify behavior and stop.
