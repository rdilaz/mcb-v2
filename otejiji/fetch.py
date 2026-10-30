"""Recent games from Chess.com's public API (PubAPI). No key needed."""
import json
import time
import urllib.parse
import urllib.request

UA = "otejiji-pipeline/0.1 (+https://github.com/rdilaz/mcb-v2)"


def _get_json(url: str, tries: int = 3):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except Exception:
            if attempt == tries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def recent_games(username: str, months: int = 2, time_classes=("bullet", "blitz", "rapid", "daily")):
    """Newest first: [{"id": url, "pgn": str, "end_time": int, "time_class": str}]"""
    user = urllib.parse.quote(username.lower(), safe="")
    archives = _get_json(f"https://api.chess.com/pub/player/{user}/games/archives").get("archives", [])
    games = []
    for url in archives[-months:]:
        for g in _get_json(url).get("games", []):
            if g.get("rules") != "chess" or not g.get("pgn"):
                continue
            if time_classes and g.get("time_class") not in time_classes:
                continue
            games.append({"id": g.get("url") or g.get("uuid"), "pgn": g["pgn"],
                          "end_time": int(g.get("end_time", 0)), "time_class": g.get("time_class")})
    games.sort(key=lambda g: g["end_time"], reverse=True)
    return games
