#!/usr/bin/env python3
"""Generate podcast RSS feed(s) from a directory of audio files.

Usage: python3 make_feed.py <show-dir> [--release-tag TAG]
Files in <show-dir> are expected to be release assets under
  https://github.com/jm-darnel/private-podcasts/releases/download/<TAG>/<filename>
Episode order = sorted by filename. Durations/sizes read via ffprobe.
Writes <show-name>.xml in the repo root.
"""
import argparse, html, json, subprocess, sys
from pathlib import Path
from email.utils import formatdate
import time

BASE = "https://github.com/jm-darnel/private-podcasts/releases/download"
FEED_URL = "https://jm-darnel.github.io/private-podcasts"

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
    ap.add_argument("--release-tag", required=True)
    ap.add_argument("--title", required=True)
    args = ap.parse_args()

    d = Path(args.show_dir).expanduser()
    files = sorted(p for p in d.iterdir() if p.suffix.lower() in (".m4a", ".mp3", ".mp4", ".aac", ".ogg"))

    items = []
    for f in files:
        dur, size = probe(f)
        url = f"{BASE}/{args.release_tag}/{f.name}"
        items.append(f"""    <item>
      <title>{html.escape(f.stem)}</title>
      <enclosure url="{url}" length="{size}" type="audio/x-m4a"/>
      <guid isPermaLink="false">{url}</guid>
      <pubDate>{formatdate(time.time(), True)}</pubDate>
      <itunes:duration>{fmt_dur(dur)}</itunes:duration>
    </item>""")

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>{html.escape(args.title)}</title>
    <link>{FEED_URL}</link>
    <language>en-us</language>
    <itunes:author>Jonah Darnel</itunes:author>
    <itunes:owner><itunes:name>Jonah Darnel</itunes:name></itunes:owner>
    <description>{html.escape(args.title)} - personal feed</description>
{chr(10).join(items)}
  </channel>
</rss>
"""
    out = Path(__file__).parent / f"{args.title.replace(' ', '-').lower()}.xml"
    out.write_text(rss)
    print(f"wrote {out} with {len(items)} episodes")

if __name__ == "__main__":
    main()
