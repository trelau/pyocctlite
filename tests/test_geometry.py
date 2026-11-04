import math
import unittest

from pyocctlite._occtlite import ICurve2D
from pyocctlite.geometry import (
    Axis,
    Circle,
    Curve,
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
    TrimmedCurve,
    TrimmedCurve2D,
    Vector,
    Vector2D,
)


class TestPoint2D(unittest.TestCase):
    def test_by_xy(self):
        p = Point2D.by_xy(1, 2)
        self.assertAlmostEqual(p.x, 1.0)
        self.assertAlmostEqual(p.y, 2.0)

    def test_is_equal(self):
        p = Point2D.by_xy(1, 2)
        self.assertTrue(p.is_equal(Point2D.by_xy(1, 2)))
        self.assertFalse(p.is_equal(Point2D.by_xy(1, 2.1)))
        self.assertTrue(p.is_equal(Point2D.by_xy(1, 2.1), tol=0.2))

    def test_init_wrong_type(self):
        with self.assertRaises(TypeError):
            Point2D(Vector2D.by_xy(1, 2).ivector)


class TestVector2D(unittest.TestCase):
    def test_by_xy(self):
        v = Vector2D.by_xy(1, 2)
        self.assertAlmostEqual(v.x, 1.0)
        self.assertAlmostEqual(v.y, 2.0)
        self.assertAlmostEqual(v.magnitude, math.sqrt(5.0))

    def test_scaled(self):
        v = Vector2D.by_xy(1, 2).scaled(2)
        self.assertAlmostEqual(v.x, 2.0)
        self.assertAlmostEqual(v.y, 4.0)


class TestFrame2D(unittest.TestCase):
    def test_by_origin(self):
        f = Frame2D.by_origin(Point2D.by_xy(1, 2))
        self.assertAlmostEqual(f.x_direction.x, 1.0)
        self.assertAlmostEqual(f.x_direction.y, 0.0)
        self.assertAlmostEqual(f.y_direction.x, 0.0)
        self.assertAlmostEqual(f.y_direction.y, 1.0)

    def test_by_vector(self):
        f = Frame2D.by_vector(Point2D.by_xy(0, 0), Vector2D.by_xy(0, 2))
        self.assertAlmostEqual(f.x_direction.x, 0.0)
        self.assertAlmostEqual(f.x_direction.y, 1.0)
        self.assertAlmostEqual(f.y_direction.x, -1.0)
        self.assertAlmostEqual(f.y_direction.y, 0.0)


class TestCurve2D(unittest.TestCase):
    def test_by_icurve2d(self):
        e = Ellipse2D.by_radii(2, 1)
        t = TrimmedCurve2D.by_curve(e, 0, 1)
        self.assertIsInstance(Curve2D.by_icurve2d(e.icurve), Ellipse2D)
        self.assertIsInstance(Curve2D.by_icurve2d(t.icurve), TrimmedCurve2D)

    def test_by_icurve2d_unsupported(self):
        # 2D lines have no Python class yet
        icurve = ICurve2D.MakeLine(Point2D.by_xy(0, 0).ipoint, Point2D.by_xy(1, 0).ipoint)
        with self.assertRaises(NotImplementedError):
            Curve2D.by_icurve2d(icurve)


class TestEllipse2D(unittest.TestCase):
    def test_by_radii(self):
        frame = Frame2D.by_origin(Point2D.by_xy(1, 0))
        e = Ellipse2D.by_radii(2, 1, frame)
        p = e.evaluate(math.pi / 2.0)
        self.assertAlmostEqual(p.x, 1.0)
        self.assertAlmostEqual(p.y, 1.0)

    def test_by_radii_default_frame(self):
        p = Ellipse2D.by_radii(2, 1).evaluate(0)
        self.assertAlmostEqual(p.x, 2.0)
        self.assertAlmostEqual(p.y, 0.0)

    def test_init_wrong_kind(self):
        t = TrimmedCurve2D.by_points(Point2D.by_xy(0, 0), Point2D.by_xy(1, 0))
        with self.assertRaises(TypeError):
            Ellipse2D(t.icurve)


class TestTrimmedCurve2D(unittest.TestCase):
    def test_by_curve(self):
        t = TrimmedCurve2D.by_curve(Ellipse2D.by_radii(2, 1), 0, math.pi)
        p = t.evaluate(math.pi)
        self.assertAlmostEqual(p.x, -2.0)
        self.assertAlmostEqual(p.y, 0.0)

    def test_by_points(self):
        t = TrimmedCurve2D.by_points(Point2D.by_xy(0, 0), Point2D.by_xy(3, 4))
        p = t.evaluate(5.0)
        self.assertAlmostEqual(p.x, 3.0)
        self.assertAlmostEqual(p.y, 4.0)


class TestPoint(unittest.TestCase):
    def test_by_xyz(self):
        p = Point.by_xyz(1, 2, 3)
        self.assertAlmostEqual(p.x, 1.0)
        self.assertAlmostEqual(p.y, 2.0)
        self.assertAlmostEqual(p.z, 3.0)

    def test_is_equal(self):
        p = Point.by_xyz(1, 2, 3)
        self.assertTrue(p.is_equal(Point.by_xyz(1, 2, 3 + 1.0e-9)))
        self.assertFalse(p.is_equal(Point.by_xyz(1, 2, 3.1)))
        self.assertTrue(p.is_equal(Point.by_xyz(1, 2, 3.1), tol=0.2))

    def test_init_wrong_type(self):
        with self.assertRaises(TypeError):
            Point(Vector.by_xyz(1, 2, 3).ivector)


class TestVector(unittest.TestCase):
    def test_by_xyz(self):
        v = Vector.by_xyz(1, 2, 3)
        self.assertAlmostEqual(v.x, 1.0)
        self.assertAlmostEqual(v.y, 2.0)
        self.assertAlmostEqual(v.z, 3.0)
        self.assertAlmostEqual(v.magnitude, math.sqrt(14.0))

    def test_scaled(self):
        v = Vector.by_xyz(1, 2, 3).scaled(-2)
        self.assertAlmostEqual(v.x, -2.0)
        self.assertAlmostEqual(v.y, -4.0)
        self.assertAlmostEqual(v.z, -6.0)


class TestFrame(unittest.TestCase):
    def test_by_origin(self):
        f = Frame.by_origin(Point.by_xyz(1, 2, 3))
        for d, expected in [
            (f.x_direction, (1, 0, 0)),
            (f.y_direction, (0, 1, 0)),
            (f.z_direction, (0, 0, 1)),
        ]:
            self.assertAlmostEqual(d.x, expected[0])
            self.assertAlmostEqual(d.y, expected[1])
            self.assertAlmostEqual(d.z, expected[2])


class TestAxis(unittest.TestCase):
    def test_properties(self):
        f = Frame.by_origin(Point.by_xyz(1, 2, 3))
        a = Axis(f.iframe.Axis())
        self.assertTrue(a.origin.is_equal(Point.by_xyz(1, 2, 3)))
        self.assertAlmostEqual(a.direction.z, 1.0)

    def test_init_wrong_type(self):
        with self.assertRaises(TypeError):
            Axis(Point.by_xyz(0, 0, 0).ipoint)


class TestTransform(unittest.TestCase):
    def test_by_mirror(self):
        t = Transform.by_mirror(Point.by_xyz(0, 0, 0), Vector.by_xyz(1, 0, 0))
        self.assertIsInstance(t, Transform)


class TestCurve(unittest.TestCase):
    def test_by_icurve(self):
        line = Line.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0))
        self.assertIsInstance(Curve.by_icurve(line.icurve), Line)
        self.assertIsInstance(Curve.by_icurve(Circle.by_radius(1.0).icurve), Circle)

    def test_evaluate(self):
        line = Line.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(10, 0, 0))
        self.assertTrue(line.evaluate(5.0).is_equal(Point.by_xyz(5, 0, 0)))


class TestLine(unittest.TestCase):
    def test_by_points(self):
        line = Line.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(10, 0, 0))
        self.assertTrue(line.origin.is_equal(Point.by_xyz(0, 0, 0)))
        self.assertAlmostEqual(line.direction.x, 1.0)
        self.assertAlmostEqual(line.direction.y, 0.0)
        self.assertAlmostEqual(line.direction.z, 0.0)

    def test_init_wrong_kind(self):
        with self.assertRaises(TypeError):
            Line(Circle.by_radius(1.0).icurve)


class TestCircle(unittest.TestCase):
    def test_by_radius(self):
        c = Circle.by_radius(2.0)
        self.assertAlmostEqual(c.radius, 2.0)
        self.assertTrue(c.evaluate(0.0).is_equal(Point.by_xyz(2, 0, 0)))

    def test_by_radius_frame(self):
        c = Circle.by_radius(1.0, Frame.by_origin(Point.by_xyz(0, 0, 5)))
        self.assertAlmostEqual(c.evaluate(0.0).z, 5.0)

    def test_by_points(self):
        c = Circle.by_points(Point.by_xyz(1, 0, 0), Point.by_xyz(0, 1, 0), Point.by_xyz(-1, 0, 0))
        self.assertAlmostEqual(c.radius, 1.0)

    def test_init_wrong_kind(self):
        line = Line.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0))
        with self.assertRaises(TypeError):
            Circle(line.icurve)


class TestTrimmedCurve(unittest.TestCase):
    def test_by_circular_arc(self):
        t = TrimmedCurve.by_circular_arc(
            Point.by_xyz(1, 0, 0), Point.by_xyz(0, 1, 0), Point.by_xyz(-1, 0, 0)
        )
        self.assertIsInstance(t, TrimmedCurve)
        self.assertTrue(t.evaluate(math.pi / 2.0).is_equal(Point.by_xyz(0, 1, 0)))


class TestSurface(unittest.TestCase):
    def test_by_isurface(self):
        s = CylindricalSurface.by_radius(1)
        self.assertIsInstance(Surface.by_isurface(s.isurface), CylindricalSurface)


class TestCylindricalSurface(unittest.TestCase):
    def test_by_radius(self):
        s = CylindricalSurface.by_radius(1, Frame.by_origin(Point.by_xyz(0, 0, 0)))
        self.assertIsInstance(s, CylindricalSurface)

    def test_by_radius_default_frame(self):
        self.assertIsInstance(CylindricalSurface.by_radius(1), CylindricalSurface)


if __name__ == "__main__":
    unittest.main()
