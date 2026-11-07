"""
Render shapes to PNG images, with no GPU, display or extra packages.
"""

from __future__ import annotations

import math
import struct
import zlib
from collections.abc import Iterable
from enum import Enum
from typing import TypeVar

from pyocctlite._occtlite import RenderIShapes
from pyocctlite.geometry import Point, Vector
from pyocctlite.topology import Edge, Face, MapShape, Shape, Vertex

__all__ = [
    "Callout",
    "Camera",
    "RenderShapes",
    "Section",
    "Shading",
    "Styled",
    "View",
    "render_edges",
    "render_faces",
    "render_image",
    "render_views",
]

_DEFAULT_COLOR = (0.72, 0.75, 0.8)

T = TypeVar("T", bound=Shape)

# How far the default color of a section's cut is from a shape's color toward white
_CUT_TINT = 0.7

# Faces that are not numbered stay pale, so that the numbered colors stand out
_BACKDROP_COLOR = (0.9, 0.9, 0.92)
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
    Standard views for a Z-up model, each holding the direction toward the viewer and the up
    direction.
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
    How faces are shaded: LIGHT by the way a face faces the light, and DEPTH also darkening faces
    that are farther from the viewer.
    """

    LIGHT = "light"
    DEPTH = "depth"


def _check_color(color: tuple[float, float, float]) -> None:
    """
    Check that a color has three components from 0 to 1.

    :param color: Red, green and blue.
    :raises ValueError: If a color component is not from 0 to 1.
    """
    if not (len(color) == 3 and all(0.0 <= c <= 1.0 for c in color)):
        raise ValueError(f"Expected 3 color components from 0 to 1, got {color}.")


class Styled:
    """
    A shape with its appearance in an image.

    :ivar shape: Shape to draw.
    :ivar color: Red, green and blue from 0 to 1.
    :ivar transparency: From 0 for opaque to 1 for invisible faces.
    """

    def __init__(
        self,
        shape: Shape,
        color: tuple[float, float, float] | None = None,
        transparency: float = 0.0,
    ):
        """
        Initialize from a shape and its appearance.

        :param shape: Shape to draw.
        :param color: Red, green and blue from 0 to 1. Defaults to
            a neutral gray.
        :param transparency: From 0 for opaque to 1 for invisible faces.
        :raises ValueError: If a color component or the transparency is not from 0 to 1.
        """
        if color is None:
            color = _DEFAULT_COLOR
        _check_color(color)
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
        """
        return self._shape

    @property
    def color(self) -> tuple[float, float, float]:
        """
        Color of the shape.

        :return: Red, green and blue from 0 to 1.
        """
        return self._color

    @property
    def transparency(self) -> float:
        """
        Transparency of the faces.

        :return: From 0 for opaque to 1 for invisible.
        """
        return self._transparency


class Camera:
    """
    A custom orthographic view.

    :ivar direction: Direction from the view's center toward the viewer.
    :ivar up: Direction that appears up in the image.
    :ivar target: Point at the center of the image, or None to fit all shapes.
    :ivar span: Length across the image's smaller side, or None to fit all shapes.
    :ivar label: Name shown on the image.
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

        :param direction: Direction from the view's center toward the viewer.
        :param up: Direction that appears up in the image. Defaults to +z, or +y if
            looking along z.
        :param target: Point at the center of the image. Defaults to the center of all
            shapes.
        :param span: Length across the image's smaller side. Defaults to fitting all
            shapes.
        :return: New camera.
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

        :param position: Point to look from, which only sets the direction of the view.
        :param target: Point at the center of the image.
        :param up: Direction that appears up in the image. Defaults to +z, or +y if
            looking along z.
        :param span: Length across the image's smaller side. Defaults to fitting all
            shapes.
        :return: New camera.
        :raises ValueError: If the points coincide, up is parallel to the view, or the span is not
            positive.
        """
        return cls(Vector.by_points(target, position), up, target, span)

    @classmethod
    def by_view(cls, view: View, target: Point | None = None, span: float | None = None) -> Camera:
        """
        Create a camera from a standard view, usually to look closer at something.

        :param view: Standard view.
        :param target: Point at the center of the image. Defaults to the center of all
            shapes.
        :param span: Length across the image's smaller side. Defaults to fitting all
            shapes.
        :return: New camera.
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

        :param direction: Direction from the view's center toward the viewer.
        :param up: Direction that appears up in the image. Defaults to +z, or +y if
            looking along z.
        :param target: Point at the center of the image, or None to fit all shapes.
        :param span: Length across the image's smaller side, or None to fit all
            shapes.
        :param label: Name shown on the image.
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
        """
        return self._direction

    @property
    def up(self) -> Vector:
        """
        Direction that appears up in the image.

        :return: Up direction.
        """
        return self._up

    @property
    def target(self) -> Point | None:
        """
        Point at the center of the image.

        :return: Target, or None to fit all shapes.
        """
        return self._target

    @property
    def span(self) -> float | None:
        """
        Length across the image's smaller side.

        :return: Span, or None to fit all shapes.
        """
        return self._span

    @property
    def label(self) -> str:
        """
        Name shown on the image.

        :return: Label.
        """
        return self._label


class Callout:
    """
    A text box beside the part with a line pointing at a target.

    :ivar target: What to point at.
    :ivar text: Text in printable ASCII, where a newline starts a new line.
    """

    def __init__(self, target: Shape | Point, text: str):
        """
        Initialize from a target and text.

        :param target: What to point at.
        :param text: Text in printable ASCII, where a newline starts a new line.
        """
        self._target = target
        self._text = text

    @property
    def target(self) -> Shape | Point:
        """
        What to point at.

        :return: Target.
        """
        return self._target

    @property
    def text(self) -> str:
        """
        Text in the box.

        :return: Text.
        """
        return self._text


class Section:
    """
    A plane that cuts away part of an image to show the inside of a part, without changing shapes.

    :ivar origin: Point on the plane.
    :ivar normal: Normal of the plane, pointing to the side that is removed.
    :ivar color: Red, green and blue of the cut from 0 to 1, or
        None for a pale tint of each shape's color.
    """

    @classmethod
    def by_plane(
        cls,
        origin: Point,
        normal: Vector,
        color: tuple[float, float, float] | None = None,
    ) -> Section:
        """
        Create a section from a plane.

        :param origin: Point on the plane.
        :param normal: Normal of the plane, pointing to the side that is removed.
        :param color: Red, green and blue of the cut from 0 to 1.
            Defaults to a pale tint of each shape's color.
        :return: New section.
        :raises ValueError: If the normal has no length or a color component is not from 0 to 1.
        """
        return cls(origin, normal, color)

    def __init__(
        self,
        origin: Point,
        normal: Vector,
        color: tuple[float, float, float] | None = None,
    ):
        """
        Initialize from named parts.

        :param origin: Point on the plane.
        :param normal: Normal of the plane, pointing to the side that is removed.
        :param color: Red, green and blue of the cut from 0 to 1.
            Defaults to a pale tint of each shape's color.
        :raises ValueError: If the normal has no length or a color component is not from 0 to 1.
        """
        if normal.magnitude == 0.0:
            raise ValueError("Expected a normal with a length.")
        if color is not None:
            _check_color(color)
        self._origin = origin
        self._normal = normal
        self._color = color

    @property
    def origin(self) -> Point:
        """
        Point on the plane.

        :return: Origin.
        """
        return self._origin

    @property
    def normal(self) -> Vector:
        """
        Normal of the plane, pointing to the side that is removed.

        :return: Normal.
        """
        return self._normal

    @property
    def color(self) -> tuple[float, float, float] | None:
        """
        Color of the cut.

        :return: Red, green and blue from 0 to 1, or None for a pale tint of each shape's color.
        """
        return self._color


def _check_size(width: int, height: int) -> None:
    """
    Check that an image size is positive.

    :param width: Width in pixels.
    :param height: Height in pixels.
    :raises ValueError: If either size is not positive.
    """
    if width < 1 or height < 1:
        raise ValueError(f"Expected a positive image size, got {width} by {height}.")


def _write_png(path: str, rgb: bytes, width: int, height: int) -> None:
    """
    Write RGB bytes to a PNG file.

    :param path: File path.
    :param rgb: Rows of RGB bytes, from the top row down.
    :param width: Width in pixels.
    :param height: Height in pixels.
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


def _numbered_indices(subshapes: MapShape[T], chosen: T | Iterable[T] | None) -> list[int]:
    """
    Get the indices of the sub-shapes to number.

    :param subshapes: Sub-shapes of the numbered shape.
    :param chosen: Sub-shape(s) to number, or None for all of them.
    :return: Indices in the sub-shapes.
    :raises ValueError: If a chosen shape is not one of the sub-shapes.
    """
    if chosen is None:
        return list(range(len(subshapes)))

    indices = []
    for s in [chosen] if isinstance(chosen, Shape) else chosen:
        index = subshapes.find_index(s)
        if index is None:
            raise ValueError(f"Expected a sub-shape of the numbered shape, got {s.kind}.")
        indices.append(index)
    return indices


class RenderShapes:
    """
    Tool to render shapes to PNG images, reusing its prepared shapes between renders.
    """

    def __init__(self, width: int = 1200, height: int = 900):
        """
        Initialize with the image size.

        :param width: Image width in pixels.
        :param height: Image height in pixels.
        :raises ValueError: If the image size is not positive.
        """
        _check_size(width, height)
        self._width = width
        self._height = height
        self._itool = RenderIShapes(width, height)
        self._colors: list[tuple[float, float, float]] = []
        self._section: Section | None = None
        self._has_numbered = False

    def add_shape(self, shape: Shape | Styled) -> None:
        """
        Add a shape, drawn over those already added.

        :param shape: Shape to draw.
        """
        styled = shape if isinstance(shape, Styled) else Styled(shape)
        r, g, b = styled.color
        self._itool.AddShape(styled.shape.ishape, r, g, b, styled.transparency)
        self._add_color(styled.color)

    def add_numbered_faces(self, shape: Shape, faces: Face | Iterable[Face] | None = None) -> None:
        """
        Add the one numbered shape, with faces colored and numbered by index in ``shape.faces()``
        and any others pale.

        :param shape: Shape to draw.
        :param faces: Face(s) to number. Defaults to every face.
        :raises ValueError: If a shape is already numbered or a face is not part of the shape.
        """
        self._check_not_numbered()
        indices = _numbered_indices(shape.faces(), faces)
        r, g, b = _BACKDROP_COLOR
        self._itool.AddNumberedFaces(
            shape.ishape, r, g, b, [c for color in _FACE_COLORS for c in color], indices
        )
        self._has_numbered = True
        self._add_color(_BACKDROP_COLOR)

    def add_numbered_edges(self, shape: Shape, edges: Edge | Iterable[Edge] | None = None) -> None:
        """
        Add the one numbered shape, with edges colored and numbered by index in ``shape.edges()``
        and any others plain.

        :param shape: Shape to draw.
        :param edges: Edge(s) to number. Defaults to every edge.
        :raises ValueError: If a shape is already numbered or an edge is not part of the shape.
        """
        self._check_not_numbered()
        indices = _numbered_indices(shape.edges(), edges)
        r, g, b = _BACKDROP_COLOR
        self._itool.AddNumberedEdges(
            shape.ishape, r, g, b, [c for color in _FACE_COLORS for c in color], indices
        )
        self._has_numbered = True
        self._add_color(_BACKDROP_COLOR)

    def add_callout(self, callout: Callout) -> None:
        """
        Add a text box pointing at a target.

        :param callout: Text box.
        """
        target = callout.target
        shape = Vertex.by_point(target) if isinstance(target, Point) else target
        self._itool.AddCallout(shape.ishape, callout.text)

    def set_section(self, section: Section) -> None:
        """
        Set the plane that cuts the images, replacing any earlier one.

        :param section: Plane to cut the images with.
        """
        self._section = section
        self._apply_section()

    def render(
        self,
        path: str,
        view: View | Camera = View.ISO,
        shading: Shading = Shading.LIGHT,
        labels: bool = True,
    ) -> None:
        """
        Write one orthographic view of the shapes to a PNG file.

        :param path: PNG file path.
        :param view: View to render.
        :param shading: How faces are shaded.
        :param labels: Whether to draw the view name, the axes and any numbers.
        :raises BuildFailed: If there is nothing to render, a shape is unbounded, or a face fails
            to mesh.
        :raises OSError: If the file cannot be written.
        """
        _write_png(path, self._render(view, shading, labels), self._width, self._height)

    def render_views(
        self, path: str, shading: Shading = Shading.LIGHT, labels: bool = True
    ) -> None:
        """
        Write a sheet of four views to a PNG file, with each view at the image size.

        :param path: PNG file path.
        :param shading: How faces are shaded.
        :param labels: Whether to draw the view name, the axes and any numbers.
        :raises BuildFailed: If there is nothing to render, a shape is unbounded, or a face fails
            to mesh.
        :raises OSError: If the file cannot be written.
        """
        stride = self._width * 3

        def rows(left: View, right: View) -> list[bytes]:
            left_rgb = self._render(left, shading, labels)
            right_rgb = self._render(right, shading, labels)
            return [
                left_rgb[y * stride : (y + 1) * stride - 3]
                + _SEPARATOR
                + right_rgb[y * stride : (y + 1) * stride]
                for y in range(self._height)
            ]

        upper = rows(View.TOP, View.ISO)
        lower = rows(View.FRONT, View.RIGHT)
        upper[-1] = _SEPARATOR * (self._width * 2)
        _write_png(path, b"".join(upper + lower), self._width * 2, self._height * 2)

    def visible_pixels(self) -> dict[int, int]:
        """
        Get what is visible of the numbered shape, in the latest view.

        :return: Number of visible pixels for each visible face, or visible length in pixels for
            each visible edge, by index.
        """
        return {i: count for i, count in enumerate(self._itool.VisiblePixels()) if count > 0}

    def _check_not_numbered(self) -> None:
        """
        Check that no shape is numbered yet, since numbers from two shapes could not be told apart.

        :raises ValueError: If a shape is already numbered.
        """
        if self._has_numbered:
            raise ValueError("Expected only one numbered shape.")

    def _add_color(self, color: tuple[float, float, float]) -> None:
        """
        Record the color of an added shape, which the default color of a section's cut depends on.

        :param color: Red, green and blue.
        """
        self._colors.append(color)
        self._apply_section()

    def _apply_section(self) -> None:
        """
        Pass the section on with a cut color for each added shape.
        """
        section = self._section
        if section is None:
            return
        cut_colors: list[float] = []
        for color in self._colors:
            tint = [c + (1.0 - c) * _CUT_TINT for c in color]
            cut_colors.extend(tint if section.color is None else section.color)
        self._itool.SetSection(section.origin.ipoint, section.normal.ivector, cut_colors)

    def _render(self, view: View | Camera, shading: Shading, labels: bool) -> bytes:
        """
        Render one view.

        :param view: View to render.
        :param shading: How faces are shaded.
        :param labels: Whether to draw the view name, the axes and any numbers.
        :return: Rows of RGB bytes, from the top row down.
        """
        camera = view if isinstance(view, Camera) else Camera.by_view(view)
        target = camera.target.ipoint if camera.target is not None else None
        return self._itool.Render(
            camera.direction.ivector,
            camera.up.ivector,
            camera.label,
            target,
            camera.span,
            shading is Shading.DEPTH,
            labels,
        )


def _make_tool(
    shapes: Shape | Styled | Iterable[Shape | Styled],
    width: int,
    height: int,
    section: Section | None,
) -> RenderShapes:
    """
    Make the render tool for the given shapes.

    :param shapes: Shape(s) to draw, in drawing order.
    :param width: Width in pixels.
    :param height: Height in pixels.
    :param section: Plane to cut the image with, if any.
    :return: Tool with the shapes added.
    :raises ValueError: If the image size is not positive.
    """
    tool = RenderShapes(width, height)
    for shape in [shapes] if isinstance(shapes, Shape | Styled) else shapes:
        tool.add_shape(shape)
    if section is not None:
        tool.set_section(section)
    return tool


def render_image(
    shapes: Shape | Styled | Iterable[Shape | Styled],
    path: str,
    view: View | Camera = View.ISO,
    width: int = 1200,
    height: int = 900,
    callouts: Callout | Iterable[Callout] = (),
    shading: Shading = Shading.LIGHT,
    labels: bool = True,
    section: Section | None = None,
) -> None:
    """
    Write one orthographic view of the shapes to a PNG file.

    :param shapes: Shape(s) to draw, in drawing order.
    :param path: PNG file path.
    :param view: View to render.
    :param width: Image width in pixels.
    :param height: Image height in pixels.
    :param callouts: Text boxes pointing at targets.
    :param shading: How faces are shaded.
    :param labels: Whether to draw the view name, the axes and any numbers.
    :param section: Plane to cut the image with, to show the inside of a part.
    :raises ValueError: If the image size is not positive.
    :raises BuildFailed: If there is nothing to render, a shape is unbounded, or a face fails
        to mesh.
    :raises OSError: If the file cannot be written.
    """
    tool = _make_tool(shapes, width, height, section)
    for callout in [callouts] if isinstance(callouts, Callout) else callouts:
        tool.add_callout(callout)
    tool.render(path, view, shading, labels)


def render_faces(
    shape: Shape,
    path: str,
    view: View | Camera = View.ISO,
    width: int = 1200,
    height: int = 900,
    shading: Shading = Shading.LIGHT,
    labels: bool = True,
    faces: Face | Iterable[Face] | None = None,
) -> dict[int, int]:
    """
    Write a view with faces colored and numbered to a PNG file, and return what is visible.

    :param shape: Shape to draw.
    :param path: PNG file path.
    :param view: View to render.
    :param width: Image width in pixels.
    :param height: Image height in pixels.
    :param shading: How faces are shaded.
    :param labels: Whether to draw the view name, the axes and any numbers.
    :param faces: Face(s) to number, with any others pale. Defaults to every face.
    :return: Number of visible pixels for each visible numbered face, by index in ``shape.faces()``.
    :raises ValueError: If the image size is not positive or a face is not part of the shape.
    :raises BuildFailed: If there is nothing to render, the shape is unbounded, or a face fails to
        mesh.
    :raises OSError: If the file cannot be written.
    """
    tool = RenderShapes(width, height)
    tool.add_numbered_faces(shape, faces)
    tool.render(path, view, shading, labels)
    return tool.visible_pixels()


def render_edges(
    shape: Shape,
    path: str,
    view: View | Camera = View.ISO,
    width: int = 1200,
    height: int = 900,
    shading: Shading = Shading.LIGHT,
    labels: bool = True,
    edges: Edge | Iterable[Edge] | None = None,
) -> dict[int, int]:
    """
    Write a view with edges colored and numbered to a PNG file, and return what is visible.

    :param shape: Shape to draw.
    :param path: PNG file path.
    :param view: View to render.
    :param width: Image width in pixels.
    :param height: Image height in pixels.
    :param shading: How faces are shaded.
    :param labels: Whether to draw the view name, the axes and any numbers.
    :param edges: Edge(s) to number, with any others plain. Defaults to every edge.
    :return: Visible length in pixels for each visible numbered edge, by index in ``shape.edges()``.
    :raises ValueError: If the image size is not positive or an edge is not part of the shape.
    :raises BuildFailed: If there is nothing to render, the shape is unbounded, or a face fails to
        mesh.
    :raises OSError: If the file cannot be written.
    """
    tool = RenderShapes(width, height)
    tool.add_numbered_edges(shape, edges)
    tool.render(path, view, shading, labels)
    return tool.visible_pixels()


def render_views(
    shapes: Shape | Styled | Iterable[Shape | Styled],
    path: str,
    width: int = 1500,
    height: int = 1124,
    shading: Shading = Shading.LIGHT,
    labels: bool = True,
    section: Section | None = None,
) -> None:
    """
    Write a sheet of four views of the shapes to a PNG file.

    :param shapes: Shape(s) to draw, in drawing order.
    :param path: PNG file path.
    :param width: Sheet width in pixels.
    :param height: Sheet height in pixels.
    :param shading: How faces are shaded.
    :param labels: Whether to draw the view name, the axes and any numbers.
    :param section: Plane to cut every view with.
    :raises ValueError: If the sheet is too small to hold four views.
    :raises BuildFailed: If there is nothing to render, a shape is unbounded, or a face fails
        to mesh.
    :raises OSError: If the file cannot be written.
    """
    tool = _make_tool(shapes, width // 2, height // 2, section)
    tool.render_views(path, shading, labels)
