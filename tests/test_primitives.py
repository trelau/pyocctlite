from __future__ import annotations

import math
import unittest

from pyocctlite.geometry import Axis, Frame, Point, Vector
from pyocctlite.primitives import Box, Cylinder, Sphere
from pyocctlite.topology import Face

_X_AXIS = Axis.by_vector(Point.by_xyz(0, 0, 0), Vector.by_xyz(1, 0, 0))
_Z_AXIS = Axis.by_vector(Point.by_xyz(0, 0, 0), Vector.by_xyz(0, 0, 1))


class TestBox(unittest.TestCase):
    def _assert_valid(self, b: Box):
        self.assertIsInstance(b, Box)
        faces = set(b.faces())
        named = {
            b.bottom_face,
            b.top_face,
            b.back_face,
            b.front_face,
            b.left_face,
            b.right_face,
        }
        for f in named:
            self.assertIsInstance(f, Face)
        # each name is a distinct face, and together they are all of the faces
        self.assertEqual(len(named), 6)
        self.assertEqual(named, faces)

    def _assert_on_plane(self, f: Face, x=None, y=None, z=None):
        vertices = list(f.vertices())
        self.assertEqual(len(vertices), 4)
        for v in vertices:
            if x is not None:
                self.assertAlmostEqual(v.point.x, x)
            if y is not None:
                self.assertAlmostEqual(v.point.y, y)
            if z is not None:
                self.assertAlmostEqual(v.point.z, z)

    def test_by_size(self):
        b = Box.by_size(1.0, 2.0, 3.0)
        self._assert_valid(b)
        self.assertAlmostEqual(b.volume, 6.0)
        self.assertAlmostEqual(b.area, 22.0)
        self.assertEqual(len(b.edges()), 12)
        self.assertEqual(len(b.vertices()), 8)

    def test_named_faces(self):
        b = Box.by_size(1.0, 2.0, 3.0)
        self._assert_on_plane(b.bottom_face, z=0.0)
        self._assert_on_plane(b.top_face, z=3.0)
        self._assert_on_plane(b.back_face, x=0.0)
        self._assert_on_plane(b.front_face, x=1.0)
        self._assert_on_plane(b.left_face, y=0.0)
        self._assert_on_plane(b.right_face, y=2.0)

    def test_by_size_frame(self):
        frame = Frame.by_origin(Point.by_xyz(10.0, 20.0, 30.0))
        b = Box.by_size(1.0, 2.0, 3.0, frame)
        self._assert_on_plane(b.back_face, x=10.0)
        self._assert_on_plane(b.left_face, y=20.0)
        self._assert_on_plane(b.bottom_face, z=30.0)

    def test_by_size_invalid(self):
        for size in ((0.0, 1.0, 1.0), (1.0, 0.0, 1.0), (1.0, 1.0, 0.0)):
            with self.subTest(size=size), self.assertRaises(ValueError):
                Box.by_size(*size)

    def test_copy(self):
        b = Box.by_size(1.0, 2.0, 3.0)
        result = b.copy()
        self._assert_valid(result)
        self.assertNotEqual(result, b)
        self.assertAlmostEqual(result.volume, b.volume)
        self._assert_on_plane(result.top_face, z=3.0)

    def test_mirror(self):
        b = Box.by_size(1.0, 2.0, 3.0)
        result = b.mirror(Point.by_xyz(0, 0, 5), Vector.by_xyz(0, 0, 1))
        self._assert_valid(result)
        self.assertAlmostEqual(result.volume, b.volume)
        self._assert_on_plane(result.bottom_face, z=10.0)
        self._assert_on_plane(result.top_face, z=7.0)

    def test_rotate(self):
        b = Box.by_size(1.0, 2.0, 3.0)
        result = b.rotate(_Z_AXIS, math.pi / 2.0)
        self._assert_valid(result)
        self.assertAlmostEqual(result.volume, b.volume)
        self._assert_on_plane(result.back_face, y=0.0)
        self._assert_on_plane(result.front_face, y=1.0)
        self._assert_on_plane(result.left_face, x=0.0)
        self._assert_on_plane(result.right_face, x=-2.0)
        self._assert_on_plane(result.top_face, z=3.0)


class TestSphere(unittest.TestCase):
    def _assert_valid(self, s: Sphere):
        self.assertIsInstance(s, Sphere)
        self.assertIsInstance(s.face, Face)
        self.assertEqual(set(s.faces()), {s.face})

    def test_by_size(self):
        s = Sphere.by_size(2.0)
        self._assert_valid(s)
        self.assertAlmostEqual(s.volume, 4.0 / 3.0 * math.pi * 8.0, places=6)
        self.assertAlmostEqual(s.area, 4.0 * math.pi * 4.0, places=6)

    def test_by_size_frame(self):
        frame = Frame.by_origin(Point.by_xyz(10.0, 20.0, 30.0))
        s = Sphere.by_size(2.0, frame)
        # the vertices are the poles, on the z-axis through the center
        for v in s.vertices():
            self.assertAlmostEqual(v.point.x, 10.0)
            self.assertAlmostEqual(v.point.y, 20.0)
            self.assertAlmostEqual(abs(v.point.z - 30.0), 2.0)

    def test_by_size_invalid(self):
        for radius in (0.0, -1.0, 1.0e-9, math.nan, math.inf):
            with self.subTest(radius=radius), self.assertRaises(ValueError):
                Sphere.by_size(radius)

    def test_copy(self):
        s = Sphere.by_size(2.0)
        result = s.copy()
        self._assert_valid(result)
        self.assertNotEqual(result, s)
        self.assertAlmostEqual(result.volume, s.volume)

    def test_mirror(self):
        s = Sphere.by_size(2.0)
        result = s.mirror(Point.by_xyz(0, 0, 5), Vector.by_xyz(0, 0, 1))
        self._assert_valid(result)
        self.assertAlmostEqual(result.volume, s.volume, places=6)
        for v in result.vertices():
            self.assertAlmostEqual(abs(v.point.z - 10.0), 2.0)

    def test_rotate(self):
        s = Sphere.by_size(2.0)
        result = s.rotate(_X_AXIS, math.pi / 2.0)
        self._assert_valid(result)
        self.assertAlmostEqual(result.volume, s.volume, places=6)
        # the poles move from the z-axis to the y-axis
        for v in result.vertices():
            self.assertAlmostEqual(abs(v.point.y), 2.0)
            self.assertAlmostEqual(v.point.z, 0.0)


class TestCylinder(unittest.TestCase):
    def _assert_valid(self, c: Cylinder):
        self.assertIsInstance(c, Cylinder)
        faces = set(c.faces())
        for f in (c.bottom_face, c.top_face, c.lateral_face):
            self.assertIsInstance(f, Face)
            self.assertIn(f, faces)

    def test_by_size(self):
        c = Cylinder.by_size(1.0, 2.0)
        self._assert_valid(c)
        self.assertAlmostEqual(c.volume, 2.0 * 3.141592653589793, places=6)
        self.assertNotEqual(c.bottom_face, c.top_face)

    def test_by_size_invalid(self):
        for size in ((0.0, 1.0), (-1.0, 1.0), (1.0, 0.0), (1.0, -1.0)):
            with self.subTest(size=size), self.assertRaises(ValueError):
                Cylinder.by_size(*size)

    def test_copy(self):
        c = Cylinder.by_size(1.0, 2.0)
        result = c.copy()
        self._assert_valid(result)
        self.assertNotEqual(result, c)
        self.assertAlmostEqual(result.volume, c.volume)

    def test_mirror(self):
        c = Cylinder.by_size(1.0, 2.0)
        result = c.mirror(Point.by_xyz(0, 0, 5), Vector.by_xyz(0, 0, 1))
        self._assert_valid(result)
        self.assertAlmostEqual(result.volume, c.volume)
        self.assertAlmostEqual(result.top_face.area, c.top_face.area)

    def test_rotate(self):
        c = Cylinder.by_size(1.0, 2.0)
        result = c.rotate(_X_AXIS, math.pi)
        self._assert_valid(result)
        self.assertAlmostEqual(result.volume, c.volume)
        for v in result.top_face.vertices():
            self.assertAlmostEqual(v.point.z, -2.0)


if __name__ == "__main__":
    unittest.main()
