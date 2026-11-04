import unittest

from pyocctlite.geometry import (
    Circle,
    Curve2D,
    CylindricalSurface,
    Ellipse2D,
    Frame,
    Frame2D,
    Line,
    Point,
    Point2D,
    Surface,
    Transform,
    TrimmedCurve2D,
    Vector,
    Vector2D,
)


class TestPoint2D(unittest.TestCase):

    def test_by_xyz(self):
        p = Point2D.by_xy(1, 2)
        self.assertEqual(p.x, 1.)
        self.assertEqual(p.y, 2.)

    def test_is_equal(self):
        p = Point2D.by_xy(1, 2)
        self.assertTrue(p.is_equal(Point2D.by_xy(1, 2)))
        self.assertFalse(p.is_equal(Point2D.by_xy(1, 2.1)))


class TestVector2D(unittest.TestCase):

    def test_by_xy(self):
        v = Vector2D.by_xy(1, 2)
        self.assertEqual(v.x, 1.)
        self.assertEqual(v.y, 2.)
        self.assertEqual(v.magnitude, 2.23606797749979)

    def test_scaled(self):
        v = Vector2D.by_xy(1, 2).scaled(2)
        self.assertEqual(v.x, 2.)
        self.assertEqual(v.y, 4.)


class TestPoint(unittest.TestCase):

    def test_by_xyz(self):
        p = Point.by_xyz(1, 2, 3)
        self.assertEqual(p.x, 1.)
        self.assertEqual(p.y, 2.)
        self.assertEqual(p.z, 3.)

    def test_is_equal(self):
        p = Point.by_xyz(1, 2, 3)
        self.assertTrue(p.is_equal(Point.by_xyz(1, 2, 3 + 1.0e-9)))
        self.assertFalse(p.is_equal(Point.by_xyz(1, 2, 3.1)))
        self.assertTrue(p.is_equal(Point.by_xyz(1, 2, 3.1), tol=0.2))

    def test_init_wrong_type(self):
        with self.assertRaises(TypeError):
            Point(Vector.by_xyz(1, 2, 3).ivector)


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
        line = Line.by_points(p1, p2)
        self.assertEqual(line.origin.x, 0)
        self.assertEqual(line.origin.y, 0)
        self.assertEqual(line.origin.z, 0)
        self.assertEqual(line.direction.x, 1)
        self.assertEqual(line.direction.y, 0)
        self.assertEqual(line.direction.z, 0)


class TestCircle(unittest.TestCase):

    def test_by_radius(self):
        c = Circle.by_radius(1.)
        self.assertEqual(c.radius, 1.)


if __name__ == '__main__':
    unittest.main()


class TestCurve2D(unittest.TestCase):

    def test_by_icurve2d(self):
        frame = Frame2D.by_origin(Point2D.by_xy(0, 0))
        e = Ellipse2D.by_radii(2, 1, frame)
        t = TrimmedCurve2D.by_curve(e, 0, 1)
        self.assertIsInstance(Curve2D.by_icurve2d(e.icurve), Ellipse2D)
        self.assertIsInstance(Curve2D.by_icurve2d(t.icurve), TrimmedCurve2D)

    def test_init_wrong_kind(self):
        t = TrimmedCurve2D.by_points(Point2D.by_xy(0, 0), Point2D.by_xy(1, 0))
        with self.assertRaises(TypeError):
            Ellipse2D(t.icurve)


class TestSurface(unittest.TestCase):

    def test_by_isurface(self):
        frame = Frame.by_origin(Point.by_xyz(0, 0, 0))
        s = CylindricalSurface.by_radius(1, frame)
        self.assertIsInstance(Surface.by_isurface(s.isurface), CylindricalSurface)

    def test_by_radius_default_frame(self):
        s = CylindricalSurface.by_radius(1)
        self.assertIsInstance(s, CylindricalSurface)


class TestEllipse2D(unittest.TestCase):

    def test_by_radii_default_frame(self):
        e = Ellipse2D.by_radii(2, 1)
        p = e.evaluate(0)
        self.assertAlmostEqual(p.x, 2.)
        self.assertAlmostEqual(p.y, 0.)


class TestTransform(unittest.TestCase):

    def test_by_mirror(self):
        t = Transform.by_mirror(Point.by_xyz(0, 0, 0), Vector.by_xyz(1, 0, 0))
        self.assertIsInstance(t, Transform)


class TestCurveKind(unittest.TestCase):

    def test_init_wrong_kind(self):
        line = Line.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0))
        with self.assertRaises(TypeError):
            Circle(line.icurve)
