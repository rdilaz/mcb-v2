"""Frames for an episode: real board positions (never AI-drawn), subtitles, cards."""
import os
import textwrap
from io import BytesIO

import cairosvg
import chess
import chess.svg
from PIL import Image, ImageDraw, ImageFont

from .lines import DISPLAY, line, voice_key

W, H = 1080, 1920
BOARD = 820
BX, BY = 80, 430          # nudged left: TikTok/Reels side buttons sit over the right edge
BG = (14, 22, 17)
WHITE, GREY, GOLD = (255, 255, 255), (150, 170, 158), (250, 176, 5)
ORANGE, RED, GREEN = "#f76707dd", "#e03131dd", "#2f9e44dd"
FONT = os.environ.get("OTEJIJI_FONT", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")


def _font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default()


def _text(draw, text, y, size, fill, width_chars, shadow=False):
    f = _font(size)
    for ln in textwrap.wrap(text, width_chars):
        w = draw.textlength(ln, font=f)
        x = (W - w) / 2
        if shadow:
            draw.text((x + 3, y + 3), ln, font=f, fill=(0, 0, 0))
        draw.text((x, y), ln, font=f, fill=fill)
        y += int(size * 1.25)
    return y


def _board_img(board, orientation, arrows=(), fill=None):
    svg = chess.svg.board(board, orientation=orientation, arrows=list(arrows), fill=fill or {},
                          size=BOARD, coordinates=True)
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=BOARD, output_height=BOARD)
    return Image.open(BytesIO(png)).convert("RGB")


def board_frame(board, orientation, arrows, fill, header, title, main, detail):
    img = Image.new("RGB", (W, H), BG)
    img.paste(_board_img(board, orientation, arrows, fill), (BX, BY))
    d = ImageDraw.Draw(img)
    _text(d, header, 225, 34, GREY, 40)
    _text(d, title, 280, 62, WHITE, 30)
    y = _text(d, main, BY + BOARD + 60, 54, WHITE, 26)
    if detail:
        _text(d, detail, y + 14, 40, GOLD, 34)
    return img


def card_frame(big, small_lines):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    y = _text(d, big, 700, 68, WHITE, 20)
    y += 60
    for s, color in small_lines:
        y = _text(d, s, y, 38, color, 36) + 18
    return img


def face_overlay(main):
    """Transparent layer for face/clip segments: subtitle + AI disclosure tag."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1180, W, 1620], fill=(0, 0, 0, 110))
    _text(d, main, 1260, 60, WHITE, 24, shadow=True)
    tag = _font(30)
    d.text((60, 170), "AI character", font=tag, fill=(255, 255, 255, 200))
    return img


def face_background(face_path):
    """Cover-crop the face to 9:16 at 1.2x so ffmpeg can slowly zoom without upscaling artifacts."""
    if not face_path or not os.path.exists(face_path):
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        _text(d, "OTEJIJI", 560, 120, WHITE, 12)
        _text(d, "chess grandpa", 720, 44, GREY, 30)
        return img.resize((int(W * 1.2), int(H * 1.2)))
    src = Image.open(face_path).convert("RGB")
    tw, th = int(W * 1.2), int(H * 1.2)
    scale = max(tw / src.width, th / src.height)
    src = src.resize((int(src.width * scale + 0.5), int(src.height * scale + 0.5)), Image.LANCZOS)
    left, top = (src.width - tw) // 2, (src.height - th) // 2
    return src.crop((left, top, left + tw, top + th))


def _arrow(mv, color):
    return chess.svg.Arrow(mv.from_square, mv.to_square, color=color)


def story_segments(story, workdir, stats=None, cta=None):
    """Write frames to workdir and return the segment list for assemble.py."""
    os.makedirs(workdir, exist_ok=True)
    cat = story["category"]
    me = chess.WHITE if story["color"] == "white" else chess.BLACK
    before = chess.Board(story["fen"])
    played = chess.Move.from_uci(story["played"]["uci"])
    best = chess.Move.from_uci(story["best"]["uci"])
    title = DISPLAY.get(cat, "One Bad Move")
    top = stats.get("header") if stats else None
    header = top or "TODAY'S BLUNDER"
    segs, n = [], [0]

    def save(img, base, role=None, detail_only=False):
        n[0] += 1
        p = os.path.join(workdir, f"s{n[0]:02d}.png")
        img.save(p)
        segs.append({"type": "image", "path": p, "base": base,
                     "voice": voice_key(cat, role) if role else None})

    def face(role, base):
        n[0] += 1
        p = os.path.join(workdir, f"s{n[0]:02d}_overlay.png")
        face_overlay(line(cat, role)["en"]).save(p)
        segs.append({"type": "face", "overlay": p, "base": base, "voice": voice_key(cat, role), "role": role})

    face("intro", 2.4)
    hook_fill = {played.to_square: "#f7670766"}
    if story.get("focus"):
        hook_fill[chess.parse_square(story["focus"])] = "#e0313188"
    save(board_frame(before, me, [_arrow(played, ORANGE)], hook_fill,
                     header, title, line(cat, "hook")["en"], f"You played {story['played']['san']}"),
         2.8, "hook")

    start = chess.Board(story["line_start_fen"])
    moves = [chess.Move.from_uci(u) for u in story["line"]]
    b = start.copy()
    for i, mv in enumerate(moves):
        mover = b.turn
        b.push(mv)
        color = GREEN if (mover == me) else RED
        fill = {}
        if b.is_checkmate():
            fill = {b.king(b.turn): "#e03131cc"}
        last = i == len(moves) - 1
        so_far = start.variation_san(moves[: i + 1])
        detail = f"{so_far}  {story['outcome']}" if last else so_far
        role = "punish" if i == 0 else None
        main = line(cat, "punish")["en"]
        if story["kind"] == "missed" and i == 0:
            detail = f"Better: {story['best']['san']}"
        save(board_frame(b, me, [_arrow(mv, color)], fill, header, title, main, detail),
             2.6 if i == 0 else (2.0 if last else 1.3), role)

    if story["kind"] == "allowed":
        save(board_frame(before, me, [_arrow(best, GREEN)], {best.to_square: "#2f9e4466"},
                         header, title, line(cat, "fix")["en"], f"Better: {story['best']['san']}"),
             2.6, "fix")

    small = []
    if stats and stats.get("most_common"):
        small.append((stats["most_common"], GREY))
    if cta:
        small.append((cta, GOLD))
    save(card_frame(line(cat, "lesson")["en"], small), 3.2, "lesson")
    face("outro", 1.8)
    return segs
