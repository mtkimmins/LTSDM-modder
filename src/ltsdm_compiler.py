#!/usr/bin/env python3
"""Minimal LTSDM compiler.

Builds a single 1 MiB LTSDM cartridge from up to 12 audio tracks.

Pipeline:
  1. validate inputs
  2. normalize all audio files to 16 kHz mono 16-bit PCM WAV
  3. write raw PCM payloads into a cartridge buffer
  4. emit pointer table at the start of the file
  5. validate final file size and pointer ranges

This intentionally keeps the implementation small and easy to extend.
"""

from __future__ import annotations

import argparse
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

CARTRIDGE_SIZE = 1_048_576
POINTER_TABLE_ENTRIES = 12
POINTER_TABLE_BYTES = POINTER_TABLE_ENTRIES * 4
AUDIO_DATA_OFFSET = POINTER_TABLE_BYTES


def ensure_ffmpeg():
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required but not installed or not on PATH")


def validate_audio_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"audio file not found: {path}")
    if path.suffix.lower() not in {".wav", ".mp3", ".m4a", ".ogg", ".flac"}:
        raise ValueError(f"unsupported audio format: {path.suffix or '<none>'}")


def normalize_to_pcm_wav(src: Path, dst: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-ar",
        "16000",
        "-ac",
        "1",
        "-acodec",
        "pcm_s16le",
        str(dst),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def wav_to_pcm_bytes(path: Path) -> bytes:
    with open(path, "rb") as f:
        data = f.read()

    riff = data[:4]
    if riff != b"RIFF":
        raise ValueError(f"not a WAV file: {path}")

    data_tag = b"data"
    idx = data.find(data_tag)
    if idx < 0:
        raise ValueError(f"could not find PCM data chunk in {path}")

    chunk_size = struct.unpack_from("<I", data, idx + 4)[0]
    return data[idx + 8 : idx + 8 + chunk_size]


def build_cartridge(audio_files: list[tuple[int, Path]], output_path: Path) -> None:
    ensure_ffmpeg()

    if len(audio_files) > POINTER_TABLE_ENTRIES:
        raise ValueError(f"maximum supported tracks is {POINTER_TABLE_ENTRIES}")

    sorted_files = sorted(audio_files, key=lambda item: item[0])
    track_map: dict[int, Path] = {}
    for track_num, path in sorted_files:
        if not (1 <= track_num <= POINTER_TABLE_ENTRIES):
            raise ValueError(f"track number out of range: {track_num}")
        validate_audio_file(path)
        track_map[track_num] = path

    tempdir = Path(tempfile.mkdtemp(prefix="ltsdm_"))
    try:
        normalized: dict[int, bytes] = {}
        for track_num in range(1, POINTER_TABLE_ENTRIES + 1):
            if track_num not in track_map:
                continue

            src = track_map[track_num]
            wav_path = tempdir / f"track_{track_num:02d}.wav"
            normalize_to_pcm_wav(src, wav_path)
            normalized[track_num] = wav_to_pcm_bytes(wav_path)

        cartridge = bytearray(CARTRIDGE_SIZE)
        pointer_table = [0] * POINTER_TABLE_ENTRIES
        data_cursor = AUDIO_DATA_OFFSET

        for track_num in range(1, POINTER_TABLE_ENTRIES + 1):
            payload = normalized.get(track_num)
            if payload is None:
                continue

            if data_cursor + len(payload) > CARTRIDGE_SIZE:
                raise ValueError(
                    f"audio payload for track {track_num} exceeds cartridge capacity"
                )

            pointer_table[track_num - 1] = data_cursor
            cartridge[data_cursor : data_cursor + len(payload)] = payload
            data_cursor += len(payload)

        for i, ptr in enumerate(pointer_table):
            base = i * 4
            cartridge[base : base + 4] = struct.pack("<I", ptr)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(cartridge)

        validate_cartridge(output_path)

    finally:
        for child in sorted(tempdir.iterdir(), reverse=True):
            if child.is_file() or child.is_symlink():
                child.unlink()
            elif child.is_dir():
                for nested in sorted(child.rglob("*"), reverse=True):
                    if nested.is_file() or nested.is_symlink():
                        nested.unlink()
                    elif nested.is_dir():
                        nested.rmdir()
                child.rmdir()
        tempdir.rmdir()


def validate_cartridge(path: Path) -> None:
    data = path.read_bytes()
    if len(data) != CARTRIDGE_SIZE:
        raise ValueError(f"file size mismatch: expected {CARTRIDGE_SIZE}, got {len(data)}")

    ptrs = []
    for i in range(POINTER_TABLE_ENTRIES):
        val = struct.unpack_from("<I", data, i * 4)[0]
        ptrs.append(val)

    for idx, ptr in enumerate(ptrs, start=1):
        if ptr == 0:
            continue
        if ptr < AUDIO_DATA_OFFSET or ptr >= CARTRIDGE_SIZE:
            raise ValueError(f"pointer {idx} out of range: {ptr}")
        if ptr % 4 != 0:
            raise ValueError(f"pointer {idx} is not 4-byte aligned: {ptr}")

    # Rough overlap check: ensure pointers are monotonic when non-zero.
    seen = [p for p in ptrs if p != 0]
    if seen != sorted(seen):
        raise ValueError("pointers are not ordered correctly")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an LTSDM cartridge from audio tracks")
    parser.add_argument(
        "audio",
        nargs="+",
        help="audio files to compile; if fewer than 12 tracks are provided, remaining entries are empty",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="story.bin",
        help="output cartridge path (default: story.bin)",
    )
    parser.add_argument(
        "--track",
        action="append",
        default=[],
        help="explicit track number mapping as --track 1=track01.wav. Use either positional audio files or explicit mappings.",
    )
    return parser.parse_args()


def parse_explicit_tracks(raw_tracks: list[str]) -> list[tuple[int, Path]]:
    result: list[tuple[int, Path]] = []
    for item in raw_tracks:
        if "=" not in item:
            raise ValueError(f"invalid --track value, expected TRACK=FILE, got: {item!r}")
        track_str, file_str = item.split("=", 1)
        track_num = int(track_str)
        result.append((track_num, Path(file_str)))
    return result


def main() -> int:
    args = parse_args()

    try:
        if args.track:
            files = parse_explicit_tracks(args.track)
        else:
            files = []
            for idx, p in enumerate(args.audio, start=1):
                files.append((idx, Path(p)))

        output_path = Path(args.output)
        build_cartridge(files, output_path)

        used = sum(1 for _, _ in files)
        print(f"Built {output_path} from {used} track(s)")
        print(f"size: {output_path.stat().st_size} bytes / {CARTRIDGE_SIZE} bytes")
        print("status: VALID")
        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
