#!/usr/bin/env python3
"""Read-only, network-free desktop capability probe for local presenters."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import platform
import re
import subprocess
import sys


def manifest() -> dict:
    return json.loads(Path(__file__).with_name("avatar_models.json").read_text(encoding="utf-8"))


def progress(phase: str, message: str, **details) -> None:
    print(json.dumps({"phase": phase, "message": message, **details}), file=sys.stderr, flush=True)


def compatible(config: dict, kind: str, memory: int, *, allow_restricted: bool = False) -> list[dict]:
    rows = []
    for row in config["backends"]:
        minimum = row["minAccelMemoryBytes"]
        minimum = minimum.get(kind, math.inf) if isinstance(minimum, dict) else minimum
        if kind not in row["accel"] or memory < minimum:
            continue
        if row["licenseClass"] == "research-only" or (row["licenseClass"] == "restricted" and not allow_restricted):
            continue
        if not row.get("files") or any(not isinstance(f.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", f["sha256"]) for f in row["files"]):
            continue
        rows.append(row)
    rows.sort(key=lambda row: (-row["qualityTier"], row["downloadBytes"], row["id"]))
    default = config.get("defaults", {}).get(kind)
    rows.sort(key=lambda row: row["id"] != default)
    return rows


def command(args: list[str], failures: list[dict]) -> str | None:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        failures.append({"source": args[0], "reason": "command-failed", "exitCode": result.returncode})
    except (OSError, subprocess.TimeoutExpired, UnicodeError) as error:
        failures.append({"source": args[0], "reason": type(error).__name__})
    return None


def probe(config: dict | None = None, *, allow_restricted: bool = False) -> dict:
    system = platform.system()
    machine = platform.machine().lower()
    arch = "x64" if machine in ("x86_64", "amd64", "x64") else "arm64" if machine in ("arm64", "aarch64") else machine
    failures = []
    accelerator = {"kind": "cpu", "name": platform.processor() or None, "memoryBytes": 0, "source": "platform"}
    result = {"schemaVersion": 1, "os": system, "arch": arch, "accelerator": accelerator,
              "eligible": False, "thresholdBytes": None, "reason": "unsupported-accelerator:cpu", "candidates": [], "candidateDetails": [], "sourcesFailed": failures}
    progress("probe", "Checking local avatar hardware without downloads")
    try:
        config = config or manifest()
        if system in ("Linux", "Windows"):
            output = command(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"], failures)
            devices = []
            if output:
                for index, row in enumerate(csv.reader(output.splitlines())):
                    try:
                        name, mib, driver = (item.strip() for item in row)
                        amount = float(mib)
                        if not math.isfinite(amount) or amount < 0:
                            raise ValueError("Invalid GPU memory")
                        devices.append({"kind": "cuda", "name": name, "memoryBytes": int(amount * 1048576),
                                        "source": "nvidia-smi", "driverVersion": driver, "deviceIndex": index})
                    except (ValueError, OverflowError):
                        failures.append({"source": "nvidia-smi", "reason": "unparseable-output"})
            if devices:
                accelerator = max(devices, key=lambda row: row["memoryBytes"])
            elif system == "Linux" and Path("/dev/kfd").exists():
                accelerator.update(kind="rocm", source="/dev/kfd", name="AMD ROCm")
        elif system == "Darwin" and arch == "arm64":
            output = command(["sysctl", "-n", "hw.memsize"], failures)
            try:
                amount = int(output or "")
                if amount <= 0:
                    raise ValueError("Invalid unified memory")
                accelerator = {"kind": "mps", "name": "Apple Silicon", "memoryBytes": amount, "source": "sysctl:hw.memsize"}
            except ValueError:
                failures.append({"source": "sysctl:hw.memsize", "reason": "unparseable-output"})
        result["accelerator"] = accelerator
        kind = accelerator["kind"]
        threshold = config["thresholds"].get(kind + "Bytes")
        result["thresholdBytes"] = threshold
        if (system, arch) not in (("Linux", "x64"), ("Windows", "x64"), ("Darwin", "arm64")):
            result["reason"] = f"unsupported-platform:{system}/{arch}"
        elif kind == "mps" and (not platform.mac_ver()[0] or int(platform.mac_ver()[0].split(".")[0]) < 14):
            result["reason"] = "unsupported-platform:macOS-14-required"
        elif threshold is None:
            result["reason"] = f"unsupported-accelerator:{kind}"
        elif accelerator["memoryBytes"] < threshold:
            result["reason"] = f"insufficient-memory:{kind}"
        else:
            candidates = compatible(config, kind, accelerator["memoryBytes"], allow_restricted=allow_restricted)
            result.update(eligible=bool(candidates), candidates=[row["id"] for row in candidates],
                          candidateDetails=[{key: row[key] for key in ("id", "displayName", "qualityTier", "license", "licenseClass", "componentLicenses", "downloadBytes", "diskBytes", "recommendedMaxSeconds", "estimatedSecondsPerSecond", "requiresSmokeTest")} for row in candidates],
                          reason="eligible" if candidates else f"no-compatible-backend:{kind}")
    except Exception as error:
        result.update(eligible=False, reason="probe-error", error=str(error), candidates=[], candidateDetails=[])
    progress("eligible", "Local avatar capability check finished", eligible=result["eligible"], reason=result["reason"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-restricted", action="store_true")
    args = parser.parse_args()
    print(json.dumps(probe(allow_restricted=args.allow_restricted)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
