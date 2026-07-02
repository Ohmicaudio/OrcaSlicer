#!/usr/bin/env python3
"""Generate a detail-rich AMP validation fixture as ASCII STL.

The fixture is intentionally more useful than a plain ring. It includes a
cosmetic face, raised text/logo surrogates, pinstripe grooves, mounting holes,
boss/counterbore features, a chamfer-like face slope, and enough backside bulk
to make width-only internal planning worth measuring.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Sequence, Tuple


Point = Tuple[float, float, float]
Triangle = Tuple[Point, Point, Point]


@dataclass(frozen=True)
class RectFeature:
    cx: float
    cy: float
    sx: float
    sy: float

    def contains(self, x: float, y: float) -> bool:
        return abs(x - self.cx) <= self.sx / 2 and abs(y - self.cy) <= self.sy / 2


OUTER_RADIUS = 45.0
INNER_RADIUS = 17.0
BASE_THICKNESS = 3.2
BACKSIDE_BULK_EXTRA = 2.8
FACE_DETAIL_EXTRA = 0.55
GROOVE_DEPTH = 0.45
GRID_STEP = 1.0
SCREW_RADIUS = 3.1
SCREW_CIRCLE_RADIUS = 32.5
BOSS_OUTER_RADIUS = 7.0


def length(v: Point) -> float:
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def normal(a: Point, b: Point, c: Point) -> Point:
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    nlen = length((nx, ny, nz))
    if nlen == 0:
        return (0.0, 0.0, 0.0)
    return (nx / nlen, ny / nlen, nz / nlen)


def screw_centers() -> List[Tuple[float, float]]:
    return [
        (
            math.cos(math.radians(angle)) * SCREW_CIRCLE_RADIUS,
            math.sin(math.radians(angle)) * SCREW_CIRCLE_RADIUS,
        )
        for angle in (45, 135, 225, 315)
    ]


def in_screw_hole(x: float, y: float) -> bool:
    return any(math.hypot(x - cx, y - cy) < SCREW_RADIUS for cx, cy in screw_centers())


def in_footprint(x: float, y: float) -> bool:
    r = math.hypot(x, y)
    return INNER_RADIUS <= r <= OUTER_RADIUS and not in_screw_hole(x, y)


def in_boss(x: float, y: float) -> bool:
    return any(
        SCREW_RADIUS + 0.8 <= math.hypot(x - cx, y - cy) <= BOSS_OUTER_RADIUS
        for cx, cy in screw_centers()
    )


def in_pinstripe_groove(x: float, y: float) -> bool:
    r = math.hypot(x, y)
    return any(abs(r - target) < 0.45 for target in (24.0, 39.0))


def text_surrogate_rects() -> Sequence[RectFeature]:
    # Raised bar-letter surrogate for "OHMIC" without requiring font/boolean deps.
    rects: List[RectFeature] = []
    base_x = -22.0
    y = 6.5
    spacing = 9.0

    def add_letter_o(cx: float) -> None:
        rects.extend(
            [
                RectFeature(cx - 2.4, y, 1.2, 7.0),
                RectFeature(cx + 2.4, y, 1.2, 7.0),
                RectFeature(cx, y - 2.9, 5.8, 1.2),
                RectFeature(cx, y + 2.9, 5.8, 1.2),
            ]
        )

    def add_letter_h(cx: float) -> None:
        rects.extend(
            [
                RectFeature(cx - 2.4, y, 1.2, 7.0),
                RectFeature(cx + 2.4, y, 1.2, 7.0),
                RectFeature(cx, y, 5.8, 1.2),
            ]
        )

    def add_letter_m(cx: float) -> None:
        rects.extend(
            [
                RectFeature(cx - 3.0, y, 1.0, 7.0),
                RectFeature(cx + 3.0, y, 1.0, 7.0),
                RectFeature(cx - 1.0, y + 1.0, 1.0, 5.0),
                RectFeature(cx + 1.0, y + 1.0, 1.0, 5.0),
            ]
        )

    def add_letter_i(cx: float) -> None:
        rects.extend(
            [
                RectFeature(cx, y, 1.2, 7.0),
                RectFeature(cx, y + 3.6, 4.0, 1.0),
                RectFeature(cx, y - 3.6, 4.0, 1.0),
            ]
        )

    def add_letter_c(cx: float) -> None:
        rects.extend(
            [
                RectFeature(cx - 2.4, y, 1.2, 7.0),
                RectFeature(cx, y - 2.9, 5.8, 1.2),
                RectFeature(cx, y + 2.9, 5.8, 1.2),
            ]
        )

    add_letter_o(base_x)
    add_letter_h(base_x + spacing)
    add_letter_m(base_x + spacing * 2)
    add_letter_i(base_x + spacing * 3)
    add_letter_c(base_x + spacing * 4)

    # Small lower detail bars, like a logo underline / calibration text surrogate.
    for idx in range(7):
        rects.append(RectFeature(-18.0 + idx * 6.0, -10.0, 3.4, 0.85))
    return rects


TEXT_RECTS = text_surrogate_rects()


def in_text_surrogate(x: float, y: float) -> bool:
    return any(rect.contains(x, y) for rect in TEXT_RECTS)


def top_z(x: float, y: float) -> float:
    r = math.hypot(x, y)
    z = BASE_THICKNESS

    # Cosmetic face slope/chamfer proxy.
    if r > OUTER_RADIUS - 5.0:
        z -= (r - (OUTER_RADIUS - 5.0)) * 0.12
    if r < INNER_RADIUS + 5.0:
        z -= ((INNER_RADIUS + 5.0) - r) * 0.10

    if in_boss(x, y):
        z += 0.9
    if in_pinstripe_groove(x, y):
        z -= GROOVE_DEPTH
    if in_text_surrogate(x, y):
        z += FACE_DETAIL_EXTRA

    return max(1.4, z)


def bottom_z(x: float, y: float) -> float:
    r = math.hypot(x, y)
    # Hidden backside bulk rib on the rear half of the ring.
    if 22.0 <= r <= 36.0 and y < 0:
        return -BACKSIDE_BULK_EXTRA
    return 0.0


def add_quad(tris: List[Triangle], p00: Point, p10: Point, p11: Point, p01: Point, flip: bool = False) -> None:
    if flip:
        tris.append((p00, p01, p11))
        tris.append((p00, p11, p10))
    else:
        tris.append((p00, p10, p11))
        tris.append((p00, p11, p01))


def cell_vertices(x: float, y: float, zfunc: Callable[[float, float], float], step: float) -> Tuple[Point, Point, Point, Point]:
    return (
        (x, y, zfunc(x, y)),
        (x + step, y, zfunc(x + step, y)),
        (x + step, y + step, zfunc(x + step, y + step)),
        (x, y + step, zfunc(x, y + step)),
    )


def build_mesh(step: float) -> List[Triangle]:
    tris: List[Triangle] = []
    cells = set()
    min_i = math.floor(-OUTER_RADIUS / step)
    max_i = math.ceil(OUTER_RADIUS / step)
    for i in range(min_i, max_i):
        for j in range(min_i, max_i):
            cx = (i + 0.5) * step
            cy = (j + 0.5) * step
            if in_footprint(cx, cy):
                cells.add((i, j))

    for i, j in sorted(cells):
        x = i * step
        y = j * step
        top = cell_vertices(x, y, top_z, step)
        bottom = cell_vertices(x, y, bottom_z, step)
        add_quad(tris, *top)
        add_quad(tris, bottom[0], bottom[1], bottom[2], bottom[3], flip=True)

        # Boundary side walls.
        neighbor_edges = [
            ((i, j - 1), top[0], top[1], bottom[1], bottom[0]),
            ((i + 1, j), top[1], top[2], bottom[2], bottom[1]),
            ((i, j + 1), top[2], top[3], bottom[3], bottom[2]),
            ((i - 1, j), top[3], top[0], bottom[0], bottom[3]),
        ]
        for neighbor, a, b, c, d in neighbor_edges:
            if neighbor not in cells:
                add_quad(tris, a, b, c, d)

    return tris


def write_ascii_stl(tris: Iterable[Triangle], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("solid amp_detail_ring_fixture\n")
        for a, b, c in tris:
            nx, ny, nz = normal(a, b, c)
            fh.write(f"  facet normal {nx:.6g} {ny:.6g} {nz:.6g}\n")
            fh.write("    outer loop\n")
            for vx, vy, vz in (a, b, c):
                fh.write(f"      vertex {vx:.6g} {vy:.6g} {vz:.6g}\n")
            fh.write("    endloop\n")
            fh.write("  endfacet\n")
        fh.write("endsolid amp_detail_ring_fixture\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default="outputs/amp_detail_fixture/models/amp_detail_ring_fixture.stl",
        help="Output STL path",
    )
    parser.add_argument("--step", type=float, default=GRID_STEP, help="Grid step in mm")
    args = parser.parse_args()

    tris = build_mesh(args.step)
    out = Path(args.out)
    write_ascii_stl(tris, out)
    print(f"wrote {out} with {len(tris)} triangles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
