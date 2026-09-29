# Kokoro TTS — local course narration (CPU, offline). Two ways to run.

## Option A — native (fastest, no sudo needed)
```bash
cd course-creator/tools/kokoro
./start.sh --sample
# sample -> ../../assets/audio/kokoro_sample.mp3
./start.sh --text "Welcome to chapter one" --out ../../assets/audio/ch1-intro.mp3 --voice af_bella
./start.sh --text-file lesson.txt --out ../../assets/audio/lesson.mp3 --voice af_sky --speed 1.0
```
`start.sh` creates `.venv` (Python 3.12 via uv), installs `requirements.txt`,
downloads models (~350MB, once) into `models/`, then runs `generate.py`.

Direct use without the wrapper:
```bash
.venv/bin/python generate.py --text "Hi" --out ../../assets/audio/hi.mp3
```
Output is MP3 by default (use `.wav` only if you need uncompressed).

## Option B — docker
```bash
cd course-creator/tools/kokoro
docker compose build
docker compose run --rm kokoro --text "Welcome to chapter one" --out /audio/ch1-intro.mp3 --voice af_bella
docker compose run --rm kokoro --text-file /audio/lesson.txt --out /audio/lesson.mp3
```
`models/` is bind-mounted, so native and docker share the same download.
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
- `stop.sh` — tear down docker leftovers (native needs no stop)
- `download_models.sh` — fetch/refresh `models/` (resume-safe)
- `Dockerfile`, `docker-compose.yml`, `docker-entrypoint.sh` — container path
- `models/` — gitignored binaries (never committed)
