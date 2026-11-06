# pyocctlite.errors

```
class BuildFailed
class KindMismatch
```

# pyocctlite.geometry

```
class Point2D
    Point2D.by_xy(x: float, y: float) -> Point2D
    .x: float
    .y: float
    .translate(vector: Vector2D) -> Point2D
    .distance(other: Point2D) -> float
    .is_equal(other: Point2D, tol: float = 1e-07) -> bool
class Vector2D
    Vector2D.by_xy(x: float, y: float) -> Vector2D
    Vector2D.by_points(p1: Point2D, p2: Point2D) -> Vector2D
    .x: float
    .y: float
    .magnitude: float
    .scale(scale: float) -> Vector2D
    .normalize() -> Vector2D
    .dot(other: Vector2D) -> float
    .cross(other: Vector2D) -> float
    .is_equal(other: Vector2D, tol: float = 1e-07, angular_tol: float = 1e-12) -> bool
class Frame2D
    Frame2D.by_origin(origin: Point2D) -> Frame2D
    Frame2D.by_vector(origin: Point2D, xvec: Vector2D) -> Frame2D
    .origin: Point2D
    .x_direction: Vector2D
    .y_direction: Vector2D
class Curve2D
    .evaluate(u: float) -> Point2D
    .derivative(u: float, order: int = 1) -> Vector2D
    .is_closed: bool
    .is_periodic: bool
    .first_parameter: float
    .last_parameter: float
class Ellipse2D(Curve2D)
    Ellipse2D.by_radii(rmajor: float, rminor: float, frame: Frame2D | None = None) -> Ellipse2D
class TrimmedCurve2D(Curve2D)
    TrimmedCurve2D.by_curve(curve: Curve2D, u0: float, u1: float) -> TrimmedCurve2D
    TrimmedCurve2D.by_points(p1: Point2D, p2: Point2D) -> TrimmedCurve2D
class Point
    Point.by_xyz(x: float, y: float, z: float) -> Point
    .x: float
    .y: float
    .z: float
    .translate(vector: Vector) -> Point
    .distance(other: Point) -> float
    .is_equal(other: Point, tol: float = 1e-07) -> bool
class Vector
    Vector.by_xyz(x: float, y: float, z: float) -> Vector
    Vector.by_points(p1: Point, p2: Point) -> Vector
    .x: float
    .y: float
    .z: float
    .magnitude: float
    .scale(scale: float) -> Vector
    .normalize() -> Vector
    .dot(other: Vector) -> float
    .cross(other: Vector) -> Vector
    .is_equal(other: Vector, tol: float = 1e-07, angular_tol: float = 1e-12) -> bool
class Axis
    Axis.by_vector(origin: Point, direction: Vector) -> Axis
    .origin: Point
    .direction: Vector
class Frame
    Frame.by_origin(origin: Point) -> Frame
    Frame.by_vectors(origin: Point, xvec: Vector, zvec: Vector) -> Frame
    .origin: Point
    .axis: Axis
    .x_direction: Vector
    .y_direction: Vector
    .z_direction: Vector
class Transform
    Transform.by_mirror(origin: Point, normal: Vector) -> Transform
    Transform.by_rotation(axis: Axis, angle: float) -> Transform
    Transform.by_translation(vector: Vector) -> Transform
class BoundingBox
    .min_point: Point
    .max_point: Point
    .dx: float
    .dy: float
    .dz: float
    .center: Point
class Curve
    .evaluate(u: float) -> Point
    .derivative(u: float, order: int = 1) -> Vector
    .is_closed: bool
    .is_periodic: bool
    .first_parameter: float
    .last_parameter: float
class Line(Curve)
    Line.by_points(p1: Point, p2: Point) -> Line
    .origin: Point
    .direction: Vector
class Circle(Curve)
    Circle.by_radius(radius: float, frame: Frame | None = None) -> Circle
    Circle.by_points(p1: Point, p2: Point, p3: Point) -> Circle
    .frame: Frame
    .radius: float
class TrimmedCurve(Curve)
    TrimmedCurve.by_circular_arc(p1: Point, p2: Point, p3: Point) -> TrimmedCurve
class Surface
class CylindricalSurface(Surface)
    CylindricalSurface.by_radius(radius: float, frame: Frame | None = None) -> CylindricalSurface
class ProjectPointToCurve
    ProjectPointToCurve(p: Point, c: Curve, u0: float | None = None, u1: float | None = None)
    .perform(p: Point) -> None
    .is_done: bool
    .num_points: int
    .point(index: int) -> Point
    .parameter(index: int) -> float
    .distance(index: int) -> float
    .nearest_point: Point
    .nearest_parameter: float
    .nearest_distance: float
```

# pyocctlite.primitives

```
class Box(Solid)
    Box.by_size(dx: float, dy: float, dz: float, frame: Frame | None = None) -> Box
    .bottom_face: Face
    .top_face: Face
    .back_face: Face
    .front_face: Face
    .left_face: Face
    .right_face: Face
class Sphere(Solid)
    Sphere.by_size(radius: float, frame: Frame | None = None) -> Sphere
    .face: Face
class Cylinder(Solid)
    Cylinder.by_size(radius: float, height: float, frame: Frame | None = None) -> Cylinder
    .bottom_face: Face
    .top_face: Face
    .lateral_face: Face
```

# pyocctlite.rendering

```
class View(Enum)
    View.ISO
    View.TOP
    View.BOTTOM
    View.FRONT
    View.BACK
    View.LEFT
    View.RIGHT
class Shading(Enum)
    Shading.LIGHT
    Shading.DEPTH
class Styled
    Styled(shape: Shape, color: tuple[float, float, float] | None = None, transparency: float = 0.0)
    .shape: Shape
    .color: tuple[float, float, float]
    .transparency: float
class Camera
    Camera.by_direction(direction: Vector, up: Vector | None = None, target: Point | None = None, span: float | None = None) -> Camera
    Camera.by_position(position: Point, target: Point, up: Vector | None = None, span: float | None = None) -> Camera
    Camera.by_view(view: View, target: Point | None = None, span: float | None = None) -> Camera
    .direction: Vector
    .up: Vector
    .target: Point | None
    .span: float | None
    .label: str
class Callout
    Callout(target: Shape | Point, text: str)
    .target: Shape | Point
    .text: str
render_image(shapes: Shape | Styled | Iterable[Shape | Styled], path: str, view: View | Camera = View.ISO, width: int = 1200, height: int = 900, callouts: Callout | Iterable[Callout] = (), shading: Shading = Shading.LIGHT, labels: bool = True) -> None
render_faces(shape: Shape, path: str, view: View | Camera = View.ISO, width: int = 1200, height: int = 900, shading: Shading = Shading.LIGHT, labels: bool = True) -> dict[int, int]
render_edges(shape: Shape, path: str, view: View | Camera = View.ISO, width: int = 1200, height: int = 900, shading: Shading = Shading.LIGHT, labels: bool = True) -> dict[int, int]
render_views(shapes: Shape | Styled | Iterable[Shape | Styled], path: str, width: int = 1500, height: int = 1124, shading: Shading = Shading.LIGHT, labels: bool = True) -> None
```

# pyocctlite.topology

```
class ShapeKind(Enum)
    ShapeKind.SHAPE
    ShapeKind.VERTEX
    ShapeKind.EDGE
    ShapeKind.WIRE
    ShapeKind.FACE
    ShapeKind.SHELL
    ShapeKind.SOLID
    ShapeKind.COMPSOLID
    ShapeKind.COMPOUND
class Shape
    .kind: ShapeKind
    .length: float
    .area: float
    .volume: float
    .bounding_box: BoundingBox
    .centroid: Point
    .is_valid: bool
    .is_equal(other: Shape) -> bool
    .explore(find: type[T], ignore: type[Shape] | None = None) -> ExploreShape[T]
    .map(kind: type[T]) -> MapShape[T]
    .vertices() -> MapShape[Vertex]
    .edges() -> MapShape[Edge]
    .wires() -> MapShape[Wire]
    .faces() -> MapShape[Face]
    .shells() -> MapShape[Shell]
    .solids() -> MapShape[Solid]
    .compsolids() -> MapShape[CompSolid]
    .compounds() -> MapShape[Compound]
    .copy() -> Self
    .mirror(origin: Point, normal: Vector) -> Self
    .rotate(axis: Axis, angle: float) -> Self
    .translate(vector: Vector) -> Self
    .extrude(vector: Vector) -> Shape
    .revolve(axis: Axis) -> Shape
    .unite(other: Shape | Iterable[Shape]) -> Shape
    .cut(other: Shape | Iterable[Shape]) -> Shape
    .intersect(other: Shape | Iterable[Shape]) -> Shape
    .fillet(edge: Edge | Iterable[Edge], radius: float) -> Shape
    .chamfer(edge: Edge | Iterable[Edge], distance: float) -> Shape
    .thicken(thickness: float, faces: Face | Iterable[Face] | None = None, tol: float = 0.001) -> Shape
    .export_step(path: str) -> None
class Vertex(Shape)
    Vertex.by_point(p: Point) -> Vertex
    .point: Point
    .extrude(vector: Vector) -> Edge
    .revolve(axis: Axis) -> Edge
class Edge(Shape)
    Edge.by_curve(c: Curve) -> Edge
    Edge.by_curve2d(c: Curve2D, s: Surface) -> Edge
    Edge.by_points(p1: Point, p2: Point) -> Edge
    Edge.by_vertices(v1: Vertex, v2: Vertex) -> Edge
    Edge.by_circular_arc(p1: Point, p2: Point, p3: Point) -> Edge
    .curve: Curve | None
    .extrude(vector: Vector) -> Face
    .revolve(axis: Axis) -> Face
class Wire(Shape)
    Wire.by_edge(e: Edge) -> Wire
    Wire.by_edges(edges: Iterable[Edge]) -> Wire
    .combine(other: Wire) -> Wire
    .extrude(vector: Vector) -> Shell
    .revolve(axis: Axis) -> Shell
class Face(Shape)
    Face.by_wire(w: Wire) -> Face
    .extrude(vector: Vector) -> Solid
    .revolve(axis: Axis) -> Solid
class Shell(Shape)
    .extrude(vector: Vector) -> CompSolid
    .revolve(axis: Axis) -> CompSolid
class Solid(Shape)
    Solid.by_loft(shapes: Iterable[Vertex | Edge | Wire], is_ruled: bool = False, tol: float = 1e-06) -> Solid
class CompSolid(Shape)
class Compound(Shape)
    Compound.by_shapes(shapes: Iterable[Shape]) -> Compound
class ShapeTool
    .is_done: bool
    .build() -> None
    .shape() -> Shape
    .generated_shapes(s: Shape) -> list[Shape]
    .modified_shapes(s: Shape) -> list[Shape]
    .is_deleted(s: Shape) -> bool
class BooleanShapes(ShapeTool)
    .intersection_edges() -> list[Edge]
class UniteShapes(BooleanShapes)
    UniteShapes(target: Shape | Iterable[Shape], tool: Shape | Iterable[Shape])
class CutShapes(BooleanShapes)
    CutShapes(target: Shape | Iterable[Shape], tool: Shape | Iterable[Shape])
class IntersectShapes(BooleanShapes)
    IntersectShapes(target: Shape | Iterable[Shape], tool: Shape | Iterable[Shape])
class CopyShape(ShapeTool, Generic[T])
    CopyShape(s: T, copy_geom: bool = True)
    .shape() -> T
    .modified_shape(s: S) -> S
class TransformShape(ShapeTool, Generic[T])
    TransformShape(s: T, t: Transform, copy_geom: bool = False)
    .shape() -> T
    .modified_shape(s: S) -> S
class ExtrudeShape(ShapeTool, Generic[T])
    ExtrudeShape(s: T, v: Vector)
    .shape(self: ExtrudeShape[Vertex]) -> Edge
    .shape(self: ExtrudeShape[Edge]) -> Face
    .shape(self: ExtrudeShape[Wire]) -> Shell
    .shape(self: ExtrudeShape[Face]) -> Solid
    .shape(self: ExtrudeShape[Shell]) -> CompSolid
    .shape() -> Shape
    .first_shape() -> T
    .first_shape(s: S) -> S
    .last_shape() -> T
    .last_shape(s: S) -> S
class RevolveShape(ShapeTool, Generic[T])
    RevolveShape(s: T, axis: Axis)
    .shape(self: RevolveShape[Vertex]) -> Edge
    .shape(self: RevolveShape[Edge]) -> Face
    .shape(self: RevolveShape[Wire]) -> Shell
    .shape(self: RevolveShape[Face]) -> Solid
    .shape(self: RevolveShape[Shell]) -> CompSolid
    .shape() -> Shape
class FilletShape(ShapeTool)
    FilletShape(s: Shape)
    .add_edge(e: Edge, radius: float) -> None
class ChamferShape(ShapeTool)
    ChamferShape(s: Shape)
    .add_edge(e: Edge, distance: float) -> None
class ThickenShape(ShapeTool)
    ThickenShape(s: Shape, thickness: float, faces: Face | Iterable[Face] | None = None, tol: float = 0.001)
class LoftShape(ShapeTool)
    LoftShape(is_solid: bool = False, is_ruled: bool = False, tol: float = 1e-06)
    .add_wire(w: Wire) -> None
class MapShape(Generic[T])
    MapShape(shape: Shape, kind: type[T])
    .__len__() -> int
    .__iter__() -> Iterator[T]
    .__getitem__(index: int) -> T
    .size: int
    .extent: int
    .find_shape(index: int) -> T
    .find_index(shape: T) -> int | None
    .contains(shape: T) -> bool
    .__contains__(shape: T) -> bool
class ExploreShape(Generic[T])
    ExploreShape(shape: Shape, find: type[T], ignore: type[Shape] | None = None)
    .__iter__() -> Iterator[T]
```
