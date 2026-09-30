#!/usr/bin/env python3
"""Run pinned presenter inference with networking disabled in this process."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import runpy
import socket
import sys
import urllib.request


def block_network() -> None:
    def denied(*_args, **_kwargs):
        raise RuntimeError("Local presenter generation cannot access the network; install all pinned model files first")
    socket.create_connection = denied
    socket.socket.connect = denied
    socket.socket.connect_ex = denied
    urllib.request.urlopen = denied


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    block_network()
    root = Path(config["root"])
    os.chdir(root)
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "musetalk/utils"))
    import torch
    if config["accelerator"] == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("The installed PyTorch runtime cannot use this NVIDIA accelerator")
    if config["accelerator"] == "mps" and not torch.backends.mps.is_available():
        raise RuntimeError("The installed PyTorch runtime cannot use Apple Metal")
    kind = config["workerKind"]
    if kind == "musetalk":
        task = {"presenter": {"video_path": "media/portrait.png", "audio_path": "media/narration.wav", "result_name": "presenter.mp4"}}
        (root / "task.json").write_text(json.dumps(task), encoding="utf-8")
        sys.argv = ["inference", "--inference_config", "task.json", "--result_dir", "results", "--version", "v15",
                    "--unet_model_path", "models/musetalkV15/unet.pth", "--unet_config", "models/musetalkV15/musetalk.json",
                    "--whisper_dir", "models/whisper", "--batch_size", "2", "--output_vid_name", "presenter.mp4"]
        if config["accelerator"] == "cuda":
            sys.argv.append("--use_float16")
        runpy.run_module("scripts.inference", run_name="__main__")
    elif kind == "sadtalker":
        # The official SadTalker path uses CPU for operators unsupported by
        # Metal. Keep that compatibility behavior instead of pretending every
        # conv3d operator runs on MPS; the smoke result records the slower path.
        sys.argv = [str(root / "inference.py"), "--source_image", "media/portrait.png", "--driven_audio", "media/narration.wav",
                    "--result_dir", "results", "--checkpoint_dir", "checkpoints", "--old_version", "--size", "256", "--batch_size", "1", "--verbose"]
        runpy.run_path(str(root / "inference.py"), run_name="__main__")
    elif kind == "latentsync":
        # Bind pretrained VAE loading to the pinned local copy. The upstream
        # 1.5 entrypoint otherwise names the hosted Hugging Face repository.
        from diffusers import AutoencoderKL
        original = AutoencoderKL.from_pretrained
        def local_vae(path, *args, **kwargs):
            if path == "stabilityai/sd-vae-ft-mse":
                path = str(root / "checkpoints/sd-vae")
            kwargs["local_files_only"] = True
            return original(path, *args, **kwargs)
        AutoencoderKL.from_pretrained = local_vae
        sys.argv = ["inference", "--unet_config_path", "configs/unet/stage2.yaml", "--inference_ckpt_path", "checkpoints/latentsync_unet.pt",
                    "--video_path", "media/portrait.mp4", "--audio_path", "media/inference.wav", "--video_out_path", "results/presenter.mp4", "--temp_dir", "temp"]
        runpy.run_module("scripts.inference", run_name="__main__")
    else:
        raise ValueError("Unsupported local presenter inference adapter")


if __name__ == "__main__":
    main()
