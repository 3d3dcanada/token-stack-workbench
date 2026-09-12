# Token Stack Workbench

A measured Claude Code + Codex token-efficiency setup, its safety checks, and a prompt
for another person or coding agent to review it. Built by 3D3D with Claude and Codex.

**The main lesson: test what executes. A registered hook is not proof that it works.**

This is the sanitized handoff of a real Linux workstation investigation on September
11–12, 2026. It includes the installation story, corrected findings, source examples,
reproducible checks and open decisions. It contains no private transcripts, memory,
customer records, credentials, personal configuration or hook-trust hashes.

## Start here

Give your reviewer [REVIEW-PROMPT.md](REVIEW-PROMPT.md). It is the single entry point
for checking the whole setup and deciding what transfers to another machine.

Read [the full handoff](docs/HANDOFF.md), then [measurements](docs/MEASUREMENTS.md),
[setup](docs/SETUP.md) and [verification boundaries](docs/VERIFICATION.md).

## What is in the stack

| Component | Role | State on the source workstation |
|---|---|---|
| RTK 0.49.0 | Compress supported shell output; record local estimates | Installed, used by Claude and Codex |
| CodeGraph 1.6.0 | On-demand structural repository exploration | Installed; seven repositories indexed |
| Headroom 0.37.0 | Optional tool-output compression/proxy | Installed, deliberately off |
| Catastrophe guard | Block selected dangerous command patterns | Preserved; original and rewritten checks |
| Codex RTK adapter | Validate → guard → RTK → guard → compatible rewrite | Working; existing implementation retained |
| Token-stack doctor | Check registration plus actual host behavior | Repaired with loopback host execution probes |
| Shared agent instructions | One source of truth; bounded reads and RTK fallback | Corrected after verification |
| Work orders/evidence | Preserve decisions and distinguish claims from proof | Local originals; sanitized summary here |

Ponytail and Caveman were also present as instruction/workflow plugins. They are
not prerequisites for these scripts. MCP schemas were already deferred by Tool Search.
Do not copy model choices, plugins or permissions blindly from another machine.

## Run the checks

Linux, Bash, Python 3.11+, Git and RTK at `~/.local/bin/rtk` are prerequisites.
The source example deliberately pins that RTK path. Read the code first.

```bash
python3 tests/test_adapter.py
```

After the adapter is installed and explicitly trusted in your Codex configuration:

```bash
python3 tools/host_probe.py --check
```

The latter uses the **real local Codex host** with a loopback scripted Responses
endpoint. No model inference or provider token spend. It does not install anything,
grant trust, edit the guard or send a force-push. Its denial canary is an inert printf.
It starts in an already-trusted home directory and makes a disposable Git fixture.
This has been tested on Codex 0.154.0 and Bash; later versions must be revalidated.

To measure your own recorded usage without exposing transcript contents:

```bash
python3 tools/usage_census.py --self-test
python3 tools/usage_census.py --since 2026-09-04
```

## Findings worth carrying forward

- The claimed Codex guard gap was disproved: nested shell calls are normalized to
  `Bash`. Automatic RTK rewriting also reached execution. Keep code mode.
- Deduplicate transcript usage by request ID. Counting each content block inflated
  output totals 2.81x in the measured window.
- Earlier compaction is the largest modeled lever. A 200k fixed-sequence clamp
  removes 54.84% of input before summary, cache-rebuild and recovery overhead.
- RTK counters are estimates, not money saved. Effort cohorts are not causal A/B tests.
- Keep necessary full reads. Targeted ranges and avoiding unnecessary rereads beat
  adding another automatic context layer without measurement.

## Scope and provenance

The source guard is an existing heuristic, not a complete security sandbox. Its parser
fails open; the adapter fails closed on adapter validation and subprocess failures.
Neither claim should be confused with comprehensive command containment.

`src/` contains portable derivatives of the actual local guard/adapter. Only path
handling was adapted: the guard lives beside the adapter, RTK uses the current home,
and the guard's home-path regex derives from the current user. Installed originals
were unchanged. The full machine-specific doctor was not copied; `tools/host_probe.py`
is its new behavior-checking component. All dependencies retain their own licenses.
No license grant is implied for upstream dependencies or third-party material.
