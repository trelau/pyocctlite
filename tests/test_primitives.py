import unittest

from pyocctlite.geometry import Point, Vector
from pyocctlite.primitives import Cylinder
from pyocctlite.topology import Face


class TestCylinder(unittest.TestCase):

    def _assert_valid(self, c: Cylinder):
        self.assertIsInstance(c, Cylinder)
        faces = set(c.faces())
        for f in (c.bottom_face, c.top_face, c.lateral_face):
            self.assertIsInstance(f, Face)
            self.assertIn(f, faces)

    def test_by_size(self):
        c = Cylinder.by_size(1., 2.)
        self._assert_valid(c)
        self.assertAlmostEqual(c.volume, 2. * 3.141592653589793, places=6)
        self.assertNotEqual(c.bottom_face, c.top_face)

    def test_copy(self):
        c = Cylinder.by_size(1., 2.)
        result = c.copy()
        self._assert_valid(result)
        self.assertNotEqual(result, c)
        self.assertAlmostEqual(result.volume, c.volume)

    def test_mirror(self):
        c = Cylinder.by_size(1., 2.)
        result = c.mirror(Point.by_xyz(0, 0, 5), Vector.by_xyz(0, 0, 1))
        self._assert_valid(result)
        self.assertAlmostEqual(result.volume, c.volume)
        self.assertAlmostEqual(result.top_face.area, c.top_face.area)


if __name__ == '__main__':
    unittest.main()
