from __future__ import annotations

from collections.abc import Iterable, Iterator
from enum import Enum
from functools import cached_property
from typing import Generic, Self, TypeVar, cast

from pyocctlite._occtlite import (
    CopyIShape,
    CutIShapes,
    ExploreIShape,
    ExtrudeIShape,
    FilletIShape,
    IShape,
    IShapeKind,
    LoftIShape,
    MapIShape,
    ThickenIShape,
    TransformIShape,
    UniteIShapes,
)
from pyocctlite.geometry import Curve, Curve2D, Point, Surface, Transform, TrimmedCurve, Vector

T = TypeVar('T', bound='Shape')
S = TypeVar('S', bound='Shape')

# C++ tools wrapping OCCT BRepBuilderAPI_MakeShape (see MakeIShape.hpp)
MakeShapeITool = (CopyIShape | CutIShapes | ExtrudeIShape | FilletIShape | LoftIShape
                  | ThickenIShape | TransformIShape | UniteIShapes)
ToolT = TypeVar('ToolT', bound=MakeShapeITool)


class ShapeKind(Enum):
    """
    Kinds of shapes.
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
                raise NotImplementedError(f'Unsupported shape kind: {ishape.Kind()}.')

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
            raise TypeError(f'Expected IShape, got {type(s).__name__}.')
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
        The length of all edges of the shape.

        :rtype: float
        :return: The length of all edges of the shape.
        """
        return self.ishape.Length()

    @cached_property
    def area(self) -> float:
        """
        The area of all faces of the shape.

        :rtype: float
        :return: The area of all faces of the shape.
        """
        return self.ishape.Area()

    @cached_property
    def volume(self) -> float:
        """
        The volume of all solids of the shape.

        :rtype: float
        :return: The volume of all solids of the shape.
        """
        return self.ishape.Volume()

    def explore(self, find: type[T], ignore: type[Shape] | None = None) -> ExploreShape[T]:
        """
        Explore sub-shapes.

        :param type[T] find: Class of shapes to find (e.g. ``Edge``).
        :param type[Shape] | None ignore: Class of shapes to skip over, if any.
        :return: Explore tool.
        :rtype: ExploreShape[T]
        """
        return ExploreShape(self, find, ignore)

    def map(self, kind: type[T]) -> MapShape[T]:
        """
        Map sub-shapes.

        :param type[T] kind: Class of shapes to map (e.g. ``Edge``).
        :return: Map tool.
        :rtype: MapShape[T]
        """
        return MapShape(self, kind)

    def vertices(self) -> MapShape[Vertex]:
        """
        Get all vertices.

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

        :param Point origin: Mirror origin.
        :param Vector normal: Mirror normal.
        :return: Mirrored shape of the same type.
        :rtype: Self
        """
        t = Transform.by_mirror(origin, normal)
        return TransformShape(self, t).shape()

    def extrude(self, vector: Vector) -> Shape:
        """
        Extrude this shape along a vector. The result is one dimension higher (e.g. face to solid).

        :param Vector vector: Extrusion vector.
        :return: Extruded shape.
        :rtype: Shape
        """
        return ExtrudeShape(self, vector).shape()

    def unite(self, other: Shape) -> Shape:
        """
        Unite this shape with another (boolean union).

        :param Shape other: Shape to unite.
        :return: United shape.
        :rtype: Shape
        """
        ishape = UniteIShapes(self.ishape, other.ishape).Shape()
        return Shape.by_ishape(ishape)

    def cut(self, other: Shape) -> Shape:
        """
        Cut another shape from this shape (boolean subtraction).

        :param Shape other: Shape to subtract.
        :return: Resulting shape.
        :rtype: Shape
        """
        ishape = CutIShapes(self.ishape, other.ishape).Shape()
        return Shape.by_ishape(ishape)

    def fillet(self, edge: Edge | Iterable[Edge], radius: float) -> Shape:
        """
        Fillet edges of this shape.

        :param Edge | Iterable[Edge] edge: Edge(s) to fillet.
        :param float radius: Fillet radius.
        :return: Filleted shape.
        :rtype: Shape
        """
        itool = FilletIShape(self.ishape)
        if isinstance(edge, Edge):
            itool.AddEdge(edge.ishape, radius)
        else:
            for e in edge:
                itool.AddEdge(e.ishape, radius)

        ishape = itool.Shape()
        return Shape.by_ishape(ishape)

    def thicken(self, thickness: float, tol: float = 1.0e-3,
                faces: Iterable[Face] | None = None) -> Shape:
        """
        Thicken this shape.

        :param float thickness: Thickness.
        :param float tol: Tolerance.
        :param Iterable[Face] | None faces: Faces to remove.
        :return: Thickened shape.
        :rtype: Shape
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
            raise RuntimeError(f'Failed to export STEP file: {path}')


class Vertex(Shape):
    """
    Represents a vertex.
    """

    def __init__(self, v: IShape):
        """
        Initialize from an IShape.

        :param IShape v: Underlying topological shape.
        """
        super().__init__(v)
        if v.Kind() != IShapeKind.Vertex:
            raise TypeError(f'Expected IShapeKind.Vertex, got {v.Kind()}.')


class Edge(Shape):
    """
    Represents an edge.
    """

    @classmethod
    def by_curve(cls, c: Curve) -> Edge:
        """
        Create an edge from a 3D curve.

        :param Curve c: 3D curve.
        :return: New edge.
        :rtype: Edge
        """
        iedge = IShape.MakeEdge(c.icurve)
        return cls(iedge)

    @classmethod
    def by_curve2d(cls, c: Curve2D, s: Surface) -> Edge:
        """
        Create an edge from a 2D curve and a surface.

        :param Curve2D c: 2D curve.
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
        """
        iedge = IShape.MakeEdge(p1.ipoint, p2.ipoint)
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
            raise TypeError(f'Expected IShapeKind.Edge, got {e.Kind()}.')

    @cached_property
    def curve(self) -> Curve | None:
        """
        Get the underlying curve of the edge.

        :return: The underlying curve, or None if the edge has no 3D curve.
        :rtype: Curve | None
        """
        icurve = self.ishape.Curve()
        return None if icurve is None else Curve.by_icurve(icurve)


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
        """
        iwire = IShape.MakeWire(e.ishape)
        return cls(iwire)

    @classmethod
    def by_edges(cls, edges: Iterable[Edge]) -> Wire:
        """
        Create a wire from edges.

        :param Iterable[Edge] edges: Edges.
        :return: New wire.
        :rtype: Wire
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
            raise TypeError(f'Expected IShapeKind.Wire, got {w.Kind()}.')

    def combine(self, other: Wire) -> Wire:
        """
        Combine this wire with another.

        :param Wire other: Other wire.
        :return: New wire.
        :rtype: Wire
        """
        iwire = IShape.MakeWire(self.ishape, other.ishape)
        return Wire(iwire)


class Face(Shape):
    """
    Represents a face.
    """

    @classmethod
    def by_wire(cls, w: Wire) -> Face:
        """
        Create a face from a wire.

        :param Wire w: Wire.
        :return: New face.
        :rtype: Face
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
            raise TypeError(f'Expected IShapeKind.Face, got {f.Kind()}.')


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
            raise TypeError(f'Expected IShapeKind.Shell, got {s.Kind()}.')


class Solid(Shape):
    """
    Represents a solid.
    """

    @classmethod
    def by_loft(cls, shapes: Iterable[Vertex | Edge | Wire],
                is_ruled: bool = False, tol: float = 1.0e-6) -> Solid:
        """
        Create a solid by lofting through shapes.

        :param Iterable[Vertex | Edge | Wire] shapes: Sections.
        :param bool is_ruled: True if ruled.
        :param float tol: Tolerance.
        :return: New solid.
        :rtype: Solid
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
            raise TypeError(f'Expected IShapeKind.Solid, got {s.Kind()}.')


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
            raise TypeError(f'Expected IShapeKind.CompSolid, got {cs.Kind()}.')


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
            raise TypeError(f'Expected IShapeKind.Compound, got {c.Kind()}.')


def _kind_of(cls: type[Shape]) -> ShapeKind:
    """
    Get the shape kind of a core shape class.

    :param type[Shape] cls: Core shape class (e.g. ``Edge``).
    :return: Shape kind.
    :rtype: ShapeKind
    :raises TypeError: If the class is not a core shape class (e.g. a composite).
    """
    kinds = {Shape: ShapeKind.SHAPE, Vertex: ShapeKind.VERTEX, Edge: ShapeKind.EDGE,
             Wire: ShapeKind.WIRE, Face: ShapeKind.FACE, Shell: ShapeKind.SHELL,
             Solid: ShapeKind.SOLID, CompSolid: ShapeKind.COMPSOLID, Compound: ShapeKind.COMPOUND}
    if cls not in kinds:
        raise TypeError(f'Expected a core shape class, got {cls.__name__}.')
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
        """
        return Shape.by_ishape(self._itool.Shape())

    def generated_shapes(self, s: Shape) -> list[Shape]:
        """
        Get shapes generated from a source shape.

        :param Shape s: Source shape.
        :return: Generated shapes.
        :rtype: list[Shape]
        """
        return Shape.by_ishapes(self._itool.GeneratedShapes(s.ishape))


class UniteShapes(ShapeTool[UniteIShapes]):
    """
    Tool to unite shapes.
    """

    def __init__(self, target: Shape, tool: Shape):
        """
        Initialize with target and tool shapes.

        :param Shape target: Target shape to unit with.
        :param Shape tool: Tool shape to unite.
        """
        itool = UniteIShapes(target.ishape, tool.ishape)
        super().__init__(itool)

    def intersection_edges(self) -> list[Edge]:
        """
        Get intersection edges.

        :return: Intersection edges.
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
        Get intersection edges.

        :return: Intersection edges.
        :rtype: list[Edge]
        """
        return [Edge(e) for e in self._itool.IntersectionEdges()]


class CopyShape(ShapeTool[CopyIShape], Generic[T]):
    """
    Tool to copy a shape. The copy has the same type as the source.
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

        :return: Resulting shape, of the same type as the source.
        :rtype: T
        """
        return cast(T, super().shape())

    def modified_shape(self, s: S) -> S:
        """
        Get the copy of a sub-shape of the source shape.

        :param S s: Sub-shape of the source shape.
        :return: Copied sub-shape, of the same type.
        :rtype: S
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

        :return: Resulting shape, of the same type as the source.
        :rtype: T
        """
        return cast(T, super().shape())

    def modified_shape(self, s: S) -> S:
        """
        Get the transformed version of a sub-shape of the source shape.

        :param S s: Sub-shape of the source shape.
        :return: Transformed sub-shape, of the same type.
        :rtype: S
        """
        return cast(S, Shape.by_ishape(self._itool.ModifiedShape(s.ishape)))


class ExtrudeShape(ShapeTool[ExtrudeIShape], Generic[T]):
    """
    Tool to extrude a shape. The result is one dimension higher than the source.
    """

    def __init__(self, s: T, v: Vector):
        """
        Initialize with shape and vector.

        :param T s: Source shape.
        :param Vector v: Extrusion vector.
        """
        itool = ExtrudeIShape(s.ishape, v.ivector)
        super().__init__(itool)

    def first_shape(self) -> T:
        """
        Get the shape at the start of extrusion.

        :return: First shape, of the same type as the source.
        :rtype: T
        """
        return cast(T, Shape.by_ishape(self._itool.FirstShape()))

    def last_shape(self) -> T:
        """
        Get the shape at the end of extrusion.

        :return: Last shape, of the same type as the source.
        :rtype: T
        """
        return cast(T, Shape.by_ishape(self._itool.LastShape()))


class ThickenShape(ShapeTool[ThickenIShape]):
    """
    Tool to thicken a shape.
    """

    def __init__(self, s: Shape, thickness: float, tol: float = 1.0e-3,
                 faces: Iterable[Face] | None = None):
        """
        Initialize with shape and thickness.

        :param Shape s: Source shape.
        :param float thickness: Thickness.
        :param float tol: Tolerance.
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
    Tool to loft through sections.
    """

    def __init__(self, is_solid: bool = False, is_ruled: bool = False, tol: float = 1.0e-6):
        """
        Initialize loft tool.

        :param bool is_solid: True to create a solid.
        :param bool is_ruled: True if ruled.
        :param float tol: Tolerance.
        """
        itool = LoftIShape(is_solid, is_ruled, tol)
        super().__init__(itool)


    def add_wire(self, w: Wire) -> None:
        """
        Add a section wire.

        :param Wire w: Section wire.
        """
        self._itool.AddWire(w.ishape)


class MapShape(Generic[T]):
    """
    Tool to map and access sub-shapes.
    """

    def __init__(self, shape: Shape, kind: type[T]):
        """
        Initialize with shape and class of sub-shapes.

        :param Shape shape: Source shape.
        :param type[T] kind: Class of sub-shapes to map (e.g. ``Edge``).
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
        :rtype: Iterator[Shape]
        """
        # OCCT is 1-based
        for i in range(1, self._itool.Size() + 1):
            yield cast(T, Shape.by_ishape(self._itool.FindShape(i)))

    def __getitem__(self, index: int) -> T:
        """
        Get shape by index.

        :param int index: 0-based index.
        :return: Sub-shape.
        :rtype: Shape
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
        Find shape by 0-based index.

        :param int index: 0-based index.
        :return: Sub-shape.
        :rtype: T
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
    Tool to explore sub-shapes.
    """

    def __init__(self, shape: Shape, find: type[T], ignore: type[Shape] | None = None):
        """
        Initialize explore tool.

        :param Shape shape: Source shape.
        :param type[T] find: Class of shapes to find (e.g. ``Edge``).
        :param type[Shape] | None ignore: Class of shapes to skip over, if any.
        """
        self._shape = shape
        self._find = _kind_of(find)
        self._ignore = ShapeKind.SHAPE if ignore is None else _kind_of(ignore)

    def __iter__(self) -> Iterator[T]:
        """
        Iterate over discovered shapes.

        :return: Iterator of shapes of type T.
        :rtype: Iterator[T]
        """
        itool = ExploreIShape(self._shape.ishape, self._find.value, self._ignore.value)
        while itool.More():
            yield cast(T, Shape.by_ishape(itool.Current()))
            itool.Next()
