// Lists every phrase the app can speak, computed from the app's own data in index.html,
// as JSON lines: {"key": "...", "text": "..."} where "text" is what Piper should read.
// The app looks clips up by the same key (see phraseKey() in index.html).
import fs from "node:fs";

const html = fs.readFileSync(new URL("../index.html", import.meta.url), "utf8");
const src = html.slice(html.indexOf("<script>\n") + 9, html.lastIndexOf("</script>"));
const slice = (from, to) => {
  const a = src.indexOf(from), b = src.indexOf(to, a);
  if (a < 0 || b < 0) throw new Error(`marker not found: ${a < 0 ? from : to}`);
  return src.slice(a, b);
};
const body = [
  slice("const rng", "const imgCache"),            // drawings + ART (puzzle names)
  slice("const WORDS", "let activeGame"),           // number words, balloon colors
  slice("const heartPath", "const NUM_COLORS"),     // counting objects
  slice("const LETTER_NAMES", "const abcGame"),     // ABC
  slice("const abcPic", "const splatSVG"),          // Colors
  slice("const numPic", "const shadowGame"),        // Shadow match
].join("\n");
const data = new Function(body + "; return { ART, WORDS, NUM_ITEMS, LETTER_NAMES, ABC, COLORS, BALLOON_COLORS, SHAPE_POOL };")();

const phraseKey = (t) => t.toLowerCase().replace(/[^a-z0-9' -]+/g, " ").replace(/\s+/g, " ").trim();
const out = new Map();
const add = (text, piperText = text) => { const k = phraseKey(text); if (k && (!out.has(k) || piperText.endsWith("!"))) out.set(k, piperText); };

// Letter names are read from the letter itself; "A" and "I" alone at a sentence start are read
// as words ("uh", "I"), so those two are given as phonemes.
const LETTER_SOUND = (i) => ({ 0: "[[ ˈeɪ ]]", 8: "[[ ˈaɪ ]]" }[i] || String.fromCharCode(65 + i));

const { ART, WORDS, NUM_ITEMS, LETTER_NAMES, ABC, COLORS, BALLOON_COLORS, SHAPE_POOL } = data;
// Fixed phrases
["Yay! You did it!", "Yay! All popped!", "Rainbow!", "Red, orange, yellow, green, blue, purple!"].forEach(t => add(t));
// Puzzles: "Yay! You did it!" then the picture's name
ART.forEach(a => add(a.name + "!"));
// Numbers and numbered balloons
for (let n = 1; n <= 10; n++) {
  add(WORDS[n] + "!"); add(WORDS[n]);
  const [one, many] = NUM_ITEMS[n - 1];
  add(`${WORDS[n]} ${n === 1 ? one : many}!`);
}
// ABC
LETTER_NAMES.forEach((name, i) => {
  add(name + "!", LETTER_SOUND(i) + "!");
  add(`${name} is for ${ABC[i][0]}!`, `${LETTER_SOUND(i)} is for ${ABC[i][0]}!`);
});
// Colors and colored balloons
COLORS.forEach(([name, , , items]) => { add(name + "!"); items.forEach(([spoken]) => add(spoken)); });
BALLOON_COLORS.forEach(([name]) => add(name + "!"));
// Shadow match
SHAPE_POOL.forEach(([name]) => add(name + "!"));

for (const [key, text] of out) console.log(JSON.stringify({ key, text }));
