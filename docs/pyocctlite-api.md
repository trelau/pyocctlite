# pyocctlite.drawing

```
class Symbol(StrEnum)
class LinePattern(Enum)
    LinePattern.SOLID
    LinePattern.HIDDEN
    LinePattern.CENTER
    LinePattern.PHANTOM
class TextAlign(Enum)
    TextAlign.LEFT
    TextAlign.CENTER
    TextAlign.RIGHT
class Paper(Enum)
    Paper.A
    Paper.B
    Paper.C
    Paper.D
    Paper.E
class Stroke
    Stroke(color: Color = _BLACK, width: float | None = None, pattern: LinePattern = LinePattern.SOLID)
    .color: Color
    .width: float | None
    .pattern: LinePattern
class Canvas
    Canvas(width: float, height: float, units_per_inch: float = 1.0)
    .width: float
    .height: float
    .units_per_inch: float
    .thin_width: float
    .thick_width: float
    .text_height: float
    .text_width(text: str, height: float | None = None) -> float
    .add_line(p1: Point2D, p2: Point2D, stroke: Stroke | None = None) -> None
    .add_polyline(points: Iterable[Point2D], stroke: Stroke | None = None) -> None
    .add_curve(curve: Curve2D, stroke: Stroke | None = None) -> None
    .add_edges(edges: Edge | Iterable[Edge], stroke: Stroke | None = None) -> None
    .add_polygon(points: Iterable[Point2D], color: Color = _BLACK) -> None
    .add_text(at: Point2D, text: str, height: float | None = None, color: Color = _BLACK, angle: float = 0.0, align: TextAlign = TextAlign.LEFT) -> None
    .add_arrow(tip: Point2D, direction: Vector2D, color: Color = _BLACK) -> None
    .add_leader(tip: Point2D, at: Point2D, text: str) -> None
    .add_linear_dimension(p1: Point2D, p2: Point2D, offset: float, text: str, along: Vector2D | None = None) -> None
    .add_radial_dimension(center: Point2D, radius: float, text: str, angle: float = math.pi / 4.0) -> None
    .add_angular_dimension(vertex: Point2D, p1: Point2D, p2: Point2D, radius: float, text: str) -> None
    .add_center_mark(center: Point2D, radius: float) -> None
    .add_table(top_left: Point2D, rows: Iterable[Iterable[str]], column_widths: Iterable[float], row_height: float | None = None, height: float | None = None) -> None
    .add_feature_control_frame(at: Point2D, cells: Iterable[str]) -> None
    .add_datum_feature(tip: Point2D, at: Point2D, letter: str) -> None
    .add_surface_finish(tip: Point2D, value: str) -> None
    .write(path: str, dpi: int = _DEFAULT_DPI) -> None
class SheetView
    SheetView(sheet: Sheet, shape: Shape, camera: Camera, scale: float, origin: Point2D, min_point: Point2D, max_point: Point2D, lines: list[_ViewLine] | None = None)
    .sheet: Sheet
    .shape: Shape
    .camera: Camera
    .scale: float
    .origin: Point2D
    .min_point: Point2D
    .max_point: Point2D
    .lines: list[_ViewLine]
    .to_sheet(point: Point) -> Point2D
    .add_dimension(p1: Point, p2: Point, offset: float, along: Vector2D | None = None, text: str | None = None, prefix: str = '', suffix: str = '', decimals: int = 2) -> None
    .add_radius(edge: Edge, angle: float = math.pi / 4.0, text: str | None = None, suffix: str = '', decimals: int = 2) -> None
    .add_diameter(edge: Edge, angle: float = math.pi / 4.0, text: str | None = None, prefix: str = '', suffix: str = '', decimals: int = 2) -> None
    .add_center_line(p1: Point, p2: Point) -> None
    .add_cutting_plane(origin: Point, normal: Vector, label: str) -> None
    .add_label(text: str, gap: float | None = None) -> None
    .add_angle(vertex: Point, p1: Point, p2: Point, radius: float, text: str | None = None) -> None
    .add_center_mark(edge: Edge) -> None
class Sheet(Canvas)
    Sheet(paper: Paper = Paper.B, units_per_inch: float = 1.0)
    .paper: Paper
    .add_view(shape: Shape, view: View | Camera, at: Point2D, scale: float = 1.0, hidden: bool = True) -> SheetView
    .add_projected_view(parent: SheetView, view: View, gap: float, hidden: bool = True) -> SheetView
    .add_section_view(parent: SheetView, origin: Point, normal: Vector, gap: float, label: str = 'A') -> SheetView
    .add_detail_view(parent: SheetView, center: Point, radius: float, at: Point2D, scale: float, label: str = 'B') -> SheetView
    .add_zones(columns: int, rows: int) -> None
    .add_title_block(title: str, number: str = '', revision: str = '', date: str = '', drawn_by: str = '', scale: float | None = None) -> None
```

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
    .add(other: Vector2D) -> Vector2D
    .subtract(other: Vector2D) -> Vector2D
    .reverse() -> Vector2D
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
    .points(deflection: float, angular_deflection: float = 0.2) -> list[Point2D]
class Line2D(Curve2D)
    Line2D.by_points(p1: Point2D, p2: Point2D) -> Line2D
    .origin: Point2D
    .direction: Vector2D
class Circle2D(Curve2D)
    Circle2D.by_radius(radius: float, frame: Frame2D | None = None) -> Circle2D
    .frame: Frame2D
    .radius: float
class Ellipse2D(Curve2D)
    Ellipse2D.by_radii(rmajor: float, rminor: float, frame: Frame2D | None = None) -> Ellipse2D
    .frame: Frame2D
    .rmajor: float
    .rminor: float
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
    .add(other: Vector) -> Vector
    .subtract(other: Vector) -> Vector
    .reverse() -> Vector
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
class Ellipse(Curve)
    Ellipse.by_radii(rmajor: float, rminor: float, frame: Frame | None = None) -> Ellipse
    .frame: Frame
    .rmajor: float
    .rminor: float
class TrimmedCurve(Curve)
    TrimmedCurve.by_circular_arc(p1: Point, p2: Point, p3: Point) -> TrimmedCurve
class BSplineCurve(Curve)
    BSplineCurve.by_interpolation(points: Iterable[Point], tol: float = 1e-07) -> BSplineCurve
class Surface
class CylindricalSurface(Surface)
    CylindricalSurface.by_radius(radius: float, frame: Frame | None = None) -> CylindricalSurface
    .frame: Frame
    .radius: float
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
class Box(Shape)
    Box.by_size(dx: float, dy: float, dz: float, frame: Frame | None = None) -> Box
    .bottom_face: Face
    .top_face: Face
    .back_face: Face
    .front_face: Face
    .left_face: Face
    .right_face: Face
class Sphere(Shape)
    Sphere.by_size(radius: float, frame: Frame | None = None) -> Sphere
    .face: Face
class Cylinder(Shape)
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
    Shading.HIDDEN_LINE
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
    .right: Vector
    .project(point: Point) -> Point2D
class Callout
    Callout(target: Shape | Point, text: str)
    .target: Shape | Point
    .text: str
class Section
    Section.by_plane(origin: Point, normal: Vector, color: tuple[float, float, float] | None = None) -> Section
    .origin: Point
    .normal: Vector
    .color: tuple[float, float, float] | None
class RenderShapes
    RenderShapes(width: int = 1200, height: int = 900)
    .add_shape(shape: Shape | Styled) -> None
    .add_numbered_faces(shape: Shape, faces: Face | Iterable[Face] | None = None) -> None
    .add_numbered_edges(shape: Shape, edges: Edge | Iterable[Edge] | None = None) -> None
    .add_callout(callout: Callout) -> None
    .add_line(p1: Point, p2: Point, color: tuple[float, float, float] = _LINE_COLOR, width: float = _LINE_WIDTH, dashed: bool = False) -> None
    .add_edges(edges: Edge | Iterable[Edge], color: tuple[float, float, float] = _LINE_COLOR, width: float = _LINE_WIDTH, dashed: bool = False) -> None
    .add_text(point: Point, text: str, height: float = _TEXT_HEIGHT, color: tuple[float, float, float] = _LINE_COLOR, background: tuple[float, float, float] | None = None) -> None
    .set_section(section: Section) -> None
    .render(path: str, view: View | Camera = View.ISO, shading: Shading = Shading.LIGHT, labels: bool = True) -> None
    .render_views(path: str, shading: Shading = Shading.LIGHT, labels: bool = True) -> None
    .visible_pixels() -> dict[int, int]
render_image(shapes: Shape | Styled | Iterable[Shape | Styled], path: str, view: View | Camera = View.ISO, width: int = 1200, height: int = 900, callouts: Callout | Iterable[Callout] = (), shading: Shading = Shading.LIGHT, labels: bool = True, section: Section | None = None) -> None
render_faces(shape: Shape, path: str, view: View | Camera = View.ISO, width: int = 1200, height: int = 900, shading: Shading = Shading.LIGHT, labels: bool = True, faces: Face | Iterable[Face] | None = None) -> dict[int, int]
render_edges(shape: Shape, path: str, view: View | Camera = View.ISO, width: int = 1200, height: int = 900, shading: Shading = Shading.LIGHT, labels: bool = True, edges: Edge | Iterable[Edge] | None = None) -> dict[int, int]
render_views(shapes: Shape | Styled | Iterable[Shape | Styled], path: str, width: int = 1500, height: int = 1124, shading: Shading = Shading.LIGHT, labels: bool = True, section: Section | None = None) -> None
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
    .unite(other: Shape | Iterable[Shape], tol: float = 0.0) -> Shape
    .cut(other: Shape | Iterable[Shape], tol: float = 0.0) -> Shape
    .intersect(other: Shape | Iterable[Shape], tol: float = 0.0) -> Shape
    .fillet(edges: Edge | Iterable[Edge], radius: float) -> Shape
    .chamfer(edges: Edge | Iterable[Edge], distance: float) -> Shape
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
    Edge.by_interpolation(points: Iterable[Point], tol: float = 1e-07) -> Edge
    .curve: Curve | None
    .points(deflection: float, angular_deflection: float = 0.2) -> list[Point]
    .extrude(vector: Vector) -> Face
    .revolve(axis: Axis) -> Face
class Wire(Shape)
    Wire.by_edge(e: Edge) -> Wire
    Wire.by_edges(edges: Iterable[Edge]) -> Wire
    .combine(other: Wire) -> Wire
    .offset(distance: float, spine: Face | None = None) -> Shape
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
    UniteShapes(target: Shape | Iterable[Shape], tool: Shape | Iterable[Shape], tol: float = 0.0)
class CutShapes(BooleanShapes)
    CutShapes(target: Shape | Iterable[Shape], tool: Shape | Iterable[Shape], tol: float = 0.0)
class IntersectShapes(BooleanShapes)
    IntersectShapes(target: Shape | Iterable[Shape], tool: Shape | Iterable[Shape], tol: float = 0.0)
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
class OffsetWire(ShapeTool)
    OffsetWire(w: Wire, distance: float, spine: Face | None = None)
class LoftShape(ShapeTool)
    LoftShape(is_solid: bool = False, is_ruled: bool = False, tol: float = 1e-06)
    .add_wire(w: Wire) -> None
class HiddenLineShape
    HiddenLineShape(s: Shape, direction: Vector, up: Vector)
    .visible() -> Compound
    .hidden() -> Compound
    .visible_smooth() -> Compound
    .hidden_smooth() -> Compound
class MapShape(Sequence[T])
    MapShape(shape: Shape, kind: type[T])
    .__len__() -> int
    .__iter__() -> Iterator[T]
    .__getitem__(index: int) -> T
    .__getitem__(index: slice) -> list[T]
    .size: int
    .extent: int
    .find_shape(index: int) -> T
    .find_index(shape: T) -> int | None
    .contains(shape: T) -> bool
    .__contains__(shape: object) -> bool
class ExploreShape(Generic[T])
    ExploreShape(shape: Shape, find: type[T], ignore: type[Shape] | None = None)
    .__iter__() -> Iterator[T]
```
