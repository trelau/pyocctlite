import unittest

from pyocctlite.geometry import Point, Vector
from pyocctlite.topology import Compound, Edge, Face, ShapeKind, Solid, Wire


class TestEdge(unittest.TestCase):

    def test_by_points(self):
        p1 = Point.by_xyz(0, 0, 0)
        p2 = Point.by_xyz(1, 0, 0)
        e = Edge.by_points(p1, p2)
        self.assertEqual(e.kind, ShapeKind.EDGE)
        self.assertEqual(e.length, 1.)


class TestCompound(unittest.TestCase):

    def test_by_shapes(self):
        # Create multiple shapes to combine into a compound
        p1 = Point.by_xyz(0, 0, 0)
        p2 = Point.by_xyz(1, 0, 0)
        p3 = Point.by_xyz(1, 1, 0)
        p4 = Point.by_xyz(0, 1, 0)

        # Create a wire and extrude to solid
        e1 = Edge.by_points(p1, p2)
        e2 = Edge.by_points(p2, p3)
        e3 = Edge.by_points(p3, p4)
        e4 = Edge.by_points(p4, p1)

        w = Wire.by_edges([e1, e2, e3, e4])
        f = Face.by_wire(w)
        solid = f.extrude(Vector.by_xyz(0, 0, 1))

        # Create another edge
        edge = Edge.by_points(Point.by_xyz(2, 0, 0), Point.by_xyz(3, 0, 0))

        # Create compound from shapes
        compound = Compound.by_shapes([solid, edge])

        # Verify it's a compound
        self.assertEqual(compound.kind, ShapeKind.COMPOUND)

        # Verify we can access the sub-shapes
        solids = list(compound.solids())
        self.assertEqual(len(solids), 1)

        edges = list(compound.edges())
        self.assertEqual(len(edges), 13)

        # Verify mass properties
        self.assertAlmostEqual(compound.length, 13., 7)
        self.assertAlmostEqual(compound.area, 6., 7)
        self.assertAlmostEqual (compound.volume, 1., 7)


if __name__ == '__main__':
    unittest.main()
