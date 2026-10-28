# Bridge Implementation Notes (Updated 2026-07-15)

## Architecture Correction

Initial assumption: Playwright upload runs from WSL. **WRONG.** WSL Playwright fails at chromium launch — system libs missing, broken. Upload must run via Windows PowerShell using the browser binaries there.

Correct flow:
```
gpu-node:/pipeline/final/*.mp4  --scp-->  WSL ~/income-work/youtube-shorts/videos/
                                                 |
                                    queue/*.json (WSL auto-creates)
                                                 |
                               powershell.exe → C:\...\youtube_uploader.py --queue
                                                  |
                                    Windows Playwright headless chromium
```

## Session Discoveries

### WSL Playwright Launches Fail
Playwright installed in WSL at v1.61.0, chromium binary downloaded to `~/.cache/ms-playwright/chromium-1228`. However `p.chromium.launch(headless=True)` crashes because `libnspr4`, `libnss3`, etc. are missing from this WSL instance and the dependency installer repeatedly fails with "authentication failed, try again" even though the user has elevation rights.

Diagnosed attempts:
- `echo "" | -S ...` — fails (no TTY available through pipe)
- `pty=True` mode — fails (not root, can't escalate interactive)
- `python3 -m playwright install-deps chromium` — fails: "a terminal is required to authenticate"

### Windows Playwright Works
Playwright v1.60.0 installed on Windows with chromium at `C:\Users\<you>\AppData\Local\ms-playwright\chromium-1223`. Python 3.14.4 on Windows. Browser launches headless fine from PowerShell. Login step also runs there.

### Bridge Script Must Invoke Windows Python
Crosspost orchestrator (`youtube_crosspost.py`) SCPs from GPU-NODE + queues in WSL, but MUST call the uploader via:
```bash
powershell.exe -Command "python <windows-home>/Documents/youtube_uploader.py --queue"
```
NOT `python3 ~/income-work/trend-data/youtube_uploader.py --queue`.

Previous version called `python3` directly which caused the chromium launch failure.

### Windows SSH to GPU-NODE Doesn't Work
Windows PowerShell cannot reach GPU-NODE (<lan-ip>) via SSH — WSL2 and Windows network stacks are isolated. SCP must come from WSL, not from a Windows-side script. This is correct in the design and doesn't need changing.

### Samba Share Z:\ Not Available
The original `Z:\final\` or `Z:\\` Samba mount that was supposed to point to GPU-NODE's data is not accessible. SCP via SSH works as the only reliable method to get files from GPU-NODE. No workaround needed — bridge already uses SCP exclusively.

### Uploader Path on Windows
Uploader was copied to `C:\Users\<you>\Documents\youtube_uploader.py` for Windows execution. Original at `~/income-work/trend-data/youtube_uploader.py` stays as the source of truth. The Windows copy is just for play.


## Privileges and elevation

Some system commands (service management, package installs, writes to system-owned paths) may need elevated rights. Run them as the user that owns the service, or apply your environment's elevation mechanism where required.
