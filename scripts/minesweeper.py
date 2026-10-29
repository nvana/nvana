"""Regenerate the click-to-reveal minesweeper board inside README.md.

GitHub strips JS/CSS from READMEs, but <details> still toggles on click,
so every cell is a <details> hiding its number (or a mine).

    python scripts/minesweeper.py            # board seeded by today's date
    python scripts/minesweeper.py --seed 42  # reproducible board
"""
import argparse
import datetime
import pathlib
import random
import re

ROWS, COLS, MINES = 8, 8, 10
README = pathlib.Path(__file__).resolve().parent.parent / "README.md"
START, END = "<!-- minesweeper:start -->", "<!-- minesweeper:end -->"

TILE = "⬛"
MINE = "💥"
NUMBERS = ["▫️", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"]


def build_board(rng):
    cells = [(r, c) for r in range(ROWS) for c in range(COLS)]
    mines = set(rng.sample(cells, MINES))
    board = [[0] * COLS for _ in range(ROWS)]
    for r, c in cells:
        if (r, c) in mines:
            board[r][c] = -1
            continue
        board[r][c] = sum(
            (r + dr, c + dc) in mines
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if dr or dc
        )
    return board


def render(board, seed):
    rows = []
    for row in board:
        tds = "".join(
            f"<td><details><summary>{TILE}</summary>"
            f"{MINE if v < 0 else NUMBERS[v]}</details></td>"
            for v in row
        )
        rows.append(f"<tr>{tds}</tr>")
    return "\n".join([
        START,
        '<div align="center">',
        "",
        f"**💣 readme sweeper** · {ROWS}×{COLS} · {MINES} mines · board `{seed}`",
        "",
        "<table>",
        *rows,
        "</table>",
        "",
        "<sub>click a tile to reveal it · hit 💥 and you lose · "
        "refresh the page to reset · new board every day</sub>",
        "",
        "</div>",
        END,
    ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", default=datetime.date.today().isoformat())
    seed = parser.parse_args().seed

    block = render(build_board(random.Random(seed)), seed)
    text = README.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + ".*?" + re.escape(END), re.S)
    text = pattern.sub(lambda _: block, text) if pattern.search(text) else text.rstrip() + "\n\n" + block + "\n"
    README.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
