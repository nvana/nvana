"""Community 2048 for the profile README.

Every arrow in the README opens a pre-filled issue titled `2048|<direction>`.
The 2048 workflow passes that title and the author's login in through env vars,
this script plays the move, redraws assets/2048.svg and the README section,
and prints the reply posted on the issue.

    python scripts/game2048.py new      # wipe everything, start game #1
    python scripts/game2048.py render   # redraw svg + README from state
    MOVE=2048|left PLAYER=octocat python scripts/game2048.py move
"""
import json
import os
import pathlib
import random
import re
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE = ROOT / "game" / "state.json"
BOARD_SVG = ROOT / "assets" / "2048.svg"
README = ROOT / "README.md"
REPO = "nvana/nvana"
START, END = "<!-- 2048:start -->", "<!-- 2048:end -->"

N = 4
DIRS = ("up", "left", "down", "right")
ARROWS = {"up": "↑", "left": "←", "down": "↓", "right": "→"}
FONT = "ui-monospace,'JetBrains Mono','SFMono-Regular',Menlo,monospace"
TILE_COLORS = {
    2: "#16365c", 4: "#0A66C2", 8: "#3d5afe", 16: "#5b4bff", 32: "#6E44FF",
    64: "#9b44ff", 128: "#c445e0", 256: "#e2559c", 512: "#FF6B6B",
    1024: "#ff8c5a", 2048: "#ffc24b",
}


# --- game rules -------------------------------------------------------------

def lines(direction):
    """Cell coordinates per line, ordered in the direction tiles slide."""
    idx = range(N)
    rev = range(N - 1, -1, -1)
    return {
        "left": [[(r, c) for c in idx] for r in idx],
        "right": [[(r, c) for c in rev] for r in idx],
        "up": [[(r, c) for r in idx] for c in idx],
        "down": [[(r, c) for r in rev] for c in idx],
    }[direction]


def slide(board, direction):
    """Return (new_board, gained, merged_cells) without spawning a tile."""
    new = [[0] * N for _ in range(N)]
    gained, merged = 0, []
    for line in lines(direction):
        tiles = [board[r][c] for r, c in line if board[r][c]]
        out = []
        i = 0
        while i < len(tiles):
            if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
                out.append(tiles[i] * 2)
                gained += tiles[i] * 2
                merged.append(list(line[len(out) - 1]))
                i += 2
            else:
                out.append(tiles[i])
                i += 1
        for (r, c), v in zip(line, out):
            new[r][c] = v
    return new, gained, merged


def spawn(board, rng):
    empty = [(r, c) for r in range(N) for c in range(N) if not board[r][c]]
    if not empty:
        return None
    r, c = rng.choice(empty)
    board[r][c] = 4 if rng.random() < 0.1 else 2
    return [r, c]


def can_move(board):
    return any(slide(board, d)[0] != board for d in DIRS)


def new_game(state, rng):
    board = [[0] * N for _ in range(N)]
    spawn(board, rng)
    state.update(
        game=state.get("game", 0) + 1, board=board, score=0, moves=0,
        over=False, spawn=spawn(board, rng), merged=[],
    )


# --- state ------------------------------------------------------------------

def fresh_state(rng):
    state = {"best": 0, "total_moves": 0, "players": {}, "recent": [], "finished": []}
    new_game(state, rng)
    return state


def load():
    return json.loads(STATE.read_text(encoding="utf-8"))


def save(state):
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state, indent=1) + "\n", encoding="utf-8", newline="\n")


def play(state, move, player, rng):
    """Apply one move and return the markdown reply for the issue."""
    board_link = f"[Back to the board →](https://github.com/{REPO.split('/')[0]})"

    if state["over"]:
        ended = state["game"]
        new_game(state, rng)
        record(state, player, "new game", 0)
        return (f"Game #{ended} was already over, so you kicked off **game #{state['game']}** 🎲\n\n"
                f"{board_link}")

    board, gained, merged = slide(state["board"], move)
    if board == state["board"]:
        return (f"Sliding **{move}** {ARROWS[move]} doesn't move anything right now — "
                f"try another direction.\n\n{board_link}")

    state.update(board=board, merged=merged, spawn=spawn(board, rng))
    state["score"] += gained
    state["moves"] += 1
    state["best"] = max(state["best"], state["score"])
    record(state, player, move, gained)

    reply = f"You slid **{move}** {ARROWS[move]}"
    reply += f" and merged for **+{gained}**" if gained else ""
    reply += f". Score is now **{state['score']}** after {state['moves']} move{'s' * (state['moves'] != 1)}."
    if not can_move(board):
        state["over"] = True
        top = max(max(row) for row in board)
        state["finished"] = ([{"game": state["game"], "score": state["score"], "top": top}]
                             + state["finished"])[:5]
        reply += f"\n\n💀 That was the last possible move — **game #{state['game']} is over** (top tile {top})."
    return f"{reply}\n\n{board_link}"


def record(state, player, move, gained):
    state["total_moves"] += 1
    state["players"][player] = state["players"].get(player, 0) + 1
    state["recent"] = ([{"player": player, "move": move, "gain": gained}] + state["recent"])[:5]


# --- rendering --------------------------------------------------------------

def tile_svg(r, c, v, spawned, merged):
    size, gap, top = 76, 10, 92
    x = 20 + c * (size + gap)
    y = top + r * (size + gap)
    cx, cy = x + size / 2, y + size / 2
    if not v:
        return f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="10" fill="#1a2030"/>'

    fill = TILE_COLORS.get(v, "#f5f7ff")
    ink = "#0f1320" if v >= 2048 else "#f5f7ff"
    digits = len(str(v))
    font = {1: 34, 2: 32, 3: 27, 4: 22}.get(digits, 18)
    anim = ""
    if spawned:
        anim = ('<animateTransform attributeName="transform" type="scale" values="0;0;1" '
                'keyTimes="0;.5;1" dur=".5s" fill="freeze"/>')
    elif merged:
        anim = ('<animateTransform attributeName="transform" type="scale" values="1;1.14;1" '
                'dur=".35s" begin=".15s" fill="freeze"/>')
    glow = (f'<rect x="{-size/2 - 3}" y="{-size/2 - 3}" width="{size + 6}" height="{size + 6}" rx="13" '
            f'fill="none" stroke="{fill}" stroke-opacity=".45" stroke-width="2"/>') if v >= 128 else ""
    return (
        f'<g transform="translate({cx} {cy})"><g>{anim}{glow}'
        f'<rect x="{-size/2}" y="{-size/2}" width="{size}" height="{size}" rx="10" fill="{fill}"/>'
        f'<text y="{font * 0.36:.1f}" text-anchor="middle" font-size="{font}" font-weight="700" '
        f'fill="{ink}">{v}</text></g></g>'
    )


def board_svg(state):
    width, height = 384, 450
    spawn_at = state.get("spawn")
    merged = {tuple(m) for m in state.get("merged", [])}
    tiles = "\n  ".join(
        tile_svg(r, c, state["board"][r][c], [r, c] == spawn_at, (r, c) in merged)
        for r in range(N) for c in range(N)
    )
    over = ""
    if state["over"]:
        over = (
            f'<rect x="12" y="84" width="{width - 24}" height="{width - 24}" rx="14" fill="#0f1320" fill-opacity=".78">'
            '<animate attributeName="fill-opacity" values="0;.78" dur=".6s" fill="freeze"/></rect>'
            f'<text x="{width / 2}" y="250" text-anchor="middle" font-size="34" font-weight="700" fill="#FF6B6B">game over</text>'
            f'<text x="{width / 2}" y="282" text-anchor="middle" font-size="13" fill="#8892a6">any arrow starts game #{state["game"] + 1}</text>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="community 2048, score {state['score']}">
  <defs>
    <linearGradient id="ink" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#0A66C2"/><stop offset="55%" stop-color="#6E44FF"/><stop offset="100%" stop-color="#FF6B6B"/>
    </linearGradient>
    <style>text {{ font-family: {FONT} }}</style>
  </defs>
  <rect width="{width}" height="{height}" rx="18" fill="#0f1320"/>
  <text x="20" y="44" font-size="30" font-weight="700" fill="url(#ink)">2048</text>
  <text x="20" y="66" font-size="11" fill="#8892a6" letter-spacing=".5">game #{state['game']} · move {state['moves']}</text>
  <rect x="{width - 196}" y="20" width="84" height="48" rx="8" fill="#1a2030"/>
  <text x="{width - 154}" y="38" text-anchor="middle" font-size="10" fill="#8892a6">SCORE</text>
  <text x="{width - 154}" y="59" text-anchor="middle" font-size="17" font-weight="700" fill="#f5f7ff">{state['score']}</text>
  <rect x="{width - 104}" y="20" width="84" height="48" rx="8" fill="#1a2030"/>
  <text x="{width - 62}" y="38" text-anchor="middle" font-size="10" fill="#8892a6">BEST</text>
  <text x="{width - 62}" y="59" text-anchor="middle" font-size="17" font-weight="700" fill="#FF6B6B">{state['best']}</text>
  <rect x="12" y="84" width="{width - 24}" height="{width - 24}" rx="14" fill="#141a28"/>
  {tiles}
  {over}
</svg>
"""


def key_svg(direction):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" role="img" aria-label="{direction}">
  <defs><linearGradient id="k" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#0A66C2"/><stop offset="100%" stop-color="#6E44FF"/>
  </linearGradient></defs>
  <rect x="2" y="6" width="60" height="56" rx="12" fill="#0b0f1a"/>
  <rect x="2" y="2" width="60" height="56" rx="12" fill="url(#k)"/>
  <text x="32" y="41" text-anchor="middle" font-size="30" font-weight="700" fill="#f5f7ff"
    font-family="{FONT}">{ARROWS[direction]}</text>
</svg>
"""


def key_link(direction):
    body = ("Just hit **Submit new issue** below — a bot will play your move on the shared board "
            "and close this issue in about 30 seconds.")
    url = (f"https://github.com/{REPO}/issues/new?title=2048%7C{direction}"
           f"&body={urllib.parse.quote_plus(body)}")
    return f'<a href="{url}"><img src="./assets/2048-key-{direction}.svg" width="56" alt="{direction}" /></a>'


def player_link(name):
    return f"[{name}](https://github.com/{name})" if name != "someone" else "someone"


def readme_block(state):
    recent = " · ".join(
        f"{player_link(m['player'])} {ARROWS.get(m['move'], '🎲')}" + (f" +{m['gain']}" if m["gain"] else "")
        for m in state["recent"]
    ) or "no moves yet — be the first"
    top = sorted(state["players"].items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    leaders = " · ".join(f"{player_link(p)} **{n}**" for p, n in top) or "—"
    finished = " · ".join(f"#{g['game']}: {g['score']}" for g in state["finished"]) or "none yet"
    return "\n".join([
        START,
        '<div align="center">',
        "",
        f'<img src="./assets/2048.svg?v={state["game"]}-{state["moves"]}" width="384" alt="community 2048 board" />',
        "",
        key_link("up"),
        "<br/>",
        f'{key_link("left")} {key_link("down")} {key_link("right")}',
        "",
        "**one board, everyone plays.** click an arrow → GitHub opens an issue → hit *Submit* →",
        "a bot plays your move and redraws this board in ~30s.",
        "",
        f"<sub>last moves: {recent}</sub><br/>",
        f"<sub>top players: {leaders} · {state['total_moves']} moves so far</sub><br/>",
        f"<sub>finished games: {finished}</sub>",
        "",
        "</div>",
        END,
    ])


def render(state):
    BOARD_SVG.write_text(board_svg(state), encoding="utf-8", newline="\n")
    for d in DIRS:
        (ROOT / "assets" / f"2048-key-{d}.svg").write_text(key_svg(d), encoding="utf-8", newline="\n")
    text = README.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + ".*?" + re.escape(END), re.S)
    block = readme_block(state)
    text = pattern.sub(lambda _: block, text) if pattern.search(text) else text.rstrip() + "\n\n" + block + "\n"
    README.write_text(text, encoding="utf-8", newline="\n")


def main():
    rng = random.Random()
    command = sys.argv[1] if len(sys.argv) > 1 else "render"
    if command == "new":
        state = fresh_state(rng)
    elif command == "move":
        # Both values come from the issue, so treat them as hostile input.
        move = os.environ.get("MOVE", "").split("|", 1)[-1].strip().lower()
        player = os.environ.get("PLAYER", "")
        if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", player):
            player = "someone"
        if move not in DIRS:
            sys.stdout.reconfigure(encoding="utf-8")
            print(f"I only understand `2048|up`, `2048|down`, `2048|left` or `2048|right`.")
            return
        state = load()
        reply = play(state, move, player, rng)
        save(state)
        render(state)
        sys.stdout.reconfigure(encoding="utf-8")
        print(reply)
        return
    else:
        state = load()
    save(state)
    render(state)


if __name__ == "__main__":
    main()
