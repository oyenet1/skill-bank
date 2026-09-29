# Local Kokoro narration

The native tool uses `uv`, Kokoro ONNX, and CPU inference. Its first run creates `.venv` and downloads the Kokoro v1.0 model and voices into `models/`. Later runs reuse them. The script exits after each generation; no service stays running.

From this folder:

```bash
./start.sh --text-file /absolute/path/to/script.txt --out /absolute/path/to/narration.wav --voice af_bella
```

Use `--speed 1.0` and `--lang en-us` if you need to set them explicitly. Try `af_bella`, `af_sky`, `am_adam`, `bf_emma`, or `bm_george`; available IDs are stored in the downloaded voices file. Keep the editable script next to the output WAV and check the actual recording before timing slides or video to it.

`generate.py` can also run directly with an existing environment and model files. `download_models.sh` fetches the model files from the Kokoro ONNX release. For current API behavior, see [Kokoro ONNX](https://github.com/thewh1teagle/kokoro-onnx).
