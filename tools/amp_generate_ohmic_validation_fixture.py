#!/usr/bin/env python3
"""Generate an Ohmic-style AMP product validation fixture as ASCII STL.

The fixture is a practical speaker/LED ring surrogate. It contains visible
cosmetic detail that should be preserved plus hidden/internal bulk where the
Stage 1 width-only candidate might help. The text/logo is represented with
geometric bar surrogates so the generator has no font or boolean dependency.

The default mode targets a 0.6 mm nozzle proxy pass. Detail features include
safe, borderline, and stress-only sizes so later passes can be regenerated for
0.4 mm and 0.2 mm nozzles without changing the overall fixture.
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


OUTER_RADIUS = 54.0
INNER_RADIUS = 20.0
BASE_Z0 = 0.0
BASE_Z1 = 3.0
SEGMENTS = 224
SCREW_RADIUS = 3.0
SCREW_CIRCLE_RADIUS = 39.0
BOSS_RADIUS = 8.5
BOSS_Z1 = 4.25
DETAIL_Z1 = 3.75
PINSTRIPE_Z1 = 3.45
LED_RAIL_Z1 = 3.6
BACK_RIB_Z0 = -2.2
BACK_RIB_OUTER_RADIUS = 45.0
BACK_RIB_INNER_RADIUS = 25.0
DEFAULT_NOZZLE_DIAMETER = 0.6


@dataclass(frozen=True)
class RectFeature:
    cx: float
    cy: float
    sx: float
    sy: float
    z0: float = BASE_Z1
    z1: float = DETAIL_Z1

    def corners(self) -> Tuple[Point2, Point2, Point2, Point2]:
        x0 = self.cx - self.sx / 2.0
        x1 = self.cx + self.sx / 2.0
        y0 = self.cy - self.sy / 2.0
        y1 = self.cy + self.sy / 2.0
        return (x0, y0), (x1, y0), (x1, y1), (x0, y1)


def screw_centers() -> List[Point2]:
    # Slightly product-like asymmetric clocking keeps the fixture from being a
    # pure synthetic ring while still being easy to inspect.
    return [
        (
            math.cos(math.radians(angle)) * SCREW_CIRCLE_RADIUS,
            math.sin(math.radians(angle)) * SCREW_CIRCLE_RADIUS,
        )
        for angle in (38, 142, 218, 322)
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
    if full:
        angles = [2.0 * math.pi * i / segments for i in range(segments)]
    else:
        angles = [math.radians(start_deg + (end_deg - start_deg) * i / count) for i in range(count + 1)]

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


def add_side_patch(
    tris: List[Triangle],
    start_deg: float,
    end_deg: float,
    z0: float,
    z1: float,
    depth: float,
    segments: int = 12,
) -> None:
    """Add a curved raised side-wall patch on the outside diameter."""
    count = max(2, segments)
    angles = [math.radians(start_deg + (end_deg - start_deg) * i / count) for i in range(count + 1)]
    inner_radius = OUTER_RADIUS
    outer_radius = OUTER_RADIUS + depth

    inner = [(math.cos(a) * inner_radius, math.sin(a) * inner_radius) for a in angles]
    outer = [(math.cos(a) * outer_radius, math.sin(a) * outer_radius) for a in angles]
    for i in range(count):
        j = i + 1
        i0, i1 = inner[i], inner[j]
        o0, o1 = outer[i], outer[j]
        add_quad(tris, (o0[0], o0[1], z0), (o1[0], o1[1], z0), (o1[0], o1[1], z1), (o0[0], o0[1], z1))
        add_quad(tris, (i0[0], i0[1], z0), (o0[0], o0[1], z0), (o1[0], o1[1], z0), (i1[0], i1[1], z0))
        add_quad(tris, (i0[0], i0[1], z1), (i1[0], i1[1], z1), (o1[0], o1[1], z1), (o0[0], o0[1], z1))

    for idx in (0, count):
        i_pt = inner[idx]
        o_pt = outer[idx]
        add_quad(tris, (i_pt[0], i_pt[1], z0), (o_pt[0], o_pt[1], z0), (o_pt[0], o_pt[1], z1), (i_pt[0], i_pt[1], z1))


def side_mm_to_deg(width_mm: float, radius: float = OUTER_RADIUS) -> float:
    return math.degrees(width_mm / radius)


def add_side_rect(
    tris: List[Triangle],
    center_deg: float,
    center_z: float,
    width_mm: float,
    height_mm: float,
    depth: float,
    segments: int = 4,
) -> None:
    half_angle = side_mm_to_deg(width_mm) / 2.0
    add_side_patch(
        tris,
        center_deg - half_angle,
        center_deg + half_angle,
        center_z - height_mm / 2.0,
        center_z + height_mm / 2.0,
        depth,
        segments=segments,
    )


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


def logo_surrogate_features(nozzle_diameter: float) -> List[RectFeature]:
    rects: List[RectFeature] = []
    y = 35.0
    base_x = -21.0
    spacing = 8.4
    stroke = max(0.9, nozzle_diameter * 1.5)

    def add_o(cx: float) -> None:
        rects.extend([
            RectFeature(cx - 2.2, y, stroke, 6.2),
            RectFeature(cx + 2.2, y, stroke, 6.2),
            RectFeature(cx, y - 2.6, 5.0, stroke),
            RectFeature(cx, y + 2.6, 5.0, stroke),
        ])

    def add_h(cx: float) -> None:
        rects.extend([
            RectFeature(cx - 2.2, y, stroke, 6.2),
            RectFeature(cx + 2.2, y, stroke, 6.2),
            RectFeature(cx, y, 5.0, stroke),
        ])

    def add_m(cx: float) -> None:
        rects.extend([
            RectFeature(cx - 2.5, y, stroke, 6.2),
            RectFeature(cx + 2.5, y, stroke, 6.2),
            RectFeature(cx - 0.85, y + 0.9, stroke, 4.4),
            RectFeature(cx + 0.85, y + 0.9, stroke, 4.4),
        ])

    def add_i(cx: float) -> None:
        rects.extend([
            RectFeature(cx, y, stroke, 6.2),
            RectFeature(cx, y - 3.0, 3.8, max(0.75, stroke * 0.85)),
            RectFeature(cx, y + 3.0, 3.8, max(0.75, stroke * 0.85)),
        ])

    def add_c(cx: float) -> None:
        rects.extend([
            RectFeature(cx - 2.2, y, stroke, 6.2),
            RectFeature(cx, y - 2.6, 5.0, stroke),
            RectFeature(cx, y + 2.6, 5.0, stroke),
        ])

    add_o(base_x)
    add_h(base_x + spacing)
    add_m(base_x + spacing * 2.0)
    add_i(base_x + spacing * 3.0)
    add_c(base_x + spacing * 4.0)
    return rects


def lower_led_detail_features(nozzle_diameter: float) -> List[RectFeature]:
    rects: List[RectFeature] = []
    safe_width = max(0.9, nozzle_diameter * 1.5)
    borderline_width = max(0.55, nozzle_diameter)
    for idx in range(9):
        rects.append(RectFeature(-24.0 + idx * 6.0, -36.0, 3.4, safe_width, BASE_Z1, 3.55))
    for idx in range(4):
        rects.append(RectFeature(-18.0 + idx * 12.0, -31.0, 5.5, borderline_width, BASE_Z1, 3.45))
    return rects


def face_detail_ladder_features(nozzle_diameter: float) -> List[RectFeature]:
    rects: List[RectFeature] = []
    widths = [0.25, 0.35, 0.45, nozzle_diameter, nozzle_diameter * 1.5, nozzle_diameter * 2.0]
    x0 = 27.0
    y0 = 4.0
    for idx, width in enumerate(widths):
        rects.append(RectFeature(x0, y0 + idx * 3.0, 12.0, width, BASE_Z1, 3.5))
        rects.append(RectFeature(x0 + 8.0, y0 + idx * 3.0, width, 2.0, BASE_Z1, 3.5))
    return rects


def add_side_label_panel(tris: List[Triangle], nozzle_diameter: float) -> None:
    # Lower outer wall label: raised border, inset-looking panel floor, and
    # OHMIC-like side text bars. This stresses side-wall detail on a 0.6 nozzle
    # while retaining 0.2-like micro bars for later small-nozzle comparison.
    panel_start = 222.0
    panel_end = 318.0
    panel_z0 = 0.65
    panel_z1 = 2.55
    border = max(0.6, nozzle_diameter)

    # Shallow floor is proud of the side wall but lower than the border, giving
    # an inset-panel effect without boolean subtraction.
    add_side_patch(tris, panel_start, panel_end, panel_z0, panel_z1, depth=0.12, segments=32)
    add_side_patch(tris, panel_start, panel_end, panel_z0, panel_z0 + border, depth=0.48, segments=32)
    add_side_patch(tris, panel_start, panel_end, panel_z1 - border, panel_z1, depth=0.48, segments=32)
    add_side_patch(tris, panel_start, panel_start + side_mm_to_deg(border), panel_z0, panel_z1, depth=0.48, segments=3)
    add_side_patch(tris, panel_end - side_mm_to_deg(border), panel_end, panel_z0, panel_z1, depth=0.48, segments=3)

    stroke = max(0.55, nozzle_diameter * 0.9)
    center = 270.0
    spacing = 6.2
    start = center - spacing * 2.0

    def add_side_o(cdeg: float) -> None:
        add_side_rect(tris, cdeg - side_mm_to_deg(1.8), 1.58, stroke, 1.2, 0.82)
        add_side_rect(tris, cdeg + side_mm_to_deg(1.8), 1.58, stroke, 1.2, 0.82)
        add_side_rect(tris, cdeg, 1.04, 4.4, stroke, 0.82)
        add_side_rect(tris, cdeg, 2.12, 4.4, stroke, 0.82)

    def add_side_h(cdeg: float) -> None:
        add_side_rect(tris, cdeg - side_mm_to_deg(1.8), 1.58, stroke, 1.2, 0.82)
        add_side_rect(tris, cdeg + side_mm_to_deg(1.8), 1.58, stroke, 1.2, 0.82)
        add_side_rect(tris, cdeg, 1.58, 4.4, stroke, 0.82)

    def add_side_i(cdeg: float) -> None:
        add_side_rect(tris, cdeg, 1.58, stroke, 1.25, 0.82)
        add_side_rect(tris, cdeg, 1.0, 3.1, max(0.45, stroke * 0.75), 0.82)
        add_side_rect(tris, cdeg, 2.16, 3.1, max(0.45, stroke * 0.75), 0.82)

    add_side_o(start)
    add_side_h(start + spacing)
    add_side_h(start + spacing * 2.0)
    add_side_i(start + spacing * 3.0)
    add_side_h(start + spacing * 4.0)

    # Side detail ladder: stress-only through safe sizes.
    ladder_widths = [0.22, 0.3, 0.45, nozzle_diameter, nozzle_diameter * 1.5, nozzle_diameter * 2.0]
    for idx, width in enumerate(ladder_widths):
        cdeg = 236.0 + idx * 4.4
        add_side_rect(tris, cdeg, 0.98, width, 0.65, 0.9, segments=2)
        add_side_rect(tris, cdeg, 2.22, width, 0.65, 0.9, segments=2)


def triangulated_base(tris: List[Triangle]) -> None:
    points: List[Point2] = []
    points.extend(circle_points(OUTER_RADIUS))
    points.extend(circle_points(INNER_RADIUS))
    for center in screw_centers():
        points.extend(circle_points(SCREW_RADIUS, segments=84, center=center))
    for radius in (23.0, 29.0, 33.5, 37.5, 43.0, 49.0):
        for point in circle_points(radius, segments=SEGMENTS):
            if in_base_footprint(point[0], point[1]):
                points.append(point)

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
        add_vertical_circle_wall(tris, circle_points(SCREW_RADIUS, segments=84, center=center), BASE_Z0, BASE_Z1, flip=True)


def build_mesh(nozzle_diameter: float = DEFAULT_NOZZLE_DIAMETER) -> List[Triangle]:
    tris: List[Triangle] = []
    triangulated_base(tris)

    # Screw bosses / counterbore-like raised pads.
    for center in screw_centers():
        add_annular_cylinder(tris, SCREW_RADIUS + 0.4, BOSS_RADIUS, BASE_Z1, BOSS_Z1, center=center, segments=104)

    # LED channel is represented as two raised rails with a flat channel between.
    add_annular_cylinder(tris, 28.5, 29.3, BASE_Z1, LED_RAIL_Z1, segments=SEGMENTS)
    add_annular_cylinder(tris, 37.2, 38.0, BASE_Z1, LED_RAIL_Z1, segments=SEGMENTS)

    # Cosmetic pinstripes near the speaker opening and outer lip.
    add_annular_cylinder(tris, 22.4, 23.0, BASE_Z1, PINSTRIPE_Z1, segments=SEGMENTS)
    add_annular_cylinder(tris, 48.3, 49.0, BASE_Z1, PINSTRIPE_Z1, segments=SEGMENTS)

    # Hidden backside/internal bulk rib on the lower half.
    add_annular_cylinder(
        tris,
        BACK_RIB_INNER_RADIUS,
        BACK_RIB_OUTER_RADIUS,
        BACK_RIB_Z0,
        BASE_Z0,
        segments=SEGMENTS,
        start_deg=200.0,
        end_deg=340.0,
    )

    # Additional backside-style local bulk pads behind the lower mounting area.
    add_annular_cylinder(tris, 31.0, 45.5, BACK_RIB_Z0, BASE_Z0, segments=SEGMENTS, start_deg=230.0, end_deg=270.0)
    add_annular_cylinder(tris, 31.0, 45.5, BACK_RIB_Z0, BASE_Z0, segments=SEGMENTS, start_deg=270.0, end_deg=310.0)

    add_side_label_panel(tris, nozzle_diameter)

    for feature in logo_surrogate_features(nozzle_diameter):
        add_box(tris, feature)
    for feature in lower_led_detail_features(nozzle_diameter):
        add_box(tris, feature)
    for feature in face_detail_ladder_features(nozzle_diameter):
        add_box(tris, feature)

    return tris


def write_ascii_stl(tris: Iterable[Triangle], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("solid ohmic_led_speaker_ring_fixture\n")
        for a, b, c in tris:
            nx, ny, nz = cross_normal(a, b, c)
            fh.write(f"  facet normal {nx:.6g} {ny:.6g} {nz:.6g}\n")
            fh.write("    outer loop\n")
            for vx, vy, vz in (a, b, c):
                fh.write(f"      vertex {vx:.6g} {vy:.6g} {vz:.6g}\n")
            fh.write("    endloop\n")
            fh.write("  endfacet\n")
        fh.write("endsolid ohmic_led_speaker_ring_fixture\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default="outputs/amp_ohmic_fixture/models/ohmic_led_speaker_ring_fixture.stl",
        help="Output STL path",
    )
    parser.add_argument(
        "--nozzle-diameter",
        type=float,
        default=DEFAULT_NOZZLE_DIAMETER,
        help="Nominal nozzle diameter used to scale detail stress features.",
    )
    args = parser.parse_args()
    tris = build_mesh(args.nozzle_diameter)
    write_ascii_stl(tris, Path(args.out))
    print(f"wrote {args.out} with {len(tris)} triangles for {args.nozzle_diameter:g} mm nozzle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
