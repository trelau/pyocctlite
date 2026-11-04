import unittest

from pyocctlite.geometry import Line, Point, Vector
from pyocctlite.topology import Compound, Edge, Face, ShapeKind, Solid, Vertex, Wire


class TestEdge(unittest.TestCase):

    def test_by_points(self):
        p1 = Point.by_xyz(0, 0, 0)
        p2 = Point.by_xyz(1, 0, 0)
        e = Edge.by_points(p1, p2)
        self.assertEqual(e.kind, ShapeKind.EDGE)
        self.assertEqual(e.length, 1.)

    def test_curve(self):
        p1 = Point.by_xyz(0, 0, 0)
        p2 = Point.by_xyz(1, 0, 0)
        e = Edge.by_points(p1, p2)
        c = e.curve
        p = c.evaluate(0.5)
        self.assertIsInstance(c, Line)
        self.assertEqual(p.x, 0.5)
        self.assertEqual(p.y, 0.)
        self.assertEqual(p.z, 0.)


    def test_init_wrong_kind(self):
        e = Edge.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0))
        w = Wire.by_edge(e)
        with self.assertRaises(TypeError):
            Edge(w.ishape)


class TestWire(unittest.TestCase):

    def test_by_edge_wrong_kind(self):
        e = Edge.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0))
        w = Wire.by_edge(e)
        with self.assertRaises(TypeError):
            Wire.by_edge(w)


class TestShape(unittest.TestCase):

    def _box(self) -> Solid:
        pts = [Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0),
               Point.by_xyz(1, 1, 0), Point.by_xyz(0, 1, 0)]
        edges = [Edge.by_points(pts[i], pts[(i + 1) % 4]) for i in range(4)]
        f = Face.by_wire(Wire.by_edges(edges))
        return f.extrude(Vector.by_xyz(0, 0, 1))

    def test_fillet(self):
        box = self._box()
        result = box.fillet(box.edges()[0], 0.1)
        self.assertEqual(len(result.solids()), 1)
        self.assertLess(result.volume, box.volume)

    def test_fillet_fails(self):
        box = self._box()
        with self.assertRaises(RuntimeError):
            box.fillet(box.edges(), 10.)

    def test_eq_hash(self):
        box = self._box()
        edges = list(box.edges())
        explored = list(box.explore(Edge))
        self.assertEqual(edges[0], Edge(edges[0].ishape))
        self.assertNotEqual(edges[0], edges[1])
        self.assertEqual(len(set(explored)), len(edges))

    def test_export_step_fails(self):
        box = self._box()
        with self.assertRaises(RuntimeError):
            box.export_step('missing_dir/does/not/exist/box.step')

    def test_mirror(self):
        box = self._box()
        result = box.mirror(Point.by_xyz(0, 0, 0), Vector.by_xyz(1, 0, 0))
        self.assertIsInstance(result, Solid)
        self.assertAlmostEqual(result.volume, box.volume)

    def test_copy(self):
        e = Edge.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0))
        result = e.copy()
        self.assertIsInstance(result, Edge)
        self.assertNotEqual(result, e)
        self.assertAlmostEqual(result.length, 1.)


class TestMapExplore(unittest.TestCase):

    def _box(self) -> Solid:
        return TestShape()._box()

    def test_map(self):
        box = self._box()
        faces = box.map(Face)
        self.assertEqual(len(faces), 6)
        self.assertTrue(all(isinstance(f, Face) for f in faces))

    def test_explore_ignore(self):
        box = self._box()
        self.assertEqual(len(list(box.explore(Vertex))), 48)
        self.assertEqual(len(list(box.explore(Vertex, ignore=Edge))), 0)

    def test_map_composite_rejected(self):
        from pyocctlite.primitives import Cylinder
        with self.assertRaises(TypeError):
            self._box().map(Cylinder)


class TestExtrude(unittest.TestCase):

    def test_kinds(self):
        p1, p2 = Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0)
        e = Edge.by_points(p1, p2)
        self.assertIsInstance(e.extrude(Vector.by_xyz(0, 1, 0)), Face)


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
        self.assertAlmostEqual(compound.volume, 1., 7)


if __name__ == '__main__':
    unittest.main()
