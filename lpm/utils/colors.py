from math import sqrt

COLORS = [
    (255, 255, 255),  # 0 white
    (225, 190, 255),  # 1 light purple
    (225, 110, 255),  # 2 purple
    (230, 0, 0),  # 3 red
    (255, 80, 0),  # 4 orange
    (255, 255, 0),  # 5 yellow
    (50, 140, 0),  # 6 green
    (0, 150, 210),  # 7 light blue
    (0, 75, 180),  # 8 blue
    (0, 35, 115),  # 9 dark blue
    (128, 128, 128),  # 10 light grey
    (77, 77, 77),  # 11 dark grey
    (0, 0, 0),  # 12 black
]

HI_P = COLORS[:4]
MD_P = COLORS[4:9]
LO_P = COLORS[9:]


def match_color(rgb: list) -> tuple:
    r, g, b = rgb
    color_diffs = []
    for color in COLORS:
        cr, cg, cb = color
        color_diff = sqrt(abs(r - cr) ** 2 + abs(g - cg) ** 2 + abs(b - cb) ** 2)
        color_diffs.append((color_diff, color))
    return min(color_diffs)[1]
