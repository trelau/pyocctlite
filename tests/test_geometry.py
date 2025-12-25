import unittest

from pyocctlite.geometry import Circle, Line, Point, Point2D, Vector, Vector2D


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


class TestLine(unittest.TestCase):

    def test_by_points(self):
        p1 = Point.by_xyz(0, 0, 0)
        p2 = Point.by_xyz(10, 0, 0)
        l = Line.by_points(p1, p2)
        self.assertEqual(l.origin.x, 0)
        self.assertEqual(l.origin.y, 0)
        self.assertEqual(l.origin.z, 0)
        self.assertEqual(l.direction.x, 1)
        self.assertEqual(l.direction.y, 0)
        self.assertEqual(l.direction.z, 0)


class TestCircle(unittest.TestCase):

    def test_by_radius(self):
        c = Circle.by_radius(1.)
        self.assertEqual(c.radius, 1.)


if __name__ == '__main__':
    unittest.main()
