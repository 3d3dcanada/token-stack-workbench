# Measurements and recommendations

Local sample: September 4–12, 2026, ending 11:03:59 UTC. 84 top-level transcript
files, 75 sessions, 13,231 unique request IDs. Subagent directories excluded. Provider
usage counters are deduplicated by request ID, with message ID fallback, keeping the
largest output counter for split/streamed records. This is not an invoice audit.

## Context

| Measure | Recorded value |
|---|---:|
| Total input | 5,321,615,018 tokens |
| Cached input | 5,250,995,257 |
| Cache creation | 70,525,318 |
| Uncached input | 94,443 |
| Output | 13,291,392 |
| Recorded thinking | 4,748,151 |
| Median request context | 361,915 |
| Maximum request context | 966,473 |
| Sessions exceeding 200k | 46 / 75 |

Clamp the same sequence to 200k and 2,918,369,669 input tokens disappear (54.84%).
At 300k, 2,037,659,008 disappear (38.29%). This calculation excludes summary calls,
new cache writes, recovery reads, extra turns and quality effects. It is a modeled
opportunity, not demonstrated savings. Fresh and cached input have different costs.

Recommendation: pilot a native 200k auto-compact threshold on ordinary tasks, keeping
a larger-window exception. Do not assume removing `[1m]` enforces 200k: current
Claude models can have native 1M windows. Claude Code 2.1.269 was installed; current
official docs describe `claude --autocompact 200k` for one launch and
`CLAUDE_CODE_DISABLE_1M_CONTEXT=1` for a model-window hold. Verify on the recipient's
version before adoption. [Model configuration](https://code.claude.com/docs/en/model-config).

## Effort

| Model / effective effort | Calls | Mean output | Mean thinking |
|---|---:|---:|---:|
| Opus 5 high | 2,999 | 568.5 | 175.8 |
| Opus 5 xhigh | 5,276 | 761.6 | 233.1 |
| Fable 5.1 high | 685 | 2,017.8 | 789.9 |
| Fable 5.1 xhigh | 1,532 | 2,013.5 | 778.1 |

Opus high correlates with 25.4% less output; Fable shows no useful reduction. These
are different tasks, not a causal A/B. Thinking accounts for 35.7% of recorded output,
with some missing thinking detail. Global xhigh does not prove every request used it.

Recommendation: a matched high-effort pilot, with acceptance checks and exceptions
for difficult work. Keep effort stable during a task; changing it can invalidate
caches. [Thinking and cost](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost).

## Memory

The source memory index was 21,068 bytes, 123 lines, 306 links and 6,929 cl100k tokens.
A cost-only link-preserving candidate was 17,973 bytes and 5,962 tokens: 967 fewer
tokens per inclusion (14.0%). It removed prose and grew to 307 lines, so it was not a
safe drop-in index. The real memory was unchanged and is not in this repository.

Recommendation: preserve all entries and hard rules, verify detail in topic files,
then shorten the index under the actual loader limits. A 2,000-token target would
save 4,929 tokens per inclusion, but that target has not been achieved or approved.

## Read output

525 successful text Read results totaled 5,062,917 bytes. Line-number scaffolding
used 329,757 bytes (6.51%). Reads before later edit attempts accounted for 1,345,724
bytes (26.58%); that does not prove they remained stale in model context. Exact text
repeats without a recorded intervening edit were zero in this sample.

Recommendation: targeted ranges and changed-range review; omit numbering only when
unneeded. Preserve full unfiltered source for correctness. Do not add a stale-read
deletion proxy based on this evidence. This narrower sample is not the earlier lifetime pie.

Encoded non-text/media Read blocks occupied 234.251 MB. Base64 byte length is not
image token usage and must not enter text-token savings estimates.

## Accounting correction

Naive summation of assistant blocks yielded 37,386,763 output tokens; deduplication
yielded 13,291,392: a 2.81x overcount. Cached input similarly dropped from 9.663 billion
to 5.251 billion. Preserve provider request IDs when comparing measurements.

## Code mode

The one-shell-call local fixture serialized first requests of 23,254 cl100k tokens
with code mode and 23,271 without. Returned tool envelopes were 126 versus 94 tokens.
Random IDs and metadata affect these tiny deltas. The custom-provider requests had
no `tools` schema field, so this is not a production schema-savings benchmark. Broader
batch/filter savings remain workload-dependent. There is no reason here to disable
working code mode to repair a guard gap that did not exist.

All cl100k counts are reproducible local tokenizer estimates, not exact provider
billing counts. RTK gain totals are also estimates, never dollars saved. No claim of
measured subscription savings is made.
