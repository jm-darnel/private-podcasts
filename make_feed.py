#!/usr/bin/env python3
"""Generate podcast RSS feed(s) from a directory of audio files.

Usage: python3 make_feed.py <show-dir> --title "Show Title" --artwork art.png
Audio lives in the repo (served by GitHub Pages) at shows/<dir>/<file>.
Order = sorted by filename. Durations/sizes read via ffprobe.
Writes <show-slug>.xml in the repo root.
"""
import argparse, html, json, subprocess
from pathlib import Path
from email.utils import formatdate
import time

BASE = "https://jm-darnel.github.io/private-podcasts"

def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
        capture_output=True, text=True, check=True).stdout
    fmt = json.loads(out)["format"]
    return int(float(fmt["duration"])), int(fmt["size"])

def fmt_dur(seconds):
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("show_dir")
    ap.add_argument("--title", required=True)
    ap.add_argument("--artwork", required=True, help="path to artwork image; copied into repo root")
    args = ap.parse_args()

    repo = Path(__file__).parent
    d = Path(args.show_dir).expanduser()
    rel_dir = str(Path(args.show_dir))

    art_src = Path(args.artwork).expanduser()
    art_dest = repo / art_src.name
    if not art_dest.exists() and art_src.exists():
        art_dest.write_bytes(art_src.read_bytes())
    art_url = f"{BASE}/{art_src.name}"

    files = sorted(p for p in d.iterdir() if p.suffix.lower() in (".m4a", ".mp3", ".mp4", ".aac", ".ogg"))

    items = []
    for i, f in enumerate(files):
        dur, size = probe(f)
        url = f"{BASE}/{rel_dir}/{f.name}"
        items.append(f"""    <item>
      <title>{html.escape(f.stem)}</title>
      <enclosure url="{url}" length="{size}" type="audio/x-m4a"/>
      <guid isPermaLink="false">{url}</guid>
      <pubDate>{formatdate(time.time() - (len(files) - i) * 3600, True)}</pubDate>
      <itunes:duration>{fmt_dur(dur)}</itunes:duration>
      <itunes:image href="{art_url}"/>
    </item>""")

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{html.escape(args.title)}</title>
    <link>{BASE}</link>
    <language>en-us</language>
    <itunes:author>Jonah Darnel</itunes:author>
    <itunes:owner><itunes:name>Jonah Darnel</itunes:name></itunes:owner>
    <description>{html.escape(args.title)} - personal feed</description>
    <image>
      <url>{art_url}</url>
      <title>{html.escape(args.title)}</title>
      <link>{BASE}</link>
    </image>
    <itunes:image href="{art_url}"/>
{chr(10).join(items)}
  </channel>
</rss>
"""
    slug = args.title.replace(" ", "-").lower()
    out = repo / f"{slug}.xml"
    out.write_text(rss)
    print(f"wrote {out} with {len(items)} episodes, artwork {art_url}")

if __name__ == "__main__":
    main()
