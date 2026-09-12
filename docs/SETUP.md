# Adapt to another machine

Review first. This repository does not auto-install, overwrite config, grant hook
trust or enable a proxy. Back up owner files before any approved change. Existing
guard policy wins over these examples.

## Adapter layout

The portable adapter expects `3d3d-guard.sh` beside it, and RTK at `~/.local/bin/rtk`.
The guard must be executable. If installing the example in an approved location,
copy both files together and use an absolute path to the adapter in config.
If another guard already exists, review how to reference it; do not replace it blindly.

The original machine used its existing guard in the Claude hooks directory. This
public copy's adjacent-file layout is the only architectural portability change.

## Codex config fragment

Merge into existing config; replace `/ABSOLUTE/PATH` locally. Never copy hook trust
hashes. The owner reviews/trusts the hook through Codex's supported hook interface.

```toml
[[hooks.PreToolUse]]
matcher = "^Bash$"

[[hooks.PreToolUse.hooks]]
type = "command"
command = "/usr/bin/python3 /ABSOLUTE/PATH/rtk-pre-tool.py"
```

Keep existing code-mode settings. Codex normalizes nested shell calls to Bash for
hooks, and a rewrite requires `permissionDecision: allow` with `updatedInput.command`.
[Official Codex hooks](https://learn.chatgpt.com/docs/hooks).

## Claude config fragment

The existing catastrophe guard stays first in registration. Merge only with approval:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [
        {"type": "command", "command": "/ABSOLUTE/PATH/3d3d-guard.sh"},
        {"type": "command", "command": "/ABSOLUTE/PATH/rtk hook claude"}
      ]
    }]
  }
}
```

Claude matching hooks run concurrently. Do not claim that array order makes a serial
pipeline. Verify original and rewritten denial. RTK rewriting may trigger permission
prompts unless the owner's allow-list covers it; review that permission explicitly.
No broad permission allow-list is installed by this repository.
[Claude hooks](https://code.claude.com/docs/en/hooks-guide).

## CodeGraph and instructions

Use CodeGraph on demand for broad structural questions only when the target has a
usable index. Pass the explicit project path. Exclude legacy/vendor material with
the installed version's supported configuration and verify stale rows disappear.
Keep index databases out of commits. A directory named `.codegraph` alone proves nothing.

Do not restore automatic prompt injection just because the installer offers it.
For exact source, diffs or failure diagnosis, read the unfiltered text. After one
irrelevant graph query, use targeted file search.

Keep agent instructions in a clear owner-approved source of truth. Installers can
replace symlinks or duplicate guidance; verify after upgrades. Prefix RTK manually
until the current client hook passes a behavioral test. Use `rtk proxy` for raw output.

## Headroom and model defaults

Headroom stays off in this handoff. It is not required to run any script here.
Do not change API routing or load a model to reproduce these tests. Context and effort
recommendations are proposed pilots, not configuration changes to apply silently.

## Host probe prerequisites

`tools/host_probe.py --check` requires Codex, the owner's already-trusted hook and an
already-trusted home project. It refuses to grant project trust. It disables MCP servers
only for the fixture invocation and uses a loopback custom provider with no API auth.
It runs in full-access mode with **fixed harmless calls only**; read the harness first.
It does not disable or bypass hook trust. Normal model/provider quality is not tested.

The fixture uses protocol/tool names observed on Codex 0.154.0. If an upgrade changes
them, the check must fail; inspect official docs and the actual boundary before fixing it.
