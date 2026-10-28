#!/usr/bin/env python3
"""Pre-flight check for YouTube cross-post bridge. Run before uploading — OAuth + API uploader."""
import subprocess, sys, json, os
from pathlib import Path

def ok(msg):   print(f"  [OK] {msg}")
def fail(msg): print(f" [FAIL] {msg}")

checks = 0
passes = 0

# 1. OAuth token (NOT Playwright cookies — Data API v3)
checks += 1
tf = Path("C:/pipeline/auth/youtube_token.json")
cs = Path("C:/pipeline/auth/client_secret.json")
if tf.exists():
    ok(f"YouTube OAuth token at {tf}")
    passes += 1
elif cs.exists():
    fail("youtube_token.json missing but client_secret.json exists. Run: python C:\\pipeline\\youtube_api_uploader.py --setup")
else:
    fail("No YouTube auth. Create Google Cloud project, enable YouTube Data API v3, download client_secret.json to C:\\pipeline\\auth\\")

# 2. API uploader script exists
checks += 1
api_up = Path("C:/pipeline/youtube_api_uploader.py")
if api_up.exists():
    ok(f"API uploader at {api_up}")
    passes += 1
else:
    fail("youtube_api_uploader.py not found in C:\\pipeline\\")

# 3. Queue directories exist
checks += 1
base = Path("C:/pipeline/youtube-queue")
dirs = ["queue", "posted", "videos", "failed"]
if all((base / d).exists() for d in dirs):
    ok(f"All queue dirs under {base}")
    passes += 1
else:
    fail("Some queue directories missing — run the bridge script, it creates them")

# 4. SSH to m2 works (from this side — WSL or Windows)
checks += 1
host = "m2"
if sys.platform == "win32":
    r = subprocess.run(["ssh", "-o", "ConnectTimeout=5", host, "hostname"], capture_output=True, text=True)
else:
    r = subprocess.run(["powershell.exe", "-Command", f"ssh -o ConnectTimeout=5 {host} hostname"], capture_output=True, text=True)
if r.returncode == 0:
    ok(f"SSH to GPU-NODE ({r.stdout.strip()})")
    passes += 1
else:
    fail(f"SSH to GPU-NODE failed — check <windows-home>\\.ssh\\config has the correct host entry and IdentityFile")

# 5. Videos on GPU-NODE
checks += 1
r = subprocess.run(["ssh", "-o", "ConnectTimeout=5", "m2", "find", "/pipeline/final/", "-name", "*.mp4", "-type", "f", "|", "wc", "-l"], capture_output=True, text=True, timeout=10)
if r.returncode == 0:
    count = r.stdout.strip()
    ok(f"{count} videos available on GPU-NODE at /pipeline/final/")
    passes += 1
else:
    fail("No videos on GPU-NODE — check Samba mount or pipeline output")

# 6. Python packages for API uploader
checks += 1
pkgs = ["googleapiclient", "google_auth_oauthlib"]
if sys.platform == "win32":
    r = subprocess.run(["python", "-c", "import googleapiclient, google_auth_oauthlib; print('OK')"], capture_output=True, text=True)
else:
    r = subprocess.run(["powershell.exe", "-Command", "python -c \"import googleapiclient, google_auth_oauthlib; print('OK')\""], capture_output=True, text=True)
if "OK" in r.stdout:
    ok("Google API client libraries installed")
    passes += 1
else:
    fail("pip install google-api-python-client google-auth-oauthlib")

# Summary
print(f"\n--- {passes}/{checks} checks passed ---")
sys.exit(0 if passes == checks else 1)