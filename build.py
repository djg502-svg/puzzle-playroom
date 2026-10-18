#!/usr/bin/env python3
"""Build the standalone website in docs/ (served by GitHub Pages) from index.html (the claude.ai artifact source).

The artifact host wraps index.html in its own <!doctype>/<head> and supplies a small CSS
reset; this script adds the same pieces, swaps Google Fonts for the bundled font, and adds
the Home Screen manifest, icons and offline service worker. Run it after editing index.html.
"""
import hashlib
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT / "docs"
SITE.mkdir(exist_ok=True)

src = (ROOT / "index.html").read_text()
# Drop the artifact-only head lines; the wrapper below provides them.
src = re.sub(r'<meta name="claude:[^>]*>\n', "", src)
src = re.sub(r'<meta name="(apple-)?mobile-web-app-[^>]*>\n', "", src)
src = re.sub(r'<link rel="(preconnect|stylesheet)" href="https://fonts\.[^>]*>\n', "", src)

head = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no">
<meta name="theme-color" content="#fff3e4">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Puzzles">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="icon" type="image/png" href="icon-192.png">
<style>
@font-face { font-family: "Baloo 2"; font-weight: 400 800; font-display: swap; src: url("fonts/baloo2-latin.woff2") format("woff2"); }
:root { padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); box-sizing: border-box; }
body { margin: 0; font: 14px system-ui, sans-serif; }
img { max-width: 100%; }
[hidden] { display: none !important; }
</style>
"""
foot = """
<script>
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));
}
</script>
</body>
</html>
"""
# The artifact source starts with <title>/<style>; split so they land in <head>.
cut = src.index("</style>") + len("</style>")
html = head + src[:cut] + "\n</head>\n<body>\n" + src[cut:] + foot
(SITE / "index.html").write_text(html)

for size, name in [(180, "apple-touch-icon.png"), (192, "icon-192.png"), (512, "icon-512.png")]:
    subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size), str(ROOT / "icon.svg"), "-o", str(SITE / name)], check=True)

(SITE / "manifest.webmanifest").write_text(json.dumps({
    "name": "Puzzle Playroom",
    "short_name": "Puzzles",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "orientation": "any",
    "background_color": "#fff3e4",
    "theme_color": "#fff3e4",
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
    ],
}, indent=2))

files = ["./", "index.html", "manifest.webmanifest", "apple-touch-icon.png", "icon-192.png", "icon-512.png", "fonts/baloo2-latin.woff2"]
# Recorded voices (voices/make_voices.py) are cached too, so speech works offline.
files += sorted(str(f.relative_to(SITE)) for f in (SITE / "voice").glob("**/*") if f.is_file() and not f.name.startswith("."))
# Cache name changes whenever the game changes, so iPads pick up new versions.
voice_meta = b"".join((SITE / "voice" / n).read_bytes() for n in ("voices.json", ".stamps.json") if (SITE / "voice" / n).exists())
version = hashlib.sha256(html.encode() + voice_meta).hexdigest()[:10]
(SITE / "sw.js").write_text(f"""const CACHE = "puzzles-{version}";
const FILES = {json.dumps(files)};
self.addEventListener("install", (e) => {{
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(FILES)).then(() => self.skipWaiting()));
}});
self.addEventListener("activate", (e) => {{
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
}});
// Online: fetch fresh copies (and refresh the cache). Offline: serve the cached game.
// "no-cache" makes the browser check with the server instead of reusing GitHub's
// 10-minute HTTP cache, so updates appear on the next online launch.
self.addEventListener("fetch", (e) => {{
  if (e.request.method !== "GET") return;
  const sameOrigin = new URL(e.request.url).origin === location.origin;
  e.respondWith(
    fetch(sameOrigin ? new Request(e.request.url, {{ cache: "no-cache" }}) : e.request).then((res) => {{
      if (res.ok && sameOrigin) {{
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
      }}
      return res;
    }}).catch(() => caches.match(e.request, {{ ignoreSearch: true }}).then((r) => r || caches.match("index.html")))
  );
}});
""")
(SITE / ".nojekyll").write_text("")
print(f"Built {SITE} (cache {version})")
