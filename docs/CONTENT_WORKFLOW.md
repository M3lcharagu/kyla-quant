# Content creation lane

## Daily clipping pipeline

Use this exact lightweight pipeline:

**choose song → clip segments → auto-edit via CapCut/Canva → post on TikTok @lemiii1_ and Instagram @lemmii1_.**

1. **Choose song** — select the song and the angle for the day's topic. Confirm that the audio and source material can be used on the intended platforms.
2. **Clip segments** — select short, useful or entertaining moments and keep a simple note of the source and segment order.
3. **Auto-edit via CapCut/Canva** — use a repeatable vertical template, captions, a clear hook, and a short close. Keep manual review before export.
4. **Post** — publish the approved clip on TikTok **@lemiii1_** and Instagram **@lemmii1_** with a concise caption and platform-appropriate tags.

## Daily plan helper

`content/daily_content_plan.py` is a dependency-free Python skeleton. It uses a small in-file topic list and prints a JSON plan of 3–5 clips; it needs no API keys or network access.

```bash
python3 content/daily_content_plan.py
python3 content/daily_content_plan.py --count 5 --topic "a client lesson" --topic "a quick market note"
```

The script only creates a plan. It does not download media, edit videos, or post automatically.
