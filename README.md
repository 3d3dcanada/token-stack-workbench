# Token Stack Workbench

**Measure and check a Claude Code and Codex setup that spends fewer tokens, without trusting a hook just because it is registered.**

This repository is the cleaned-up record of a real Linux workstation where Claude Code and Codex run every day. It holds the hook scripts that make it work, the tests and host probes that prove they actually execute, the measurements behind each recommendation, and a review prompt you can hand to another person or agent before adopting anything.

Built by [3D3D](https://3d3d.ca) with Claude and Codex. Apache-2.0.

> The main lesson: **test what executes.** A hook listed in a config file is not proof that it runs, rewrites or blocks anything.

## Who it is for

- People running Claude Code or Codex for long sessions who want lower token use they can measure.
- Anyone adding RTK or a command guard to an agent and wanting proof that it fires on the real host.
- Reviewers who need to see which numbers were measured and which were modelled.

## What is inside

| Path | What it is |
|---|---|
| `src/rtk-pre-tool.py` | Codex `PreToolUse` adapter: validate, guard, rewrite through RTK, guard again, return a compatible rewrite. Fails closed on its own errors. |
| `src/3d3d-guard.sh` | A pattern guard that blocks a short list of catastrophic shell commands. A heuristic, not a sandbox. |
| `tests/test_adapter.py` | Unit tests for the adapter: malformed input, guard denials, idempotence, multi-command strings. |
| `tests/test_host_validation.py` | Tests for the host probe's own checks. |
| `tools/host_probe.py` | Runs the real local Codex host against a loopback scripted endpoint and checks that the rewrite and the denial actually happen. No model calls, no token spend. |
| `tools/usage_census.py` | Counts recorded usage from your own transcripts, deduplicated by request ID, without printing their contents. |
| `REVIEW-PROMPT.md` | One prompt that walks a reviewer through the whole setup before anything is copied. |
| `docs/` | The full handoff, measurements, setup notes, verification limits and sources. |

## Quick start

Requirements: Linux, Bash, Python 3.11 or newer, Git, and [RTK](https://github.com/rtk-ai/rtk) at `~/.local/bin/rtk`. Read the code before running it.

```bash
git clone https://github.com/3d3dcanada/token-stack-workbench.git
cd token-stack-workbench
python3 tests/test_adapter.py
python3 tools/usage_census.py --self-test
```

After you have installed the adapter yourself and trusted it in your Codex configuration:

```bash
python3 tools/host_probe.py --check
```

The probe uses a disposable Git fixture and an inert `printf` as its denial canary. It installs nothing, grants no trust and edits no guard. It was tested on Codex 0.154.0; revalidate on later versions.

To measure your own usage:

```bash
python3 tools/usage_census.py --since 2026-09-04
```

Setup details, config fragments and what never to copy between machines are in [docs/SETUP.md](docs/SETUP.md).

## What the measurements showed

From 75 sessions and 13,231 unique requests on the source workstation, September 4 to 12, 2026. Full tables and caveats are in [docs/MEASUREMENTS.md](docs/MEASUREMENTS.md).

- **Count by request ID.** Summing every content block overstated output tokens 2.81 times.
- **Earlier compaction is the largest modelled lever.** A 200k fixed-sequence clamp removes 54.84% of input before summary and cache-rebuild overhead.
- **The suspected Codex guard gap did not exist.** Nested shell calls are normalised to `Bash`, and the RTK rewrite reached execution. Keep code mode on.
- **Keep the full reads you need.** Targeted line ranges and fewer rereads beat adding another automatic context layer.
- **RTK counters are estimates,** not money saved. Effort comparisons in the sample are correlations, not A/B tests.

## Safety notes

- The guard is a pattern filter with known limits; its parser fails open. The adapter fails closed on its own validation and subprocess errors. Neither is a security sandbox.
- Nothing here edits your configuration. Merge the config fragments by hand, keep your existing guard first, and never copy hook-trust hashes from another machine.
- The repository holds no transcripts, memory, credentials, customer records or personal configuration.

## Documentation

1. [REVIEW-PROMPT.md](REVIEW-PROMPT.md): start here if you are reviewing.
2. [docs/HANDOFF.md](docs/HANDOFF.md): what was installed, what was corrected and why.
3. [docs/MEASUREMENTS.md](docs/MEASUREMENTS.md): the numbers and how they were counted.
4. [docs/SETUP.md](docs/SETUP.md): adapting it to another machine.
5. [docs/VERIFICATION.md](docs/VERIFICATION.md): what was proven and what was not.
6. [docs/SOURCES.md](docs/SOURCES.md): official documentation used.

## Licence

Apache License 2.0. See [LICENSE](LICENSE). RTK, CodeGraph, Claude Code, Codex and every other dependency keep their own licences; nothing here grants rights to them.

Copyright 2026 3D3D.
