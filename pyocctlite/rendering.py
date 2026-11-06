"""
Render shapes to PNG images, with no GPU, display or extra packages needed.

Start with :func:`render_views`, which shows most of a part in one image. Use
:func:`render_image` for one other view, or with a :class:`Camera` to look from any direction or
closer at a feature. Use :class:`Styled` to highlight a sub-shape or see through a part, and
:class:`Callout` to label something on an image. Use :func:`render_faces` or
:func:`render_edges` to tell which face or edge is which. Use :class:`Shading` to show depth.
"""

from __future__ import annotations

import math
import struct
import zlib
from collections.abc import Iterable
from enum import Enum

from pyocctlite._occtlite import RenderIShapes
from pyocctlite.geometry import Point, Vector
from pyocctlite.topology import Shape, Vertex

__all__ = [
    "Callout",
    "Camera",
    "Shading",
    "Styled",
    "View",
    "render_edges",
    "render_faces",
    "render_image",
    "render_views",
]

_DEFAULT_COLOR = (0.72, 0.75, 0.8)

# Faces stay pale behind numbered edges, so that the edge colors stand out
_EDGE_BACKDROP_COLOR = (0.9, 0.9, 0.92)
_SEPARATOR = bytes((190, 190, 190))

# Well-separated colors for telling faces apart, which repeat on parts with more faces
_FACE_COLORS = (
    (0.90, 0.30, 0.30),
    (0.30, 0.60, 0.95),
    (0.35, 0.80, 0.40),
    (0.98, 0.75, 0.20),
    (0.70, 0.40, 0.90),
    (0.20, 0.80, 0.80),
    (0.98, 0.55, 0.20),
    (0.95, 0.50, 0.75),
    (0.60, 0.80, 0.25),
    (0.55, 0.38, 0.25),
    (0.35, 0.40, 0.70),
    (0.60, 0.60, 0.60),
)

# Below this cross product of unit vectors, an up direction is treated as parallel to the view
_PARALLEL_TOLERANCE = 1.0e-7


class View(Enum):
    """
    Standard views for a Z-up model. FRONT looks from -y, RIGHT from +x and TOP from +z with +y up.
    ISO looks from (+x, -y, +z), showing the front, right and top. Each value is the direction
    toward the viewer and the up direction, as (x, y, z) components.
    """

    ISO = ((1.0, -1.0, 1.0), (0.0, 0.0, 1.0))
    TOP = ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0))
    BOTTOM = ((0.0, 0.0, -1.0), (0.0, -1.0, 0.0))
    FRONT = ((0.0, -1.0, 0.0), (0.0, 0.0, 1.0))
    BACK = ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    LEFT = ((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    RIGHT = ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0))


class Shading(Enum):
    """
    How faces are shaded. LIGHT shades a face by the way it faces the light, so parallel faces look
    the same however far apart they are. DEPTH also darkens faces that are farther from the viewer,
    which shows which of them is nearer. It only shows relative depth, from the nearest face to the
    farthest one in each view.
    """

    LIGHT = "light"
    DEPTH = "depth"


class Styled:
    """
    A shape with its appearance in an image.

    Faces take the color and are outlined by dark edges. Edges and vertices that are not part of a
    face take the color and are drawn thicker, which makes them suitable as highlights.

    :ivar Shape shape: Shape to draw.
    :ivar tuple[float, float, float] color: Red, green and blue from 0 to 1.
    :ivar float transparency: From 0 for opaque to 1 for invisible faces.
    """

    def __init__(
        self,
        shape: Shape,
        color: tuple[float, float, float] | None = None,
        transparency: float = 0.0,
    ):
        """
        Initialize from a shape and its appearance.

        :param Shape shape: Shape to draw.
        :param tuple[float, float, float] | None color: Red, green and blue from 0 to 1. Defaults to
            a neutral gray.
        :param float transparency: From 0 for opaque to 1 for invisible faces. Edges of the faces
            stay visible but become lighter.
        :raises ValueError: If a color component or the transparency is not from 0 to 1.
        """
        if color is None:
            color = _DEFAULT_COLOR
        if not (len(color) == 3 and all(0.0 <= c <= 1.0 for c in color)):
            raise ValueError(f"Expected 3 color components from 0 to 1, got {color}.")
        if not 0.0 <= transparency <= 1.0:
            raise ValueError(f"Expected transparency from 0 to 1, got {transparency}.")
        self._shape = shape
        self._color = color
        self._transparency = transparency

    @property
    def shape(self) -> Shape:
        """
        Shape to draw.

        :return: Shape.
        :rtype: Shape
        """
        return self._shape

    @property
    def color(self) -> tuple[float, float, float]:
        """
        Color of the shape.

        :return: Red, green and blue from 0 to 1.
        :rtype: tuple[float, float, float]
        """
        return self._color

    @property
    def transparency(self) -> float:
        """
        Transparency of the faces.

        :return: From 0 for opaque to 1 for invisible.
        :rtype: float
        """
        return self._transparency


class Camera:
    """
    A custom orthographic view, for when the standard views do not show what is needed.

    Views have no perspective, so distance has no effect and a position only sets the direction of
    the view. Everything along the line of sight stays in the image, so use ``span`` and ``target``
    to look closer, and a transparent :class:`Styled` or another direction to see past something in
    front.

    :ivar Vector direction: Direction from the view's center toward the viewer.
    :ivar Vector up: Direction that appears up in the image.
    :ivar Point | None target: Point at the center of the image, or None to fit all shapes.
    :ivar float | None span: Length across the image's smaller side, or None to fit all shapes.
    :ivar str label: Name shown on the image.
    """

    @classmethod
    def by_direction(
        cls,
        direction: Vector,
        up: Vector | None = None,
        target: Point | None = None,
        span: float | None = None,
    ) -> Camera:
        """
        Create a camera from the direction toward the viewer.

        :param Vector direction: Direction from the view's center toward the viewer.
        :param Vector | None up: Direction that appears up in the image. Defaults to +z, or +y if
            looking along z.
        :param Point | None target: Point at the center of the image. Defaults to the center of all
            shapes.
        :param float | None span: Length across the image's smaller side. Defaults to fitting all
            shapes.
        :return: New camera.
        :rtype: Camera
        :raises ValueError: If the direction has no length, up is parallel to it, or the span is not
            positive.
        """
        return cls(direction, up, target, span)

    @classmethod
    def by_position(
        cls,
        position: Point,
        target: Point,
        up: Vector | None = None,
        span: float | None = None,
    ) -> Camera:
        """
        Create a camera that looks from a position at a target.

        :param Point position: Point to look from, which only sets the direction of the view.
        :param Point target: Point at the center of the image.
        :param Vector | None up: Direction that appears up in the image. Defaults to +z, or +y if
            looking along z.
        :param float | None span: Length across the image's smaller side. Defaults to fitting all
            shapes.
        :return: New camera.
        :rtype: Camera
        :raises ValueError: If the points coincide, up is parallel to the view, or the span is not
            positive.
        """
        return cls(Vector.by_points(target, position), up, target, span)

    @classmethod
    def by_view(cls, view: View, target: Point | None = None, span: float | None = None) -> Camera:
        """
        Create a camera from a standard view, usually to look closer at something.

        :param View view: Standard view.
        :param Point | None target: Point at the center of the image. Defaults to the center of all
            shapes.
        :param float | None span: Length across the image's smaller side. Defaults to fitting all
            shapes.
        :return: New camera.
        :rtype: Camera
        :raises ValueError: If the span is not positive.
        """
        direction, up = view.value
        return cls(Vector.by_xyz(*direction), Vector.by_xyz(*up), target, span, view.name)

    def __init__(
        self,
        direction: Vector,
        up: Vector | None = None,
        target: Point | None = None,
        span: float | None = None,
        label: str = "CUSTOM",
    ):
        """
        Initialize from named parts.

        :param Vector direction: Direction from the view's center toward the viewer.
        :param Vector | None up: Direction that appears up in the image. Defaults to +z, or +y if
            looking along z.
        :param Point | None target: Point at the center of the image, or None to fit all shapes.
        :param float | None span: Length across the image's smaller side, or None to fit all
            shapes.
        :param str label: Name shown on the image.
        :raises ValueError: If the direction has no length, up is parallel to it, or the span is not
            positive.
        """
        if direction.magnitude == 0.0:
            raise ValueError("Expected a direction with a length.")
        if span is not None and not 0.0 < span < math.inf:
            raise ValueError(f"Expected a positive span, got {span}.")

        unit = direction.normalize()
        if up is None:
            up = Vector.by_xyz(0.0, 0.0, 1.0)
            if unit.cross(up).magnitude < _PARALLEL_TOLERANCE:
                up = Vector.by_xyz(0.0, 1.0, 0.0)
        elif up.magnitude == 0.0 or unit.cross(up.normalize()).magnitude < _PARALLEL_TOLERANCE:
            raise ValueError("Expected an up direction that is not parallel to the view.")

        self._direction = direction
        self._up = up
        self._target = target
        self._span = span
        self._label = label

    @property
    def direction(self) -> Vector:
        """
        Direction from the view's center toward the viewer.

        :return: Direction.
        :rtype: Vector
        """
        return self._direction

    @property
    def up(self) -> Vector:
        """
        Direction that appears up in the image.

        :return: Up direction.
        :rtype: Vector
        """
        return self._up

    @property
    def target(self) -> Point | None:
        """
        Point at the center of the image.

        :return: Target, or None to fit all shapes.
        :rtype: Point | None
        """
        return self._target

    @property
    def span(self) -> float | None:
        """
        Length across the image's smaller side.

        :return: Span, or None to fit all shapes.
        :rtype: float | None
        """
        return self._span

    @property
    def label(self) -> str:
        """
        Name shown on the image.

        :return: Label.
        :rtype: str
        """
        return self._label


class Callout:
    """
    A text box beside the part with a line pointing at a target.

    The line ends on the middle of the target's visible part, so it does not need to be aimed. If
    the target is hidden in the view, the line is dashed and the text adds "(hidden)". If it is
    outside the image, there is no line and the text adds "(out of view)". Boxes are placed
    automatically in columns at the sides of the image.

    :ivar Shape | Point target: What to point at, which is not drawn itself. It does not need to be
        part of the image's shapes.
    :ivar str text: Text in printable ASCII, where other characters are drawn as "?". A newline
        starts a new line.
    """

    def __init__(self, target: Shape | Point, text: str):
        """
        Initialize from a target and text.

        :param Shape | Point target: What to point at.
        :param str text: Text in printable ASCII. A newline starts a new line.
        """
        self._target = target
        self._text = text

    @property
    def target(self) -> Shape | Point:
        """
        What to point at.

        :return: Target.
        :rtype: Shape | Point
        """
        return self._target

    @property
    def text(self) -> str:
        """
        Text in the box.

        :return: Text.
        :rtype: str
        """
        return self._text


def _check_size(width: int, height: int) -> None:
    """
    Check that an image size is positive.

    :param int width: Width in pixels.
    :param int height: Height in pixels.
    :raises ValueError: If either size is not positive.
    """
    if width < 1 or height < 1:
        raise ValueError(f"Expected a positive image size, got {width} by {height}.")


def _make_tool(shapes: Shape | Styled | Iterable[Shape | Styled], w: int, h: int) -> RenderIShapes:
    """
    Make the render tool for the given shapes.

    :param Shape | Styled | Iterable[Shape | Styled] shapes: Shape(s) to draw, in drawing order.
    :param int w: Width in pixels.
    :param int h: Height in pixels.
    :return: Tool with the shapes added.
    :rtype: RenderIShapes
    """
    items = [shapes] if isinstance(shapes, Shape | Styled) else shapes
    tool = RenderIShapes(w, h)
    for item in items:
        styled = item if isinstance(item, Styled) else Styled(item)
        r, g, b = styled.color
        tool.AddShape(styled.shape.ishape, r, g, b, styled.transparency)
    return tool


def _render(tool: RenderIShapes, view: View | Camera, shading: Shading, labels: bool) -> bytes:
    """
    Render one view.

    :param RenderIShapes tool: Render tool.
    :param View | Camera view: View to render.
    :param Shading shading: How faces are shaded.
    :param bool labels: Whether to draw the view name, the axes and any numbers.
    :return: Rows of RGB bytes, from the top row down.
    :rtype: bytes
    """
    camera = view if isinstance(view, Camera) else Camera.by_view(view)
    target = camera.target.ipoint if camera.target is not None else None
    return tool.Render(
        camera.direction.ivector,
        camera.up.ivector,
        camera.label,
        target,
        camera.span,
        shading is Shading.DEPTH,
        labels,
    )


def _write_png(path: str, rgb: bytes, width: int, height: int) -> None:
    """
    Write RGB bytes to a PNG file.

    :param str path: File path.
    :param bytes rgb: Rows of RGB bytes, from the top row down.
    :param int width: Width in pixels.
    :param int height: Height in pixels.
    """

    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
        )

    stride = width * 3
    # each row starts with a filter type, where 0 means no filter
    rows = b"".join(b"\x00" + rgb[y * stride : (y + 1) * stride] for y in range(height))
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(rows)))
        f.write(chunk(b"IEND", b""))


def render_image(
    shapes: Shape | Styled | Iterable[Shape | Styled],
    path: str,
    view: View | Camera = View.ISO,
    width: int = 1200,
    height: int = 900,
    callouts: Callout | Iterable[Callout] = (),
    shading: Shading = Shading.LIGHT,
    labels: bool = True,
) -> None:
    """
    Write one orthographic view of the shapes to a PNG file.

    The image shows the view name and the X, Y and Z axes as colored red, green and blue. A shape
    that coincides with an earlier one draws over it. Only visible edges are drawn, so hidden
    features need another view or a transparent :class:`Styled`.

    :param Shape | Styled | Iterable[Shape | Styled] shapes: Shape(s) to draw, in drawing order.
    :param str path: PNG file path.
    :param View | Camera view: View to render.
    :param int width: Image width in pixels.
    :param int height: Image height in pixels.
    :param Callout | Iterable[Callout] callouts: Text boxes pointing at targets.
    :param Shading shading: How faces are shaded.
    :param bool labels: Whether to draw the view name, the axes and any numbers. Turn it off to see
        the shapes alone. Callouts are drawn either way.
    :raises ValueError: If the image size is not positive.
    :raises BuildFailed: If there is nothing to render, a shape is unbounded, or a face fails
        to mesh.
    :raises OSError: If the file cannot be written.
    """
    _check_size(width, height)
    tool = _make_tool(shapes, width, height)
    for callout in [callouts] if isinstance(callouts, Callout) else callouts:
        target = callout.target
        shape = Vertex.by_point(target) if isinstance(target, Point) else target
        tool.AddCallout(shape.ishape, callout.text)
    _write_png(path, _render(tool, view, shading, labels), width, height)


def render_faces(
    shape: Shape,
    path: str,
    view: View | Camera = View.ISO,
    width: int = 1200,
    height: int = 900,
    shading: Shading = Shading.LIGHT,
    labels: bool = True,
) -> dict[int, int]:
    """
    Write a view with each face colored and numbered to a PNG file, and return what is visible.

    A number is the face's index in ``shape.faces()``. It only applies to this shape, since an
    operation returns a new shape with its own order, where trimmed faces are new faces. Keep a face
    itself rather than its number to refer to it later. A number is drawn on the face if it fits,
    and otherwise in a text box at the side of the image with a line pointing at the face. Colors
    only help to tell faces apart and repeat on parts with many faces, so rely on the numbers and
    the returned pixels. A face that is entirely hidden has no number, so look from another view.

    :param Shape shape: Shape to draw.
    :param str path: PNG file path.
    :param View | Camera view: View to render.
    :param int width: Image width in pixels.
    :param int height: Image height in pixels.
    :param Shading shading: How faces are shaded.
    :param bool labels: Whether to draw the view name, the axes and any numbers. Turn it off to see
        the shapes alone. Callouts are drawn either way.
    :return: Number of visible pixels for each visible face, by index in ``shape.faces()``.
    :rtype: dict[int, int]
    :raises ValueError: If the image size is not positive.
    :raises BuildFailed: If there is nothing to render, the shape is unbounded, or a face fails to
        mesh.
    :raises OSError: If the file cannot be written.
    """
    _check_size(width, height)
    tool = RenderIShapes(width, height)
    tool.AddNumberedFaces(shape.ishape, [c for color in _FACE_COLORS for c in color])
    _write_png(path, _render(tool, view, shading, labels), width, height)
    return {i: count for i, count in enumerate(tool.VisiblePixels()) if count > 0}


def render_edges(
    shape: Shape,
    path: str,
    view: View | Camera = View.ISO,
    width: int = 1200,
    height: int = 900,
    shading: Shading = Shading.LIGHT,
    labels: bool = True,
) -> dict[int, int]:
    """
    Write a view with each edge colored and numbered to a PNG file, and return what is visible.

    A number is the edge's index in ``shape.edges()``. It only applies to this shape, since an
    operation returns a new shape with its own order. Keep an edge itself rather than its number to
    refer to it later. A number is in a text box at the side of the image with a line pointing at
    the middle of the edge's longest visible part. An edge that is entirely hidden
    or seen end-on has no number, so look from another view. Seam edges of closed surfaces are real
    edges and are numbered too. Colors only help to tell edges apart and repeat, so rely on the
    numbers and the returned lengths. Text boxes overlap if there are too many for the image, so use
    a larger image or a :class:`Camera` that looks closer.

    :param Shape shape: Shape to draw.
    :param str path: PNG file path.
    :param View | Camera view: View to render.
    :param int width: Image width in pixels.
    :param int height: Image height in pixels.
    :param Shading shading: How faces are shaded.
    :param bool labels: Whether to draw the view name, the axes and any numbers. Turn it off to see
        the shapes alone. Callouts are drawn either way.
    :return: Visible length in pixels for each visible edge, by index in ``shape.edges()``.
    :rtype: dict[int, int]
    :raises ValueError: If the image size is not positive.
    :raises BuildFailed: If there is nothing to render, the shape is unbounded, or a face fails to
        mesh.
    :raises OSError: If the file cannot be written.
    """
    _check_size(width, height)
    tool = RenderIShapes(width, height)
    r, g, b = _EDGE_BACKDROP_COLOR
    tool.AddNumberedEdges(shape.ishape, r, g, b, [c for color in _FACE_COLORS for c in color])
    _write_png(path, _render(tool, view, shading, labels), width, height)
    return {i: length for i, length in enumerate(tool.VisiblePixels()) if length > 0}


def render_views(
    shapes: Shape | Styled | Iterable[Shape | Styled],
    path: str,
    width: int = 1500,
    height: int = 1124,
    shading: Shading = Shading.LIGHT,
    labels: bool = True,
) -> None:
    """
    Write a sheet of four views of the shapes to a PNG file.

    TOP is above FRONT and RIGHT is beside FRONT, as in a third-angle drawing, with ISO in the free
    corner. All views use the same scale, so sizes can be compared between them. See
    :func:`render_image` for what each view shows.

    :param Shape | Styled | Iterable[Shape | Styled] shapes: Shape(s) to draw, in drawing order.
    :param str path: PNG file path.
    :param int width: Sheet width in pixels. An odd width is rounded down.
    :param int height: Sheet height in pixels. An odd height is rounded down.
    :param Shading shading: How faces are shaded.
    :param bool labels: Whether to draw the view name, the axes and any numbers. Turn it off to see
        the shapes alone. Callouts are drawn either way.
    :raises ValueError: If the sheet is too small to hold four views.
    :raises BuildFailed: If there is nothing to render, a shape is unbounded, or a face fails
        to mesh.
    :raises OSError: If the file cannot be written.
    """
    tile_width = width // 2
    tile_height = height // 2
    _check_size(tile_width, tile_height)

    tool = _make_tool(shapes, tile_width, tile_height)
    stride = tile_width * 3

    def rows(left: View, right: View) -> list[bytes]:
        left_rgb = _render(tool, left, shading, labels)
        right_rgb = _render(tool, right, shading, labels)
        return [
            left_rgb[y * stride : (y + 1) * stride - 3]
            + _SEPARATOR
            + right_rgb[y * stride : (y + 1) * stride]
            for y in range(tile_height)
        ]

    upper = rows(View.TOP, View.ISO)
    lower = rows(View.FRONT, View.RIGHT)
    upper[-1] = _SEPARATOR * (tile_width * 2)
    sheet = b"".join(upper + lower)
    _write_png(path, sheet, tile_width * 2, tile_height * 2)
