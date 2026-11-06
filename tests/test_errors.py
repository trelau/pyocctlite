from __future__ import annotations

import unittest

from pyocctlite.errors import BuildFailed, KindMismatch
from pyocctlite.geometry import Point, Vector
from pyocctlite.topology import Edge, Face, Solid, Wire


def _box() -> Solid:
    pts = [
        Point.by_xyz(0, 0, 0),
        Point.by_xyz(1, 0, 0),
        Point.by_xyz(1, 1, 0),
        Point.by_xyz(0, 1, 0),
    ]
    w = Wire.by_edges([Edge.by_points(pts[i], pts[(i + 1) % 4]) for i in range(4)])
    solid = Face.by_wire(w).extrude(Vector.by_xyz(0, 0, 1))
    assert isinstance(solid, Solid)
    return solid


class TestKindMismatch(unittest.TestCase):
    def test_is_type_error(self):
        self.assertTrue(issubclass(KindMismatch, TypeError))

    def test_name(self):
        self.assertEqual(KindMismatch.__name__, "KindMismatch")
        self.assertEqual(KindMismatch.__module__, "pyocctlite.errors")

    def test_raised(self):
        w = Wire.by_edge(Edge.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0)))
        with self.assertRaises(KindMismatch):
            Wire.by_edge(w)


class TestBuildFailed(unittest.TestCase):
    def test_is_runtime_error(self):
        self.assertTrue(issubclass(BuildFailed, RuntimeError))

    def test_name(self):
        self.assertEqual(BuildFailed.__name__, "BuildFailed")
        self.assertEqual(BuildFailed.__module__, "pyocctlite.errors")

    def test_raised(self):
        box = _box()
        with self.assertRaises(BuildFailed):
            box.fillet(box.edges(), 10.0)


if __name__ == "__main__":
    unittest.main()
