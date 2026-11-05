#!/usr/bin/env python3
"""Background flush: sends queued telemetry events to the endpoint and clears them.
Called as a detached subprocess from the hook; must never raise or block the hook."""
import json, pathlib, sys, urllib.request, urllib.error

QUEUE_FILE = pathlib.Path.home() / ".config" / "axiom-csc" / "queue.jsonl"
TIMEOUT = 2


def main():
    endpoint = sys.argv[1] if len(sys.argv) > 1 else ""
    if not endpoint or not QUEUE_FILE.exists():
        return
    try:
        lines = [l for l in QUEUE_FILE.read_text().splitlines() if l.strip()]
    except Exception:
        return
    if not lines:
        return
    events = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except Exception:
            pass
    if not events:
        return
    try:
        body = json.dumps({"events": events}).encode()
        req = urllib.request.Request(endpoint, data=body,
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=TIMEOUT)
        # Only clear on success
        sent_set = {json.dumps(e) for e in events}
        remaining = [l for l in lines if l not in sent_set]
        QUEUE_FILE.write_text("\n".join(remaining) + ("\n" if remaining else ""))
    except Exception:
        pass  # Network errors are always silently swallowed


if __name__ == "__main__":
    main()
