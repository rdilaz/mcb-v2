# MCB v2: Most Common Blunder + Otejiji

MCB v2 takes MCB v1's blunder categorizer and runs it on a schedule. Every day it turns your worst
verified blunder into a short vertical video starring **Otejiji**, an AI chess grandpa.

## What runs every day (GitHub Actions, free)

1. **Fetch**: new games for `roygbiv6` from Chess.com's public API.
2. **Scan**: MCB's categorizer (`mcb_core/`, vendored from v1) flags blunders with Stockfish.
3. **Verify**: a deep Stockfish pass (depth 20) re-checks the top candidates and keeps the most severe
   one that holds up. A clip is made only when the position wasn't already lost and the move really
   dropped the win chance. Every move shown on screen is replayed by python-chess first, so the board
   is never AI-drawn and never wrong.
4. **Render**: real board frames, subtitles, the lesson card, and an "AI character" tag.
5. **Assemble**: ffmpeg builds `episode.mp4` (1080x1920, about 18-25 s) plus `caption.txt`.
6. **Output**: the episode is published as a GitHub release. The newest one is always at
   https://github.com/rdilaz/mcb-v2/releases/latest/download/episode.mp4

Posting is the next increment (see below).

## Changes from MCB v1

- **Mate checks run first.** v1 checked hanging pieces before checkmate, so a move that walked into
  mate in 2 could be reported as "Hanging a Piece".
- **Deep verification** before anything is shown publicly.

## Run it

Actions tab, then **Otejiji daily episode**, then **Run workflow**. It also runs every day at 7:07pm ET.

Offline test:

```bash
sudo apt-get install stockfish ffmpeg libcairo2
pip install -r requirements.txt
STOCKFISH_PATH=/usr/games/stockfish python -m otejiji.run --pgn-file tests/sample.pgn --out out
```

## Assets (`assets/otejiji.json`)

- `face`: Otejiji's portrait (Higgsfield).
- `clips`: optional reaction videos keyed `intro` / `outro`. These replace the slow zoom on the photo.
- `voice.lines`: one audio URL per line key in `otejiji/lines.py` (e.g. `Hanging a Piece.hook`).
  Lines that are missing show as subtitles only.
- `assets/theme.mp3` (optional): background music, mixed in quietly.

## Next: auto-posting

The plan is to post through a social posting API (TikTok + Instagram) on a schedule, with TikTok's
AI-generated-content flag set. Adding it needs the Otejiji accounts, the API key in repo secrets,
and a check against the provider's docs.
