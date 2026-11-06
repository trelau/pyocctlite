"""
Render shapes to PNG images, with no GPU, display or extra packages needed.

Start with :func:`render_views`, which shows most of a part in one image. Use
:func:`render_image` for one other view, or to look closer at one view. Use :class:`Styled` to
highlight a sub-shape or see through a part.
"""

from __future__ import annotations

import struct
import zlib
from collections.abc import Iterable
from enum import Enum

from pyocctlite._occtlite import RenderIShapes
from pyocctlite.geometry import Vector
from pyocctlite.topology import Shape

__all__ = ["Styled", "View", "render_image", "render_views"]

_DEFAULT_COLOR = (0.72, 0.75, 0.8)
_SEPARATOR = bytes((190, 190, 190))


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


def _render(tool: RenderIShapes, view: View) -> bytes:
    """
    Render one view.

    :param RenderIShapes tool: Render tool.
    :param View view: View to render.
    :return: Rows of RGB bytes, from the top row down.
    :rtype: bytes
    """
    direction, up = view.value
    return tool.Render(Vector.by_xyz(*direction).ivector, Vector.by_xyz(*up).ivector, view.name)


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
    view: View = View.ISO,
    width: int = 1200,
    height: int = 900,
) -> None:
    """
    Write one orthographic view of the shapes to a PNG file.

    The image shows the view name and the X, Y and Z axes as colored red, green and blue. A shape
    that coincides with an earlier one draws over it. Only visible edges are drawn, so hidden
    features need another view or a transparent :class:`Styled`.

    :param Shape | Styled | Iterable[Shape | Styled] shapes: Shape(s) to draw, in drawing order.
    :param str path: PNG file path.
    :param View view: View to render.
    :param int width: Image width in pixels.
    :param int height: Image height in pixels.
    :raises ValueError: If the image size is not positive.
    :raises BuildFailed: If there is nothing to render, a shape is unbounded, or a face fails
        to mesh.
    :raises OSError: If the file cannot be written.
    """
    _check_size(width, height)
    tool = _make_tool(shapes, width, height)
    _write_png(path, _render(tool, view), width, height)


def render_views(
    shapes: Shape | Styled | Iterable[Shape | Styled],
    path: str,
    width: int = 1500,
    height: int = 1124,
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
        left_rgb = _render(tool, left)
        right_rgb = _render(tool, right)
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
