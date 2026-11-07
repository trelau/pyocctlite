from __future__ import annotations

import itertools
import math
import unittest
from collections.abc import Sequence

from pyocctlite.errors import BuildFailed, KindMismatch
from pyocctlite.geometry import (
    Axis,
    BoundingBox,
    BSplineCurve,
    Circle,
    CylindricalSurface,
    Line,
    Point,
    Point2D,
    Transform,
    TrimmedCurve2D,
    Vector,
)
from pyocctlite.primitives import Box, Sphere
from pyocctlite.topology import (
    ChamferShape,
    Compound,
    CompSolid,
    CutShapes,
    Edge,
    ExtrudeShape,
    Face,
    FilletShape,
    IntersectShapes,
    LoftShape,
    OffsetWire,
    RevolveShape,
    Shape,
    ShapeKind,
    Shell,
    Solid,
    ThickenShape,
    TransformShape,
    UniteShapes,
    Vertex,
    Wire,
)

_Y_AXIS = Axis.by_vector(Point.by_xyz(0, 0, 0), Vector.by_xyz(0, 1, 0))
_Z_AXIS = Axis.by_vector(Point.by_xyz(0, 0, 0), Vector.by_xyz(0, 0, 1))


def _triangle() -> Wire:
    p1, p2, p3 = Point.by_xyz(0, 0, 0), Point.by_xyz(3, 0, 0), Point.by_xyz(0, 3, 0)
    return Wire.by_edges(
        [Edge.by_points(p1, p2), Edge.by_points(p2, p3), Edge.by_points(p3, p1)],
    )


def _square(x0: float = 0.0, y0: float = 0.0, z: float = 0.0) -> Wire:
    pts = [
        Point.by_xyz(x0, y0, z),
        Point.by_xyz(x0 + 1, y0, z),
        Point.by_xyz(x0 + 1, y0 + 1, z),
        Point.by_xyz(x0, y0 + 1, z),
    ]
    return Wire.by_edges([Edge.by_points(pts[i], pts[(i + 1) % 4]) for i in range(4)])


def _box(x0: float = 0.0, y0: float = 0.0, z0: float = 0.0) -> Solid:
    """Unit cube with its minimum corner at (x0, y0, z0)."""
    return _box_and_top(x0, y0, z0)[0]


def _box_and_top(x0: float = 0.0, y0: float = 0.0, z0: float = 0.0) -> tuple[Solid, Face]:
    tool = ExtrudeShape(Face.by_wire(_square(x0, y0, z0)), Vector.by_xyz(0, 0, 1))
    solid = tool.shape()
    assert isinstance(solid, Solid)
    return solid, tool.last_shape()


class TestShape(unittest.TestCase):
    def test_kind(self):
        self.assertEqual(_box().kind, ShapeKind.SOLID)

    def test_mass_properties(self):
        box = _box()
        self.assertAlmostEqual(box.length, 12.0)
        self.assertAlmostEqual(box.area, 6.0)
        self.assertAlmostEqual(box.volume, 1.0)

    def test_is_valid(self):
        box = _box()
        self.assertTrue(box.is_valid)
        self.assertTrue(box.cut(_box(0.5, 0.5, 0.5)).is_valid)

    def test_is_valid_self_intersecting_face(self):
        pts = [Point.by_xyz(x, y, 0) for x, y in ((0, 0), (1, 1), (1, 0), (0, 1), (0, 0))]
        w = Wire.by_edges([Edge.by_points(a, b) for a, b in itertools.pairwise(pts)])
        self.assertFalse(Face.by_wire(w).is_valid)

    def test_is_valid_open_wire(self):
        pts = [Point.by_xyz(x, y, 0) for x, y in ((0, 0), (1, 0), (1, 1))]
        w = Wire.by_edges([Edge.by_points(a, b) for a, b in itertools.pairwise(pts)])
        self.assertTrue(w.is_valid)
        self.assertFalse(Face.by_wire(w).is_valid)

    def test_eq_hash(self):
        box = _box()
        edges = list(box.edges())
        self.assertEqual(edges[0], Edge(edges[0].ishape))
        self.assertNotEqual(edges[0], edges[1])
        self.assertEqual(len(set(box.explore(Edge))), len(edges))
        self.assertNotEqual(box, "not a shape")

    def test_copy(self):
        e = Edge.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0))
        result = e.copy()
        self.assertIsInstance(result, Edge)
        self.assertNotEqual(result, e)
        self.assertAlmostEqual(result.length, 1.0)

    def test_mirror(self):
        box = _box()
        result = box.mirror(Point.by_xyz(0, 0, 0), Vector.by_xyz(1, 0, 0))
        self.assertIsInstance(result, Solid)
        self.assertAlmostEqual(result.volume, box.volume)

    def test_rotate(self):
        v = Vertex.by_point(Point.by_xyz(1, 0, 5))
        result = v.rotate(_Z_AXIS, math.pi / 2.0)
        self.assertIsInstance(result, Vertex)
        self.assertTrue(result.point.is_equal(Point.by_xyz(0, 1, 5)))
        self.assertTrue(v.point.is_equal(Point.by_xyz(1, 0, 5)))

    def test_translate(self):
        v = Vertex.by_point(Point.by_xyz(1, 0, 5))
        result = v.translate(Vector.by_xyz(1, 2, 3))
        self.assertIsInstance(result, Vertex)
        self.assertTrue(result.point.is_equal(Point.by_xyz(2, 2, 8)))
        self.assertTrue(v.point.is_equal(Point.by_xyz(1, 0, 5)))

    def test_extrude(self):
        e = Edge.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0))
        f = e.extrude(Vector.by_xyz(0, 1, 0))
        self.assertIsInstance(f, Face)
        self.assertAlmostEqual(f.area, 1.0)

    def test_revolve_vertex(self):
        result = Vertex.by_point(Point.by_xyz(2, 0, 0)).revolve(_Z_AXIS)
        self.assertIsInstance(result, Edge)
        self.assertAlmostEqual(result.length, 4.0 * math.pi)

    def test_revolve_vertex_on_axis(self):
        result = Vertex.by_point(Point.by_xyz(0, 0, 1)).revolve(_Z_AXIS)
        self.assertIsInstance(result, Edge)
        self.assertAlmostEqual(result.length, 0.0)

    def test_revolve_edge(self):
        e = Edge.by_points(Point.by_xyz(1, 0, 0), Point.by_xyz(1, 0, 2))
        result = e.revolve(_Z_AXIS)
        self.assertIsInstance(result, Face)
        self.assertAlmostEqual(result.area, 4.0 * math.pi)

    def test_revolve_wire(self):
        result = _square(1.0).revolve(_Y_AXIS)
        self.assertIsInstance(result, Shell)
        self.assertAlmostEqual(result.area, 12.0 * math.pi)

    def test_revolve_face(self):
        result = Face.by_wire(_square(1.0)).revolve(_Y_AXIS)
        self.assertIsInstance(result, Solid)
        self.assertAlmostEqual(result.volume, 3.0 * math.pi)

    def test_revolve_face_touching_axis(self):
        result = Face.by_wire(_square()).revolve(_Y_AXIS)
        self.assertIsInstance(result, Solid)
        self.assertAlmostEqual(result.volume, math.pi)

    def test_revolve_shell(self):
        e = Edge.by_points(Point.by_xyz(1, 0, 0), Point.by_xyz(2, 0, 0))
        shell = Wire.by_edge(e).extrude(Vector.by_xyz(0, 0, 1))
        result = shell.revolve(_Z_AXIS)
        self.assertIsInstance(result, CompSolid)
        self.assertAlmostEqual(result.volume, 3.0 * math.pi)

    def test_revolve_crossing_axis_fails(self):
        f = Face.by_wire(_square(-0.5))
        with self.assertRaises(BuildFailed):
            f.revolve(_Y_AXIS)

    def test_revolve_solid_fails(self):
        with self.assertRaises(RuntimeError):
            _box().revolve(_Z_AXIS)

    def test_unite(self):
        result = _box().unite(_box(0.5))
        self.assertAlmostEqual(result.volume, 1.5)

    def test_cut(self):
        result = _box().cut(_box(0.5))
        self.assertAlmostEqual(result.volume, 0.5)

    def test_fillet(self):
        box = _box()
        result = box.fillet(box.edges()[0], 0.1)
        self.assertEqual(len(result.solids()), 1)
        self.assertLess(result.volume, box.volume)

    def test_fillet_many(self):
        box = _box()
        result = box.fillet(box.edges(), 0.1)
        self.assertLess(result.volume, box.volume)

    def test_edges_keyword(self):
        box = _box()
        self.assertLess(box.fillet(edges=box.edges()[0], radius=0.1).volume, box.volume)
        self.assertLess(box.chamfer(edges=box.edges()[0], distance=0.1).volume, box.volume)

    def test_fillet_fails(self):
        box = _box()
        with self.assertRaises(RuntimeError):
            box.fillet(box.edges(), 10.0)

    def test_fillet_keeps_distant_edges(self):
        box = _box()
        edge = box.edges()[0]
        distant = [e for e in box.edges() if not set(e.vertices()) & set(edge.vertices())]
        self.assertTrue(distant)
        result = box.fillet(edge, 0.1)
        for e in distant:
            self.assertIn(e, result.edges())

    def test_chamfer(self):
        box = _box()
        result = box.chamfer(box.edges()[0], 0.1)
        self.assertEqual(len(result.solids()), 1)
        self.assertAlmostEqual(result.volume, 1.0 - 0.1 * 0.1 / 2.0)

    def test_chamfer_many(self):
        box = _box()
        edges = list(box.edges())
        one = box.chamfer(edges[0], 0.1)
        result = box.chamfer(edges, 0.1)
        self.assertLess(result.volume, one.volume)

    def test_chamfer_fails(self):
        box = _box()
        for distance in (10.0, 0.0, -0.1):
            with self.subTest(distance=distance), self.assertRaises(BuildFailed):
                box.chamfer(box.edges(), distance)

    def test_chamfer_no_edges(self):
        with self.assertRaises(RuntimeError):
            _box().chamfer([], 0.1)

    def test_thicken(self):
        box, top = _box_and_top()
        result = box.thicken(-0.1, faces=[top])
        self.assertAlmostEqual(result.volume, 1.0 - 0.8 * 0.8 * 0.9, places=5)

    def test_thicken_one_face(self):
        box, top = _box_and_top()
        result = box.thicken(-0.1, faces=top)
        self.assertAlmostEqual(result.volume, 1.0 - 0.8 * 0.8 * 0.9, places=5)

    def test_thicken_faces_before_tol(self):
        box, top = _box_and_top()
        result = box.thicken(-0.1, [top], 1.0e-3)
        self.assertAlmostEqual(result.volume, 1.0 - 0.8 * 0.8 * 0.9, places=5)

    def test_thicken_empty_faces_does_not_hollow(self):
        result = _box().thicken(-0.1, [])
        self.assertAlmostEqual(result.volume, 0.8 * 0.8 * 0.8, places=5)
        self.assertEqual(len(result.faces()), 6)

    def test_export_step_fails(self):
        with self.assertRaises(RuntimeError):
            _box().export_step("missing_dir/does/not/exist/box.step")


class TestVertex(unittest.TestCase):
    def test_by_point(self):
        v = Vertex.by_point(Point.by_xyz(1, 2, 3))
        self.assertEqual(v.kind, ShapeKind.VERTEX)
        self.assertTrue(v.point.is_equal(Point.by_xyz(1, 2, 3)))

    def test_point(self):
        e = Edge.by_points(Point.by_xyz(1, 2, 3), Point.by_xyz(4, 5, 6))
        points = [v.point for v in e.vertices()]
        self.assertTrue(any(p.is_equal(Point.by_xyz(1, 2, 3)) for p in points))
        self.assertTrue(any(p.is_equal(Point.by_xyz(4, 5, 6)) for p in points))

    def test_box_corners(self):
        zs = sorted(v.point.z for v in _box(z0=2.0).vertices())
        self.assertEqual(len(zs), 8)
        for z, expected in zip(zs, [2.0] * 4 + [3.0] * 4, strict=True):
            self.assertAlmostEqual(z, expected)

    def test_init_wrong_kind(self):
        e = Edge.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0))
        with self.assertRaises(TypeError):
            Vertex(e.ishape)


class TestEdge(unittest.TestCase):
    def test_by_points(self):
        e = Edge.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0))
        self.assertEqual(e.kind, ShapeKind.EDGE)
        self.assertAlmostEqual(e.length, 1.0)

    def test_by_vertices(self):
        v1 = Vertex.by_point(Point.by_xyz(0, 0, 0))
        v2 = Vertex.by_point(Point.by_xyz(1, 0, 0))
        e = Edge.by_vertices(v1, v2)
        self.assertEqual(e.kind, ShapeKind.EDGE)
        self.assertAlmostEqual(e.length, 1.0)
        self.assertEqual(set(e.vertices()), {v1, v2})

    def test_by_vertices_shared_in_wire(self):
        # edges sharing vertices stay the same edges in a wire
        vs = [
            Vertex.by_point(p)
            for p in (Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0), Point.by_xyz(0, 1, 0))
        ]
        edges = [Edge.by_vertices(vs[i], vs[(i + 1) % 3]) for i in range(3)]
        self.assertEqual(set(Wire.by_edges(edges).edges()), set(edges))

    def test_by_vertices_same_vertex(self):
        v = Vertex.by_point(Point.by_xyz(0, 0, 0))
        with self.assertRaises(RuntimeError):
            Edge.by_vertices(v, v)

    def test_by_curve(self):
        e = Edge.by_curve(Circle.by_radius(1.0))
        self.assertAlmostEqual(e.length, 2.0 * math.pi)

    def test_by_curve2d(self):
        # On a unit cylinder, u is the angle, so a u-span of pi is half the circumference
        segment = TrimmedCurve2D.by_points(Point2D.by_xy(0, 0), Point2D.by_xy(math.pi, 0))
        e = Edge.by_curve2d(segment, CylindricalSurface.by_radius(1.0))
        # The 3D curve is approximated from the 2D one
        self.assertAlmostEqual(e.length, math.pi, places=5)

    def test_by_circular_arc(self):
        e = Edge.by_circular_arc(
            Point.by_xyz(1, 0, 0), Point.by_xyz(0, 1, 0), Point.by_xyz(-1, 0, 0)
        )
        self.assertAlmostEqual(e.length, math.pi)

    def test_curve(self):
        e = Edge.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0))
        c = e.curve
        self.assertIsInstance(c, Line)
        assert c is not None
        self.assertTrue(c.evaluate(0.5).is_equal(Point.by_xyz(0.5, 0, 0)))

    def test_init_wrong_kind(self):
        w = Wire.by_edge(Edge.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0)))
        with self.assertRaises(TypeError):
            Edge(w.ishape)


class TestWire(unittest.TestCase):
    def test_by_edge(self):
        w = Wire.by_edge(Edge.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0)))
        self.assertEqual(len(w.edges()), 1)

    def test_by_edges(self):
        w = _square()
        self.assertEqual(len(w.edges()), 4)
        self.assertAlmostEqual(w.length, 4.0)

    def test_by_edge_wrong_kind(self):
        w = Wire.by_edge(Edge.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0)))
        with self.assertRaises(TypeError):
            Wire.by_edge(w)

    def test_combine(self):
        p1, p2, p3 = Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0), Point.by_xyz(1, 1, 0)
        w1 = Wire.by_edge(Edge.by_points(p1, p2))
        w2 = Wire.by_edge(Edge.by_points(p2, p3))
        w = w1.combine(w2)
        self.assertEqual(len(w.edges()), 2)
        self.assertAlmostEqual(w.length, 2.0)


class TestFace(unittest.TestCase):
    def test_by_wire(self):
        f = Face.by_wire(_square())
        self.assertEqual(f.kind, ShapeKind.FACE)
        self.assertAlmostEqual(f.area, 1.0)


class TestSolid(unittest.TestCase):
    def test_by_loft(self):
        s = Solid.by_loft([_square(z=0.0), _square(z=1.0)])
        self.assertAlmostEqual(s.volume, 1.0)

    def test_by_loft_unsupported(self):
        e = Edge.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0))
        with self.assertRaises(NotImplementedError):
            Solid.by_loft([e])


class TestCompound(unittest.TestCase):
    def test_by_shapes(self):
        edge = Edge.by_points(Point.by_xyz(2, 0, 0), Point.by_xyz(3, 0, 0))
        compound = Compound.by_shapes([_box(), edge])
        self.assertEqual(compound.kind, ShapeKind.COMPOUND)
        self.assertEqual(len(compound.solids()), 1)
        self.assertEqual(len(compound.edges()), 13)
        self.assertAlmostEqual(compound.length, 13.0)
        self.assertAlmostEqual(compound.area, 6.0)
        self.assertAlmostEqual(compound.volume, 1.0)


class TestBooleanTools(unittest.TestCase):
    def test_unite_shapes(self):
        # Offset in all directions: coplanar faces produce no section edges
        tool = UniteShapes(_box(), _box(0.5, 0.5, 0.5))
        self.assertAlmostEqual(tool.shape().volume, 1.875)
        self.assertTrue(tool.is_done)
        edges = tool.intersection_edges()
        self.assertTrue(edges)
        self.assertTrue(all(isinstance(e, Edge) for e in edges))

    def test_cut_shapes(self):
        tool = CutShapes(_box(), _box(0.5, 0.5, 0.5))
        self.assertAlmostEqual(tool.shape().volume, 0.875)
        self.assertTrue(tool.intersection_edges())

    def test_intersect_shapes(self):
        tool = IntersectShapes(_box(), _box(0.5, 0.5, 0.5))
        self.assertAlmostEqual(tool.shape().volume, 0.125)
        self.assertTrue(tool.intersection_edges())

    def test_tolerance_treats_near_faces_as_touching(self):
        # The second box stands a hair clear of the first, so a coarse tolerance makes them touch
        a, b = _box(), _box(1.0 + 1.0e-5, 0.0, 0.0)
        self.assertEqual(len(a.unite(b).solids()), 2)
        self.assertEqual(len(a.unite(b, 1.0e-3).solids()), 1)
        self.assertAlmostEqual(a.cut(_box(0.5, 0.5, 0.5), 1.0e-3).volume, 0.875, places=2)
        self.assertAlmostEqual(a.intersect(_box(0.5, 0.5, 0.5), 1.0e-3).volume, 0.125, places=2)

    def test_lists(self):
        a, b, c = _box(), _box(0.5, 0.5, 0.5), _box(-0.5, -0.5, -0.5)
        self.assertAlmostEqual(a.cut([b, c]).volume, 0.75)
        self.assertAlmostEqual(a.unite([b, c]).volume, 2.75)
        self.assertAlmostEqual(UniteShapes([a, b], c).shape().volume, 2.75)

    def test_intersect_list_acts_as_union(self):
        a, b, c = _box(), _box(0.5, 0.5, 0.5), _box(-0.5, -0.5, -0.5)
        self.assertAlmostEqual(a.intersect([b, c]).volume, 0.25)

    def test_intersect_disjoint_is_empty(self):
        result = _box().intersect(_box(5.0, 5.0, 5.0))
        self.assertEqual(len(result.solids()), 0)

    def test_history_after_cut(self):
        a, b = _box(), _box(0.5, 0.5, 0.5)
        tool = CutShapes(a, b)
        tool.build()
        self.assertTrue(tool.is_done)
        modified = [tool.modified_shapes(f) for f in a.faces()]
        self.assertEqual(sum(1 for m in modified if m), 3)
        self.assertFalse(any(tool.is_deleted(f) for f in a.faces()))

    def test_history_contained_shape_is_deleted(self):
        from pyocctlite.primitives import Box

        outer, inner = Box.by_size(4.0, 4.0, 4.0), _box(1.0, 1.0, 1.0)
        tool = UniteShapes(outer, inner)
        self.assertTrue(all(tool.is_deleted(f) for f in inner.faces()))
        self.assertFalse(any(tool.is_deleted(f) for f in outer.faces()))

    def test_empty_list_fails(self):
        with self.assertRaises(BuildFailed):
            _box().cut([])


class TestShapeToolHistory(unittest.TestCase):
    def test_fillet_history(self):
        box = _box()
        e = box.edges()[0]
        tool = FilletShape(box)
        tool.add_edge(e, 0.1)
        self.assertFalse(tool.is_done)
        tool.build()
        self.assertTrue(tool.is_done)
        self.assertTrue(tool.is_deleted(e))
        self.assertEqual(len(tool.generated_shapes(e)), 1)
        self.assertEqual(sum(1 for f in box.faces() if tool.modified_shapes(f)), 4)

    def test_build_reports_failure_without_raising(self):
        box = _box()
        tool = FilletShape(box)
        tool.add_edge(box.edges()[0], 50.0)
        tool.build()
        self.assertFalse(tool.is_done)


class TestExtrudeShape(unittest.TestCase):
    def test_first_last_of_sub_shape(self):
        f = Face.by_wire(_square())
        e = f.edges()[0]
        tool = ExtrudeShape(f, Vector.by_xyz(0, 0, 2))
        self.assertEqual(tool.first_shape(e), e)
        last = tool.last_shape(e)
        self.assertIsInstance(last, Edge)
        self.assertNotEqual(last, e)
        self.assertAlmostEqual(last.length, e.length)
        for v in last.vertices():
            self.assertAlmostEqual(v.point.z, 2.0)

    def test_last_of_foreign_shape_raises(self):
        tool = ExtrudeShape(Face.by_wire(_square()), Vector.by_xyz(0, 0, 2))
        with self.assertRaises(RuntimeError):
            tool.last_shape(_box().edges()[0])

    def test_first_last_shape(self):
        f = Face.by_wire(_square())
        tool = ExtrudeShape(f, Vector.by_xyz(0, 0, 2))
        self.assertIsInstance(tool.shape(), Solid)
        self.assertEqual(tool.first_shape(), f)
        last = tool.last_shape()
        self.assertIsInstance(last, Face)
        self.assertNotEqual(last, f)
        self.assertIn(last, set(tool.shape().faces()))
        for v in last.vertices():
            self.assertAlmostEqual(v.point.z, 2.0)

    def test_generated_shapes(self):
        e = Edge.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0))
        tool = ExtrudeShape(e, Vector.by_xyz(0, 1, 0))
        generated = tool.generated_shapes(e)
        self.assertEqual(len(generated), 1)
        self.assertIsInstance(generated[0], Face)


class TestRevolveShape(unittest.TestCase):
    def test_shape(self):
        tool = RevolveShape(Face.by_wire(_square(1.0)), _Y_AXIS)
        self.assertIsInstance(tool.shape(), Solid)
        self.assertTrue(tool.is_done)

    def test_generated_shapes(self):
        v1 = Vertex.by_point(Point.by_xyz(1, 0, 0))
        v2 = Vertex.by_point(Point.by_xyz(1, 0, 2))
        e = Edge.by_vertices(v1, v2)
        tool = RevolveShape(e, _Z_AXIS)

        # a vertex generates a circular edge of the result
        circle = tool.generated_shapes(v2)[0]
        self.assertIsInstance(circle, Edge)
        self.assertAlmostEqual(circle.length, 2.0 * math.pi)
        self.assertIn(circle, set(tool.shape().edges()))

        # an edge generates a face of the result
        face = tool.generated_shapes(e)[0]
        self.assertIsInstance(face, Face)
        self.assertEqual(face, tool.shape())


def _distant_edges() -> tuple[Solid, Edge, Edge]:
    """Unit cube and two of its edges that share no vertex."""
    box = _box()
    e1 = box.edges()[0]
    e2 = next(e for e in box.edges() if not set(e.vertices()) & set(e1.vertices()))
    return box, e1, e2


class TestFilletShape(unittest.TestCase):
    def test_radius_per_edge(self):
        box, e1, e2 = _distant_edges()
        tool = FilletShape(box)
        tool.add_edge(e1, 0.1)
        tool.add_edge(e2, 0.2)
        removed = (1.0 - math.pi / 4.0) * (0.1**2 + 0.2**2)
        self.assertAlmostEqual(tool.shape().volume, 1.0 - removed)
        self.assertTrue(tool.is_done)

    def test_generated_shapes(self):
        box, edge, _ = _distant_edges()
        tool = FilletShape(box)
        tool.add_edge(edge, 0.1)
        face = tool.generated_shapes(edge)[0]
        self.assertIsInstance(face, Face)
        self.assertIn(face, set(tool.shape().faces()))
        self.assertAlmostEqual(face.area, math.pi / 2.0 * 0.1)

    def test_fails_when_requested(self):
        box, edge, _ = _distant_edges()
        tool = FilletShape(box)
        tool.add_edge(edge, -0.1)
        with self.assertRaises(BuildFailed):
            tool.shape()


class TestChamferShape(unittest.TestCase):
    def test_distance_per_edge(self):
        box, e1, e2 = _distant_edges()
        tool = ChamferShape(box)
        tool.add_edge(e1, 0.1)
        tool.add_edge(e2, 0.2)
        self.assertAlmostEqual(tool.shape().volume, 1.0 - (0.1**2 + 0.2**2) / 2.0)
        self.assertTrue(tool.is_done)

    def test_generated_shapes(self):
        box, edge, _ = _distant_edges()
        tool = ChamferShape(box)
        tool.add_edge(edge, 0.1)
        face = tool.generated_shapes(edge)[0]
        self.assertIsInstance(face, Face)
        self.assertIn(face, set(tool.shape().faces()))
        self.assertAlmostEqual(face.area, math.sqrt(2.0) * 0.1)

    def test_fails_when_requested(self):
        box, edge, _ = _distant_edges()
        tool = ChamferShape(box)
        tool.add_edge(edge, -0.1)
        with self.assertRaises(BuildFailed):
            tool.shape()


class TestThickenShape(unittest.TestCase):
    def test_faces(self):
        box, top = _box_and_top()
        tool = ThickenShape(box, -0.1, faces=[top])
        self.assertAlmostEqual(tool.shape().volume, 1.0 - 0.8 * 0.8 * 0.9, places=5)

    def test_one_face(self):
        box, top = _box_and_top()
        tool = ThickenShape(box, -0.1, faces=top)
        self.assertAlmostEqual(tool.shape().volume, 1.0 - 0.8 * 0.8 * 0.9, places=5)


class TestEdgeByInterpolation(unittest.TestCase):
    def test_passes_through_points_and_keeps_the_curve_kind(self):
        points = [Point.by_xyz(0, 0, 0), Point.by_xyz(1, 1, 0), Point.by_xyz(2, 0, 0)]
        edge = Edge.by_interpolation(points)
        self.assertIsInstance(edge.curve, BSplineCurve)
        ends = [v.point for v in edge.vertices()]
        self.assertTrue(ends[0].is_equal(points[0]))
        self.assertTrue(ends[1].is_equal(points[2]))

    def test_too_few_points(self):
        with self.assertRaises(RuntimeError):
            Edge.by_interpolation([Point.by_xyz(0, 0, 0)])


class TestOffsetWire(unittest.TestCase):
    def setUp(self):
        self.corners = [
            Point.by_xyz(0, 0, 0),
            Point.by_xyz(100, 0, 0),
            Point.by_xyz(100, 100, 0),
            Point.by_xyz(0, 100, 0),
        ]
        self.spine = Face.by_wire(
            self._square(
                [
                    Point.by_xyz(-500, -500, 0),
                    Point.by_xyz(500, -500, 0),
                    Point.by_xyz(500, 500, 0),
                    Point.by_xyz(-500, 500, 0),
                ]
            )
        )
        self.line = Wire.by_edge(Edge.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(100, 0, 0)))

    def _square(self, corners):
        pairs = zip(corners, corners[1:] + corners[:1], strict=True)
        return Wire.by_edges([Edge.by_points(a, b) for a, b in pairs])

    def _area(self, shape):
        return Face.by_wire(shape.wires()[0]).area

    def test_sign_does_not_depend_on_wire_direction(self):
        for corners in (self.corners, self.corners[::-1]):
            wire = self._square(corners)
            self.assertAlmostEqual(self._area(wire.offset(-10.0)), 6400.0, places=6)
            self.assertAlmostEqual(
                self._area(wire.offset(10.0)), 14000.0 + math.pi * 100.0, places=6
            )

    def test_straight_wire_on_a_spine_becomes_a_rounded_strip_after_the_boundary(self):
        boundary, strip = self.line.offset(-2.0, self.spine).wires()
        self.assertAlmostEqual(Face.by_wire(boundary).area, 992016.0, places=6)
        self.assertAlmostEqual(Face.by_wire(strip).area, 400.0 + math.pi * 4.0, places=6)

    def test_positive_distance_on_a_spine_drops_an_open_wire(self):
        self.assertEqual(len(self.line.offset(2.0, self.spine).wires()), 1)

    def test_sign_on_a_spine_depends_on_wire_direction(self):
        forward = self._square(self.corners).offset(10.0, self.spine).wires()[1]
        backward = self._square(self.corners[::-1]).offset(10.0, self.spine).wires()[1]
        self.assertAlmostEqual(Face.by_wire(forward).area, 14000.0 + math.pi * 100.0, places=6)
        self.assertAlmostEqual(Face.by_wire(backward).area, 6400.0, places=6)

    def test_spine_must_be_a_face(self):
        with self.assertRaises(KindMismatch):
            OffsetWire(self.line, -2.0, self._square(self.corners))

    def test_inset_past_the_middle_leaves_no_wire(self):
        self.assertEqual(len(self._square(self.corners).offset(-60.0).wires()), 0)

    def test_spline_wire(self):
        points = [Point.by_xyz(100 * math.cos(a / 8), 50 * math.sin(a / 8), 0) for a in range(26)]
        spline = Edge.by_interpolation(points)
        closing = Edge.by_points(points[-1], points[0])
        wire = Wire.by_edges([spline, closing])
        self.assertLess(self._area(wire.offset(-5.0)), Face.by_wire(wire).area)
        self.assertTrue(wire.offset(-5.0).is_valid)

    def test_tool_generates_edges_from_input_edge(self):
        wire = self._square(self.corners)
        tool = OffsetWire(wire, -10.0)
        self.assertTrue(tool.generated_shapes(wire.edges()[0]))


class TestLoftShape(unittest.TestCase):
    def test_add_wire(self):
        tool = LoftShape(is_solid=True)
        tool.add_wire(_square(z=0.0))
        tool.add_wire(_square(z=2.0))
        self.assertAlmostEqual(tool.shape().volume, 2.0)


class TestIsEqual(unittest.TestCase):
    def test_orientation_distinguishes(self):
        box = _box()
        edges = list(box.explore(Edge))
        pairs = [(a, b) for i, a in enumerate(edges) for b in edges[:i] if a == b]
        self.assertEqual(len(pairs), 12)
        self.assertTrue(all(not a.is_equal(b) for a, b in pairs))
        self.assertTrue(box.is_equal(box))


class TestBoundingBox(unittest.TestCase):
    def test_box(self):
        bb = Box.by_size(1, 2, 3).translate(Vector.by_xyz(10, 20, 30)).bounding_box
        self.assertTrue(bb.min_point.is_equal(Point.by_xyz(10, 20, 30)))
        self.assertTrue(bb.max_point.is_equal(Point.by_xyz(11, 22, 33)))
        self.assertAlmostEqual(bb.dx, 1.0)
        self.assertAlmostEqual(bb.dy, 2.0)
        self.assertAlmostEqual(bb.dz, 3.0)
        self.assertTrue(bb.center.is_equal(Point.by_xyz(10.5, 21, 31.5)))

    def test_aligned_with_global_axes(self):
        bb = Box.by_size(1, 1, 1).rotate(_Z_AXIS, math.pi / 4.0).bounding_box
        self.assertAlmostEqual(bb.dx, math.sqrt(2.0))
        self.assertAlmostEqual(bb.dy, math.sqrt(2.0))
        self.assertAlmostEqual(bb.dz, 1.0)

    def test_curved(self):
        bb = Sphere.by_size(2.0).bounding_box
        self.assertTrue(bb.min_point.is_equal(Point.by_xyz(-2, -2, -2)))
        self.assertTrue(bb.max_point.is_equal(Point.by_xyz(2, 2, 2)))

    def test_arc_uses_edge_range(self):
        p1, p2, p3 = Point.by_xyz(1, 0, 0), Point.by_xyz(0, 1, 0), Point.by_xyz(-1, 0, 0)
        bb = Edge.by_circular_arc(p1, p2, p3).bounding_box
        self.assertTrue(bb.min_point.is_equal(Point.by_xyz(-1, 0, 0)))
        self.assertTrue(bb.max_point.is_equal(Point.by_xyz(1, 1, 0)))

    def test_sub_shape(self):
        bb = Box.by_size(1, 2, 3).top_face.bounding_box
        self.assertAlmostEqual(bb.dz, 0.0)
        self.assertAlmostEqual(bb.min_point.z, 3.0)

    def test_vertex(self):
        bb = Vertex.by_point(Point.by_xyz(1, 2, 3)).bounding_box
        self.assertTrue(bb.min_point.is_equal(Point.by_xyz(1, 2, 3)))
        self.assertTrue(bb.max_point.is_equal(Point.by_xyz(1, 2, 3)))

    def test_empty_raises_when_read(self):
        box = Compound.by_shapes([]).bounding_box
        with self.assertRaises(RuntimeError):
            _ = box.min_point

    def test_init_wrong_type(self):
        with self.assertRaises(TypeError):
            BoundingBox(Point.by_xyz(0, 0, 0).ipoint)  # type: ignore[arg-type]


class TestCentroid(unittest.TestCase):
    def test_solid(self):
        c = Box.by_size(1, 2, 3).translate(Vector.by_xyz(10, 20, 30)).centroid
        self.assertTrue(c.is_equal(Point.by_xyz(10.5, 21, 31.5)))

    def test_hollow_solid_uses_volume(self):
        box = Box.by_size(2, 2, 2)
        c = box.thicken(-0.1, faces=box.top_face).centroid
        outer, inner = 8.0, 1.8 * 1.8 * 1.9
        self.assertAlmostEqual(c.z, (outer * 1.0 - inner * 1.05) / (outer - inner), places=5)

    def test_negative_volume(self):
        face = Face.by_wire(_triangle())
        solid = face.thicken(0.5)
        self.assertLess(solid.volume, 0.0)
        self.assertTrue(solid.centroid.is_equal(Point.by_xyz(1, 1, 0.25), tol=1.0e-5))

    def test_face(self):
        self.assertTrue(Face.by_wire(_triangle()).centroid.is_equal(Point.by_xyz(1, 1, 0)))

    def test_wire_uses_length(self):
        c = _triangle().centroid
        expected = (3.0 * 1.5 + 3.0 * math.sqrt(2.0) * 1.5) / (6.0 + 3.0 * math.sqrt(2.0))
        self.assertAlmostEqual(c.x, expected)
        self.assertAlmostEqual(c.y, expected)

    def test_arc(self):
        p1, p2, p3 = Point.by_xyz(1, 0, 0), Point.by_xyz(0, 1, 0), Point.by_xyz(-1, 0, 0)
        c = Edge.by_circular_arc(p1, p2, p3).centroid
        self.assertTrue(c.is_equal(Point.by_xyz(0, 2.0 / math.pi, 0), tol=1.0e-5))

    def test_vertex(self):
        v = Vertex.by_point(Point.by_xyz(1, 2, 3))
        self.assertTrue(v.centroid.is_equal(Point.by_xyz(1, 2, 3)))

    def test_vertices_use_mean(self):
        vertices = [Vertex.by_point(Point.by_xyz(x, 0, 0)) for x in (0, 2, 4)]
        self.assertTrue(Compound.by_shapes(vertices).centroid.is_equal(Point.by_xyz(2, 0, 0)))

    def test_ignores_lower_dimensions(self):
        face = Face.by_wire(_triangle()).translate(Vector.by_xyz(0, 0, 50))
        c = Compound.by_shapes([Box.by_size(1, 1, 1), face]).centroid
        self.assertTrue(c.is_equal(Point.by_xyz(0.5, 0.5, 0.5)))

    def test_empty_is_nan(self):
        self.assertTrue(math.isnan(Compound.by_shapes([]).centroid.x))

    def test_selects_edges_by_position(self):
        box = Box.by_size(1, 1, 1)
        top_edges = [e for e in box.edges() if e.centroid.z > 0.99]
        self.assertEqual(len(top_edges), 4)


class TestMapShape(unittest.TestCase):
    def test_map(self):
        faces = _box().map(Face)
        self.assertEqual(len(faces), 6)
        self.assertEqual(faces.size, 6)
        self.assertEqual(faces.extent, 6)
        self.assertTrue(all(isinstance(f, Face) for f in faces))

    def test_indexing(self):
        edges = _box().edges()
        self.assertEqual(edges[-1], edges[len(edges) - 1])
        self.assertEqual(edges.find_shape(0), edges[0])
        with self.assertRaises(IndexError):
            edges[len(edges)]
        with self.assertRaises(IndexError):
            edges[-len(edges) - 1]

    def test_slice(self):
        edges = _box().edges()
        self.assertEqual(edges[1:3], [edges[1], edges[2]])
        self.assertEqual(edges[-1:], [edges[-1]])
        self.assertEqual(edges[::-1], list(edges)[::-1])
        self.assertEqual(edges[len(edges) :], [])

    def test_sequence(self):
        edges = _box().edges()
        self.assertIsInstance(edges, Sequence)
        self.assertEqual(edges.index(edges[3]), 3)
        self.assertEqual(edges.count(edges[3]), 1)
        self.assertEqual(list(reversed(edges)), list(edges)[::-1])
        self.assertNotIn(1, edges)

    def test_find_index_contains(self):
        edges = _box().edges()
        self.assertEqual(edges.find_index(edges[3]), 3)
        other = Edge.by_points(Point.by_xyz(5, 0, 0), Point.by_xyz(6, 0, 0))
        self.assertIsNone(edges.find_index(other))
        self.assertTrue(edges.contains(edges[0]))
        self.assertFalse(edges.contains(other))
        self.assertIn(edges[0], edges)
        self.assertNotIn(other, edges)

    def test_composite_rejected(self):
        from pyocctlite.primitives import Cylinder

        with self.assertRaises(TypeError):
            _box().map(Cylinder)

    def test_base_class_rejected(self):
        with self.assertRaises(TypeError):
            _box().map(Shape)


class TestTransformShape(unittest.TestCase):
    def test_modified_shape_not_a_sub_shape(self):
        box, other = _box(), _box()
        t = Transform.by_translation(Vector.by_xyz(0, 0, 1))
        moved = TransformShape(box, t).modified_shape(other.faces()[0])
        self.assertIsInstance(moved, Face)
        with self.assertRaises(RuntimeError):
            TransformShape(box, t, copy_geom=True).modified_shape(other.faces()[0])


class TestExploreShape(unittest.TestCase):
    def test_explore(self):
        explored = list(_box().explore(Vertex))
        self.assertEqual(len(explored), 48)
        self.assertTrue(all(isinstance(v, Vertex) for v in explored))

    def test_ignore(self):
        self.assertEqual(len(list(_box().explore(Vertex, ignore=Edge))), 0)
        self.assertEqual(len(list(_box().explore(Edge, ignore=Face))), 0)

    def test_base_class_rejected(self):
        with self.assertRaises(TypeError):
            _box().explore(Shape)
        with self.assertRaises(TypeError):
            _box().explore(Edge, ignore=Shape)


if __name__ == "__main__":
    unittest.main()
