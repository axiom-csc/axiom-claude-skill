# Compatibility

| Dimension | Tested values |
|-----------|--------------|
| Claude Code version | 1.x, 2.x |
| Python version | 3.8 – 3.14 |
| OS | macOS 14+, Ubuntu 22.04+ |
| Last verified | 2026-11-05 |

The hook uses no external dependencies — stdlib only.
Older Claude Code versions (pre-1.0) used a different hook format and are not supported.
If `CLAUDE_CODE_VERSION` is set to an untested major version, a one-line warning is printed
to stderr; it does not change the hook's allow/deny/ask decision.
