from __future__ import annotations

from collections.abc import Iterable, Iterator
from enum import Enum
from functools import cached_property
from typing import Generic, Self, TypeVar, cast, overload

from pyocctlite._occtlite import (
    ChamferIShape,
    CopyIShape,
    CutIShapes,
    ExploreIShape,
    ExtrudeIShape,
    FilletIShape,
    IShape,
    IShapeKind,
    LoftIShape,
    MapIShape,
    RevolveIShape,
    ThickenIShape,
    TransformIShape,
    UniteIShapes,
)
from pyocctlite.geometry import (
    Axis,
    Curve,
    Curve2D,
    Point,
    Surface,
    Transform,
    TrimmedCurve,
    Vector,
)

T = TypeVar("T", bound="Shape")
S = TypeVar("S", bound="Shape")

# C++ tools wrapping OCCT BRepBuilderAPI_MakeShape (see MakeIShape.hpp)
MakeShapeITool = (
    ChamferIShape
    | CopyIShape
    | CutIShapes
    | ExtrudeIShape
    | FilletIShape
    | LoftIShape
    | RevolveIShape
    | ThickenIShape
    | TransformIShape
    | UniteIShapes
)
ToolT = TypeVar("ToolT", bound=MakeShapeITool)


class ShapeKind(Enum):
    """
    Enumeration of shape kinds.
    """

    SHAPE = IShapeKind.Shape
    VERTEX = IShapeKind.Vertex
    EDGE = IShapeKind.Edge
    WIRE = IShapeKind.Wire
    FACE = IShapeKind.Face
    SHELL = IShapeKind.Shell
    SOLID = IShapeKind.Solid
    COMPSOLID = IShapeKind.CompSolid
    COMPOUND = IShapeKind.Compound


class Shape:
    """
    Base class for all topological shapes.

    :ivar IShape ishape: Underlying topological shape.
    :ivar ShapeKind kind: Kind of this shape.
    """

    @staticmethod
    def by_ishape(ishape: IShape) -> Shape:
        """
        Create a Shape from an IShape.

        :param IShape ishape: Underlying topological shape.
        :return: New shape.
        :rtype: Shape
        """
        match ishape.Kind():
            case IShapeKind.Vertex:
                return Vertex(ishape)
            case IShapeKind.Edge:
                return Edge(ishape)
            case IShapeKind.Wire:
                return Wire(ishape)
            case IShapeKind.Face:
                return Face(ishape)
            case IShapeKind.Shell:
                return Shell(ishape)
            case IShapeKind.Solid:
                return Solid(ishape)
            case IShapeKind.CompSolid:
                return CompSolid(ishape)
            case IShapeKind.Compound:
                return Compound(ishape)
            case _:
                raise NotImplementedError(f"Unsupported shape kind: {ishape.Kind()}.")

    @staticmethod
    def by_ishapes(ishapes: Iterable[IShape]) -> list[Shape]:
        """
        Create a list of Shapes from an iterable of IShapes.

        :param Iterable[IShape] ishapes: Underlying topological shapes.
        :return: List of shapes.
        :rtype: list[Shape]
        """
        shapes = [Shape.by_ishape(ishape) for ishape in ishapes]
        return shapes

    def __init__(self, s: IShape):
        """
        Initialize from an IShape.

        :param IShape s: Underlying topological shape.
        """
        if not isinstance(s, IShape):
            raise TypeError(f"Expected IShape, got {type(s).__name__}.")
        self._ishape = s

    def __eq__(self, other: object) -> bool:
        """
        Check if both shapes share the same underlying shape (orientation may differ).

        :param object other: Other object.
        :return: True if the shapes are the same.
        :rtype: bool
        """
        if not isinstance(other, Shape):
            return NotImplemented
        return self.ishape.IsSame(other.ishape)

    def __hash__(self) -> int:
        """
        Hash consistent with equality.

        :return: Hash value.
        :rtype: int
        """
        return self.ishape.HashCode()

    @property
    def ishape(self) -> IShape:
        """
        Underlying topological shape.

        :return: IShape object.
        :rtype: IShape
        """
        return self._ishape

    @property
    def kind(self) -> ShapeKind:
        """
        Kind of this shape.

        :return: Shape kind.
        :rtype: ShapeKind
        """
        return ShapeKind(self.ishape.Kind())

    @cached_property
    def length(self) -> float:
        """
        Total length of all edges.

        :return: Total length.
        :rtype: float
        """
        return self.ishape.Length()

    @cached_property
    def area(self) -> float:
        """
        Total area of all faces.

        :return: Total area.
        :rtype: float
        """
        return self.ishape.Area()

    @cached_property
    def volume(self) -> float:
        """
        Total volume of all solids. Can be negative (e.g. after ``face.thicken(1.0)``).

        :return: Total volume.
        :rtype: float
        """
        return self.ishape.Volume()

    @cached_property
    def is_valid(self) -> bool:
        """
        Check if this shape and its sub-shapes are topologically and geometrically well-formed.

        :return: True if no defect was found.
        :rtype: bool
        """
        return self.ishape.IsValid()

    def explore(self, find: type[T], ignore: type[Shape] | None = None) -> ExploreShape[T]:
        """
        Iterate over sub-shapes, including repeats of shared sub-shapes (e.g. 24 edges for a box).

        Use :meth:`map` for unique sub-shapes.

        :param type[T] find: Class of shapes to find (e.g. ``Edge``).
        :param type[Shape] | None ignore: Class of shapes to skip, along with their sub-shapes.
        :return: Explore tool.
        :rtype: ExploreShape[T]
        :raises TypeError: If a class is not a core shape class (e.g. ``Box``).
        """
        return ExploreShape(self, find, ignore)

    def map(self, kind: type[T]) -> MapShape[T]:
        """
        Map the unique sub-shapes (e.g. 12 edges for a box).

        Use :meth:`explore` to include repeats of shared sub-shapes.

        :param type[T] kind: Class of shapes to map (e.g. ``Edge``).
        :return: Map tool.
        :rtype: MapShape[T]
        :raises TypeError: If a class is not a core shape class (e.g. ``Box``).
        """
        return MapShape(self, kind)

    def vertices(self) -> MapShape[Vertex]:
        """
        Get all vertices. A closed edge has one vertex.

        :return: Map of vertices.
        :rtype: MapShape[Vertex]
        """
        return self.map(Vertex)

    def edges(self) -> MapShape[Edge]:
        """
        Get all edges.

        :return: Map of edges.
        :rtype: MapShape[Edge]
        """
        return self.map(Edge)

    def wires(self) -> MapShape[Wire]:
        """
        Get all wires.

        :return: Map of wires.
        :rtype: MapShape[Wire]
        """
        return self.map(Wire)

    def faces(self) -> MapShape[Face]:
        """
        Get all faces.

        :return: Map of faces.
        :rtype: MapShape[Face]
        """
        return self.map(Face)

    def shells(self) -> MapShape[Shell]:
        """
        Get all shells.

        :return: Map of shells.
        :rtype: MapShape[Shell]
        """
        return self.map(Shell)

    def solids(self) -> MapShape[Solid]:
        """
        Get all solids.

        :return: Map of solids.
        :rtype: MapShape[Solid]
        """
        return self.map(Solid)

    def compsolids(self) -> MapShape[CompSolid]:
        """
        Get all compsolids.

        :return: Map of compsolids.
        :rtype: MapShape[CompSolid]
        """
        return self.map(CompSolid)

    def compounds(self) -> MapShape[Compound]:
        """
        Get all compounds.

        :return: Map of compounds.
        :rtype: MapShape[Compound]
        """
        return self.map(Compound)

    def copy(self) -> Self:
        """
        Create a copy of this shape.

        :return: Copied shape of the same type.
        :rtype: Self
        """
        return CopyShape(self).shape()

    def mirror(self, origin: Point, normal: Vector) -> Self:
        """
        Create a mirrored version of this shape.

        :param Point origin: Point on the mirror plane.
        :param Vector normal: Normal of the mirror plane. Must be non-zero.
        :return: Mirrored shape of the same type.
        :rtype: Self
        :raises RuntimeError: If the normal has zero length.
        """
        t = Transform.by_mirror(origin, normal)
        return TransformShape(self, t).shape()

    def rotate(self, axis: Axis, angle: float) -> Self:
        """
        Create a rotated version of this shape.

        :param Axis axis: Axis of rotation.
        :param float angle: Angle in radians, counterclockwise when looking against the axis
            direction.
        :return: Rotated shape of the same type.
        :rtype: Self
        """
        t = Transform.by_rotation(axis, angle)
        return TransformShape(self, t).shape()

    def extrude(self, vector: Vector) -> Shape:
        """
        Extrude this shape along a vector. The result is one dimension higher (e.g. face to solid).

        :param Vector vector: Extrusion direction and distance.
        :return: Extruded shape.
        :rtype: Shape
        :raises RuntimeError: If this is a solid or the vector has zero length.
        """
        return ExtrudeShape(self, vector).shape()

    def revolve(self, axis: Axis) -> Shape:
        """
        Revolve this shape a full turn about an axis. The result is one dimension higher (e.g. face
        to solid).

        The shape may touch the axis but must not cross it. Crashes the interpreter if the shape is
        an edge lying along the axis.

        :param Axis axis: Axis of revolution.
        :return: Revolved shape.
        :rtype: Shape
        :raises BuildFailed: If the shape crosses the axis.
        :raises RuntimeError: If this is a solid.
        """
        return RevolveShape(self, axis).shape()

    def unite(self, other: Shape) -> Shape:
        """
        Unite this shape with another (boolean union).

        Sub-shapes that the operation does not modify compare equal (``==``) to their counterparts
        in the result.

        :param Shape other: Shape to unite.
        :return: United shape. Typically a ``Compound``, even for one solid.
        :rtype: Shape
        :raises BuildFailed: If the operation fails.
        """
        ishape = UniteIShapes(self.ishape, other.ishape).Shape()
        return Shape.by_ishape(ishape)

    def cut(self, other: Shape) -> Shape:
        """
        Cut another shape from this shape (boolean subtraction).

        :param Shape other: Shape to subtract.
        :return: Resulting shape. Typically a ``Compound``, even for one solid.
        :rtype: Shape
        :raises BuildFailed: If the operation fails.
        """
        ishape = CutIShapes(self.ishape, other.ishape).Shape()
        return Shape.by_ishape(ishape)

    def fillet(self, edge: Edge | Iterable[Edge], radius: float) -> Shape:
        """
        Fillet edges of this shape with a constant radius.

        Edges that share no vertex with a filleted edge compare equal (``==``) to their counterparts
        in the result.

        :param Edge | Iterable[Edge] edge: Edge(s) to fillet. Must belong to this shape.
        :param float radius: Fillet radius. Must be positive.
        :return: Filleted shape. Typically a ``Compound``, even for one solid.
        :rtype: Shape
        :raises BuildFailed: If the radius is not positive or is too large.
        :raises RuntimeError: If no edges are given or they do not belong to this shape.
        """
        tool = FilletShape(self)
        for e in [edge] if isinstance(edge, Edge) else edge:
            tool.add_edge(e, radius)
        return tool.shape()

    def chamfer(self, edge: Edge | Iterable[Edge], distance: float) -> Shape:
        """
        Chamfer edges of this shape with the same distance on both adjacent faces.

        :param Edge | Iterable[Edge] edge: Edge(s) to chamfer. Must belong to this shape.
        :param float distance: Distance from the edge along each adjacent face. Must be positive.
        :return: Chamfered shape. Typically a ``Compound``, even for one solid.
        :rtype: Shape
        :raises BuildFailed: If the distance is not positive or is too large.
        :raises RuntimeError: If no edges are given or they do not belong to this shape.
        """
        tool = ChamferShape(self)
        for e in [edge] if isinstance(edge, Edge) else edge:
            tool.add_edge(e, distance)
        return tool.shape()

    def thicken(
        self, thickness: float, tol: float = 1.0e-3, faces: Iterable[Face] | None = None
    ) -> Shape:
        """
        Create a hollow solid with uniform wall thickness.

        If ``faces`` is given, the solid is opened at those faces. Otherwise, the shape must be a
        face or open shell. A thickness that is too large may produce an empty or non-hollow shape
        without raising.

        :param float thickness: Wall thickness. Negative builds inward; positive builds outward.
        :param float tol: Tolerance. Used only with ``faces``.
        :param Iterable[Face] | None faces: Faces to remove.
        :return: Hollow solid.
        :rtype: Shape
        :raises BuildFailed: If the operation fails (e.g. a solid without ``faces``).
        """
        if faces is None:
            itool = ThickenIShape(self.ishape, thickness)
        else:
            ifaces = [f.ishape for f in faces]
            itool = ThickenIShape(self.ishape, ifaces, thickness, tol)

        ishape = itool.Shape()
        return Shape.by_ishape(ishape)

    def export_step(self, path: str) -> None:
        """
        Export this shape to a STEP file.

        :param str path: File path.
        :raises RuntimeError: If the export fails.
        """
        if not self.ishape.ExportSTEP(path):
            raise RuntimeError(f"Failed to export STEP file: {path}")


class Vertex(Shape):
    """
    Represents a vertex.
    """

    @classmethod
    def by_point(cls, p: Point) -> Vertex:
        """
        Create a vertex at a point.

        :param Point p: Location.
        :return: New vertex.
        :rtype: Vertex
        """
        ivertex = IShape.MakeVertex(p.ipoint)
        return cls(ivertex)

    def __init__(self, v: IShape):
        """
        Initialize from an IShape.

        :param IShape v: Underlying topological shape.
        """
        super().__init__(v)
        if v.Kind() != IShapeKind.Vertex:
            raise TypeError(f"Expected IShapeKind.Vertex, got {v.Kind()}.")

    @cached_property
    def point(self) -> Point:
        """
        Location of the vertex.

        :return: Location.
        :rtype: Point
        """
        ipoint = self.ishape.Point()
        assert ipoint is not None  # guaranteed by the kind check in __init__
        return Point(ipoint)

    def extrude(self, vector: Vector) -> Edge:
        """
        Extrude this vertex along a vector into an edge.

        :param Vector vector: Extrusion direction and distance.
        :return: Extruded edge.
        :rtype: Edge
        :raises RuntimeError: If the vector has zero length.
        """
        return ExtrudeShape(self, vector).shape()

    def revolve(self, axis: Axis) -> Edge:
        """
        Revolve this vertex a full turn about an axis into a closed circular edge.

        A vertex on the axis produces a zero-length edge without raising.

        :param Axis axis: Axis of revolution.
        :return: Revolved edge.
        :rtype: Edge
        """
        return RevolveShape(self, axis).shape()


class Edge(Shape):
    """
    Represents an edge.
    """

    @classmethod
    def by_curve(cls, c: Curve) -> Edge:
        """
        Create an edge from a 3D curve.

        A ``Line`` is unbounded and produces a very long edge. Use :meth:`by_points` for a segment.

        :param Curve c: 3D curve.
        :return: New edge.
        :rtype: Edge
        """
        iedge = IShape.MakeEdge(c.icurve)
        return cls(iedge)

    @classmethod
    def by_curve2d(cls, c: Curve2D, s: Surface) -> Edge:
        """
        Create an edge from a 2D curve in the (u, v) parameter space of a surface.

        :param Curve2D c: 2D curve, with x as u and y as v.
        :param Surface s: Surface.
        :return: New edge.
        :rtype: Edge
        """
        iedge = IShape.MakeEdge(c.icurve, s.isurface)
        return cls(iedge)

    @classmethod
    def by_points(cls, p1: Point, p2: Point) -> Edge:
        """
        Create an edge from two points.

        :param Point p1: Start point.
        :param Point p2: End point.
        :return: New edge.
        :rtype: Edge
        :raises RuntimeError: If the points coincide.
        """
        iedge = IShape.MakeEdge(p1.ipoint, p2.ipoint)
        return cls(iedge)

    @classmethod
    def by_vertices(cls, v1: Vertex, v2: Vertex) -> Edge:
        """
        Create an edge between two vertices without copying them.

        :param Vertex v1: Start vertex.
        :param Vertex v2: End vertex.
        :return: New edge.
        :rtype: Edge
        :raises KindMismatch: If an argument is a shape other than a vertex.
        :raises RuntimeError: If the vertices coincide.
        """
        iedge = IShape.MakeEdge(v1.ishape, v2.ishape)
        return cls(iedge)

    @classmethod
    def by_circular_arc(cls, p1: Point, p2: Point, p3: Point) -> Edge:
        """
        Create an edge from a circular arc through three points.

        :param Point p1: Start point.
        :param Point p2: Intermediate point.
        :param Point p3: End point.
        :return: New edge.
        :rtype: Edge
        :raises RuntimeError: If the points are collinear.
        """
        c = TrimmedCurve.by_circular_arc(p1, p2, p3)
        iedge = IShape.MakeEdge(c.icurve)
        return cls(iedge)

    def __init__(self, e: IShape):
        """
        Initialize from an IShape.

        :param IShape e: Underlying topological shape.
        """
        super().__init__(e)
        if e.Kind() != IShapeKind.Edge:
            raise TypeError(f"Expected IShapeKind.Edge, got {e.Kind()}.")

    @cached_property
    def curve(self) -> Curve | None:
        """
        Underlying curve of the edge.

        :return: Underlying curve, or None if the edge has no 3D curve.
        :rtype: Curve | None
        :raises NotImplementedError: If the curve kind is not wrapped (e.g. an edge from
            :meth:`by_curve2d`).
        """
        icurve = self.ishape.Curve()
        return None if icurve is None else Curve.by_icurve(icurve)

    def extrude(self, vector: Vector) -> Face:
        """
        Extrude this edge along a vector into a face.

        :param Vector vector: Extrusion direction and distance.
        :return: Extruded face.
        :rtype: Face
        :raises RuntimeError: If the vector has zero length.
        """
        return ExtrudeShape(self, vector).shape()

    def revolve(self, axis: Axis) -> Face:
        """
        Revolve this edge a full turn about an axis into a face.

        The edge may end on the axis. Crashes the interpreter if it lies along the axis.

        :param Axis axis: Axis of revolution.
        :return: Revolved face.
        :rtype: Face
        :raises BuildFailed: If the edge crosses the axis.
        """
        return RevolveShape(self, axis).shape()


class Wire(Shape):
    """
    Represents a wire.
    """

    @classmethod
    def by_edge(cls, e: Edge) -> Wire:
        """
        Create a wire from an edge.

        :param Edge e: Edge.
        :return: New wire.
        :rtype: Wire
        :raises KindMismatch: If the argument is a shape other than an edge.
        """
        iwire = IShape.MakeWire(e.ishape)
        return cls(iwire)

    @classmethod
    def by_edges(cls, edges: Iterable[Edge]) -> Wire:
        """
        Create a wire from connected edges in any order.

        Crashes the interpreter if ``edges`` is empty.

        :param Iterable[Edge] edges: Edges. Must not be empty.
        :return: New wire.
        :rtype: Wire
        :raises KindMismatch: If an item is a shape other than an edge.
        :raises RuntimeError: If the edges are not connected.
        """
        iedges = [e.ishape for e in edges]
        iwire = IShape.MakeWire(iedges)
        return cls(iwire)

    def __init__(self, w: IShape):
        """
        Initialize from an IShape.

        :param IShape w: Underlying topological shape.
        """
        super().__init__(w)
        if w.Kind() != IShapeKind.Wire:
            raise TypeError(f"Expected IShapeKind.Wire, got {w.Kind()}.")

    def combine(self, other: Wire) -> Wire:
        """
        Create a wire by joining this wire to a connected wire.

        :param Wire other: Other wire.
        :return: New wire.
        :rtype: Wire
        :raises KindMismatch: If the argument is a shape other than a wire.
        :raises RuntimeError: If the wires are not connected.
        """
        iwire = IShape.MakeWire(self.ishape, other.ishape)
        return Wire(iwire)

    def extrude(self, vector: Vector) -> Shell:
        """
        Extrude this wire along a vector into a shell.

        :param Vector vector: Extrusion direction and distance.
        :return: Extruded shell.
        :rtype: Shell
        :raises RuntimeError: If the vector has zero length.
        """
        return ExtrudeShape(self, vector).shape()

    def revolve(self, axis: Axis) -> Shell:
        """
        Revolve this wire a full turn about an axis into a shell.

        An edge of the wire on the axis produces no face. A wire entirely on the axis produces an
        empty shell without raising.

        :param Axis axis: Axis of revolution.
        :return: Revolved shell.
        :rtype: Shell
        :raises BuildFailed: If the wire crosses the axis.
        """
        return RevolveShape(self, axis).shape()


class Face(Shape):
    """
    Represents a face.
    """

    @classmethod
    def by_wire(cls, w: Wire) -> Face:
        """
        Create a planar face from a wire.

        Crashes the interpreter if the wire is closed but not planar. An open wire is accepted, but
        the area of the resulting face is not valid.

        :param Wire w: Closed, planar wire.
        :return: New face.
        :rtype: Face
        :raises KindMismatch: If the argument is a shape other than a wire.
        """
        iface = IShape.MakeFace(w.ishape)
        return cls(iface)

    def __init__(self, f: IShape):
        """
        Initialize from an IShape.

        :param IShape f: Underlying topological shape.
        """
        super().__init__(f)
        if f.Kind() != IShapeKind.Face:
            raise TypeError(f"Expected IShapeKind.Face, got {f.Kind()}.")

    def extrude(self, vector: Vector) -> Solid:
        """
        Extrude this face along a vector into a solid.

        :param Vector vector: Extrusion direction and distance.
        :return: Extruded solid.
        :rtype: Solid
        :raises RuntimeError: If the vector has zero length.
        """
        return ExtrudeShape(self, vector).shape()

    def revolve(self, axis: Axis) -> Solid:
        """
        Revolve this face a full turn about an axis into a solid.

        The face may have an edge on the axis (e.g. a rectangle revolves into a full cylinder).

        :param Axis axis: Axis of revolution.
        :return: Revolved solid.
        :rtype: Solid
        :raises BuildFailed: If the face crosses the axis.
        """
        return RevolveShape(self, axis).shape()


class Shell(Shape):
    """
    Represents a shell.
    """

    def __init__(self, s: IShape):
        """
        Initialize from an IShape.

        :param IShape s: Underlying topological shape.
        """
        super().__init__(s)
        if s.Kind() != IShapeKind.Shell:
            raise TypeError(f"Expected IShapeKind.Shell, got {s.Kind()}.")

    def extrude(self, vector: Vector) -> CompSolid:
        """
        Extrude this shell along a vector into a compsolid.

        :param Vector vector: Extrusion direction and distance.
        :return: Extruded compsolid.
        :rtype: CompSolid
        :raises RuntimeError: If the vector has zero length.
        """
        return ExtrudeShape(self, vector).shape()

    def revolve(self, axis: Axis) -> CompSolid:
        """
        Revolve this shell a full turn about an axis into a compsolid.

        :param Axis axis: Axis of revolution. Must not cross the shell.
        :return: Revolved compsolid.
        :rtype: CompSolid
        """
        return RevolveShape(self, axis).shape()


class Solid(Shape):
    """
    Represents a solid.
    """

    @classmethod
    def by_loft(
        cls, shapes: Iterable[Vertex | Edge | Wire], is_ruled: bool = False, tol: float = 1.0e-6
    ) -> Solid:
        """
        Create a solid by lofting through sections in order.

        Only wire sections are implemented. Crashes the interpreter if given a single wire.

        :param Iterable[Vertex | Edge | Wire] shapes: Sections.
        :param bool is_ruled: True for ruled surfaces between sections, False for smooth surfaces.
        :param float tol: Tolerance.
        :return: New solid.
        :rtype: Solid
        :raises NotImplementedError: If a section is not a wire.
        :raises BuildFailed: If no sections are given or the loft fails.
        """
        itool = LoftIShape(is_solid=True, is_ruled=is_ruled, tol=tol)
        for s in shapes:
            if isinstance(s, Wire):
                itool.AddWire(s.ishape)
            else:
                raise NotImplementedError()

        ishape = itool.Shape()
        return cls(ishape)

    def __init__(self, s: IShape):
        """
        Initialize from an IShape.

        :param IShape s: Underlying topological shape.
        """
        super().__init__(s)
        if s.Kind() != IShapeKind.Solid:
            raise TypeError(f"Expected IShapeKind.Solid, got {s.Kind()}.")


class CompSolid(Shape):
    """
    Represents a compsolid.
    """

    def __init__(self, cs: IShape):
        """
        Initialize from an IShape.

        :param IShape cs: Underlying topological shape.
        """
        super().__init__(cs)
        if cs.Kind() != IShapeKind.CompSolid:
            raise TypeError(f"Expected IShapeKind.CompSolid, got {cs.Kind()}.")


class Compound(Shape):
    """
    Represents a compound.
    """

    @classmethod
    def by_shapes(cls, shapes: Iterable[Shape]) -> Compound:
        """
        Create a compound from a list of shapes.

        :param Iterable[Shape] shapes: Shapes to include in the compound.
        :return: New compound.
        :rtype: Compound
        """
        ishapes = [s.ishape for s in shapes]
        icompound = IShape.MakeCompound(ishapes)
        return cls(icompound)

    def __init__(self, c: IShape):
        """
        Initialize from an IShape.

        :param IShape c: Underlying topological shape.
        """
        super().__init__(c)
        if c.Kind() != IShapeKind.Compound:
            raise TypeError(f"Expected IShapeKind.Compound, got {c.Kind()}.")


def _kind_of(cls: type[Shape]) -> ShapeKind:
    """
    Get the shape kind of a core shape class.

    :param type[Shape] cls: Core shape class (e.g. ``Edge``).
    :return: Shape kind.
    :rtype: ShapeKind
    :raises TypeError: If the class is not a core shape class (e.g. a composite).
    """
    kinds = {
        Shape: ShapeKind.SHAPE,
        Vertex: ShapeKind.VERTEX,
        Edge: ShapeKind.EDGE,
        Wire: ShapeKind.WIRE,
        Face: ShapeKind.FACE,
        Shell: ShapeKind.SHELL,
        Solid: ShapeKind.SOLID,
        CompSolid: ShapeKind.COMPSOLID,
        Compound: ShapeKind.COMPOUND,
    }
    if cls not in kinds:
        raise TypeError(f"Expected a core shape class, got {cls.__name__}.")
    return kinds[cls]


class ShapeTool(Generic[ToolT]):
    """
    Base class for shape tools.
    """

    def __init__(self, itool: ToolT):
        """
        Initialize from an internal tool.

        :param ToolT itool: Internal tool.
        """
        self._itool = itool

    @property
    def is_done(self) -> bool:
        """
        Check if the tool finished successfully.

        :return: True if done.
        :rtype: bool
        """
        return self._itool.IsDone()

    def shape(self) -> Shape:
        """
        Get the resulting shape.

        :return: Resulting shape.
        :rtype: Shape
        :raises BuildFailed: If the operation fails.
        """
        return Shape.by_ishape(self._itool.Shape())

    def generated_shapes(self, s: Shape) -> list[Shape]:
        """
        Get shapes generated from a sub-shape of the source shape (e.g. the face from an edge).

        :param Shape s: Sub-shape of the source shape.
        :return: Generated shapes. Empty if there are none.
        :rtype: list[Shape]
        :raises BuildFailed: If the operation fails.
        """
        return Shape.by_ishapes(self._itool.GeneratedShapes(s.ishape))


class UniteShapes(ShapeTool[UniteIShapes]):
    """
    Tool to unite shapes.
    """

    def __init__(self, target: Shape, tool: Shape):
        """
        Initialize with target and tool shapes.

        :param Shape target: Target shape to unite with.
        :param Shape tool: Tool shape to unite.
        """
        itool = UniteIShapes(target.ishape, tool.ishape)
        super().__init__(itool)

    def intersection_edges(self) -> list[Edge]:
        """
        Get the edges where the surfaces of the shapes intersect.

        :return: Intersection edges. Empty if the shapes only touch or one contains the other.
        :rtype: list[Edge]
        """
        return [Edge(e) for e in self._itool.IntersectionEdges()]


class CutShapes(ShapeTool[CutIShapes]):
    """
    Tool to cut shapes (boolean subtraction).
    """

    def __init__(self, target: Shape, tool: Shape):
        """
        Initialize with target and tool shapes.

        :param Shape target: Target shape to cut from.
        :param Shape tool: Tool shape to subtract.
        """
        itool = CutIShapes(target.ishape, tool.ishape)
        super().__init__(itool)

    def intersection_edges(self) -> list[Edge]:
        """
        Get the edges where the surfaces of the shapes intersect.

        :return: Intersection edges. Empty if the shapes only touch or one contains the other.
        :rtype: list[Edge]
        """
        return [Edge(e) for e in self._itool.IntersectionEdges()]


class CopyShape(ShapeTool[CopyIShape], Generic[T]):
    """
    Tool to copy a shape. The result has the same type as the source.
    """

    def __init__(self, s: T, copy_geom: bool = True):
        """
        Initialize with shape.

        :param Shape s: Source shape.
        :param bool copy_geom: True to copy the underlying geometry.
        """
        itool = CopyIShape(s.ishape, copy_geom)
        super().__init__(itool)

    def shape(self) -> T:
        """
        Get the resulting shape.

        :return: Resulting shape of the same type as the source.
        :rtype: T
        """
        return cast(T, super().shape())

    def modified_shape(self, s: S) -> S:
        """
        Get the copy of a sub-shape of the source shape.

        :param S s: Sub-shape of the source shape.
        :return: Copied sub-shape of the same type.
        :rtype: S
        :raises RuntimeError: If the shape is not a sub-shape of the source shape.
        """
        return cast(S, Shape.by_ishape(self._itool.ModifiedShape(s.ishape)))


class TransformShape(ShapeTool[TransformIShape], Generic[T]):
    """
    Tool to transform a shape. The result has the same type as the source.
    """

    def __init__(self, s: T, t: Transform, copy_geom: bool = False):
        """
        Initialize with shape and transformation.

        :param Shape s: Source shape.
        :param Transform t: Transformation.
        :param bool copy_geom: True to copy the underlying geometry.
        """
        itool = TransformIShape(s.ishape, t.itransform, copy_geom)
        super().__init__(itool)

    def shape(self) -> T:
        """
        Get the resulting shape.

        :return: Resulting shape of the same type as the source.
        :rtype: T
        """
        return cast(T, super().shape())

    def modified_shape(self, s: S) -> S:
        """
        Get the transformed version of a sub-shape of the source shape.

        :param S s: Sub-shape of the source shape.
        :return: Transformed sub-shape of the same type.
        :rtype: S
        :raises RuntimeError: If the shape is not a sub-shape of the source shape.
        """
        return cast(S, Shape.by_ishape(self._itool.ModifiedShape(s.ishape)))


class ExtrudeShape(ShapeTool[ExtrudeIShape], Generic[T]):
    """
    Tool to extrude a shape. The result is one dimension higher (e.g. face to solid).
    """

    def __init__(self, s: T, v: Vector):
        """
        Initialize with shape and vector.

        :param T s: Source shape.
        :param Vector v: Extrusion direction and distance.
        :raises RuntimeError: If the source is a solid or the vector has zero length.
        """
        itool = ExtrudeIShape(s.ishape, v.ivector)
        super().__init__(itool)

    @overload
    def shape(self: ExtrudeShape[Vertex]) -> Edge: ...
    @overload
    def shape(self: ExtrudeShape[Edge]) -> Face: ...
    @overload
    def shape(self: ExtrudeShape[Wire]) -> Shell: ...
    @overload
    def shape(self: ExtrudeShape[Face]) -> Solid: ...
    @overload
    def shape(self: ExtrudeShape[Shell]) -> CompSolid: ...
    @overload
    def shape(self) -> Shape: ...

    def shape(self) -> Shape:
        """
        Get the resulting shape, one dimension higher than the source.

        :return: Extruded shape.
        :rtype: Shape
        """
        return super().shape()

    def first_shape(self) -> T:
        """
        Get the shape at the start of the extrusion. This is the source shape.

        :return: First shape of the same type as the source.
        :rtype: T
        """
        return cast(T, Shape.by_ishape(self._itool.FirstShape()))

    def last_shape(self) -> T:
        """
        Get the shape at the end of the extrusion.

        :return: Last shape of the same type as the source.
        :rtype: T
        """
        return cast(T, Shape.by_ishape(self._itool.LastShape()))


class RevolveShape(ShapeTool[RevolveIShape], Generic[T]):
    """
    Tool to revolve a shape a full turn. The result is one dimension higher (e.g. face to solid).

    Use :meth:`generated_shapes` to find what a sub-shape of the source became (e.g. the circular
    edge from a vertex, or the face from an edge).
    """

    def __init__(self, s: T, axis: Axis):
        """
        Initialize with shape and axis.

        :param T s: Source shape. May touch the axis but must not cross it.
        :param Axis axis: Axis of revolution.
        :raises RuntimeError: If the source is a solid.
        """
        itool = RevolveIShape(s.ishape, axis.iaxis)
        super().__init__(itool)

    @overload
    def shape(self: RevolveShape[Vertex]) -> Edge: ...
    @overload
    def shape(self: RevolveShape[Edge]) -> Face: ...
    @overload
    def shape(self: RevolveShape[Wire]) -> Shell: ...
    @overload
    def shape(self: RevolveShape[Face]) -> Solid: ...
    @overload
    def shape(self: RevolveShape[Shell]) -> CompSolid: ...
    @overload
    def shape(self) -> Shape: ...

    def shape(self) -> Shape:
        """
        Get the resulting shape, one dimension higher than the source.

        Crashes the interpreter if the source is an edge lying along the axis.

        :return: Revolved shape.
        :rtype: Shape
        :raises BuildFailed: If the source crosses the axis.
        """
        return super().shape()


class FilletShape(ShapeTool[FilletIShape]):
    """
    Tool to fillet edges of a shape, with a constant radius per edge.

    Use :meth:`generated_shapes` to find the fillet face made from an edge.
    """

    def __init__(self, s: Shape):
        """
        Initialize with shape.

        :param Shape s: Source shape.
        """
        itool = FilletIShape(s.ishape)
        super().__init__(itool)

    def add_edge(self, e: Edge, radius: float) -> None:
        """
        Add an edge to fillet.

        Problems with the edge or radius are raised when the result is requested.

        :param Edge e: Edge. Must belong to the source shape.
        :param float radius: Fillet radius. Must be positive.
        """
        self._itool.AddEdge(e.ishape, radius)


class ChamferShape(ShapeTool[ChamferIShape]):
    """
    Tool to chamfer edges of a shape, with the same distance on both faces adjacent to each edge.

    Use :meth:`generated_shapes` to find the chamfer face made from an edge.
    """

    def __init__(self, s: Shape):
        """
        Initialize with shape.

        :param Shape s: Source shape.
        """
        itool = ChamferIShape(s.ishape)
        super().__init__(itool)

    def add_edge(self, e: Edge, distance: float) -> None:
        """
        Add an edge to chamfer.

        Problems with the edge or distance are raised when the result is requested.

        :param Edge e: Edge. Must belong to the source shape.
        :param float distance: Distance from the edge along each adjacent face. Must be positive.
        """
        self._itool.AddEdge(e.ishape, distance)


class ThickenShape(ShapeTool[ThickenIShape]):
    """
    Tool to create a hollow solid with uniform wall thickness.
    """

    def __init__(
        self, s: Shape, thickness: float, tol: float = 1.0e-3, faces: Iterable[Face] | None = None
    ):
        """
        Initialize with shape and thickness.

        :param Shape s: Source shape.
        :param float thickness: Wall thickness. Negative builds inward; positive builds outward.
        :param float tol: Tolerance. Used only with ``faces``.
        :param Iterable[Face] | None faces: Faces to remove.
        """
        if faces is None:
            itool = ThickenIShape(s.ishape, thickness)
        else:
            ifaces = [f.ishape for f in faces]
            itool = ThickenIShape(s.ishape, ifaces, thickness, tol)
        super().__init__(itool)


class LoftShape(ShapeTool[LoftIShape]):
    """
    Tool to loft through section wires in the order they are added.

    Crashes the interpreter if built from a single wire.
    """

    def __init__(self, is_solid: bool = False, is_ruled: bool = False, tol: float = 1.0e-6):
        """
        Initialize with loft options.

        :param bool is_solid: True to create a solid, False to create a shell.
        :param bool is_ruled: True for ruled surfaces between sections, False for smooth surfaces.
        :param float tol: Tolerance.
        """
        itool = LoftIShape(is_solid, is_ruled, tol)
        super().__init__(itool)

    def add_wire(self, w: Wire) -> None:
        """
        Add the next section wire.

        :param Wire w: Section wire.
        """
        self._itool.AddWire(w.ishape)


class MapShape(Generic[T]):
    """
    Tool to map the unique sub-shapes of a shape.
    """

    def __init__(self, shape: Shape, kind: type[T]):
        """
        Initialize with shape and class of sub-shapes.

        :param Shape shape: Source shape.
        :param type[T] kind: Class of sub-shapes to map (e.g. ``Edge``).
        :raises TypeError: If a class is not a core shape class (e.g. ``Box``).
        """
        self._itool = MapIShape(shape.ishape, _kind_of(kind).value)

    def __len__(self) -> int:
        """
        Number of mapped shapes.

        :return: Count.
        :rtype: int
        """
        return self._itool.Size()

    def __iter__(self) -> Iterator[T]:
        """
        Iterate over mapped shapes.

        :return: Iterator of shapes.
        :rtype: Iterator[T]
        """
        # OCCT is 1-based
        for i in range(1, self._itool.Size() + 1):
            yield cast(T, Shape.by_ishape(self._itool.FindShape(i)))

    def __getitem__(self, index: int) -> T:
        """
        Get shape by 0-based index.

        :param int index: 0-based index. Negative values count from the end.
        :return: Sub-shape.
        :rtype: T
        :raises IndexError: If the index is out of range.
        """
        n = len(self)
        if index < 0:
            index += n
        if index < 0 or index >= n:
            raise IndexError(index)

        # Python is 0-based, OCCT is 1-based
        return cast(T, Shape.by_ishape(self._itool.FindShape(index + 1)))

    @property
    def size(self) -> int:
        """
        Number of shapes in the map.

        :return: Size.
        :rtype: int
        """
        return self._itool.Size()

    @property
    def extent(self) -> int:
        """
        Total number of shapes, including duplicates if any.

        :return: Extent.
        :rtype: int
        """
        return self._itool.Extent()

    def find_shape(self, index: int) -> T:
        """
        Find shape by 0-based index. Negative values are not supported.

        :param int index: 0-based index.
        :return: Sub-shape.
        :rtype: T
        :raises RuntimeError: If the index is out of range.
        """
        # OCCT is 1-based, Python is 0-based
        ishape = self._itool.FindShape(index + 1)
        return cast(T, Shape.by_ishape(ishape))

    def find_index(self, shape: T) -> int | None:
        """
        Find 0-based index of a shape.

        :param T shape: Sub-shape.
        :return: 0-based index, or None if not found.
        :rtype: int | None
        """
        # OCCT is 1-based, Python is 0-based
        indx = self._itool.FindIndex(shape.ishape)
        return None if indx <= 0 else indx - 1

    def contains(self, shape: T) -> bool:
        """
        Check if a shape is in the map.

        :param T shape: Sub-shape.
        :return: True if found.
        :rtype: bool
        """
        return self._itool.Contains(shape.ishape)


class ExploreShape(Generic[T]):
    """
    Tool to iterate over sub-shapes, including repeats of shared sub-shapes.
    """

    def __init__(self, shape: Shape, find: type[T], ignore: type[Shape] | None = None):
        """
        Initialize with shape and classes of sub-shapes to find and skip.

        :param Shape shape: Source shape.
        :param type[T] find: Class of shapes to find (e.g. ``Edge``).
        :param type[Shape] | None ignore: Class of shapes to skip, along with their sub-shapes.
        :raises TypeError: If a class is not a core shape class (e.g. ``Box``).
        """
        self._shape = shape
        self._find = _kind_of(find)
        self._ignore = ShapeKind.SHAPE if ignore is None else _kind_of(ignore)

    def __iter__(self) -> Iterator[T]:
        """
        Iterate over discovered shapes.

        :return: Iterator of shapes.
        :rtype: Iterator[T]
        """
        itool = ExploreIShape(self._shape.ishape, self._find.value, self._ignore.value)
        while itool.More():
            yield cast(T, Shape.by_ishape(itool.Current()))
            itool.Next()
