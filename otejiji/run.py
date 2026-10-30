"""Daily run: fetch games -> MCB scan -> deep verify -> render -> assemble.

    python -m otejiji.run --out out                      # Chess.com (what the GitHub Action runs)
    python -m otejiji.run --pgn-file tests/sample.pgn    # offline test
"""
import argparse
import hashlib
import io
import json
import os
import time
from collections import Counter

import chess.engine
import chess.pgn

from . import assemble, fetch, find, render
from .lines import DISPLAY, canon, line

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "state", "pool.json")
ASSETS = os.path.join(ROOT, "assets", "otejiji.json")
DAY = 86400


def _load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)


def _local_games(path):
    games, text = [], open(path).read()
    stream = io.StringIO(text)
    while True:
        start = stream.tell()
        g = chess.pgn.read_game(stream)
        if g is None:
            break
        pgn = text[start:stream.tell()]
        gid = g.headers.get("Link") or "local:" + hashlib.sha1(pgn.encode()).hexdigest()[:10]
        games.append({"id": gid, "pgn": pgn, "end_time": 0, "time_class": "local"})
    return games


def caption(story, stats, cta):
    lesson = line(story["category"], "lesson")["en"]
    return (f"My student played this. {DISPLAY.get(story['category'], 'One Bad Move')} ♟️ {lesson} "
            f"{cta}. #chess #chesstok #chesstips #learnchess #blunder #aicharacter")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--username", default=os.environ.get("CHESS_USERNAME", "roygbiv6"))
    ap.add_argument("--out", default="out")
    ap.add_argument("--pgn-file")
    ap.add_argument("--max-new-games", type=int, default=int(os.environ.get("MAX_NEW_GAMES", "8")))
    ap.add_argument("--state", default=STATE)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    state = _load(args.state, {"analyzed": [], "pool": [], "used": []})
    games = _local_games(args.pgn_file) if args.pgn_file else fetch.recent_games(args.username)
    new = [g for g in games if g["id"] not in set(state["analyzed"])][: args.max_new_games]
    print(f"{len(games)} games found, {len(new)} new to analyze")

    engine = chess.engine.SimpleEngine.popen_uci(os.environ.get("STOCKFISH_PATH", "stockfish"))
    story = None
    try:
        for g in new:
            t0 = time.time()
            cands = find.scan_game(g["pgn"], args.username, engine, g["id"], g["end_time"])
            state["pool"].extend(cands)
            state["analyzed"].append(g["id"])
            print(f"  {g['id']}: {len(cands)} blunders ({time.time() - t0:.0f}s)")
        cutoff = time.time() - 60 * DAY
        state["pool"] = [c for c in state["pool"] if not c.get("end_time") or c["end_time"] >= cutoff]
        # Deep-verify several candidates and keep the most severe *verified* one, so a real
        # mate beats a hanging pawn even when MCB's fast pass labeled them the other way round.
        verified = []
        for cand in find.rank(state["pool"], set(state["used"]))[:10]:
            st = find.build_story(cand, engine)
            print(f"  verify {cand['category']} {cand['san']}: {st['category'] if st else 'rejected'}")
            if st:
                verified.append((cand, st))
            else:
                state["used"].append(cand["id"])  # never retry a rejected candidate
            if len(verified) >= 4:
                break
        if verified:
            cand, story = min(verified, key=lambda cs: (find.PRIORITY.get(cs[1]["category"], 99), -cs[0]["drop"]))
            state["used"].append(cand["id"])
    finally:
        engine.quit()
        _save(args.state, state)

    if not story:
        print("No verified blunder today. Nothing to post.")
        open(os.path.join(args.out, "NO_EPISODE"), "w").close()
        return 0

    month = [c for c in state["pool"] if not c.get("end_time") or c["end_time"] >= time.time() - 30 * DAY]
    top, count = Counter(canon(c["category"]) for c in month).most_common(1)[0]
    stats = {"most_common": f"Most common this month: {DISPLAY.get(top, top)} x{count}",
             "header": "MY STUDENT'S MOST COMMON BLUNDER" if top == story["category"] else "TODAY'S BLUNDER"}
    cta = os.environ.get("MCB_CTA", "Find your most common blunder: mcb.ryo-nd.com")

    segs = render.story_segments(story, os.path.join(args.out, "frames"), stats, cta)
    timeline, total = assemble.build(segs, _load(ASSETS, {}), os.path.join(args.out, "work"),
                                     os.path.join(args.out, "episode.mp4"), os.path.join(ROOT, "assets", "theme.mp3"))
    cap = caption(story, stats, cta)
    _save(os.path.join(args.out, "episode.json"),
          {"story": story, "stats": stats, "timeline": timeline, "seconds": total, "caption": cap})
    with open(os.path.join(args.out, "caption.txt"), "w") as f:
        f.write(cap + "\n")
    print(f"episode.mp4 ready: {story['category']} {story['played']['san']} ({total}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
