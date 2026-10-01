# Voice Catalog — PocketTTS (+ Kokoro reference)

Owner preference: **always British accent**.
Male ranking: `bill_boerst` > `george` · Female ranking: `mary` > `eve` > `jane`.

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
For guaranteed British, use `bm_*` voices such as `bm_george`.
