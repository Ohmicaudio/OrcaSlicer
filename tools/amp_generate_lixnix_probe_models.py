#!/usr/bin/env python3
"""Generate self-contained LixNix mixed-nozzle probe STL models.

The models are simple dependency-free ASCII STL fixtures. They are meant to
probe mixed nozzle / per-extruder layer-height behavior in external slicers.
They are not production geometry and do not validate print quality.
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
        (p["000"], p["110"], p["100"]),
        (p["000"], p["010"], p["110"]),
        (p["001"], p["101"], p["111"]),
        (p["001"], p["111"], p["011"]),
        (p["000"], p["100"], p["101"]),
        (p["000"], p["101"], p["001"]),
        (p["010"], p["011"], p["111"]),
        (p["010"], p["111"], p["110"]),
        (p["000"], p["001"], p["011"]),
        (p["000"], p["011"], p["010"]),
        (p["100"], p["110"], p["111"]),
        (p["100"], p["111"], p["101"]),
    ]


def cylinder(cx: float, cy: float, z: float, radius: float, height: float, segments: int = 48) -> List[Triangle]:
    tris: List[Triangle] = []
    top_center = (cx, cy, z + height)
    bottom_center = (cx, cy, z)
    for i in range(segments):
        a0 = 2.0 * math.pi * i / segments
        a1 = 2.0 * math.pi * (i + 1) / segments
        b0 = (cx + radius * math.cos(a0), cy + radius * math.sin(a0), z)
        b1 = (cx + radius * math.cos(a1), cy + radius * math.sin(a1), z)
        t0 = (b0[0], b0[1], z + height)
        t1 = (b1[0], b1[1], z + height)
        tris.extend([(b0, b1, t1), (b0, t1, t0), (bottom_center, b0, b1), (top_center, t1, t0)])
    return tris


def detail_ladder(x: float, y: float, z: float, length: float = 18.0) -> List[Triangle]:
    tris: List[Triangle] = []
    for idx, width in enumerate([0.25, 0.35, 0.45, 0.6, 0.9, 1.2]):
        tris.extend(box(x, y + idx * 4.0, z, length, width, 1.0))
        tris.extend(box(x + length + 3.0, y + idx * 4.0, z, width, 2.0, 1.0))
    return tris


def two_object_detail_bulk() -> List[Triangle]:
    tris: List[Triangle] = []
    # Small/detail body: low plate with micro and normal details.
    tris.extend(box(0, 0, 0, 42, 34, 3))
    tris.extend(detail_ladder(5, 6, 3))
    for i in range(4):
        tris.extend(box(7 + i * 8, 27, 3, 4.0, 1.0, 1.0))

    # Bulk body: separated thick block with ribs and holes/pads.
    tris.extend(box(70, 0, 0, 55, 42, 12))
    tris.extend(box(75, 6, 12, 45, 4, 10))
    tris.extend(box(75, 32, 12, 45, 4, 10))
    for x, y in [(82, 10), (112, 10), (82, 32), (112, 32)]:
        tris.extend(cylinder(x, y, 12, 3.0, 4.0))
    return tris


def four_region_tool_ladder() -> List[Triangle]:
    tris: List[Triangle] = []
    # Four labeled-by-shape regions placed left to right for manual assignment.
    tris.extend(box(0, 0, 0, 28, 30, 2.4))
    tris.extend(detail_ladder(3, 4, 2.4, 10.0))

    tris.extend(box(40, 0, 0, 34, 30, 4.0))
    tris.extend(box(45, 5, 4.0, 24, 1.0, 1.0))
    tris.extend(box(45, 11, 4.0, 24, 1.4, 1.0))
    tris.extend(box(45, 18, 4.0, 24, 2.0, 1.0))

    tris.extend(box(88, 0, 0, 42, 30, 10.0))
    tris.extend(box(94, 6, 10.0, 30, 5.0, 8.0))
    tris.extend(box(94, 19, 10.0, 30, 5.0, 8.0))

    tris.extend(box(146, 0, 0, 56, 38, 18.0))
    tris.extend(box(154, 8, 18.0, 40, 8.0, 9.0))
    tris.extend(box(154, 24, 18.0, 40, 8.0, 9.0))
    return tris


def support_restriction_probe() -> List[Triangle]:
    tris: List[Triangle] = []
    tris.extend(box(0, 0, 0, 70, 44, 4))
    tris.extend(box(8, 8, 4, 8, 28, 24))
    tris.extend(box(54, 8, 4, 8, 28, 24))
    # Bridge/overhang slab between pillars.
    tris.extend(box(8, 8, 28, 54, 28, 4))
    # Smaller side ledges to trigger support/interface decisions.
    tris.extend(box(16, -10, 18, 38, 12, 4))
    tris.extend(box(16, 42, 18, 38, 12, 4))
    return tris


def layer_height_probe() -> List[Triangle]:
    tris: List[Triangle] = []
    # Tall stepped towers expose coarse-layer combination and fallback zones.
    for i in range(8):
        tris.extend(box(i * 14, 0, 0, 12, 26, 8 + i * 4))
    # Constant vertical column likely suitable for coarse layer grouping.
    tris.extend(box(0, 45, 0, 34, 28, 62))
    # Tapered/stepped detail column should force finer fallback bands.
    for i in range(10):
        shrink = i * 1.0
        tris.extend(box(55 + shrink / 2.0, 45 + shrink / 2.0, i * 5, 34 - shrink, 28 - shrink, 5))
    return tris


MODELS = {
    "lixnix_two_object_detail_bulk.stl": two_object_detail_bulk,
    "lixnix_four_region_tool_ladder.stl": four_region_tool_ladder,
    "lixnix_support_restriction_probe.stl": support_restriction_probe,
    "lixnix_layer_height_probe.stl": layer_height_probe,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="outputs/lixnix_runtime_probe/models", help="output directory")
    args = parser.parse_args()
    out = Path(args.out)
    for filename, factory in MODELS.items():
        path = out / filename
        tris = factory()
        write_ascii_stl(path, Path(filename).stem, tris)
        print(f"wrote {path} ({len(tris)} triangles)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
