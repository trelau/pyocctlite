import unittest

from pyocctlite.geometry import Point
from pyocctlite.topology import Edge, ShapeKind


class TestEdge(unittest.TestCase):

    def test_by_points(self):
        p1 = Point.by_xyz(0, 0, 0)
        p2 = Point.by_xyz(1, 0, 0)
        e = Edge.by_points(p1, p2)
        self.assertEqual(e.kind, ShapeKind.EDGE)


if __name__ == '__main__':
    unittest.main()
