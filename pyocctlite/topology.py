from __future__ import annotations

from enum import Enum
from typing import Iterable, Iterator, Optional, Self, Union

from pyocctlite._occtlite import (CopyIShape, ExploreIShape, ExtrudeIShape, FilletIShape, IShape,
                                  IShapeKind, LoftIShape, MapIShape, ThickenIShape, TransformIShape,
                                  UniteIShapes)

from pyocctlite.geometry import Curve, Curve2D, Point, Surface, Transform, TrimmedCurve, Vector

__all__ = ['Shape', 'Vertex', 'Edge', 'Wire', 'Face', 'Shell', 'Solid', 'CompSolid', 'Compound',
           'UniteShapes', 'ExtrudeShape', 'ThickenShape', 'LoftShape', 'ShapeKind', 'MapShape',
           'ExploreShape']


class ShapeKind(Enum):
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

    @staticmethod
    def by_ishape(ishape: IShape) -> Shape:
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
        shapes = [Shape.by_ishape(ishape) for ishape in ishapes]
        return shapes

    def __init__(self, s: IShape):
        assert isinstance(s, IShape)
        self._ishape = s
        self._kind = ShapeKind.SHAPE

    @property
    def ishape(self) -> IShape:
        return self._ishape

    @property
    def kind(self) -> ShapeKind:
        return self._kind

    def explore(self, find: ShapeKind, ignore: ShapeKind = ShapeKind.SHAPE) -> ExploreShape:
        return ExploreShape(self, find, ignore)

    def map(self, kind: ShapeKind) -> MapShape:
        return MapShape(self, kind)

    def vertices(self) -> Union[MapShape, Iterable[Vertex]]:
        return self.map(ShapeKind.VERTEX)

    def edges(self) -> Union[MapShape, Iterable[Edge]]:
        return self.map(ShapeKind.EDGE)

    def wires(self) -> Union[MapShape, Iterable[Wire]]:
        return self.map(ShapeKind.WIRE)

    def faces(self) -> Union[MapShape, Iterable[Face]]:
        return self.map(ShapeKind.FACE)

    def shells(self) -> Union[MapShape, Iterable[Shell]]:
        return self.map(ShapeKind.SHELL)

    def solids(self) -> Union[MapShape, Iterable[Solid]]:
        return self.map(ShapeKind.SOLID)

    def compsolids(self) -> Union[MapShape, Iterable[CompSolid]]:
        return self.map(ShapeKind.COMPSOLID)

    def compounds(self) -> Union[MapShape, Iterable[Compound]]:
        return self.map(ShapeKind.COMPOUND)

    def copy(self) -> Self:
        ishape = CopyIShape(self.ishape).Shape()
        return Shape.by_ishape(ishape)

    def mirror(self, origin: Point, normal: Vector) -> Self:
        t = Transform.mirror(origin, normal)
        ishape = TransformIShape(self.ishape, t.itransform).Shape()
        return Shape.by_ishape(ishape)

    def extrude(self, vector: Vector) -> Shape:
        ishape = ExtrudeIShape(self.ishape, vector.ivector).Shape()
        return Shape.by_ishape(ishape)

    def unite(self, other: Shape) -> Shape:
        ishape = UniteIShapes(self.ishape, other.ishape).Shape()
        return Shape.by_ishape(ishape)

    def fillet(self, edge: Union[Edge, Iterable[Edge]], radius) -> Shape:
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
        if faces is None:
            itool = ThickenIShape(self.ishape, thickness)
        else:
            ifaces = [f.ishape for f in faces]
            itool = ThickenIShape(self.ishape, ifaces, thickness, tol)

        ishape = itool.Shape()
        return Shape.by_ishape(ishape)

    def export_step(self, path: str) -> bool:
        return self.ishape.ExportSTEP(path)


class Vertex(Shape):

    def __init__(self, v: IShape):
        super().__init__(v)
        assert v.Kind() == IShapeKind.Vertex
        self._kind = ShapeKind.VERTEX


class Edge(Shape):

    @classmethod
    def by_curve(cls, c: Curve) -> Edge:
        iedge = IShape.MakeEdge(c.icurve)
        return cls(iedge)

    @classmethod
    def by_curve2d(cls, c: Curve2D, s: Surface) -> Edge:
        iedge = IShape.MakeEdge(c.icurve, s.isurface)
        return cls(iedge)

    @classmethod
    def by_points(cls, p1: Point, p2: Point) -> Edge:
        iedge = IShape.MakeEdge(p1.ipoint, p2.ipoint)
        return cls(iedge)

    @classmethod
    def by_circular_arc(cls, p1: Point, p2: Point, p3: Point) -> Edge:
        c = TrimmedCurve.by_circular_arc(p1, p2, p3)
        iedge = IShape.MakeEdge(c.icurve)
        return cls(iedge)

    def __init__(self, e: IShape):
        super().__init__(e)
        assert e.Kind() == IShapeKind.Edge
        self._kind = ShapeKind.EDGE


class Wire(Shape):

    @classmethod
    def by_edge(cls, e: Edge):
        iwire = IShape.MakeWire(e.ishape)
        return cls(iwire)

    @classmethod
    def by_edges(cls, edges: Iterable[Edge]) -> Wire:
        iedges = [e.ishape for e in edges]
        iwire = IShape.MakeWire(iedges)
        return cls(iwire)

    def __init__(self, w: IShape):
        super().__init__(w)
        assert w.Kind() == IShapeKind.Wire
        self._kind = ShapeKind.WIRE

    def combine(self, other: Wire) -> Wire:
        iwire = IShape.MakeWire(self.ishape, other.ishape)
        return Wire(iwire)


class Face(Shape):

    @classmethod
    def by_wire(cls, w: Wire) -> Face:
        iface = IShape.MakeFace(w.ishape)
        return cls(iface)

    def __init__(self, f: IShape):
        super().__init__(f)
        assert f.Kind() == IShapeKind.Face
        self._kind = ShapeKind.FACE


class Shell(Shape):

    def __init__(self, s: IShape):
        super().__init__(s)
        assert s.Kind() == IShapeKind.Shell
        self._kind = ShapeKind.SHELL


class Solid(Shape):

    @classmethod
    def by_loft(cls, shapes: Iterable[Union[Vertex, Edge, Wire]],
                is_ruled=False, tol=1.0e-6) -> Solid:
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
        super().__init__(s)
        assert s.Kind() == IShapeKind.Solid
        self._kind = ShapeKind.SOLID


class CompSolid(Shape):

    def __init__(self, cs: IShape):
        super().__init__(cs)
        assert cs.Kind() == IShapeKind.CompSolid
        self._kind = ShapeKind.COMPSOLID


class Compound(Shape):

    def __init__(self, c: IShape):
        super().__init__(c)
        assert c.Kind() == IShapeKind.Compound
        self._kind = ShapeKind.COMPOUND


class ShapeTool:

    def __init__(self, itool):
        self._itool = itool

    @property
    def is_done(self) -> bool:
        return self._itool.IsDone()

    def shape(self) -> Shape:
        return Shape.by_ishape(self._itool.Shape())

    def generated_shapes(self, s: Shape) -> list[Shape]:
        return Shape.by_ishapes(self._itool.GeneratedShapes(s.ishape))


class UniteShapes(ShapeTool):

    def __init__(self, tool: Shape, target: Shape):
        itool = UniteIShapes(tool.ishape, target.ishape)
        super().__init__(itool)

    def intersection_edges(self) -> list[Edge]:
        return [Edge(e) for e in self._itool.IntersectionEdges()]


class ExtrudeShape(ShapeTool):

    def __init__(self, s: Shape, v: Vector):
        itool = ExtrudeIShape(s.ishape, v.ivector)
        super().__init__(itool)

    def first_shape(self) -> Shape:
        return Shape.by_ishape(self._itool.FirstShape())

    def last_shape(self) -> Shape:
        return Shape.by_ishape(self._itool.LastShape())


class ThickenShape(ShapeTool):

    def __init__(self, s: Shape, thickness: float, tol=1.0e-3, faces: Optional[Iterable[Face]] = None):
        if faces is None:
            itool = ThickenIShape(s.ishape, thickness)
        else:
            ifaces = [f.ishape for f in faces]
            itool = ThickenIShape(s.ishape, ifaces, thickness, tol)
        super().__init__(itool)


class LoftShape(ShapeTool):

    def __init__(self, is_solid=False, is_ruled=False, tol=1.0e-6):
        itool = LoftIShape(is_solid, is_ruled, tol)
        super().__init__(itool)

    def build(self) -> None:
        self._itool.Build()

    def add_wire(self, w: Wire) -> None:
        self._itool.AddWire(w.ishape)


class MapShape:

    def __init__(self, shape: Shape, kind: ShapeKind):
        self._itool = MapIShape(shape.ishape, kind.value)

    def __len__(self) -> int:
        return self._itool.Size()

    def __iter__(self) -> Iterator[Shape]:
        # OCCT is 1-based
        for i in range(1, self._itool.Size() + 1):
            yield Shape.by_ishape(self._itool.FindShape(i))

    def __getitem__(self, index: int) -> Shape:
        n = len(self)
        if index < 0:
            index += n
        if index < 0 or index >= n:
            raise IndexError(index)

        # Python is 0-based, OCCT is 1-based
        return Shape.by_ishape(self._itool.FindShape(index + 1))

    @property
    def size(self) -> int:
        return self._itool.Size()

    @property
    def extent(self) -> int:
        return self._itool.Extent()

    def find_shape(self, index: int) -> Shape:
        # OCCT is 1-based, Python is 0-based
        ishape = self._itool.FindShape(index + 1)
        return Shape.by_ishape(ishape)

    def find_index(self, shape: Shape) -> Optional[int]:
        # OCCT is 1-based, Python is 0-based
        indx = self._itool.FindIndex(shape.ishape)
        return None if indx <= 0 else indx - 1

    def contains(self, shape: Shape) -> bool:
        return self._itool.Contains(shape.ishape)


class ExploreShape:

    def __init__(self, shape: Shape, find: ShapeKind, ignore: ShapeKind = ShapeKind.SHAPE):
        self._shape = shape
        self._find = find
        self._ignore = ignore

    def __iter__(self) -> Iterator[Shape]:
        itool = ExploreIShape(self._shape.ishape, self._find.value, self._ignore.value)
        while itool.More():
            yield Shape.by_ishape(itool.Current())
            itool.Next()
