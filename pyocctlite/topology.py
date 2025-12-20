from __future__ import annotations

from enum import Enum
from typing import Iterable, Iterator, Optional, Self, Union

from pyocctlite._occtlite import (CopyIShape, CutIShapes, ExploreIShape, ExtrudeIShape,
                                  FilletIShape,
                                  IShape, IShapeKind, LoftIShape, MapIShape, ThickenIShape,
                                  TransformIShape, UniteIShapes)

from pyocctlite.geometry import Curve, Curve2D, Point, Surface, Transform, TrimmedCurve, Vector

__all__ = ['Shape', 'Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound',
           'UniteShapes', 'CutShapes', 'ExtrudeShape', 'ThickenShape', 'LoftShape', 'ShapeKind',
           'MapShape', 'ExploreShape']


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
                raise RuntimeError("Cannot create unknown shape.")

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
        assert isinstance(s, IShape)
        self._ishape = s
        self._kind = ShapeKind.SHAPE

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
        return self._kind

    def explore(self, find: ShapeKind, ignore: ShapeKind = ShapeKind.SHAPE) -> ExploreShape:
        """
        Explore sub-shapes.

        :param ShapeKind find: Kind of shapes to find.
        :param ShapeKind ignore: Kind of shapes to ignore.
        :return: Explore tool.
        :rtype: ExploreShape
        """
        return ExploreShape(self, find, ignore)

    def map(self, kind: ShapeKind) -> MapShape:
        """
        Map sub-shapes.

        :param ShapeKind kind: Kind of shapes to map.
        :return: Map tool.
        :rtype: MapShape
        """
        return MapShape(self, kind)

    def vertices(self) -> Union[MapShape, Iterable[Vertex]]:
        """
        Get all vertices.

        :return: Map of vertices.
        :rtype: Union[MapShape, Iterable[Vertex]]
        """
        return self.map(ShapeKind.VERTEX)

    def edges(self) -> Union[MapShape, Iterable[Edge]]:
        """
        Get all edges.

        :return: Map of edges.
        :rtype: Union[MapShape, Iterable[Edge]]
        """
        return self.map(ShapeKind.EDGE)

    def wires(self) -> Union[MapShape, Iterable[Wire]]:
        """
        Get all wires.

        :return: Map of wires.
        :rtype: Union[MapShape, Iterable[Wire]]
        """
        return self.map(ShapeKind.WIRE)

    def faces(self) -> Union[MapShape, Iterable[Face]]:
        """
        Get all faces.

        :return: Map of faces.
        :rtype: Union[MapShape, Iterable[Face]]
        """
        return self.map(ShapeKind.FACE)

    def shells(self) -> Union[MapShape, Iterable[Shell]]:
        """
        Get all shells.

        :return: Map of shells.
        :rtype: Union[MapShape, Iterable[Shell]]
        """
        return self.map(ShapeKind.SHELL)

    def solids(self) -> Union[MapShape, Iterable[Solid]]:
        """
        Get all solids.

        :return: Map of solids.
        :rtype: Union[MapShape, Iterable[Solid]]
        """
        return self.map(ShapeKind.SOLID)

    def compsolids(self) -> Union[MapShape, Iterable[CompSolid]]:
        """
        Get all compsolids.

        :return: Map of compsolids.
        :rtype: Union[MapShape, Iterable[CompSolid]]
        """
        return self.map(ShapeKind.COMPSOLID)

    def compounds(self) -> Union[MapShape, Iterable[Compound]]:
        """
        Get all compounds.

        :return: Map of compounds.
        :rtype: Union[MapShape, Iterable[Compound]]
        """
        return self.map(ShapeKind.COMPOUND)

    def copy(self) -> Self:
        """
        Create a copy of this shape.

        :return: Copied shape.
        :rtype: Self
        """
        ishape = CopyIShape(self.ishape).Shape()
        return Shape.by_ishape(ishape)

    def mirror(self, origin: Point, normal: Vector) -> Self:
        """
        Create a mirrored version of this shape.

        :param Point origin: Mirror origin.
        :param Vector normal: Mirror normal.
        :return: Mirrored shape.
        :rtype: Self
        """
        t = Transform.mirror(origin, normal)
        ishape = TransformIShape(self.ishape, t.itransform).Shape()
        return Shape.by_ishape(ishape)

    def extrude(self, vector: Vector) -> Shape:
        """
        Extrude this shape along a vector.

        :param Vector vector: Extrusion vector.
        :return: Extruded shape.
        :rtype: Shape
        """
        ishape = ExtrudeIShape(self.ishape, vector.ivector).Shape()
        return Shape.by_ishape(ishape)

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

    def fillet(self, edge: Union[Edge, Iterable[Edge]], radius) -> Shape:
        """
        Fillet edges of this shape.

        :param Union[Edge, Iterable[Edge]] edge: Edge(s) to fillet.
        :param float radius: Fillet radius.
        :return: Filleted shape.
        :rtype: Shape
        """
        itool = FilletIShape(self.ishape)
        if isinstance(edge, Edge):
            itool.AddEdge(edge.ishape, radius)
        else:
            for e in edge: itool.AddEdge(e.ishape, radius)

        itool.Build()
        ishape = itool.Shape()
        return Shape.by_ishape(ishape)

    def thicken(self, thickness: float, tol=1.0e-3, faces: Optional[
        Iterable[Face]] = None) -> Shape:
        """
        Thicken this shape.

        :param float thickness: Thickness.
        :param float tol: Tolerance.
        :param Optional[Iterable[Face]] faces: Faces to remove.
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

    def export_step(self, path: str) -> bool:
        """
        Export this shape to a STEP file.

        :param str path: File path.
        :return: True if successful.
        :rtype: bool
        """
        return self.ishape.ExportSTEP(path)


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
        assert v.Kind() == IShapeKind.Vertex
        self._kind = ShapeKind.VERTEX


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
        assert e.Kind() == IShapeKind.Edge
        self._kind = ShapeKind.EDGE


class Wire(Shape):
    """
    Represents a wire.
    """

    @classmethod
    def by_edge(cls, e: Edge):
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
        assert w.Kind() == IShapeKind.Wire
        self._kind = ShapeKind.WIRE

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
        assert f.Kind() == IShapeKind.Face
        self._kind = ShapeKind.FACE


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
        assert s.Kind() == IShapeKind.Shell
        self._kind = ShapeKind.SHELL


class Solid(Shape):
    """
    Represents a solid.
    """

    @classmethod
    def by_loft(cls, shapes: Iterable[Union[Vertex, Edge, Wire]],
                is_ruled=False, tol=1.0e-6) -> Solid:
        """
        Create a solid by lofting through shapes.

        :param Iterable[Union[Vertex, Edge, Wire]] shapes: Sections.
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

        itool.Build()
        ishape = itool.Shape()
        return Solid(ishape)

    def __init__(self, s: IShape):
        """
        Initialize from an IShape.

        :param IShape s: Underlying topological shape.
        """
        super().__init__(s)
        assert s.Kind() == IShapeKind.Solid
        self._kind = ShapeKind.SOLID


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
        assert cs.Kind() == IShapeKind.CompSolid
        self._kind = ShapeKind.COMPSOLID


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
        assert c.Kind() == IShapeKind.Compound
        self._kind = ShapeKind.COMPOUND


class ShapeTool:
    """
    Base class for shape tools.
    """

    def __init__(self, itool):
        """
        Initialize from an internal tool.

        :param itool: Internal tool.
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


class UniteShapes(ShapeTool):
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


class CutShapes(ShapeTool):
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


class ExtrudeShape(ShapeTool):
    """
    Tool to extrude a shape.
    """

    def __init__(self, s: Shape, v: Vector):
        """
        Initialize with shape and vector.

        :param Shape s: Source shape.
        :param Vector v: Extrusion vector.
        """
        itool = ExtrudeIShape(s.ishape, v.ivector)
        super().__init__(itool)

    def first_shape(self) -> Shape:
        """
        Get the shape at the start of extrusion.

        :return: First shape.
        :rtype: Shape
        """
        return Shape.by_ishape(self._itool.FirstShape())

    def last_shape(self) -> Shape:
        """
        Get the shape at the end of extrusion.

        :return: Last shape.
        :rtype: Shape
        """
        return Shape.by_ishape(self._itool.LastShape())


class ThickenShape(ShapeTool):
    """
    Tool to thicken a shape.
    """

    def __init__(self, s: Shape, thickness: float, tol=1.0e-3, faces: Optional[
        Iterable[Face]] = None):
        """
        Initialize with shape and thickness.

        :param Shape s: Source shape.
        :param float thickness: Thickness.
        :param float tol: Tolerance.
        :param Optional[Iterable[Face]] faces: Faces to remove.
        """
        if faces is None:
            itool = ThickenIShape(s.ishape, thickness)
        else:
            ifaces = [f.ishape for f in faces]
            itool = ThickenIShape(s.ishape, ifaces, thickness, tol)
        super().__init__(itool)


class LoftShape(ShapeTool):
    """
    Tool to loft through sections.
    """

    def __init__(self, is_solid=False, is_ruled=False, tol=1.0e-6):
        """
        Initialize loft tool.

        :param bool is_solid: True to create a solid.
        :param bool is_ruled: True if ruled.
        :param float tol: Tolerance.
        """
        itool = LoftIShape(is_solid, is_ruled, tol)
        super().__init__(itool)

    def build(self) -> None:
        """
        Build the loft.
        """
        self._itool.Build()

    def add_wire(self, w: Wire) -> None:
        """
        Add a section wire.

        :param Wire w: Section wire.
        """
        self._itool.AddWire(w.ishape)


class MapShape:
    """
    Tool to map and access sub-shapes.
    """

    def __init__(self, shape: Shape, kind: ShapeKind):
        """
        Initialize with shape and kind.

        :param Shape shape: Source shape.
        :param ShapeKind kind: Kind of sub-shapes to map.
        """
        self._itool = MapIShape(shape.ishape, kind.value)

    def __len__(self) -> int:
        """
        Number of mapped shapes.

        :return: Count.
        :rtype: int
        """
        return self._itool.Size()

    def __iter__(self) -> Iterator[Shape]:
        """
        Iterate over mapped shapes.

        :return: Iterator of shapes.
        :rtype: Iterator[Shape]
        """
        # OCCT is 1-based
        for i in range(1, self._itool.Size() + 1):
            yield Shape.by_ishape(self._itool.FindShape(i))

    def __getitem__(self, index: int) -> Shape:
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
        return Shape.by_ishape(self._itool.FindShape(index + 1))

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

    def find_shape(self, index: int) -> Shape:
        """
        Find shape by 0-based index.

        :param int index: 0-based index.
        :return: Sub-shape.
        :rtype: Shape
        """
        # OCCT is 1-based, Python is 0-based
        ishape = self._itool.FindShape(index + 1)
        return Shape.by_ishape(ishape)

    def find_index(self, shape: Shape) -> Optional[int]:
        """
        Find 0-based index of a shape.

        :param Shape shape: Sub-shape.
        :return: 0-based index, or None if not found.
        :rtype: Optional[int]
        """
        # OCCT is 1-based, Python is 0-based
        indx = self._itool.FindIndex(shape.ishape)
        return None if indx <= 0 else indx - 1

    def contains(self, shape: Shape) -> bool:
        """
        Check if a shape is in the map.

        :param Shape shape: Sub-shape.
        :return: True if found.
        :rtype: bool
        """
        return self._itool.Contains(shape.ishape)


class ExploreShape:
    """
    Tool to explore sub-shapes.
    """

    def __init__(self, shape: Shape, find: ShapeKind, ignore: ShapeKind = ShapeKind.SHAPE):
        """
        Initialize explore tool.

        :param Shape shape: Source shape.
        :param ShapeKind find: Kind of shapes to find.
        :param ShapeKind ignore: Kind of shapes to ignore.
        """
        self._shape = shape
        self._find = find
        self._ignore = ignore

    def __iter__(self) -> Iterator[Shape]:
        """
        Iterate over discovered shapes.

        :return: Iterator of shapes.
        :rtype: Iterator[Shape]
        """
        itool = ExploreIShape(self._shape.ishape, self._find.value, self._ignore.value)
        while itool.More():
            yield Shape.by_ishape(itool.Current())
            itool.Next()
