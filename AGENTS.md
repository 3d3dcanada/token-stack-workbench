# Working on this handoff

Read README.md and REVIEW-PROMPT.md first. This is a portable reference package,
not authorization to change the recipient's machine.

- Preserve existing guard policy and ordering. Never bypass hook trust.
- Do not install, change model defaults, edit memory, enable proxies or publish
  without the owner's authorization.
- No raw transcript, personal config, credential, memory or trust hash in commits.
- Run `python3 tests/test_adapter.py` (requires local RTK) and
  `python3 tools/usage_census.py --self-test` for relevant changes.
- `python3 tools/host_probe.py --check` exercises the installed trusted hook, not
  necessarily this source copy. Report that distinction.
- Keep fixes small. Preserve a failing case and prove the real execution boundary.
- Reports must separate measured, modeled, historical and unverified claims.
