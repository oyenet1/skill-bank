# Voice Intake

Used by `voice-narration` and by any video that asks for synthetic speech.
Run only when narration is actually wanted. Ask in this order — language
first, because it constrains everything after it.

## 1. Language — ask first

Free answer, or offer the common set:

```
1. Language — English (recommended) / Spanish / French / German /
   Portuguese / Arabic / Hindi / Chinese / Japanese / Korean / other
```

Check the language is actually supported by the local Kokoro voice list before
promising it. If it is not, say so and offer the nearest supported language
rather than producing a broken accent.

## 2. Accent — ask only for English

When the language is English, ask which accent:

```
2. Accent — American (recommended) / British / Australian / other
```

This selects the voice family (`a*` American · `b*` British in the Kokoro list).
For non-English languages, skip this step and go straight to voice.

## 3. Voice — ask which one

```
3. Voice — female (recommended) / male / my own voice
```

| Answer | Action |
|---|---|
| female / male | pick a voice of that gender in the resolved language + accent family, and name it in the brief |
| **my own voice** | the requester supplies a recording or a custom voice. **Do not synthesise.** Ask for the audio file or voice reference and use it as the timing master. |
| no preference | use `brand.md` → `Voice and tone` → `Preferred TTS voice` if set, else the default female voice for that language |

Always name the chosen voice explicitly in the working brief
(`voice: af_sky — American, female, default`) so it can be reproduced.

## 4. Delivery of the audio

- Produce editable UTF-8 **script text** and one **WAV**.
- A supplied recording always takes priority over synthesis when the request
  says to use it.
- Inspect the WAV before claiming it exists: duration, silence at either end,
  clipping, pronunciation of names and technical terms.
- Split a long read by storyboard beat when later timing or edits matter.
- Narration is its own deliverable. Do not create slides, captions or video as a
  side effect.
