"""What Otejiji says. English is the subtitle; Japanese is what the voice speaks (VOICE_LANG=ja).

Lines are generic per blunder category so the voice library can be generated once and
reused forever. Move-specific details (squares, SAN) appear as on-screen text instead.
"""

DISPLAY = {
    "Allowed Checkmate": "Walking Into Mate",
    "Missed Checkmate": "The Missed Mate",
    "Hanging a Piece": "The Hanging Piece",
    "Allowed Trap": "The Trapped Piece",
    "Losing Exchange": "The Bad Trade",
    "Missed Material Gain": "The Free Gift",
    "Blunder": "One Bad Move",
}

# category -> role -> {"en": subtitle, "ja": spoken line}
LINES = {
    "intro": {"en": "Sit down. Let me show you today's blunder.", "ja": "まあ、座れ。今日の悪手を見せてやろう。"},
    "outro": {"en": "See you tomorrow.", "ja": "また明日。"},
    "Hanging a Piece": {
        "hook": {"en": "Look. Nobody is guarding it.", "ja": "見ろ。誰も守っていない。"},
        "punish": {"en": "A free piece. Thanks for the meal.", "ja": "タダの駒だ。ごちそうさま。"},
        "fix": {"en": "This was better.", "ja": "こっちが良かった。"},
        "lesson": {"en": "Before you let go of a piece, ask who protects it.",
                   "ja": "駒から手を離す前に、誰が守っているか確かめなさい。"},
    },
    "Allowed Checkmate": {
        "hook": {"en": "You were watching the pieces. He was watching your king.",
                 "ja": "お前は駒を見ていた。相手は王様を見ていた。"},
        "punish": {"en": "Checkmate. That's the end.", "ja": "詰みだ。おしまい。"},
        "fix": {"en": "Protect your king first.", "ja": "まず王様を守りなさい。"},
        "lesson": {"en": "Every move, look at his checks first.", "ja": "毎回、相手の王手を先に見なさい。"},
    },
    "Missed Checkmate": {
        "hook": {"en": "The win was sitting right there.", "ja": "勝ちは目の前にあったのに。"},
        "punish": {"en": "Look. This is checkmate.", "ja": "見ろ。これで詰みだ。"},
        "fix": {"en": "This was better.", "ja": "こっちが良かった。"},
        "lesson": {"en": "Look for your own checks first. Always.", "ja": "まず自分の王手を探しなさい。いつもだ。"},
    },
    "Missed Material Gain": {
        "hook": {"en": "He gave you a gift, and you said no.", "ja": "相手が贈り物をくれたのに、断ったな。"},
        "punish": {"en": "You walked right past a free piece.", "ja": "タダの駒を素通りしたな。"},
        "fix": {"en": "This was better.", "ja": "こっちが良かった。"},
        "lesson": {"en": "Every move, look: is anything free?", "ja": "毎回、タダで取れる駒がないか見なさい。"},
    },
    "Losing Exchange": {
        "hook": {"en": "You traded gold for a stone.", "ja": "金を石と交換したな。"},
        "punish": {"en": "Count again.", "ja": "もう一度数えてみなさい。"},
        "fix": {"en": "This was better.", "ja": "こっちが良かった。"},
        "lesson": {"en": "Count attackers. Count defenders. Then take.", "ja": "攻め駒を数えろ。守り駒を数えろ。それから取れ。"},
    },
    "Allowed Trap": {
        "hook": {"en": "Your piece walked into a cage.", "ja": "お前の駒は檻に入った。"},
        "punish": {"en": "No way out.", "ja": "逃げ道がない。"},
        "fix": {"en": "This was better.", "ja": "こっちが良かった。"},
        "lesson": {"en": "Before you go deep, check the exits.", "ja": "深く入る前に、逃げ道を確かめなさい。"},
    },
    "Blunder": {
        "hook": {"en": "One move. That's all it takes.", "ja": "一手。それだけで全部変わる。"},
        "punish": {"en": "And then it all falls apart.", "ja": "そして崩れる。"},
        "fix": {"en": "This was better.", "ja": "こっちが良かった。"},
        "lesson": {"en": "The bigger the moment, the slower you think.", "ja": "大事な時ほど、ゆっくり考えなさい。"},
    },
}

ALIASES = {"Critical blunder": "Blunder", "Mistake": "Blunder"}


def canon(category: str) -> str:
    category = ALIASES.get(category, category)
    return category if category in LINES else "Blunder"


def line(category: str, role: str) -> dict:
    if role in ("intro", "outro"):
        return LINES[role]
    return LINES[canon(category)][role]


def voice_key(category: str, role: str) -> str:
    return role if role in ("intro", "outro") else f"{canon(category)}.{role}"


def all_voice_lines():
    """Every (key, line) pair, for generating the voice library once."""
    yield "intro", LINES["intro"]
    yield "outro", LINES["outro"]
    for cat, roles in LINES.items():
        if cat in ("intro", "outro"):
            continue
        for role, ln in roles.items():
            yield f"{cat}.{role}", ln
