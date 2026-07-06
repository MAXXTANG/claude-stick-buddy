#!/usr/bin/env python3
"""Build the Clawd mascot animation set and emit src/character_gif.h.

Art lives on a 27-col logical grid at SCALE px per cell (~60% of the
135px panel width), bottom-center-anchored on a 135x135 canvas. Rows
0-7 are the icon zone (heart / lightbulb), body rows 8-21 (flat bottom
edge), short legs rows 22-25.

Animations (firmware picks one at weighted random every loop):
  idle  - blink + wander left/right
  heart - heart pops up beside the hand
  bulb  - lightbulb blinks above the head
  dizzy - spiral eyes + wobble

Usage: python tools/make_clawd_gif.py   (writes src/character_gif.h and
       assets/clawd-*.gif for previewing)
"""
import io
import os
from PIL import Image

CANVAS = 135
GRID_W = 27
GRID_H = 26          # 0-7 icon zone, 8-21 body, 22-25 legs
SCALE = 3            # 27*3 = 81 px wide ~= 60% of panel width

COLORS = {
    'B': (0xCC, 0x78, 0x5C),   # body — Anthropic book-cloth rust
    'K': (10, 10, 10),         # eyes
    'H': (0xD9, 0x53, 0x4F),   # heart
    'Y': (0xE8, 0xC3, 0x6A),   # bulb glass
    'G': (0x9A, 0x9A, 0x9A),   # bulb base
}
BG = (0, 0, 0)

OUT_DIR = os.path.join(os.path.dirname(__file__), '..')


def blank():
    return [['.'] * GRID_W for _ in range(GRID_H)]


def fill(g, c0, r0, c1, r1, ch='B'):
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            g[r][c] = ch


def stamp(g, art, r0, c0, ch_map=None):
    for dr, row in enumerate(art):
        for dc, ch in enumerate(row):
            if ch != '.':
                g[r0 + dr][c0 + dc] = ch


def base_body():
    g = blank()
    fill(g, 4, 8, 22, 21)            # body block, flat bottom edge (row 21)
    fill(g, 1, 12, 3, 15)            # left nub (hand)
    fill(g, 23, 12, 25, 15)          # right nub
    # short legs hang straight off the flat bottom: two pairs w/ slits
    for c0, c1 in ((5, 6), (8, 9), (17, 18), (20, 21)):
        fill(g, c0, 22, c1, 25)
    return g


def eyes_open(g):
    fill(g, 8, 11, 9, 12, 'K')
    fill(g, 17, 11, 18, 12, 'K')


def eyes_squint(g):
    for (r, c) in ((11, 7), (11, 8), (12, 9), (12, 10), (13, 7), (13, 8)):
        g[r][c] = 'K'
    for (r, c) in ((11, 18), (11, 19), (12, 15), (12, 16), (13, 18), (13, 19)):
        g[r][c] = 'K'


SPIRAL = [
    'KKKKK',
    '....K',
    '.KK.K',
    '.K..K',
    '.KKKK',
]

HEART = [
    '.HH.HH.',
    'HHHHHHH',
    'HHHHHHH',
    '.HHHHH.',
    '..HHH..',
    '...H...',
]

BULB = [
    '..YYY..',
    '.YYYYY.',
    'YYYYYYY',
    'YYYYYYY',
    '.YYYYY.',
    '..YYY..',
    '..GGG..',
    '..GGG..',
]


def make_stand():
    g = base_body(); eyes_open(g); return g


def make_squint():
    g = base_body(); eyes_squint(g); return g


def make_dizzy():
    g = base_body()
    stamp(g, SPIRAL, 9, 6)
    stamp(g, SPIRAL, 9, 16)
    return g


def make_heart(lift=0):
    g = make_stand()
    stamp(g, HEART, 1 - lift, 2)     # floats above the left hand
    return g


def make_bulb():
    g = make_stand()
    stamp(g, BULB, 0, 10)            # above the head, centered
    return g


def render(g, dx=0, dy=0):
    im = Image.new('RGB', (CANVAS, CANVAS), BG)
    px = im.load()
    x_off = (CANVAS - GRID_W * SCALE) // 2 + dx
    y_off = CANVAS - GRID_H * SCALE + dy
    for r in range(GRID_H):
        for c in range(GRID_W):
            ch = g[r][c]
            if ch == '.':
                continue
            col = COLORS[ch]
            for yy in range(SCALE):
                for xx in range(SCALE):
                    y = y_off + r * SCALE + yy
                    x = x_off + c * SCALE + xx
                    if 0 <= y < CANVAS and 0 <= x < CANVAS:
                        px[x, y] = col
    return im


def encode(frames):
    """(image, duration_ms) list -> GIF bytes with one shared palette."""
    imgs = [f for f, _ in frames]
    durs = [d for _, d in frames]
    composite = Image.new('RGB', (CANVAS, CANVAS * len(imgs)))
    for i, f in enumerate(imgs):
        composite.paste(f, (0, i * CANVAS))
    master = composite.quantize(colors=64, method=Image.Quantize.MEDIANCUT)
    q = [f.quantize(palette=master, dither=Image.Dither.NONE) for f in imgs]
    buf = io.BytesIO()
    q[0].save(buf, format='GIF', save_all=True, append_images=q[1:],
              duration=durs, loop=0, optimize=False, disposal=2)
    return buf.getvalue()


def animations():
    stand, squint, dizzy = make_stand(), make_squint(), make_dizzy()
    idle = [
        (render(stand, 0), 800), (render(squint, 0), 150), (render(stand, 0), 600),
        (render(stand, 3), 180), (render(stand, 6), 180), (render(stand, 9), 180),
        (render(stand, 9), 500), (render(squint, 9), 150), (render(stand, 9), 400),
        (render(stand, 6), 180), (render(stand, 3), 180), (render(stand, 0), 180),
        (render(stand, -3), 180), (render(stand, -6), 180), (render(stand, -6), 500),
        (render(stand, -3), 180), (render(stand, 0), 400),
    ]
    heart = [
        (render(stand, 0), 400),
        (render(make_heart(0), 0), 450), (render(make_heart(1), 0), 400),
        (render(make_heart(0), 0), 450), (render(make_heart(1), 0), 400),
        (render(stand, 0), 300),
    ]
    bulb = [
        (render(stand, 0), 400),
        (render(make_bulb(), 0), 500), (render(stand, 0), 220),
        (render(make_bulb(), 0), 800),
        (render(stand, 0), 300),
    ]
    dizzy_anim = [
        (render(dizzy, 0), 300), (render(dizzy, 2), 300), (render(dizzy, -2), 300),
        (render(dizzy, 2), 300), (render(dizzy, -2), 300), (render(dizzy, 0), 300),
        (render(stand, 0), 400),
    ]
    # (name, frames, weight) — idle dominates; specials sprinkle in.
    return [
        ('idle',  idle,       5),
        ('heart', heart,      1),
        ('bulb',  bulb,       1),
        ('dizzy', dizzy_anim, 1),
    ]


def main():
    anims = [(name, encode(frames), w) for name, frames, w in animations()]

    # Preview GIFs for humans.
    for name, data, _ in anims:
        with open(os.path.join(OUT_DIR, 'assets', f'clawd-{name}.gif'), 'wb') as f:
            f.write(data)

    out_path = os.path.join(OUT_DIR, 'src', 'character_gif.h')
    with open(out_path, 'w') as out:
        out.write('// Auto-generated by tools/make_clawd_gif.py — do not edit.\n')
        out.write('// Clawd animation set: firmware picks one at weighted random\n')
        out.write('// each time a loop finishes (see startGifPlayback).\n')
        out.write('#pragma once\n#include <stdint.h>\n#include <stddef.h>\n\n')
        out.write(f'static constexpr uint16_t CHAR_W = {CANVAS};\n')
        out.write(f'static constexpr uint16_t CHAR_H = {CANVAS};\n\n')
        for name, data, _ in anims:
            out.write(f'static const uint8_t char_gif_{name}[{len(data)}] = {{\n')
            for i in range(0, len(data), 16):
                chunk = data[i:i + 16]
                out.write('  ' + ','.join(f'0x{b:02x}' for b in chunk) + ',\n')
            out.write('};\n\n')
        out.write('struct CharGif { const uint8_t* data; size_t len; uint8_t weight; };\n')
        out.write('static const CharGif CHAR_GIFS[] = {\n')
        for name, data, w in anims:
            out.write(f'  {{ char_gif_{name}, sizeof(char_gif_{name}), {w} }},\n')
        out.write('};\n')
        out.write(f'static constexpr size_t CHAR_GIF_COUNT = {len(anims)};\n')
        out.write('// Legacy flag: non-zero means character art is present.\n')
        out.write('static constexpr size_t CHAR_GIF_LEN = sizeof(char_gif_idle);\n')
    total = sum(len(d) for _, d, _ in anims)
    print(f'wrote {out_path} ({len(anims)} animations, {total} bytes total)')


if __name__ == '__main__':
    main()
