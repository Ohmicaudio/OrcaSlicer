#!/usr/bin/env python3
"""Generate synthetic STL models for AMP Stage 1 benchmark Run 001.

The generated files are intentionally simple, dependency-free ASCII STL models.
They are benchmark fixtures for profile-only slicing comparison, not production
geometry or print-quality reference models.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

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
        "000": (x0, y0, z0), "100": (x1, y0, z0), "110": (x1, y1, z0), "010": (x0, y1, z0),
        "001": (x0, y0, z1), "101": (x1, y0, z1), "111": (x1, y1, z1), "011": (x0, y1, z1),
    }
    return [
        (p["000"], p["110"], p["100"]), (p["000"], p["010"], p["110"]),
        (p["001"], p["101"], p["111"]), (p["001"], p["111"], p["011"]),
        (p["000"], p["100"], p["101"]), (p["000"], p["101"], p["001"]),
        (p["010"], p["011"], p["111"]), (p["010"], p["111"], p["110"]),
        (p["000"], p["001"], p["011"]), (p["000"], p["011"], p["010"]),
        (p["100"], p["110"], p["111"]), (p["100"], p["111"], p["101"]),
    ]


def cylinder(cx: float, cy: float, z: float, radius: float, height: float, segments: int = 64) -> List[Triangle]:
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


def ring(cx: float, cy: float, z: float, inner: float, outer: float, height: float, segments: int = 96) -> List[Triangle]:
    tris: List[Triangle] = []
    for i in range(segments):
        a0 = 2.0 * math.pi * i / segments
        a1 = 2.0 * math.pi * (i + 1) / segments
        ob0 = (cx + outer * math.cos(a0), cy + outer * math.sin(a0), z)
        ob1 = (cx + outer * math.cos(a1), cy + outer * math.sin(a1), z)
        ot0 = (ob0[0], ob0[1], z + height)
        ot1 = (ob1[0], ob1[1], z + height)
        ib0 = (cx + inner * math.cos(a0), cy + inner * math.sin(a0), z)
        ib1 = (cx + inner * math.cos(a1), cy + inner * math.sin(a1), z)
        it0 = (ib0[0], ib0[1], z + height)
        it1 = (ib1[0], ib1[1], z + height)
        tris.extend([
            (ob0, ob1, ot1), (ob0, ot1, ot0),
            (ib1, ib0, it0), (ib1, it0, it1),
            (ot0, ot1, it1), (ot0, it1, it0),
            (ob1, ob0, ib0), (ob1, ib0, ib1),
        ])
    return tris


def radial_boxes(cx: float, cy: float, z: float, count: int, radius: float, width: float, depth: float, height: float) -> List[Triangle]:
    # Axis-aligned approximations used as visible small-detail surrogates.
    tris: List[Triangle] = []
    for i in range(count):
        a = 2.0 * math.pi * i / count
        x = cx + radius * math.cos(a) - width / 2.0
        y = cy + radius * math.sin(a) - depth / 2.0
        tris.extend(box(x, y, z, width, depth, height))
    return tris


def thin_wall_comb() -> List[Triangle]:
    tris: List[Triangle] = []
    tris.extend(box(0, 0, 0, 90, 12, 1.2))
    widths = [0.25, 0.35, 0.45, 0.6, 0.8, 1.0, 1.2]
    x = 5.0
    for w in widths:
        tris.extend(box(x, 18, 0, w, 48, 12))
        tris.extend(box(x + 3.0, 18, 0, w, 48, 8))
        x += 11.0
    return tris


def large_bracket_box() -> List[Triangle]:
    tris = box(0, 0, 0, 100, 60, 4)
    tris += box(0, 0, 4, 5, 60, 36)
    tris += box(95, 0, 4, 5, 60, 36)
    tris += box(0, 0, 4, 100, 5, 36)
    tris += box(0, 55, 4, 100, 5, 36)
    for x, y in [(18, 15), (82, 15), (18, 45), (82, 45)]:
        tris += cylinder(x, y, 4, 5, 10, 32)
    return tris


def embossed_text_plate() -> List[Triangle]:
    tris = box(0, 0, 0, 90, 40, 3)
    # Geometric text surrogate: AMP RUN 001 as raised block strokes.
    strokes = [
        (8, 10, 3, 4, 20, 1.2), (8, 26, 3, 14, 4, 1.2), (22, 10, 3, 4, 20, 1.2),
        (32, 10, 3, 4, 20, 1.2), (36, 26, 3, 10, 4, 1.2), (46, 10, 3, 4, 20, 1.2),
        (56, 10, 3, 4, 20, 1.2), (60, 26, 3, 14, 4, 1.2), (74, 10, 3, 4, 20, 1.2),
    ]
    for s in strokes:
        tris.extend(box(*s))
    return tris


def speaker_adapter_ring() -> List[Triangle]:
    tris = ring(50, 50, 0, 28, 48, 6, 128)
    tris += ring(50, 50, 6, 32, 42, 4, 128)
    for x, y in [(15, 50), (85, 50), (50, 15), (50, 85)]:
        tris += cylinder(x, y, 0, 3.0, 8, 24)
    return tris


def led_ring_face() -> List[Triangle]:
    tris = ring(50, 50, 0, 35, 48, 2.4, 128)
    tris += radial_boxes(50, 50, 2.4, 24, 42, 1.4, 2.8, 1.0)
    tris += radial_boxes(50, 50, 2.4, 12, 36, 2.0, 2.0, 1.2)
    return tris


def sloped_surface_torture() -> List[Triangle]:
    tris: List[Triangle] = []
    # Stepped base.
    for i in range(8):
        tris.extend(box(i * 10, 0, 0, 10, 40, 1.0 + i * 1.4))
    # Shallow triangular prism ramp.
    p0, p1, p2 = (0, 50, 0), (90, 50, 0), (90, 50, 14)
    p3, p4, p5 = (0, 80, 0), (90, 80, 0), (90, 80, 14)
    tris.extend([(p0, p1, p2), (p3, p5, p4), (p0, p3, p4), (p0, p4, p1), (p1, p4, p5), (p1, p5, p2), (p2, p5, p3), (p2, p3, p0)])
    return tris


MODELS = {
    "thin_wall_comb.stl": thin_wall_comb,
    "large_bracket_box.stl": large_bracket_box,
    "embossed_text_plate.stl": embossed_text_plate,
    "speaker_adapter_ring.stl": speaker_adapter_ring,
    "led_ring_face.stl": led_ring_face,
    "sloped_surface_torture.stl": sloped_surface_torture,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="outputs/amp_run_001/models/generated", help="output directory")
    args = parser.parse_args()
    out = Path(args.out)
    for filename, factory in MODELS.items():
        write_ascii_stl(out / filename, Path(filename).stem, factory())
        print(out / filename)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
