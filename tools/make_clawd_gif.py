#!/usr/bin/env python3
"""Rebuild the Clawd pixel mascot from the reference stickers and emit an
animated blink-loop GIF (idle: open eyes -> subtle bob -> squint)."""
from PIL import Image

GRID = 27          # logical pixels per side
SCALE = 5          # 27*5 = 135 = panel width
BODY = (0xCC, 0x78, 0x5C)   # Anthropic book-cloth rust
EYE = (10, 10, 10)
BG = (0, 0, 0)


def blank():
    return [['.'] * GRID for _ in range(GRID)]


def fill(g, c0, r0, c1, r1, ch='B'):
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            g[r][c] = ch


def base_body():
    g = blank()
    fill(g, 4, 2, 22, 18)            # main body block
    fill(g, 1, 7, 3, 10)             # left nub
    fill(g, 23, 7, 25, 10)           # right nub
    # legs rows 19-20: full bridge except the two slits
    fill(g, 5, 19, 21, 20)
    for r in (19, 20):
        g[r][7] = '.'
        g[r][19] = '.'
    # rows 21-25: four legs (center arch open)
    for c0, c1 in ((5, 6), (8, 9), (17, 18), (20, 21)):
        fill(g, c0, 21, c1, 25)
    return g


def eyes_open(g):
    fill(g, 8, 6, 9, 7, 'K')
    fill(g, 17, 6, 18, 7, 'K')


def eyes_squint(g):
    # '>'  (left)          '<'  (right)
    for (r, c) in ((6, 7), (6, 8), (7, 9), (7, 10), (8, 7), (8, 8)):
        g[r][c] = 'K'
    for (r, c) in ((6, 18), (6, 19), (7, 15), (7, 16), (8, 18), (8, 19)):
        g[r][c] = 'K'


def render(g, dy=0):
    im = Image.new('RGB', (GRID * SCALE, GRID * SCALE), BG)
    px = im.load()
    y_anchor = (GRID * SCALE) - (GRID * SCALE)  # grid already full-height
    for r in range(GRID):
        for c in range(GRID):
            ch = g[r][c]
            if ch == '.':
                continue
            col = BODY if ch == 'B' else EYE
            for yy in range(SCALE):
                for xx in range(SCALE):
                    y = r * SCALE + yy + dy
                    x = c * SCALE + xx
                    if 0 <= y < GRID * SCALE:
                        px[x, y] = col
    return im


def main():
    g_open = base_body(); eyes_open(g_open)
    g_squint = base_body(); eyes_squint(g_squint)

    frames = [
        (render(g_open, 0), 900),    # eyes open
        (render(g_open, SCALE // 2), 900),  # subtle bob (2px down)
        (render(g_open, 0), 700),
        (render(g_squint, 0), 180),  # blink >_<
    ]
    imgs = [f for f, _ in frames]
    durs = [d for _, d in frames]
    out = '/Users/thomastang/claude-stick-buddy/firmware/assets/clawd-blink.gif'
    imgs[0].save(out, save_all=True, append_images=imgs[1:],
                 duration=durs, loop=0, disposal=2, optimize=False)
    print('wrote', out)


if __name__ == '__main__':
    main()
