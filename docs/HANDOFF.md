# Full token-stack handoff

This covers the token-stack work by Claude and Codex, not unrelated applications on
the original workstation. Dates are snapshots, not current guarantees on another host.

## September 11: investigate and install

Claude investigated high context usage and surveyed reduction tools. The historical
tool-output split was Bash 43.5%, Read 38.2%, WebSearch 5.4% and MCP roughly 4%.
One historical analysis found a Read remained for a median 82 assistant turns. That
is not a universal multiplier, and compaction can remove older results.

RTK 0.49.0 was installed as a local binary. Its installer was reviewed and the release
checksum verified. Claude's Bash hook automatically rewrites supported commands.
Measured examples included a large Git diff shrinking from 334,418 to 30,363 bytes,
and Git log output from 25,819 to 7,786 bytes. These are output measurements, not bills.

CodeGraph 1.6.0 was installed and wired to Claude and Codex through MCP. It uses a
bundled Node runtime. On-demand structural queries worked. Its installation also
added an automatic prompt hook and broad repository indexes.

Headroom 0.37.0 was installed in an isolated Python environment, tested, then left
off. It reduced a synthetic JSON tool result substantially, but did little beyond
RTK on diffs and needed a proxy with roughly 464 MB RSS. No global routing was enabled.

The catastrophe guard stayed first in Claude's registration. A doctor checked
binaries, config, direct guard denial, rewriting/idempotence, allow-listing, indexes,
instruction symlinks, duplicate guidance and Headroom state.

## September 11: Codex review and Claude repairs

Codex found that the installed CLI did support hooks. RTK's Claude response was not
directly compatible: Codex rewrites require `permissionDecision: allow`.
The small Python adapter now runs the guard before RTK and again on a rewrite,
preserves unrelated fields, and refuses validation/processor failures.

Claude matching hooks run concurrently. Array position alone is not a serial safety
pipeline. The explicit guard → RTK → guard adapter avoids relying on that assumption.

Other reviewed defects were closed:
- Automatic CodeGraph prompt injection was removed; one prompt had cost 4,437
  cl100k tokens and included irrelevant relationships. On-demand MCP remained.
- A large runtime index contained over 93% legacy files. Scope was corrected; the
  current local doctor reports 531 files, 7,497 nodes and zero legacy rows.
- Shared AGENTS guidance and the Codex symlink were repaired after installer drift.
- RTK's allow-list was fixed after a rewrite caused an approval prompt per command.
- Seven repository indexes and their Git exclusions were checked.

MCP token-cost assumptions were also corrected. A historical zero-MCP versus all-MCP
comparison measured 30,497 versus 32,082 input tokens: **1,585 tokens total** for all
13 servers, because schemas were deferred. Their multiple gigabytes of resident RAM
were a different issue. Removing servers for large token savings was rejected.

## September 12: a misleading gap report, then direct proof

A later check saw Codex emit `custom_tool_call: exec` containing JavaScript. Passing
an invented exec-shaped event directly to the Bash adapter returned no output. That
was interpreted as “RTK and the guard never reach Codex.” The doctor still passed,
because it only checked the Bash registration and standalone processors.

The subsequent Codex investigation tested the actual boundary:
- An inert printf containing dangerous-looking text was denied in the active session.
- A loopback scripted Responses endpoint drove the real installed Codex CLI.
- Plain `git status` inside nested JavaScript executed as `rtk git status` and returned
  the fixture file listing successfully.
- The same behavior passed with a direct plain shell call.
- The nested inert canary was blocked before execution and its promise rejected.

Codex normalizes nested shell calls to canonical Bash events. The guard gap hypothesis
was disproved; neither JavaScript parsing nor disabling code mode was needed.
The existing adapter and installed guard were retained unchanged.

The doctor gained the local execution probe. Saved fixtures missing the rewrite or
denial fail. Shared instructions were corrected. Adapter tests increased from 13 to 16.
Earlier temporary-directory probes made Codex add project-trust entries; those were
removed and the harness now uses an already-trusted home directory. A full original
Codex-config byte hash did not restore; the local report records that residual limit
without claiming a blanket config restoration. Hook/model values remained preserved.

## Still decisions, not installed changes

Memory slimming, global context/effort changes and a matched quality/cost pilot remain
owner decisions. Model defaults were not changed. No memory entry was deleted.
The new cost analysis is in MEASUREMENTS.md.

Previously rejected alternatives remain rejected: context-mode, pxpipe, snip,
codeburn, agentsview and free-capacity gateways were not installed for this effort.
FreeToken was incompatible with the Pascal GPU's compute capability. No GPU was used.

The owner then explicitly requested this public, sanitized handoff so a friend could
review the complete stack and run the review prompt.
