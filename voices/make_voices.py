#!/usr/bin/env python3
"""Record every phrase the app speaks with several Piper voices into docs/voice/.

Needs the Piper environment and voice models in tools/ (not committed; see README):
    python3 -m venv tools/piper-venv && tools/piper-venv/bin/pip install piper-tts
    (cd tools/voices && ../piper-venv/bin/python -m piper.download_voices en_US-lessac-medium ...)
Run with:  tools/piper-venv/bin/python voices/make_voices.py
Only phrases that are new or changed are re-recorded.
"""
import hashlib
import json
import pathlib
import re
import subprocess
import tempfile
import wave

from piper import PiperVoice, SynthesisConfig

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "voice"
MODELS = ROOT / "tools" / "voices"
# id used in file paths -> Piper model, speed (length_scale > 1 is slower)
VOICES = {
    "lessac": ("en_US-lessac-medium", 1.22),
    "amy": ("en_US-amy-medium", 1.1),
    "hfc": ("en_US-hfc_female-medium", 1.17),
    "ryan": ("en_US-ryan-medium", 1.45),  # Ryan speaks quickly; slowed to match the others
}


def slug(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", key).strip("_")


def main() -> None:
    lines = subprocess.run(["node", str(ROOT / "voices" / "phrases.mjs")], check=True, capture_output=True, text=True).stdout
    phrases = [json.loads(l) for l in lines.splitlines() if l.strip()]
    OUT.mkdir(parents=True, exist_ok=True)
    stamp_file = OUT / ".stamps.json"
    stamps = json.loads(stamp_file.read_text()) if stamp_file.exists() else {}

    for vid, (model, speed) in VOICES.items():
        voice = PiperVoice.load(str(MODELS / f"{model}.onnx"))
        cfg = SynthesisConfig(length_scale=speed)
        vdir = OUT / vid
        vdir.mkdir(exist_ok=True)
        made = 0
        for p in phrases:
            name = slug(p["key"])
            target = vdir / f"{name}.mp3"
            stamp = hashlib.sha1(f"{model}|{speed}|{p['text']}".encode()).hexdigest()[:12]
            if target.exists() and stamps.get(f"{vid}/{name}") == stamp:
                continue
            with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
                with wave.open(tmp.name, "wb") as wav:
                    voice.synthesize_wav(p["text"], wav, syn_config=cfg)
                # Trim leading silence, even out loudness across voices, small mono MP3.
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp.name,
                                "-af", "silenceremove=start_periods=1:start_threshold=-45dB,loudnorm=I=-16:TP=-1.5:LRA=11,apad=pad_dur=0.08",
                                "-ar", "22050", "-ac", "1", "-b:a", "40k", str(target)], check=True)
            stamps[f"{vid}/{name}"] = stamp
            made += 1
        print(f"{vid}: {made} recorded, {len(phrases) - made} unchanged")

    # Remove clips for phrases the app no longer says.
    keep = {slug(p["key"]) for p in phrases}
    for f in OUT.glob("*/*.mp3"):
        if f.stem not in keep:
            f.unlink()
            stamps.pop(f"{f.parent.name}/{f.stem}", None)
    stamp_file.write_text(json.dumps(stamps, indent=0, sort_keys=True))
    (OUT / "voices.json").write_text(json.dumps({"voices": list(VOICES), "phrases": {p["key"]: slug(p["key"]) for p in phrases}}, separators=(",", ":")))
    total = sum(f.stat().st_size for f in OUT.glob("*/*.mp3"))
    print(f"{len(phrases)} phrases x {len(VOICES)} voices, {total / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
