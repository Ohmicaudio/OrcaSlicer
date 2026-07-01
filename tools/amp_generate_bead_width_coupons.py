#!/usr/bin/env python3
"""Generate simple STL coupons for AMP proxy bead-width characterization.

The generated models are synthetic measurement aids. They are not validation
models for Snapmaker U1 mixed-nozzle behavior.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Iterable, List, Tuple

Vec3 = Tuple[float, float, float]
Triangle = Tuple[Vec3, Vec3, Vec3]


def sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def normalize(v: Vec3) -> Vec3:
    length = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if length == 0:
        return (0.0, 0.0, 0.0)
    return (v[0] / length, v[1] / length, v[2] / length)


def normal(tri: Triangle) -> Vec3:
    return normalize(cross(sub(tri[1], tri[0]), sub(tri[2], tri[0])))


def write_ascii_stl(path: Path, name: str, triangles: Iterable[Triangle]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="ascii", newline="\n") as fh:
        fh.write(f"solid {name}\n")
        for tri in triangles:
            n = normal(tri)
            fh.write(f"  facet normal {n[0]:.6g} {n[1]:.6g} {n[2]:.6g}\n")
            fh.write("    outer loop\n")
            for v in tri:
                fh.write(f"      vertex {v[0]:.6g} {v[1]:.6g} {v[2]:.6g}\n")
            fh.write("    endloop\n")
            fh.write("  endfacet\n")
        fh.write(f"endsolid {name}\n")


def box(x: float, y: float, z: float, sx: float, sy: float, sz: float) -> List[Triangle]:
    x0, x1 = x, x + sx
    y0, y1 = y, y + sy
    z0, z1 = z, z + sz
    p = {
        "000": (x0, y0, z0),
        "100": (x1, y0, z0),
        "110": (x1, y1, z0),
        "010": (x0, y1, z0),
        "001": (x0, y0, z1),
        "101": (x1, y0, z1),
        "111": (x1, y1, z1),
        "011": (x0, y1, z1),
    }
    return [
        (p["000"], p["110"], p["100"]), (p["000"], p["010"], p["110"]),
        (p["001"], p["101"], p["111"]), (p["001"], p["111"], p["011"]),
        (p["000"], p["100"], p["101"]), (p["000"], p["101"], p["001"]),
        (p["010"], p["011"], p["111"]), (p["010"], p["111"], p["110"]),
        (p["000"], p["001"], p["011"]), (p["000"], p["011"], p["010"]),
        (p["100"], p["110"], p["111"]), (p["100"], p["111"], p["101"]),
    ]


def label_bars(x: float, y: float, z: float, scale: float = 1.0) -> List[Triangle]:
    tris: List[Triangle] = []
    strokes = [
        (0, 0, 8, 1.0), (0, 7, 8, 1.0), (0, 14, 8, 1.0),
        (12, 0, 1.0, 15), (16, 0, 1.0, 15), (20, 0, 1.0, 15),
    ]
    for dx, dy, sx, sy in strokes:
        tris.extend(box(x + dx * scale, y + dy * scale, z, sx * scale, sy * scale, 1.0))
    return tris


def single_wall_width_coupon() -> List[Triangle]:
    tris: List[Triangle] = []
    tris.extend(box(0, 0, 0, 90, 14, 1.2))
    widths = [0.42, 0.52, 0.58]
    y = 22.0
    for width in widths:
        tris.extend(box(10, y, 0, 70, width, 12))
        y += 10.0
    return tris


def wall_adjacency_coupon() -> List[Triangle]:
    tris: List[Triangle] = []
    tris.extend(box(0, 0, 0, 90, 18, 1.2))
    y = 25.0
    for gap in [0.20, 0.35, 0.50, 0.70]:
        tris.extend(box(8, y, 0, 70, 0.52, 10))
        tris.extend(box(8, y + 0.52 + gap, 0, 70, 0.52, 10))
        y += 8.0
    return tris


def top_surface_coupon() -> List[Triangle]:
    tris: List[Triangle] = []
    tris.extend(box(0, 0, 0, 60, 60, 3))
    tris.extend(box(8, 8, 3, 44, 44, 1.2))
    for i in range(5):
        tris.extend(box(8 + i * 8, 8, 4.2, 2, 44, 0.8))
    return tris


def detail_surrogate_coupon() -> List[Triangle]:
    tris: List[Triangle] = []
    tris.extend(box(0, 0, 0, 80, 45, 2.4))
    tris.extend(label_bars(8, 10, 2.4, 1.0))
    for i, width in enumerate([0.4, 0.5, 0.6, 0.8, 1.0]):
        tris.extend(box(45 + i * 6, 10, 2.4, width, 24, 1.2))
    return tris


COUPONS = {
    "single_wall_width_coupon.stl": single_wall_width_coupon,
    "wall_adjacency_coupon.stl": wall_adjacency_coupon,
    "top_surface_coupon.stl": top_surface_coupon,
    "detail_surrogate_coupon.stl": detail_surrogate_coupon,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default="outputs/amp_proxy_characterization/models",
        help="output directory",
    )
    args = parser.parse_args()
    out = Path(args.out)
    for filename, factory in COUPONS.items():
        path = out / filename
        write_ascii_stl(path, Path(filename).stem, factory())
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
