#!/usr/bin/env python3
"""Generate a clean detail-rich AMP validation fixture as ASCII STL.

This fixture is intentionally a product-style ring/badge surrogate, not a
square-grid heightfield. It uses circular geometry for the base, screw holes,
bosses, and pinstripes, plus raised block-letter/detail surrogates and a hidden
backside bulk rib.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from scipy.spatial import Delaunay


Point = Tuple[float, float, float]
Point2 = Tuple[float, float]
Triangle = Tuple[Point, Point, Point]


OUTER_RADIUS = 45.0
INNER_RADIUS = 16.0
BASE_Z0 = 0.0
BASE_Z1 = 3.2
SEGMENTS = 192
SCREW_RADIUS = 3.1
SCREW_CIRCLE_RADIUS = 32.0
BOSS_RADIUS = 7.4
BOSS_Z1 = 4.3
PINSTRIPE_Z1 = 3.62
TEXT_Z1 = 3.82
BACK_RIB_Z0 = -2.4
BACK_RIB_OUTER_RADIUS = 36.5
BACK_RIB_INNER_RADIUS = 23.0


@dataclass(frozen=True)
class RectFeature:
    cx: float
    cy: float
    sx: float
    sy: float
    z0: float = BASE_Z1
    z1: float = TEXT_Z1

    def corners(self) -> Tuple[Point2, Point2, Point2, Point2]:
        x0 = self.cx - self.sx / 2
        x1 = self.cx + self.sx / 2
        y0 = self.cy - self.sy / 2
        y1 = self.cy + self.sy / 2
        return (x0, y0), (x1, y0), (x1, y1), (x0, y1)


def screw_centers() -> List[Point2]:
    return [
        (
            math.cos(math.radians(angle)) * SCREW_CIRCLE_RADIUS,
            math.sin(math.radians(angle)) * SCREW_CIRCLE_RADIUS,
        )
        for angle in (45, 135, 225, 315)
    ]


def circle_points(radius: float, segments: int = SEGMENTS, center: Point2 = (0.0, 0.0)) -> List[Point2]:
    cx, cy = center
    return [
        (
            cx + math.cos(2.0 * math.pi * i / segments) * radius,
            cy + math.sin(2.0 * math.pi * i / segments) * radius,
        )
        for i in range(segments)
    ]


def in_screw_hole(x: float, y: float) -> bool:
    return any(math.hypot(x - cx, y - cy) < SCREW_RADIUS for cx, cy in screw_centers())


def in_base_footprint(x: float, y: float) -> bool:
    r = math.hypot(x, y)
    return INNER_RADIUS <= r <= OUTER_RADIUS and not in_screw_hole(x, y)


def cross_normal(a: Point, b: Point, c: Point) -> Point:
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length == 0:
        return (0.0, 0.0, 0.0)
    return (nx / length, ny / length, nz / length)


def add_tri(tris: List[Triangle], a: Point, b: Point, c: Point) -> None:
    tris.append((a, b, c))


def add_quad(tris: List[Triangle], a: Point, b: Point, c: Point, d: Point, flip: bool = False) -> None:
    if flip:
        add_tri(tris, a, d, c)
        add_tri(tris, a, c, b)
    else:
        add_tri(tris, a, b, c)
        add_tri(tris, a, c, d)


def add_vertical_circle_wall(
    tris: List[Triangle],
    points: Sequence[Point2],
    z0: float,
    z1: float,
    flip: bool = False,
) -> None:
    for i, p0 in enumerate(points):
        p1 = points[(i + 1) % len(points)]
        add_quad(
            tris,
            (p0[0], p0[1], z0),
            (p1[0], p1[1], z0),
            (p1[0], p1[1], z1),
            (p0[0], p0[1], z1),
            flip=flip,
        )


def add_annular_cylinder(
    tris: List[Triangle],
    inner_radius: float,
    outer_radius: float,
    z0: float,
    z1: float,
    center: Point2 = (0.0, 0.0),
    segments: int = SEGMENTS,
    start_deg: float = 0.0,
    end_deg: float = 360.0,
) -> None:
    full = abs((end_deg - start_deg) % 360.0) < 1e-6
    count = segments if full else max(8, int(segments * abs(end_deg - start_deg) / 360.0))
    angles = [math.radians(start_deg + (end_deg - start_deg) * i / count) for i in range(count + (0 if full else 1))]
    if full:
        angles = [2.0 * math.pi * i / segments for i in range(segments)]

    cx, cy = center
    outer = [(cx + math.cos(a) * outer_radius, cy + math.sin(a) * outer_radius) for a in angles]
    inner = [(cx + math.cos(a) * inner_radius, cy + math.sin(a) * inner_radius) for a in angles]
    n = len(outer)
    last = n if not full else n + 1
    for i in range(last - 1):
        j = (i + 1) % n
        o0, o1 = outer[i], outer[j]
        i0, i1 = inner[i], inner[j]
        add_quad(tris, (o0[0], o0[1], z1), (o1[0], o1[1], z1), (i1[0], i1[1], z1), (i0[0], i0[1], z1))
        add_quad(tris, (o0[0], o0[1], z0), (i0[0], i0[1], z0), (i1[0], i1[1], z0), (o1[0], o1[1], z0))
        add_quad(tris, (o0[0], o0[1], z0), (o1[0], o1[1], z0), (o1[0], o1[1], z1), (o0[0], o0[1], z1))
        add_quad(tris, (i0[0], i0[1], z0), (i0[0], i0[1], z1), (i1[0], i1[1], z1), (i1[0], i1[1], z0))

    if not full:
        for idx in (0, n - 1):
            o, inn = outer[idx], inner[idx]
            add_quad(tris, (inn[0], inn[1], z0), (o[0], o[1], z0), (o[0], o[1], z1), (inn[0], inn[1], z1))


def block_letter_features() -> List[RectFeature]:
    # Raised "OHMIC" surrogate placed on the upper annulus, sized for a 0.4 nozzle.
    rects: List[RectFeature] = []
    y = 28.5
    base_x = -20.0
    spacing = 8.0

    def add_o(cx: float) -> None:
        rects.extend([
            RectFeature(cx - 2.0, y, 1.1, 5.8),
            RectFeature(cx + 2.0, y, 1.1, 5.8),
            RectFeature(cx, y - 2.35, 4.8, 1.1),
            RectFeature(cx, y + 2.35, 4.8, 1.1),
        ])

    def add_h(cx: float) -> None:
        rects.extend([
            RectFeature(cx - 2.0, y, 1.1, 5.8),
            RectFeature(cx + 2.0, y, 1.1, 5.8),
            RectFeature(cx, y, 4.8, 1.1),
        ])

    def add_m(cx: float) -> None:
        rects.extend([
            RectFeature(cx - 2.4, y, 1.0, 5.8),
            RectFeature(cx + 2.4, y, 1.0, 5.8),
            RectFeature(cx - 0.8, y + 0.8, 1.0, 4.2),
            RectFeature(cx + 0.8, y + 0.8, 1.0, 4.2),
        ])

    def add_i(cx: float) -> None:
        rects.extend([
            RectFeature(cx, y, 1.1, 5.8),
            RectFeature(cx, y + 2.8, 3.7, 0.8),
            RectFeature(cx, y - 2.8, 3.7, 0.8),
        ])

    def add_c(cx: float) -> None:
        rects.extend([
            RectFeature(cx - 2.0, y, 1.1, 5.8),
            RectFeature(cx, y - 2.35, 4.8, 1.1),
            RectFeature(cx, y + 2.35, 4.8, 1.1),
        ])

    add_o(base_x)
    add_h(base_x + spacing)
    add_m(base_x + spacing * 2)
    add_i(base_x + spacing * 3)
    add_c(base_x + spacing * 4)

    # Lower detail bars / pinstripe surrogate.
    for idx in range(7):
        rects.append(RectFeature(-18.0 + idx * 6.0, -28.5, 3.6, 0.9, BASE_Z1, 3.7))
    return rects


def add_box(tris: List[Triangle], feature: RectFeature) -> None:
    (x0, y0), (x1, _), (_, y1), _ = feature.corners()
    z0, z1 = feature.z0, feature.z1
    p000 = (x0, y0, z0)
    p100 = (x1, y0, z0)
    p110 = (x1, y1, z0)
    p010 = (x0, y1, z0)
    p001 = (x0, y0, z1)
    p101 = (x1, y0, z1)
    p111 = (x1, y1, z1)
    p011 = (x0, y1, z1)
    add_quad(tris, p001, p101, p111, p011)
    add_quad(tris, p000, p010, p110, p100)
    add_quad(tris, p000, p100, p101, p001)
    add_quad(tris, p100, p110, p111, p101)
    add_quad(tris, p110, p010, p011, p111)
    add_quad(tris, p010, p000, p001, p011)


def triangulated_base(tris: List[Triangle]) -> None:
    points: List[Point2] = []
    points.extend(circle_points(OUTER_RADIUS))
    points.extend(circle_points(INNER_RADIUS))
    for center in screw_centers():
        points.extend(circle_points(SCREW_RADIUS, segments=80, center=center))
    for radius in (20.0, 26.0, 32.0, 38.0, 42.0):
        for point in circle_points(radius, segments=SEGMENTS):
            if in_base_footprint(point[0], point[1]):
                points.append(point)

    # Deduplicate rounded points before triangulation.
    seen = set()
    unique: List[Point2] = []
    for x, y in points:
        key = (round(x, 5), round(y, 5))
        if key not in seen:
            seen.add(key)
            unique.append((x, y))

    tri = Delaunay(unique)
    for simplex in tri.simplices:
        coords = [unique[int(idx)] for idx in simplex]
        cx = sum(p[0] for p in coords) / 3.0
        cy = sum(p[1] for p in coords) / 3.0
        if not in_base_footprint(cx, cy):
            continue
        a2, b2, c2 = coords
        add_tri(tris, (a2[0], a2[1], BASE_Z1), (b2[0], b2[1], BASE_Z1), (c2[0], c2[1], BASE_Z1))
        add_tri(tris, (a2[0], a2[1], BASE_Z0), (c2[0], c2[1], BASE_Z0), (b2[0], b2[1], BASE_Z0))

    add_vertical_circle_wall(tris, circle_points(OUTER_RADIUS), BASE_Z0, BASE_Z1)
    add_vertical_circle_wall(tris, circle_points(INNER_RADIUS), BASE_Z0, BASE_Z1, flip=True)
    for center in screw_centers():
        add_vertical_circle_wall(tris, circle_points(SCREW_RADIUS, segments=80, center=center), BASE_Z0, BASE_Z1, flip=True)


def build_mesh() -> List[Triangle]:
    tris: List[Triangle] = []
    triangulated_base(tris)

    # Clean raised boss rings around screw holes.
    for center in screw_centers():
        add_annular_cylinder(tris, SCREW_RADIUS + 0.35, BOSS_RADIUS, BASE_Z1, BOSS_Z1, center=center, segments=96)

    # Raised pinstripe rings, thin enough to exercise visible detail.
    add_annular_cylinder(tris, 23.6, 24.4, BASE_Z1, PINSTRIPE_Z1, segments=SEGMENTS)
    add_annular_cylinder(tris, 38.6, 39.4, BASE_Z1, PINSTRIPE_Z1, segments=SEGMENTS)

    # Hidden backside rib on lower half of the fixture.
    add_annular_cylinder(
        tris,
        BACK_RIB_INNER_RADIUS,
        BACK_RIB_OUTER_RADIUS,
        BACK_RIB_Z0,
        BASE_Z0,
        segments=SEGMENTS,
        start_deg=205.0,
        end_deg=335.0,
    )

    for feature in block_letter_features():
        add_box(tris, feature)

    return tris


def write_ascii_stl(tris: Iterable[Triangle], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("solid amp_detail_ring_fixture\n")
        for a, b, c in tris:
            nx, ny, nz = cross_normal(a, b, c)
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
    args = parser.parse_args()
    tris = build_mesh()
    write_ascii_stl(tris, Path(args.out))
    print(f"wrote {args.out} with {len(tris)} triangles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
