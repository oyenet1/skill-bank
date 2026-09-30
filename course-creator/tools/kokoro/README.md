# Kokoro TTS — local course narration (CPU, offline). Two ways to run.

## Option A — native (fastest, no sudo needed)
On Windows, macOS and Linux, use the Python entry point:
```text
python3 start.py --sample
python3 start.py --text "Welcome to chapter one" --out ../../assets/audio/ch1-intro.mp3 --voice af_bella
# On Windows use: py -3 start.py ...
```
`start.py` installs `uv` privately if missing, creates a Python 3.12 virtual
environment, installs the hash-locked wheel dependencies from `requirements.lock`, and downloads models with size and SHA-256
checks. Windows uses PowerShell for the uv installer; macOS and Linux use `sh`.
No distribution package manager or shell profile change is needed. An existing
`uv` on `PATH` is reused. MP3 output uses system FFmpeg when present or the
bundled `imageio-ffmpeg` executable. The default runtime location is the user
data directory (`LOCALAPPDATA`, `~/Library/Application Support`, or
`XDG_DATA_HOME`). Set `SKILL_BANK_KOKORO_HOME` to override it. This also lets
the skill run from a read-only AppImage resource directory. `--sample` writes
`kokoro_sample.mp3` to that runtime directory. First setup requires network
access and disk space.

On macOS and Linux, the shell wrapper remains available:
```bash
cd <installed-skill>/tools/kokoro
./start.sh --sample
# sample -> user runtime directory/kokoro_sample.mp3
./start.sh --text "Welcome to chapter one" --out ../../assets/audio/ch1-intro.mp3 --voice af_bella
./start.sh --text-file lesson.txt --out ../../assets/audio/lesson.mp3 --voice af_sky --speed 1.0
```
`start.sh` delegates to the same private `start.py` runtime. If Python is
missing, it uses the skill's setup launcher to provision private Python.
Models (~350MB, once) and environments stay in the user data directory.
Both entry points accept `--check` to verify cached readiness without
installing or downloading anything. A missing runtime returns a nonzero exit.

Direct use without the wrapper:
```bash
python3 start.py --text "Hi" --out ../../assets/audio/hi.mp3
```
Output is MP3 by default (use `.wav` only if you need uncompressed).

## Option B — docker
```bash
cd course-creator/tools/kokoro
docker compose build
docker compose run --rm kokoro --text "Welcome to chapter one" --out /audio/ch1-intro.mp3 --voice af_bella
docker compose run --rm kokoro --text-file /audio/lesson.txt --out /audio/lesson.mp3
```
Docker bind-mounts `models/`. To reuse native models, point the mount at the
`models` path reported by `start.py --check`.
Image has system espeak-ng, so no extra setup.

## Voices (Kokoro v1.0)
`af_bella` (default, warm US female), `af_sky`, `af_nicole`, `af_sarah`,
`am_adam`, `am_michael`, `bf_emma`, `bf_isabella`, `bm_george`, `bm_lewis`.
Full list lives in the voices file; any id accepted by `--voice` works.

## Stopping
Nothing runs in the background in either path — every run generates audio and
exits. To clean up docker leftovers (containers/network):
```bash
./stop.sh
```

## Files
- `generate.py` — CLI generator (native + docker entrypoint)
- `start.sh` — native setup + run
- `start.py` — cross-platform setup + run
- `ensure_uv.sh` — local uv setup when missing
- `stop.sh` — tear down docker leftovers (native needs no stop)
- `download_models.sh` — fetch/refresh `models/` (resume-safe)
- `Dockerfile`, `docker-compose.yml`, `docker-entrypoint.sh` — container path
- `models/` — gitignored binaries (never committed)

## Updating dependencies

Keep direct versions in `requirements.txt`; regenerate the universal Python
3.12 lock with hashes, then regenerate the skill mirrors:

```bash
uv pip compile requirements.txt --universal --python-version 3.12 --generate-hashes --only-binary :all: --output-file requirements.lock
```

Narration accepts `.wav` and `.mp3`. It writes to a temporary file and replaces
the destination only after successful encoding, preserving existing audio on
failure.
