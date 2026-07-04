#!/usr/bin/env python3
"""Generate AMP 0.6/0.8 break-even sweep STL models.

The models are intentionally simple enough to regenerate locally, but they are
not plain cubes: structural-shell cases include wall-like members, mounting
bosses, and hole/counterbore surrogates; bulk cases include hidden-mass blocks
with ribs and internal-style pads. Generated STL files are benchmark artifacts
and should stay under outputs/.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable, List, Tuple


Point = Tuple[float, float, float]
Point2 = Tuple[float, float]
Triangle = Tuple[Point, Point, Point]


STRUCTURAL_SIZES = {
    "small": {"length": 42.0, "width": 24.0, "height": 6.0, "wall": 4.0},
    "medium": {"length": 70.0, "width": 34.0, "height": 8.0, "wall": 5.0},
    "large": {"length": 104.0, "width": 46.0, "height": 10.0, "wall": 6.0},
    "xlarge": {"length": 142.0, "width": 58.0, "height": 12.0, "wall": 7.0},
}

BULK_SIZES = {
    "small": {"length": 36.0, "width": 26.0, "height": 8.0},
    "medium": {"length": 68.0, "width": 42.0, "height": 12.0},
    "large": {"length": 108.0, "width": 58.0, "height": 16.0},
    "xlarge": {"length": 152.0, "width": 72.0, "height": 20.0},
}


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


def circle_points(radius: float, center: Point2, segments: int = 64) -> List[Point2]:
    cx, cy = center
    return [
        (cx + math.cos(2.0 * math.pi * i / segments) * radius, cy + math.sin(2.0 * math.pi * i / segments) * radius)
        for i in range(segments)
    ]


def add_annular_cylinder(
    tris: List[Triangle],
    center: Point2,
    inner_radius: float,
    outer_radius: float,
    z0: float,
    z1: float,
    segments: int = 72,
) -> None:
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


def add_rectangular_wall_loop(
    tris: List[Triangle],
    length: float,
    width: float,
    wall: float,
    z0: float,
    z1: float,
) -> None:
    lx = length / 2.0
    wy = width / 2.0
    add_box(tris, -lx, lx, -wy, -wy + wall, z0, z1)
    add_box(tris, -lx, lx, wy - wall, wy, z0, z1)
    add_box(tris, -lx, -lx + wall, -wy, wy, z0, z1)
    add_box(tris, lx - wall, lx, -wy, wy, z0, z1)


def build_structural_shell(length: float, width: float, height: float, wall: float) -> List[Triangle]:
    tris: List[Triangle] = []
    add_box(tris, -length / 2, length / 2, -width / 2, width / 2, 0, 1.8)
    add_rectangular_wall_loop(tris, length, width, wall, 1.8, height)
    add_box(tris, -length / 2 + wall * 1.5, length / 2 - wall * 1.5, -wall / 2, wall / 2, 1.8, height * 0.82)
    add_box(tris, -wall / 2, wall / 2, -width / 2 + wall * 1.4, width / 2 - wall * 1.4, 1.8, height * 0.82)
    boss_y = width / 2 - wall * 1.7
    for x in (-length / 2 + wall * 2.1, length / 2 - wall * 2.1):
        add_annular_cylinder(tris, (x, boss_y), inner_radius=max(1.8, wall * 0.42), outer_radius=wall * 1.15, z0=1.8, z1=height + 1.0)
        add_annular_cylinder(tris, (x, -boss_y), inner_radius=max(1.8, wall * 0.42), outer_radius=wall * 1.15, z0=1.8, z1=height + 1.0)
    return tris


def build_bulk(length: float, width: float, height: float) -> List[Triangle]:
    tris: List[Triangle] = []
    add_box(tris, -length / 2, length / 2, -width / 2, width / 2, 0, height)
    rib_count = max(3, int(length // 28))
    rib_width = max(4.0, width * 0.10)
    for i in range(rib_count):
        x = -length / 2 + (i + 1) * length / (rib_count + 1)
        add_box(tris, x - rib_width / 2, x + rib_width / 2, -width / 2 - 4, width / 2 + 4, height, height + 3.0)
    for side in (-1, 1):
        add_box(tris, -length / 2 + 5, length / 2 - 5, side * (width / 2 + 2), side * (width / 2 + 7), height * 0.35, height + 2.0)
    pad_radius = min(width, length) * 0.16
    for x in (-length * 0.28, length * 0.28):
        add_annular_cylinder(tris, (x, 0.0), inner_radius=pad_radius * 0.35, outer_radius=pad_radius, z0=height, z1=height + 3.2)
    return tris


def write_ascii_stl(tris: Iterable[Triangle], path: Path, solid_name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(f"solid {solid_name}\n")
        for a, b, c in tris:
            nx, ny, nz = cross_normal(a, b, c)
            fh.write(f"  facet normal {nx:.6g} {ny:.6g} {nz:.6g}\n")
            fh.write("    outer loop\n")
            for vx, vy, vz in (a, b, c):
                fh.write(f"      vertex {vx:.6g} {vy:.6g} {vz:.6g}\n")
            fh.write("    endloop\n")
            fh.write("  endfacet\n")
        fh.write(f"endsolid {solid_name}\n")


def structural_metadata(name: str, spec: dict[str, float]) -> dict[str, object]:
    length = spec["length"]
    width = spec["width"]
    height = spec["height"]
    wall = spec["wall"]
    area = 2.0 * length * width + 2.0 * height * (length + width)
    volume = length * width * 1.8 + 2.0 * wall * height * (length + width - 2.0 * wall)
    path = 2.0 * (length + width) * max(4.0, height / 0.24)
    return {
        "model_name": f"structural_shell_{name}",
        "region_type": "structural_shell",
        "size_class": name,
        "intended_candidate_tool": "0.6",
        "baseline_tool": "0.4",
        "approximate_area_mm2": round(area, 1),
        "approximate_volume_mm3": round(volume, 1),
        "approximate_path_length_mm": round(path, 1),
        "reason": "Wall-like shell/bracket section with ribs, bosses, and hole/counterbore surrogates.",
    }


def bulk_metadata(name: str, spec: dict[str, float]) -> dict[str, object]:
    length = spec["length"]
    width = spec["width"]
    height = spec["height"]
    area = 2.0 * (length * width + length * height + width * height)
    volume = length * width * height
    path = 2.0 * (length + width) * max(4.0, height / 0.40)
    return {
        "model_name": f"bulk_{name}",
        "region_type": "bulk",
        "size_class": name,
        "intended_candidate_tool": "0.8",
        "baseline_tool": "0.4",
        "approximate_area_mm2": round(area, 1),
        "approximate_volume_mm3": round(volume, 1),
        "approximate_path_length_mm": round(path, 1),
        "reason": "Hidden/internal bulk mass surrogate with ribs and large simple features.",
    }


def generate(out_dir: Path, metadata_out: Path) -> List[dict[str, object]]:
    metadata: List[dict[str, object]] = []
    out_dir.mkdir(parents=True, exist_ok=True)
    for size, spec in STRUCTURAL_SIZES.items():
        model_name = f"structural_shell_{size}"
        tris = build_structural_shell(**spec)
        write_ascii_stl(tris, out_dir / f"{model_name}.stl", model_name)
        item = structural_metadata(size, spec)
        item["triangle_count"] = len(tris)
        metadata.append(item)
    for size, spec in BULK_SIZES.items():
        model_name = f"bulk_{size}"
        tris = build_bulk(**spec)
        write_ascii_stl(tris, out_dir / f"{model_name}.stl", model_name)
        item = bulk_metadata(size, spec)
        item["triangle_count"] = len(tris)
        metadata.append(item)
    metadata_out.parent.mkdir(parents=True, exist_ok=True)
    metadata_out.write_text(json.dumps({"models": metadata}, indent=2), encoding="utf-8", newline="\n")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="outputs/amp_tool_break_even_sweep/models")
    parser.add_argument("--metadata-out", default="outputs/amp_tool_break_even_sweep/models/metadata.json")
    args = parser.parse_args()
    metadata = generate(Path(args.out_dir), Path(args.metadata_out))
    print(f"wrote {len(metadata)} model(s) to {args.out_dir}")
    print(f"wrote metadata to {args.metadata_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
