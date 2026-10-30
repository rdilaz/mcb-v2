"""Find teachable blunders: MCB's categorizer for the scan, then a deep Stockfish pass to verify.

Nothing reaches a video unless the deep pass confirms it:
  * the position before the move was not already lost (win chance >= 20%, about -3.5 pawns)
  * the move really dropped the win chance by >= 20 points
  * every move shown on screen is legal (python-chess replays the whole line)
"""
import io
import os
import re
import sys

import chess
import chess.engine
import chess.pgn

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "mcb_core"))
import analyze_games as mcb  # noqa: E402  MCB categorizer (vendored from v1, mate check moved first)

from .lines import canon  # noqa: E402

FAST = chess.engine.Limit(depth=12, time=0.25)  # MCB's "balanced" setting
DEEP = chess.engine.Limit(depth=20, time=3.0)
MIN_WP_BEFORE = 0.20
MIN_DROP = 0.20

PRIORITY = {"Allowed Checkmate": 1, "Missed Checkmate": 2, "Hanging a Piece": 3, "Allowed Trap": 4,
            "Losing Exchange": 5, "Missed Material Gain": 6, "Critical blunder": 7, "Blunder": 8}
NAMES = {chess.PAWN: "pawn", chess.KNIGHT: "knight", chess.BISHOP: "bishop",
         chess.ROOK: "rook", chess.QUEEN: "queen"}


def _color_of(game, username):
    u = username.lower()
    if game.headers.get("White", "").lower() == u:
        return chess.WHITE
    if game.headers.get("Black", "").lower() == u:
        return chess.BLACK
    return None


def scan_game(pgn_text: str, username: str, engine, game_id: str, end_time: int = 0):
    """Fast pass over one game, mirroring MCB's analyze_game_optimized loop."""
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        return []
    color = _color_of(game, username)
    if color is None:
        return []
    state = mcb.BlunderStateManager()
    board = game.board()
    found = []
    for ply, move in enumerate(game.mainline_moves()):
        if board.turn != color:
            board.push(move)
            continue
        prev = board.move_stack[-1] if board.move_stack else None
        if mcb.should_skip_move_prefilter(board, move, prev, False):
            board.push(move)
            continue
        before = board.copy(stack=False)
        san = board.san(move)
        info_b = engine.analyse(board, FAST)
        eval_b = info_b["score"].pov(color).score(mate_score=10000)
        board.push(move)
        pv = info_b.get("pv")
        if pv and pv[0] == move:
            state.update_eval(eval_b)
            continue
        if (before.fullmove_number > 30 and len(before.piece_map()) < 10
                and eval_b is not None and abs(eval_b) < 100):
            state.update_eval(eval_b)
            continue
        info_a = engine.analyse(board, FAST)
        hit = mcb.categorize_blunder_optimized(before, board, move, info_b, info_a, info_b,
                                               state, False, before.fullmove_number)
        if hit and hit["category"] in PRIORITY:
            found.append({
                "id": f"{game_id}#{ply}", "game": game_id, "end_time": end_time,
                "fen": before.fen(), "move": move.uci(), "san": san,
                "category": hit["category"], "description": hit["description"],
                "drop": round(float(hit.get("win_prob_drop", 0.0)), 1),
            })
    return found


def _wp(score):
    return mcb.cp_to_win_prob(score.score(mate_score=10000))


def _walk(board, pv, mover_color, stop_on_capture_by, max_plies=5):
    """Replay up to max_plies of pv; stop at mate or after the first capture of a minor+ piece
    made by `stop_on_capture_by`. Returns (moves, victim_name, mated)."""
    b, shown = board.copy(), []
    for mv in pv[:max_plies]:
        if mv not in b.legal_moves:
            break
        victim = b.piece_at(mv.to_square)
        if b.is_en_passant(mv):
            victim = chess.Piece(chess.PAWN, not b.turn)
        capturer = b.turn
        shown.append(mv)
        b.push(mv)
        if b.is_checkmate():
            return shown, None, True
        if (victim and capturer == stop_on_capture_by
                and victim.piece_type in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)):
            return shown, NAMES[victim.piece_type], False
    return (shown if len(shown) <= 2 else shown[:2]), None, False


def build_story(cand: dict, engine):
    """Deep-verify one candidate and turn it into everything the video needs. None = reject."""
    before = chess.Board(cand["fen"])
    me = before.turn
    played = chess.Move.from_uci(cand["move"])
    ib = engine.analyse(before, DEEP)
    best = (ib.get("pv") or [None])[0]
    if best is None or best == played:
        return None
    after = before.copy()
    after.push(played)
    if after.is_game_over():
        return None
    ia = engine.analyse(after, DEEP)
    sb, sa = ib["score"].pov(me), ia["score"].pov(me)
    wp_b, wp_a = _wp(sb), _wp(sa)
    if wp_b < MIN_WP_BEFORE or (wp_b - wp_a) < MIN_DROP:
        return None

    category = canon(cand["category"])
    if sa.is_mate() and sa.mate() < 0 and abs(sa.mate()) <= 3:
        category = "Allowed Checkmate"
    elif sb.is_mate() and 0 < sb.mate() <= 3:
        category = "Missed Checkmate"
    kind = "missed" if category in ("Missed Checkmate", "Missed Material Gain") else "allowed"

    if kind == "allowed":
        line_start = after
        moves, victim, mated = _walk(after, ia.get("pv", []), me, stop_on_capture_by=not me)
        if mated:
            outcome = "Checkmate."
        elif victim:
            outcome = f"He takes your {victim}."
        else:
            outcome = "And your position collapses."
    else:
        line_start = before
        moves, victim, mated = _walk(before, ib.get("pv", []), me, stop_on_capture_by=me)
        if mated:
            outcome = "Checkmate."
        elif victim:
            outcome = f"You win his {victim}."
        else:
            outcome = "And you're winning."
    if not moves:
        return None

    # Full replay check: the line on screen must be legal from its start position.
    check = line_start.copy()
    for mv in moves:
        assert mv in check.legal_moves, "illegal move in on-screen line"
        check.push(mv)
    assert (check.is_checkmate() == mated)

    num = before.fullmove_number
    prefix = f"{num}." if me == chess.WHITE else f"{num}..."
    focus = None
    m = re.search(r"your \w+ on ([a-h][1-8])", cand.get("description", ""))
    if m and category == "Hanging a Piece":
        focus = m.group(1)
    return {
        "focus": focus,
        "id": cand["id"], "game": cand["game"], "category": category, "kind": kind,
        "color": "white" if me == chess.WHITE else "black",
        "fen": before.fen(),
        "played": {"uci": played.uci(), "san": prefix + before.san(played)},
        "best": {"uci": best.uci(), "san": prefix + before.san(best)},
        "line_start_fen": line_start.fen(),
        "line": [mv.uci() for mv in moves],
        "line_san": line_start.variation_san(moves),
        "mated": mated, "victim": victim, "outcome": outcome,
        "wp_before": round(wp_b, 3), "wp_after": round(wp_a, 3),
    }


def rank(pool, used):
    fresh = [c for c in pool if c["id"] not in used]
    return sorted(fresh, key=lambda c: (PRIORITY.get(c["category"], 99), -c["drop"], -c.get("end_time", 0)))
