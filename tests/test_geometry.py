import unittest

from pyocctlite.geometry import Point, Point2D, Vector, Vector2D, Circle


class TestPoint2D(unittest.TestCase):

    def test_by_xyz(self):
        p = Point2D.by_xy(1, 2)
        self.assertEqual(p.x, 1.)
        self.assertEqual(p.y, 2.)


class TestVector2D(unittest.TestCase):

    def test_by_xy(self):
        v = Vector2D.by_xy(1, 2)
        self.assertEqual(v.x, 1.)
        self.assertEqual(v.y, 2.)
        self.assertEqual(v.magnitude, 2.23606797749979)


class TestPoint(unittest.TestCase):

    def test_by_xyz(self):
        p = Point.by_xyz(1, 2, 3)
        self.assertEqual(p.x, 1.)
        self.assertEqual(p.y, 2.)
        self.assertEqual(p.z, 3.)


class TestVector(unittest.TestCase):

    def test_by_xy(self):
        v = Vector.by_xyz(1, 2, 3)
        self.assertEqual(v.x, 1.)
        self.assertEqual(v.y, 2.)
        self.assertEqual(v.z, 3.)
        self.assertEqual(v.magnitude, 3.7416573867739413)

class TestCircle(unittest.TestCase):

    def test_by_radius(self):
        c = Circle.by_radius(1.)
        self.assertEqual(c.radius, 1.)


if __name__ == '__main__':
    unittest.main()
