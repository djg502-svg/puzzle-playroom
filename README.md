# Puzzle Playroom

A toddler puzzle game for iPad: jigsaw (6/9/12 pieces), slices (3/4/5 strips) or squares, forgiving snapping, 28 pictures of animals, dinosaurs, ice cream, unicorns and Halloween, and puzzles from your own photos (press and hold the + card; photos stay on the device).

Games: Numbers 1–10 (tap to hear and count), ABC board (tap a letter to hear "bee is for ball"), Colors (paint splats with three things of each color), Shadow match (drag 4 random items onto their silhouettes), Balloon pop (colors or numbers), Bubble wrap (tap or swipe to pop, new color each sheet) and a Rainbow xylophone.

- `index.html` is the game source.
- `python3 build.py` builds the offline Home Screen web app into `docs/`, which GitHub Pages serves.

## Voices

Spoken words are recorded clips in `docs/voice/` (four Piper voices; the app picks one at random each time a game or puzzle opens, and falls back to the iPad's own voice for anything without a clip). To re-record after changing words in the app:

```
python3 -m venv tools/piper-venv && tools/piper-venv/bin/pip install piper-tts
(cd tools && mkdir -p voices && cd voices && ../piper-venv/bin/python -m piper.download_voices en_US-lessac-medium en_US-amy-medium en_US-hfc_female-medium en_US-ryan-medium)
tools/piper-venv/bin/python voices/make_voices.py
python3 build.py
```

`tools/` is not committed. `voices/phrases.mjs` lists every phrase from the app's own data, so new pictures, letters or colors are picked up automatically.
