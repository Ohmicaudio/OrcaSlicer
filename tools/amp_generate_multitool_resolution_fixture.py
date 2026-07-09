#!/usr/bin/env python3
"""Generate a four-zone AMP multi-tool resolution validation fixture."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from scipy.spatial import Delaunay


Point = Tuple[float, float, float]
Point2 = Tuple[float, float]
Triangle = Tuple[Point, Point, Point]

X0, X1 = -80.0, 80.0
Y0, Y1 = -42.0, 42.0
BASE_Z0, BASE_Z1 = 0.0, 3.0
HOLE_RADIUS = 3.0
HOLES: Sequence[Point2] = [(-62, -27), (-18, -27), (24, -27), (62, -27), (24, 23), (39, 23)]


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


def circle_points(radius: float, center: Point2, segments: int = 80) -> List[Point2]:
    cx, cy = center
    return [
        (cx + math.cos(2.0 * math.pi * i / segments) * radius, cy + math.sin(2.0 * math.pi * i / segments) * radius)
        for i in range(segments)
    ]


def in_hole(x: float, y: float) -> bool:
    return any(math.hypot(x - cx, y - cy) < HOLE_RADIUS for cx, cy in HOLES)


def in_plate(x: float, y: float) -> bool:
    return X0 <= x <= X1 and Y0 <= y <= Y1 and not in_hole(x, y)


def add_box(tris: List[Triangle], x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> None:
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


def add_sloped_panel(tris: List[Triangle], x0: float, x1: float, y0: float, y1: float, z0: float, z_low: float, z_high: float) -> None:
    p000 = (x0, y0, z0)
    p100 = (x1, y0, z0)
    p110 = (x1, y1, z0)
    p010 = (x0, y1, z0)
    p001 = (x0, y0, z_low)
    p101 = (x1, y0, z_high)
    p111 = (x1, y1, z_high)
    p011 = (x0, y1, z_low)
    add_quad(tris, p001, p101, p111, p011)
    add_quad(tris, p000, p010, p110, p100)
    add_quad(tris, p000, p100, p101, p001)
    add_quad(tris, p100, p110, p111, p101)
    add_quad(tris, p110, p010, p011, p111)
    add_quad(tris, p010, p000, p001, p011)


def add_annular_cylinder(tris: List[Triangle], center: Point2, inner_radius: float, outer_radius: float, z0: float, z1: float, segments: int = 96) -> None:
    inner = circle_points(inner_radius, center, segments)
    outer = circle_points(outer_radius, center, segments)
    for i in range(segments):
        j = (i + 1) % segments
        i0, i1 = inner[i], inner[j]
        o0, o1 = outer[i], outer[j]
        add_quad(tris, (o0[0], o0[1], z1), (o1[0], o1[1], z1), (i1[0], i1[1], z1), (i0[0], i0[1], z1))
        add_quad(tris, (o0[0], o0[1], z0), (i0[0], i0[1], z0), (i1[0], i1[1], z0), (o1[0], o1[1], z0))
        add_quad(tris, (o0[0], o0[1], z0), (o1[0], o1[1], z0), (o1[0], o1[1], z1), (o0[0], o0[1], z1))
        add_quad(tris, (i0[0], i0[1], z0), (i0[0], i0[1], z1), (i1[0], i1[1], z1), (i1[0], i1[1], z0))


def add_vertical_wall_loop(tris: List[Triangle], points: Sequence[Point2], z0: float, z1: float, flip: bool = False) -> None:
    for i, p0 in enumerate(points):
        p1 = points[(i + 1) % len(points)]
        add_quad(tris, (p0[0], p0[1], z0), (p1[0], p1[1], z0), (p1[0], p1[1], z1), (p0[0], p0[1], z1), flip=flip)


def triangulated_base(tris: List[Triangle]) -> None:
    points: List[Point2] = []
    for i in range(81):
        x = X0 + (X1 - X0) * i / 80
        points.append((x, Y0))
        points.append((x, Y1))
    for i in range(43):
        y = Y0 + (Y1 - Y0) * i / 42
        points.append((X0, y))
        points.append((X1, y))
    for center in HOLES:
        points.extend(circle_points(HOLE_RADIUS, center, 80))
    for x in range(-70, 71, 10):
        for y in range(-30, 31, 10):
            if in_plate(x, y):
                points.append((float(x), float(y)))

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
        if not in_plate(cx, cy):
            continue
        a2, b2, c2 = coords
        add_tri(tris, (a2[0], a2[1], BASE_Z1), (b2[0], b2[1], BASE_Z1), (c2[0], c2[1], BASE_Z1))
        add_tri(tris, (a2[0], a2[1], BASE_Z0), (c2[0], c2[1], BASE_Z0), (b2[0], b2[1], BASE_Z0))

    rect = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]
    add_vertical_wall_loop(tris, rect, BASE_Z0, BASE_Z1)
    for center in HOLES:
        add_vertical_wall_loop(tris, circle_points(HOLE_RADIUS, center, 80), BASE_Z0, BASE_Z1, flip=True)


def add_bar_text(tris: List[Triangle], x: float, y: float, scale: float, stroke: float, z0: float, z1: float) -> None:
    # OHMIC-like geometric text surrogate. Each character is made from bars.
    spacing = scale * 5.8
    height = scale * 4.5
    width = scale * 3.5

    def box(cx: float, cy: float, sx: float, sy: float) -> None:
        add_box(tris, cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, z0, z1)

    def o(cx: float) -> None:
        box(cx - width / 2, y, stroke, height)
        box(cx + width / 2, y, stroke, height)
        box(cx, y - height / 2, width + stroke, stroke)
        box(cx, y + height / 2, width + stroke, stroke)

    def h(cx: float) -> None:
        box(cx - width / 2, y, stroke, height)
        box(cx + width / 2, y, stroke, height)
        box(cx, y, width + stroke, stroke)

    def m(cx: float) -> None:
        box(cx - width / 2, y, stroke, height)
        box(cx + width / 2, y, stroke, height)
        box(cx - width / 6, y + height / 8, stroke, height * 0.75)
        box(cx + width / 6, y + height / 8, stroke, height * 0.75)

    def i(cx: float) -> None:
        box(cx, y, stroke, height)
        box(cx, y - height / 2, width, stroke)
        box(cx, y + height / 2, width, stroke)

    def c(cx: float) -> None:
        box(cx - width / 2, y, stroke, height)
        box(cx, y - height / 2, width + stroke, stroke)
        box(cx, y + height / 2, width + stroke, stroke)

    for idx, fn in enumerate((o, h, m, i, c)):
        fn(x + idx * spacing)


def build_mesh() -> List[Triangle]:
    tris: List[Triangle] = []
    triangulated_base(tris)

    # Region 0.2: micro/fine visible detail.
    for idx, width in enumerate((0.22, 0.30, 0.42, 0.60, 0.90)):
        add_box(tris, -72, -52, 24 - idx * 4, 24 - idx * 4 + width, BASE_Z1, 3.45)
        add_box(tris, -48 + idx * 2.6, -48 + idx * 2.6 + width, 3, 8, BASE_Z1, 3.45)
    for idx in range(8):
        add_box(tris, -73 + idx * 3.5, -72.4 + idx * 3.5, 12, 12.6, BASE_Z1, 3.55)

    # Region 0.4: normal visible/detail and cosmetic slope.
    # Keep raised details on a supported flat pad, with a separate sloped face
    # behind it. Earlier revisions placed the text at the high side of the
    # slope, which left most bars floating above the surface.
    add_box(tris, -36, 0, 8, 29, BASE_Z1, 4.2)
    add_sloped_panel(tris, -36, 0, 29, 34, BASE_Z1, 3.2, 4.2)
    add_bar_text(tris, -33, 25, scale=1.0, stroke=0.65, z0=4.15, z1=4.75)
    for idx in range(5):
        add_box(tris, -34 + idx * 7, -31 + idx * 7, 10, 10.8, 4.15, 4.6)

    # Region 0.6: structural shell / bosses / holes.
    add_box(tris, 10, 45, 6, 34, BASE_Z1, 5.1)
    add_box(tris, 16, 39, 12, 28, 5.1, 5.8)
    for center in ((24, 23), (39, 23)):
        add_annular_cylinder(tris, center, HOLE_RADIUS + 0.4, 8.0, BASE_Z1, 6.2)

    # Region 0.8: bulk / large internal mass.
    add_box(tris, 52, 76, 4, 36, BASE_Z1, 8.0)
    for idx in range(4):
        add_box(tris, 54, 74, 8 + idx * 7, 11 + idx * 7, 8.0, 9.8)

    # Hidden backside/internal mass shared by structural/bulk side.
    add_box(tris, 8, 78, -39, -18, -2.6, BASE_Z0)
    add_box(tris, 52, 78, -18, 0, -2.6, BASE_Z0)

    return tris


def build_region_mesh(region_name: str) -> List[Triangle]:
    tris: List[Triangle] = []
    if region_name == "micro_detail_zone":
        add_box(tris, -18, 18, -12, 12, 0, 1.2)
        for idx, width in enumerate((0.22, 0.30, 0.42, 0.60, 0.90)):
            y = -8 + idx * 4
            add_box(tris, -15, 15, y, y + width, 1.2, 1.65)
            add_box(tris, -14 + idx * 5, -14 + idx * 5 + width, 3, 8, 1.2, 1.65)
        for idx in range(8):
            add_box(tris, -14 + idx * 4, -13.4 + idx * 4, -2, -1.4, 1.2, 1.75)
    elif region_name == "normal_visible_detail_zone":
        add_box(tris, -22, 22, -16, 16, 0, 1.4)
        # Supported visible-detail pad plus a separate slope strip. Text and
        # ladder bars are slightly embedded into the pad so slicers do not
        # treat them as floating independent islands.
        add_box(tris, -18, 18, -13, 10, 1.4, 2.7)
        add_sloped_panel(tris, -18, 18, 10, 15, 1.4, 1.7, 2.7)
        add_bar_text(tris, -16, 4, scale=0.9, stroke=0.65, z0=2.65, z1=3.25)
        for idx in range(5):
            add_box(tris, -16 + idx * 7, -13 + idx * 7, -12, -11.2, 2.65, 3.1)
    elif region_name == "structural_shell_zone":
        add_box(tris, -22, 22, -18, 18, 0, 2.4)
        add_box(tris, -14, 14, -10, 10, 2.4, 3.1)
        for center in ((-9, 8), (9, 8)):
            add_annular_cylinder(tris, center, HOLE_RADIUS + 0.4, 7.0, 2.4, 4.0)
    elif region_name == "bulk_zone":
        add_box(tris, -20, 20, -18, 18, 0, 5.0)
        for idx in range(4):
            add_box(tris, -15, 15, -13 + idx * 7, -10 + idx * 7, 5.0, 6.8)
    else:
        raise ValueError(f"unknown region: {region_name}")
    return tris


def regions() -> List[dict]:
    return [
        {
            "region_name": "micro_detail_zone",
            "intended_nozzle": "0.2",
            "intended_layer_height_class": "0.06-0.10",
            "intended_width_class": "0.22",
            "reason": "Tiny text/logo surrogate, fine grooves, and small dots are visible-detail stress features.",
            "risk_level": "high if assigned to coarse tools",
        },
        {
            "region_name": "normal_visible_detail_zone",
            "intended_nozzle": "0.4",
            "intended_layer_height_class": "0.12-0.20",
            "intended_width_class": "0.42-0.45",
            "reason": "Readable text surrogate, cosmetic wall, and sloped visible face need normal detail without the cost of 0.2 everywhere.",
            "risk_level": "medium",
        },
        {
            "region_name": "structural_shell_zone",
            "intended_nozzle": "0.6",
            "intended_layer_height_class": "0.24-0.36",
            "intended_width_class": "0.62",
            "reason": "Thicker walls, holes, and bosses can use structural shell resolution if visible faces are protected.",
            "risk_level": "medium",
        },
        {
            "region_name": "bulk_zone",
            "intended_nozzle": "0.8",
            "intended_layer_height_class": "0.32-0.56",
            "intended_width_class": "0.82",
            "reason": "Large hidden/internal mass is the intended coarse bulk region.",
            "risk_level": "low for visibility, high if used near mating/detail features",
        },
    ]


def region_assignments() -> List[dict]:
    return [
        {
            "region_name": "micro_detail_zone",
            "intended_tool_class": "0.2",
            "intended_nozzle": "0.2",
            "intended_layer_height_class": "0.06-0.10",
            "intended_line_width_class": "0.22",
            "fallback_tool_class": "0.4",
            "reason": "Visible micro detail is plausible for the 0.2 fine/detail class.",
            "risk_flags": [
                "preview_required",
                "touchscreen_mixed_nozzle_blocked",
            ],
        },
        {
            "region_name": "normal_visible_detail_zone",
            "intended_tool_class": "0.4",
            "intended_nozzle": "0.4",
            "intended_layer_height_class": "0.12-0.20",
            "intended_line_width_class": "0.42-0.45",
            "fallback_tool_class": "0.2",
            "reason": "Normal visible/detail geometry should use the 0.4 general class and avoid 0.8.",
            "risk_flags": [
                "avoid_large_visible_tool",
                "touchscreen_mixed_nozzle_blocked",
            ],
        },
        {
            "region_name": "structural_shell_zone",
            "intended_tool_class": "0.6",
            "intended_nozzle": "0.6",
            "intended_layer_height_class": "0.24-0.36",
            "intended_line_width_class": "0.62",
            "fallback_tool_class": "0.4",
            "reason": "Internal/low-detail structural shell is a 0.6 candidate.",
            "risk_flags": [
                "touchscreen_mixed_nozzle_blocked",
            ],
        },
        {
            "region_name": "bulk_zone",
            "intended_tool_class": "0.8",
            "intended_nozzle": "0.8",
            "intended_layer_height_class": "0.32-0.56",
            "intended_line_width_class": "0.82",
            "fallback_tool_class": "0.6",
            "reason": "Hidden/internal bulk is large enough for the 0.8 bulk class.",
            "risk_flags": [
                "touchscreen_mixed_nozzle_blocked",
            ],
        },
    ]


def write_ascii_stl(tris: Iterable[Triangle], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("solid amp_multitool_resolution_fixture\n")
        for a, b, c in tris:
            nx, ny, nz = cross_normal(a, b, c)
            fh.write(f"  facet normal {nx:.6g} {ny:.6g} {nz:.6g}\n")
            fh.write("    outer loop\n")
            for vx, vy, vz in (a, b, c):
                fh.write(f"      vertex {vx:.6g} {vy:.6g} {vz:.6g}\n")
            fh.write("    endloop\n")
            fh.write("  endfacet\n")
        fh.write("endsolid amp_multitool_resolution_fixture\n")


def write_regions(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"regions": regions()}, indent=2), encoding="utf-8", newline="\n")


def write_split_regions(out_dir: Path, assignments_out: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for assignment in region_assignments():
        region_name = str(assignment["region_name"])
        write_ascii_stl(build_region_mesh(region_name), out_dir / f"{region_name}.stl")
    assignments_out.parent.mkdir(parents=True, exist_ok=True)
    assignments_out.write_text(json.dumps({"regions": region_assignments()}, indent=2), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="outputs/amp_multitool_resolution_fixture/models/amp_multitool_resolution_fixture.stl")
    parser.add_argument("--regions-out", default="outputs/amp_multitool_resolution_fixture/models/amp_multitool_resolution_fixture_regions.json")
    parser.add_argument("--split-regions", action="store_true")
    parser.add_argument("--split-out-dir", default="outputs/amp_multitool_resolution_fixture/region_bodies")
    parser.add_argument("--region-assignments-out", default="outputs/amp_multitool_resolution_fixture/region_bodies/region_assignments.json")
    args = parser.parse_args()
    tris = build_mesh()
    write_ascii_stl(tris, Path(args.out))
    write_regions(Path(args.regions_out))
    print(f"wrote {args.out} with {len(tris)} triangles")
    print(f"wrote {args.regions_out} with {len(regions())} regions")
    if args.split_regions:
        write_split_regions(Path(args.split_out_dir), Path(args.region_assignments_out))
        print(f"wrote split region bodies to {args.split_out_dir}")
        print(f"wrote {args.region_assignments_out} with {len(region_assignments())} assignments")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
