# Generated scene images

Use uploaded product/screenshots/footage when a scene demonstrates a real product
or makes an evidential claim. Supporting illustrations may be generated when
requested; keep them identifiable as illustrations and review the actual output.

The bundled `tools/generate_image_asset.py` uses the OpenAI Images API with a
GPT image model. It has no Python package dependencies. Desktop first use
prepares a private Python interpreter; standalone use requires Python 3.10+.
Read the brief and settle the visual prompt before making a provider request.
Use the requester's configured OpenAI credential through `OPENAI_API_KEY`;
never put it in the request JSON, command arguments, logs, or exported source.
An account with image model access and API quota is required. Do not silently
replace a requested hosted image with an unrelated generated card on failure.

Create `image-request.json`:

```json
{
  "model": "gpt-image-2",
  "prompt": "A clear supporting illustration for this scene, no text or invented product UI",
  "size": "1536x1024",
  "quality": "medium"
}
```

Run `python3 tools/generate_image_asset.py image-request.json --out assets/scene-01`
(`py -3` on Windows). Supported sizes are `1536x1024`, `1024x1536`, `1024x1024`.
Quality is `low`, `medium`, `high`, or `auto`. Model access and charges depend on
the configured account. Prompts leave the machine; uploaded media is not sent by
this text-to-image adapter.

The command returns a verified PNG and `asset.json` with provider, model, prompt,
creation time, dimensions, quality, SHA-256, and terms URL. Both files are
published together. Repeating the same request reuses verified output without
another API call; changed inputs or modified output need a fresh directory.
SIGTERM cancels locally; a hosted provider may continue processing a request.
Provider/network/validation failures never publish a partial final image.

Import generated images into the normal scene renderer, retain their provenance,
and inspect framing, factual implications and image rights before publishing.
Keep the original script, uploads and failed-phase logs so rendering can resume.
