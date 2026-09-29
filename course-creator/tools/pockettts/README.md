# PocketTTS — CPU voice synthesis with cloning (Kyutai, 100M params)

Local, offline-after-download TTS. Best when you need **your own voice**
or CPU-only cloning; otherwise Kokoro (`../kokoro/`) is lighter.

## Start

```bash
cd course-creator/tools/pockettts
./start.sh --sample   # demo mp3 -> ../../assets/audio/pocket_sample_alba.mp3
./start.sh --text "Hi class" --voice marius --out ../../assets/audio/hi.mp3 --language english
./start.sh serve      # FastAPI web UI + API server
```

Languages: `english`, `french`, `german`, `italian`, `spanish`,
`portuguese` (+ dated variants like `english_2026-09`).

## Voices (built-in, no login needed)

User preference: **always British accent**.
Male ranking: `bill_boerst` > `george` (also liked: marius).
Female ranking: `mary` > `eve` > `jane`.
(Kokoro British male: `bm_george`.)

alba, anna, marius, javert, jean, vera, fantine, charles, paul,
eponine, azelma, george, mary, jane, michael, eve, estelle,
giovanni, lola, juergen, rafael, daan + more (27 catalogued).

## Clone YOUR voice (one-time setup)

1. Accept terms at https://huggingface.co/kyutai/pocket-tts
2. `uvx hf auth login` (paste a token from huggingface.co/settings/tokens)
3. Record a clean 10s wav of yourself, then:
   `./start.sh --text "..." --voice ./my_10s.wav --out ../../assets/audio/me.mp3`

## Files

- `start.sh` — setup + generate + serve
- `requirements.txt` — `pocket-tts`, `soundfile`
- `.venv/` — gitignored runtime (never committed)
- Models auto-download from HuggingFace on first run (~GBs, cached in
  `~/.cache/huggingface`, also gitignored by nature).
