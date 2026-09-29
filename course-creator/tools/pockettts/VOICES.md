# Voice Catalog — PocketTTS (+ Kokoro reference)

Owner preference: **always British accent**.
Male ranking: `bill_boerst` > `george` · Female ranking: `mary` > `eve` > `jane`.

## Flagship files (course assets: `course-creator/assets/audio/`)

| File | Engine | Voice | Length |
|---|---|---|---|
| `pitch_lodgestatus.mp3` | Kokoro | `bm_george` (British male, guaranteed) | 1m40s |
| `pockettts.mp3` | PocketTTS | `marius` (male) | 78s |
| `pockettts_mary.mp3` | PocketTTS | `mary` (female, top pick) | 96s |

Same LodgeStatus investor pitch text in all three
(source: `tools/kokoro/pitch_lodgestatus.txt`).

## Experiments (`~/Audio/`, next to `~/Pictures/` — NOT in git)

Demos (one test line each) moved out of the repo to keep it lean:

| File | Voice | Notes |
|---|---|---|
| `voice_demo_bill_boerst.mp3` | bill_boerst (M) | ⭐ top male pick |
| `voice_demo_george.mp3` | george (M) | ⭐ 2nd male pick |
| `voice_demo_mary.mp3` | mary (F) | ⭐ top female pick |
| `voice_demo_eve.mp3` | eve (F) | 2nd female pick |
| `voice_demo_jane.mp3` | jane (F) | 3rd female pick |
| `voice_demo_charles.mp3` | charles (M) | candidate |
| `voice_demo_javert.mp3` | javert (M) | candidate |
| `voice_demo_paul.mp3` | paul (M) | candidate |
| `voice_demo_jean.mp3` | jean (M) | candidate |
| `pocket_sample_alba.mp3` | alba (F) | first PocketTTS test |
| `pocket_sample_marius.mp3` | marius (M) | first male test |
| `kokoro_sample.mp3` | af_bella (F) | first Kokoro test |
| `docker_sample.mp3` | af_sky (F) | docker path test |

## PocketTTS full catalog (27 built-in, no login)

English male: marius, javert, jean, paul, charles, michael,
george, bill_boerst, peter_yearsley, stuart_bell.
English female: alba, anna, vera, fantine, eponine, azelma,
mary, jane, eve, cosette, caro_davy.
French: estelle (F). German: juergen (M). Italian: giovanni (M).
Spanish: lola (F). Portuguese: rafael (M). + daan.
Languages: english, french, german, italian, spanish, portuguese.

Render any of them:
```bash
./start.sh --text "..." --voice <name> --out ../../assets/audio/<file>.mp3 --language english
```

## Custom voice cloning

1. Accept terms: https://huggingface.co/kyutai/pocket-tts
2. `uvx hf auth login`
3. `./start.sh --text "..." --voice ./my_10s.wav --out ../../assets/audio/me.mp3`

## Kokoro voices (54, `../kokoro/`, guaranteed accents)

Prefix = accent+gender: `af_` US female (11), `am_` US male (9),
`bf_` UK female (4), `bm_` UK male (4: george, lewis, daniel, fable),
plus Spanish/French/Hindi/Italian/Japanese/Portuguese/Mandarin sets.
For guaranteed British, use `bm_*` — that is why the flagship
`pitch_lodgestatus.mp3` uses `bm_george`.
