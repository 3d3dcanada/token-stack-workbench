#!/usr/bin/env bash
# 3D3D catastrophe guard — PreToolUse hook for Bash.
# Philosophy: let the AI act freely, but hard-block the handful of commands
# that are never "oops, undo it": recursive deletes of home/root/cwd, disk
# wipes, fork bombs, force/mirror pushes, repo deletion, recursive perms on
# system roots, and power/reboot.
# Blocking is GUARANTEED here (runs even under bypassPermissions). Exit 2 = block.
# Fail-OPEN by design: if anything is unparseable, allow (never break normal work).
#
# Detection runs in Python (shlex tokenization) for robustness. It deliberately
# does NOT block project-local deletes like `rm -rf node_modules`, `rm -rf dist`,
# `rm -rf .next`, or deletes of paths nested inside a project.

input=$(cat)

verdict=$(GUARD_INPUT_JSON="$input" python3 - <<'PY' 2>/dev/null
import sys, json, shlex, re, os

try:
    d = json.loads(os.environ.get("GUARD_INPUT_JSON", "") or "{}")
    cmd = d.get("tool_input", {}).get("command", "") or ""
except Exception:
    print("ALLOW"); sys.exit(0)

if not cmd.strip():
    print("ALLOW"); sys.exit(0)

low = cmd.lower()

def block(reason):
    print("BLOCK:" + reason); sys.exit(0)

# --- tokenize (fall back to regex-only if tokenization fails) ---
try:
    tokens = shlex.split(cmd, comments=False, posix=True)
except Exception:
    tokens = cmd.split()

home = os.path.expanduser("~")

# Catastrophic delete targets (after stripping quotes/trailing slash).
CATASTROPHIC = {
    "/", "~", "~/", "$home", "${home}", ".", "..", "*", "/*", "./*",
    "/home", "/home/", "/home/*", home.lower(), home.lower() + "/",
    "/etc", "/usr", "/var", "/bin", "/sbin", "/lib", "/lib64", "/opt",
    "/boot", "/root", "/sys", "/proc", "/dev",
}

def norm_target(t):
    t = t.strip().strip('"').strip("'")
    tl = t.lower()
    if len(tl) > 1 and tl.endswith("/"):
        tl = tl.rstrip("/")
    return tl

# --- 1. recursive + forced rm with a catastrophic target ---
# Walk tokens; identify `rm` invocations, gather flags + operands.
i = 0
while i < len(tokens):
    if tokens[i] in ("rm", "/bin/rm") or tokens[i].endswith("/rm"):
        recursive = forced = False
        operands = []
        j = i + 1
        while j < len(tokens):
            tok = tokens[j]
            if tok in (";", "&&", "||", "|", "&"):
                break
            if tok.startswith("--"):
                if tok in ("--recursive",): recursive = True
                if tok in ("--force",): forced = True
                if tok == "--no-preserve-root": forced = recursive = True
            elif tok.startswith("-") and len(tok) > 1:
                if "r" in tok[1:].lower(): recursive = True
                if "f" in tok[1:].lower(): forced = True
            else:
                operands.append(tok)
            j += 1
        if recursive and forced:
            for op in operands:
                if norm_target(op) in CATASTROPHIC:
                    block("recursive delete of a catastrophic path (%s)" % op)
        i = j
    else:
        i += 1

# Matches a system/home root appearing as a standalone path argument.
ROOT_ARG = r'(?:^|\s)(/|~|\$\{?home\}?|/home|' + re.escape(home.lower()) + r'|/etc|/usr|/var|/bin|/sbin|/lib|/lib64|/opt|/boot|/root)(?:/\s|/$|\s|$)'

# --- 2. find on / or ~ that deletes ---
if re.search(r'\bfind\b', low) and re.search(r'(-delete\b|-exec\s+rm\b)', low):
    if re.search(r'\bfind\s+(/|~|\$\{?home\}?|/home|/etc|/usr|/var)(?:/|\s|$)', low):
        block("find with -delete/-exec rm over a system/home root")

# --- 3. disk / partition wipes ---
if re.search(r'\bmkfs\b', low): block("filesystem creation (mkfs) — disk wipe")
if re.search(r'\bwipefs\b', low): block("wipefs — disk signature wipe")
if re.search(r'\bsgdisk\b.*(--zap|-Z)', low): block("sgdisk zap — partition table wipe")
if re.search(r'\bparted\b.*\brm\b', low): block("parted rm — partition delete")
if re.search(r'\bdd\b.*\bof=/dev/(sd|nvme|hd|disk|mmcblk|vd)', low): block("dd raw write to a disk device")
if re.search(r'>\s*/dev/(sd|nvme|hd|disk|mmcblk|vd)', low): block("redirect to a raw disk device")

# --- 4. fork bomb ---
if re.search(r':\s*\(\s*\)\s*\{\s*:\s*\|\s*:', cmd) or ":(){:|:" in cmd.replace(" ", ""):
    block("fork bomb")

# --- 5. dangerous git / gh ---
if re.search(r'\bgit\s+push\b', low):
    if re.search(r'(--force(?!-with-lease)\b|\s-f\b|--mirror\b)', low):
        block("force/mirror push (use --force-with-lease yourself if you mean it)")
if re.search(r'\bgh\s+repo\s+delete\b', low):
    block("gh repo delete — repository deletion")

# --- 6. recursive perms / ownership on a system root ---
if re.search(r'\bchmod\s+(-[a-z]*r[a-z]*|--recursive)\b', low) and re.search(ROOT_ARG, low):
    block("recursive chmod on a system/home root")
if re.search(r'\bchown\s+(-[a-z]*r[a-z]*|--recursive)\b', low) and re.search(ROOT_ARG, low):
    block("recursive chown on a system/home root")

# --- 7. power / reboot ---
if re.search(r'\b(shutdown|reboot|poweroff|halt)\b', low) or re.search(r'\binit\s+[06]\b', low) \
   or re.search(r'\bsystemctl\s+(poweroff|reboot|halt)\b', low):
    block("power off / reboot (you reboot manually)")

print("ALLOW")
PY
)

case "$verdict" in
  BLOCK:*)
    echo "🛑 3D3D guard BLOCKED: ${verdict#BLOCK:}. Run it yourself if you really mean it." >&2
    exit 2 ;;
  *)
    exit 0 ;;
esac
