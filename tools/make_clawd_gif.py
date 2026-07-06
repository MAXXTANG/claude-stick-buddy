#!/usr/bin/env python3
"""Rebuild the Clawd pixel mascot from the reference stickers and emit an
animated blink-loop GIF (idle: open eyes -> subtle bob -> squint).

The art is drawn on a 27x19 logical grid (squat proportions, like the
stickers) at SCALE px per cell, then bottom-center-anchored on a 135x135
canvas — the size tickGifPlayback paints at the bottom of the screen."""
from PIL import Image

CANVAS = 135        # GIF frame size expected by encode_gif.py / firmware
GRID_W = 27
GRID_H = 19
SCALE = 3           # 27*3 = 81 px wide ~= 60% of the panel width
BODY = (0xCC, 0x78, 0x5C)   # Anthropic book-cloth rust
EYE = (10, 10, 10)
BG = (0, 0, 0)


def blank():
    return [['.'] * GRID_W for _ in range(GRID_H)]


def fill(g, c0, r0, c1, r1, ch='B'):
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            g[r][c] = ch


def base_body():
    g = blank()
    fill(g, 4, 0, 22, 12)            # main body block (squat)
    fill(g, 1, 4, 3, 7)              # left nub
    fill(g, 23, 4, 25, 7)            # right nub
    # leg bridge rows 13-14: full width except the two slits
    fill(g, 5, 13, 21, 14)
    for r in (13, 14):
        g[r][7] = '.'
        g[r][19] = '.'
    # rows 15-18: four legs (center arch open)
    for c0, c1 in ((5, 6), (8, 9), (17, 18), (20, 21)):
        fill(g, c0, 15, c1, 18)
    return g


def eyes_open(g):
    fill(g, 8, 3, 9, 4, 'K')
    fill(g, 17, 3, 18, 4, 'K')


def eyes_squint(g):
    # '>'  (left)          '<'  (right)
    for (r, c) in ((3, 7), (3, 8), (4, 9), (4, 10), (5, 7), (5, 8)):
        g[r][c] = 'K'
    for (r, c) in ((3, 18), (3, 19), (4, 15), (4, 16), (5, 18), (5, 19)):
        g[r][c] = 'K'


def render(g, dy=0):
    im = Image.new('RGB', (CANVAS, CANVAS), BG)
    px = im.load()
    x_off = (CANVAS - GRID_W * SCALE) // 2          # centered
    y_off = CANVAS - GRID_H * SCALE                 # bottom-anchored
    for r in range(GRID_H):
        for c in range(GRID_W):
            ch = g[r][c]
            if ch == '.':
                continue
            col = BODY if ch == 'B' else EYE
            for yy in range(SCALE):
                for xx in range(SCALE):
                    y = y_off + r * SCALE + yy + dy
                    x = x_off + c * SCALE + xx
                    if 0 <= y < CANVAS:
                        px[x, y] = col
    return im


def main():
    g_open = base_body(); eyes_open(g_open)
    g_squint = base_body(); eyes_squint(g_squint)

    frames = [
        (render(g_open, 0), 900),        # eyes open
        (render(g_open, -2), 900),       # subtle bob (2px up)
        (render(g_open, 0), 700),
        (render(g_squint, 0), 180),      # blink >_<
    ]
    imgs = [f for f, _ in frames]
    durs = [d for _, d in frames]
    out = '/Users/thomastang/claude-stick-buddy/firmware/assets/clawd-blink.gif'
    imgs[0].save(out, save_all=True, append_images=imgs[1:],
                 duration=durs, loop=0, disposal=2, optimize=False)
    print('wrote', out)


if __name__ == '__main__':
    main()
