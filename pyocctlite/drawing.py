"""
Make engineering drawings: flat lines and text on a canvas, and sheets of projected views with
dimensions, written to PNG, SVG or PDF files.
"""

from __future__ import annotations

import itertools
import math
import zlib
from collections.abc import Iterable
from enum import Enum, StrEnum
from pathlib import Path
from typing import NamedTuple

from pyocctlite._occtlite import RenderICanvas
from pyocctlite.geometry import (
    Circle,
    Circle2D,
    Curve2D,
    Frame,
    Frame2D,
    Point,
    Point2D,
    Vector,
    Vector2D,
)
from pyocctlite.primitives import Box
from pyocctlite.rendering import Camera, View, _check_color, _write_png
from pyocctlite.topology import Compound, Edge, Face, HiddenLineShape, Shape, Wire

__all__ = [
    "Canvas",
    "LinePattern",
    "Paper",
    "Sheet",
    "SheetView",
    "Stroke",
    "Symbol",
    "TextAlign",
]

Color = tuple[float, float, float]

_BLACK = (0.0, 0.0, 0.0)
_SMOOTH_EDGE_COLOR = (0.55, 0.55, 0.55)

# Drafting sizes in inches of paper
_THIN_WIDTH = 0.012
_THICK_WIDTH = 0.024
_TEXT_HEIGHT = 0.12
_ARROW_LENGTH = 0.125
_ARROW_WIDTH = 0.042
_EXTENSION_GAP = 0.0625
_EXTENSION_OVERRUN = 0.125
_TEXT_GAP = 0.05
_LEADER_LENGTH = 0.5
_LEADER_SHOULDER = 0.25
_CENTER_MARK_ARM = 0.0625
_BORDER_MARGIN = 0.5
_SAMPLE_DEFLECTION = 0.001

# Distance between lines of text and thickness of its strokes, relative to the letter height
_LINE_ADVANCE = 1.5
_TEXT_STROKE_FRACTION = 0.1

_DEFAULT_DPI = 150
_POINTS_PER_INCH = 72.0

# Largest angle in radians between neighboring segments of a drawn arc
_ARC_STEP = 0.05

# Below this cross product of unit vectors, directions are treated as parallel
_PARALLEL_TOLERANCE = 1.0e-7

# Sizes in inches of paper for the marks of a section, a table and a sheet's zones
_HATCH_SPACING = 0.1
_CUTTING_PLANE_OVERRUN = 0.25
_CUTTING_PLANE_ARROW = 0.4
_TABLE_PAD = 0.05
_ZONE_TICK = 0.25

# How much larger than a shape a tool for cutting it is, relative to the shape's size
_CUT_TOOL_SIZE = 4.0


class Symbol(StrEnum):
    """
    Drawing symbols that text can hold, such as ``f"{Symbol.DIAMETER}12"``.
    """

    DIAMETER = "\u2300"
    DEGREE = "\u00b0"
    PLUS_MINUS = "\u00b1"
    PERPENDICULAR = "\u27c2"
    PARALLEL = "\u2225"
    FLATNESS = "\u23e5"
    POSITION = "\u2316"
    RUNOUT = "\u2197"
    CONCENTRICITY = "\u25ce"
    MAX_MATERIAL = "\u24c2"
    COUNTERBORE = "\u2334"
    COUNTERSINK = "\u2335"
    DEPTH = "\u21a7"


class LinePattern(Enum):
    """
    Drafting line patterns, each holding alternating dash and gap lengths in inches of paper.
    """

    SOLID = ()
    HIDDEN = (0.125, 0.0625)
    CENTER = (0.75, 0.0625, 0.125, 0.0625)
    PHANTOM = (0.75, 0.0625, 0.125, 0.0625, 0.125, 0.0625)


class TextAlign(Enum):
    """
    Which part of each line of text is at the position of the text.
    """

    LEFT = 0.0
    CENTER = 0.5
    RIGHT = 1.0


class Paper(Enum):
    """
    ANSI paper sizes in landscape, each holding the width and height in inches.
    """

    A = (11.0, 8.5)
    B = (17.0, 11.0)
    C = (22.0, 17.0)
    D = (34.0, 22.0)
    E = (44.0, 34.0)


class Stroke:
    """
    The appearance of a line.

    :ivar color: Red, green and blue from 0 to 1.
    :ivar width: Width in the units of the canvas, or None for the thin drafting width.
    :ivar pattern: Pattern of dashes.
    """

    def __init__(
        self,
        color: Color = _BLACK,
        width: float | None = None,
        pattern: LinePattern = LinePattern.SOLID,
    ):
        """
        Initialize from named parts.

        :param color: Red, green and blue from 0 to 1.
        :param width: Width in the units of the canvas. Defaults to the thin drafting width.
        :param pattern: Pattern of dashes.
        :raises ValueError: If a color component is not from 0 to 1 or the width is not positive.
        """
        _check_color(color)
        if width is not None and width <= 0.0:
            raise ValueError(f"Expected a positive width, got {width}.")
        self._color = color
        self._width = width
        self._pattern = pattern

    @property
    def color(self) -> Color:
        """
        Color of the line.

        :return: Red, green and blue from 0 to 1.
        """
        return self._color

    @property
    def width(self) -> float | None:
        """
        Width of the line.

        :return: Width in the units of the canvas, or None for the thin drafting width.
        """
        return self._width

    @property
    def pattern(self) -> LinePattern:
        """
        Pattern of dashes.

        :return: Pattern.
        """
        return self._pattern


class _Polyline(NamedTuple):
    """
    A connected run of straight lines on a canvas.
    """

    points: list[tuple[float, float]]
    color: Color
    width: float


class _ViewLine(NamedTuple):
    """
    A line of a view, in the plane of the view.
    """

    points: list[tuple[float, float]]
    stroke: Stroke


class _Polygon(NamedTuple):
    """
    A filled convex polygon on a canvas.
    """

    points: list[tuple[float, float]]
    color: Color


def _dashes(
    points: list[tuple[float, float]], pattern: tuple[float, ...]
) -> list[list[tuple[float, float]]]:
    """
    Split a line into dashes that continue around its corners.

    :param points: Points along the line.
    :param pattern: Alternating dash and gap lengths.
    :return: Points along each dash.
    """
    dashes: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = [points[0]]
    index = 0
    remaining = pattern[0]
    for (x1, y1), (x2, y2) in itertools.pairwise(points):
        length = math.hypot(x2 - x1, y2 - y1)
        position = 0.0
        while length - position > remaining:
            position += remaining
            t = position / length
            point = (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)
            if index % 2 == 0:
                current.append(point)
                dashes.append(current)
                current = []
            else:
                current = [point]
            index = (index + 1) % len(pattern)
            remaining = pattern[index]
        remaining -= length - position
        if index % 2 == 0:
            current.append((x2, y2))
    if index % 2 == 0 and len(current) > 1:
        dashes.append(current)
    return dashes


def _clip_to_circle(
    points: list[tuple[float, float]], center: tuple[float, float], radius: float
) -> list[list[tuple[float, float]]]:
    """
    Keep the parts of a line that are inside a circle.

    :param points: Points along the line.
    :param center: Center of the circle.
    :param radius: Radius of the circle.
    :return: Points along each part.
    """
    parts: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    for (x1, y1), (x2, y2) in itertools.pairwise(points):
        dx, dy = x2 - x1, y2 - y1
        fx, fy = x1 - center[0], y1 - center[1]
        a = dx * dx + dy * dy
        b = 2.0 * (fx * dx + fy * dy)
        c = fx * fx + fy * fy - radius * radius
        discriminant = b * b - 4.0 * a * c
        if a == 0.0 or discriminant <= 0.0:
            continue

        root = math.sqrt(discriminant)
        start = max((-b - root) / (2.0 * a), 0.0)
        end = min((-b + root) / (2.0 * a), 1.0)
        if start >= end:
            if current:
                parts.append(current)
                current = []
            continue

        if start > 0.0 and current:
            parts.append(current)
            current = []
        if not current:
            current = [(x1 + dx * start, y1 + dy * start)]
        current.append((x1 + dx * end, y1 + dy * end))
        if end < 1.0:
            parts.append(current)
            current = []
    if current:
        parts.append(current)
    return parts


def _unit_at(angle: float) -> Vector2D:
    """
    Get the unit vector at an angle.

    :param angle: Angle in radians from the x-direction.
    :return: Unit vector.
    """
    return Vector2D.by_xy(math.cos(angle), math.sin(angle))


def _angle_to(origin: Point2D, point: Point2D) -> float:
    """
    Get the angle of the direction from one point to another.

    :param origin: Point to measure from.
    :param point: Point to measure to.
    :return: Angle in radians from the x-direction.
    """
    return math.atan2(point.y - origin.y, point.x - origin.x)


def _sweep(start: float, end: float) -> float:
    """
    Get the counterclockwise angle from one angle to another.

    :param start: Start angle in radians.
    :param end: End angle in radians.
    :return: Angle in radians from 0 up to a full turn.
    """
    return (end - start) % (2.0 * math.pi)


def _format_length(value: float, decimals: int = 2) -> str:
    """
    Format a measured length for a dimension.

    :param value: Length.
    :param decimals: Number of decimal places.
    :return: Text of the value.
    """
    return f"{value:.{decimals}f}"


def _format_scale(scale: float) -> str:
    """
    Format a drawing scale as a ratio.

    :param scale: Length on the sheet for each length on the part.
    :return: Text such as 1:2 or 2:1.
    """
    return f"{scale:g}:1" if scale >= 1.0 else f"1:{1.0 / scale:g}"


class Canvas:
    """
    Tool to draw flat lines, curves, polygons, text and annotations on a page, then write it to a
    file. Coordinates use any length unit, with x to the right, y up and the origin at the lower
    left corner. Later drawing goes over earlier drawing.
    """

    def __init__(self, width: float, height: float, units_per_inch: float = 1.0):
        """
        Initialize with the page size.

        :param width: Page width.
        :param height: Page height.
        :param units_per_inch: Length units in an inch of paper, such as 25.4 for millimeters.
        :raises ValueError: If a size is not positive.
        """
        if width <= 0.0 or height <= 0.0 or units_per_inch <= 0.0:
            raise ValueError(
                f"Expected positive sizes, got {width} by {height} at {units_per_inch} per inch."
            )
        self._width = width
        self._height = height
        self._units_per_inch = units_per_inch
        self._items: list[_Polyline | _Polygon] = []

    @property
    def width(self) -> float:
        """
        Width of the page.

        :return: Width.
        """
        return self._width

    @property
    def height(self) -> float:
        """
        Height of the page.

        :return: Height.
        """
        return self._height

    @property
    def units_per_inch(self) -> float:
        """
        Length units in an inch of paper.

        :return: Units per inch.
        """
        return self._units_per_inch

    @property
    def thin_width(self) -> float:
        """
        Drafting width of thin lines, used for hidden edges and annotations.

        :return: Width.
        """
        return self._inches(_THIN_WIDTH)

    @property
    def thick_width(self) -> float:
        """
        Drafting width of thick lines, used for visible edges and the border.

        :return: Width.
        """
        return self._inches(_THICK_WIDTH)

    @property
    def text_height(self) -> float:
        """
        Drafting letter height.

        :return: Height.
        """
        return self._inches(_TEXT_HEIGHT)

    def text_width(self, text: str, height: float | None = None) -> float:
        """
        Get the width of the longest line of text.

        :param text: Text, where a newline starts a new line.
        :param height: Letter height. Defaults to the drafting height.
        :return: Width.
        """
        return RenderICanvas.TextWidth(text, self.text_height if height is None else height)

    def add_line(self, p1: Point2D, p2: Point2D, stroke: Stroke | None = None) -> None:
        """
        Draw a straight line between two points.

        :param p1: Start point.
        :param p2: End point.
        :param stroke: Appearance. Defaults to a thin solid black line.
        """
        self.add_polyline([p1, p2], stroke)

    def add_polyline(self, points: Iterable[Point2D], stroke: Stroke | None = None) -> None:
        """
        Draw connected straight lines through points.

        :param points: Points in order.
        :param stroke: Appearance. Defaults to a thin solid black line.
        """
        self._add_path([(p.x, p.y) for p in points], Stroke() if stroke is None else stroke)

    def add_curve(self, curve: Curve2D, stroke: Stroke | None = None) -> None:
        """
        Draw a 2D curve.

        :param curve: Curve, which must be bounded.
        :param stroke: Appearance. Defaults to a thin solid black line.
        :raises ValueError: If the curve is unbounded.
        """
        self.add_polyline(curve.points(self._inches(_SAMPLE_DEFLECTION)), stroke)

    def add_edges(self, edges: Edge | Iterable[Edge], stroke: Stroke | None = None) -> None:
        """
        Draw edges, using the x and y of their points as coordinates on the page.

        :param edges: Edge(s) to draw.
        :param stroke: Appearance. Defaults to a thin solid black line.
        """
        deflection = self._inches(_SAMPLE_DEFLECTION)
        for edge in [edges] if isinstance(edges, Edge) else edges:
            self.add_polyline([Point2D.by_xy(p.x, p.y) for p in edge.points(deflection)], stroke)

    def add_polygon(self, points: Iterable[Point2D], color: Color = _BLACK) -> None:
        """
        Fill a convex polygon.

        :param points: Corners in order.
        :param color: Red, green and blue from 0 to 1.
        :raises ValueError: If a color component is not from 0 to 1.
        """
        _check_color(color)
        self._items.append(_Polygon([(p.x, p.y) for p in points], color))

    def add_text(
        self,
        at: Point2D,
        text: str,
        height: float | None = None,
        color: Color = _BLACK,
        angle: float = 0.0,
        align: TextAlign = TextAlign.LEFT,
    ) -> None:
        """
        Draw text, vertically centered on a position.

        :param at: Position of the text.
        :param text: Text in printable ASCII with any :class:`Symbol`, where a newline starts a new
            line.
        :param height: Letter height. Defaults to the drafting height.
        :param color: Red, green and blue from 0 to 1.
        :param angle: Counterclockwise rotation about the position, in radians.
        :param align: Which part of each line is at the position.
        :raises ValueError: If a color component is not from 0 to 1 or the height is not positive.
        """
        _check_color(color)
        letter_height = self.text_height if height is None else height
        if letter_height <= 0.0:
            raise ValueError(f"Expected a positive height, got {letter_height}.")

        lines = text.split("\n")
        block_height = letter_height * (1.0 + _LINE_ADVANCE * (len(lines) - 1))
        cos, sin = math.cos(angle), math.sin(angle)
        width = letter_height * _TEXT_STROKE_FRACTION
        for i, line in enumerate(lines):
            left = -RenderICanvas.TextWidth(line, letter_height) * align.value
            top = block_height * 0.5 - letter_height * _LINE_ADVANCE * i
            for stroke in RenderICanvas.TextStrokes(line, letter_height):
                points = []
                for j in range(0, len(stroke), 2):
                    x = left + stroke[j]
                    y = top - stroke[j + 1]
                    points.append((at.x + x * cos - y * sin, at.y + x * sin + y * cos))
                self._items.append(_Polyline(points, color, width))

    def add_arrow(self, tip: Point2D, direction: Vector2D, color: Color = _BLACK) -> None:
        """
        Draw a filled arrowhead.

        :param tip: Point of the arrowhead.
        :param direction: Direction the arrowhead points in.
        :param color: Red, green and blue from 0 to 1.
        :raises ValueError: If a color component is not from 0 to 1.
        """
        unit = direction.normalize()
        base = tip.translate(unit.scale(-self._inches(_ARROW_LENGTH)))
        side = Vector2D.by_xy(-unit.y, unit.x).scale(self._inches(_ARROW_WIDTH) * 0.5)
        self.add_polygon([tip, base.translate(side), base.translate(side.reverse())], color)

    def add_leader(self, tip: Point2D, at: Point2D, text: str) -> None:
        """
        Draw a line with an arrowhead at a feature, a short horizontal shoulder and text.

        :param tip: Point the arrowhead touches.
        :param at: Point where the line meets the shoulder.
        :param text: Text after the shoulder.
        """
        self.add_line(tip, at)
        self.add_arrow(tip, Vector2D.by_points(at, tip))
        self._add_shoulder(at, 1.0 if at.x >= tip.x else -1.0, text)

    def add_linear_dimension(
        self,
        p1: Point2D,
        p2: Point2D,
        offset: float,
        text: str,
        along: Vector2D | None = None,
    ) -> None:
        """
        Draw the distance between two points with extension lines, arrowheads and horizontal text.

        :param p1: First point.
        :param p2: Second point.
        :param offset: Distance of the dimension line from the farther point, toward the left of the
            measuring direction if positive.
        :param text: Text of the dimension.
        :param along: Direction to measure in. Defaults to the direction between the points.
        :raises ValueError: If the points coincide along the measuring direction.
        """
        between = Vector2D.by_points(p1, p2)
        direction = between if along is None else along
        if direction.magnitude == 0.0 or between.dot(direction.normalize()) == 0.0:
            raise ValueError("Expected points that differ along the measuring direction.")
        unit = direction.normalize()
        normal = Vector2D.by_xy(-unit.y, unit.x)

        # Keep the dimension line clear of both points, whichever of them is farther out
        heights = [Vector2D.by_xy(p.x, p.y).dot(normal) for p in (p1, p2)]
        line_height = (max(heights) if offset >= 0.0 else min(heights)) + offset
        end1 = p1.translate(normal.scale(line_height - heights[0]))
        end2 = p2.translate(normal.scale(line_height - heights[1]))

        outward = normal if offset >= 0.0 else normal.reverse()
        self._add_extension(p1, end1, outward)
        self._add_extension(p2, end2, outward)
        self._add_dimension_line(end1, end2, text)

    def add_radial_dimension(
        self, center: Point2D, radius: float, text: str, angle: float = math.pi / 4.0
    ) -> None:
        """
        Draw a radius with a line from the center, an arrowhead at the arc and text outside it.

        :param center: Center of the arc.
        :param radius: Radius of the arc.
        :param text: Text of the dimension.
        :param angle: Direction from the center to the arrowhead, in radians.
        """
        unit = _unit_at(angle)
        tip = center.translate(unit.scale(radius))
        at = tip.translate(unit.scale(self._inches(_LEADER_LENGTH)))
        self.add_line(center, at)
        self.add_arrow(tip, unit)
        self._add_shoulder(at, 1.0 if unit.x >= 0.0 else -1.0, text)

    def add_angular_dimension(
        self, vertex: Point2D, p1: Point2D, p2: Point2D, radius: float, text: str
    ) -> None:
        """
        Draw the angle counterclockwise from one point to another around a vertex, with an arc,
        arrowheads and horizontal text.

        :param vertex: Point at the corner of the angle.
        :param p1: Point on the side the angle starts from.
        :param p2: Point on the side the angle ends at.
        :param radius: Radius of the arc.
        :param text: Text of the dimension.
        """
        start = _angle_to(vertex, p1)
        sweep = _sweep(start, _angle_to(vertex, p2))
        middle = start + sweep * 0.5
        arc_length = radius * sweep

        tangent = _unit_at(middle + math.pi / 2.0)
        half = self._text_clearance(text, tangent)
        arrow = self._inches(_ARROW_LENGTH)
        is_inside = arc_length >= 2.0 * (half + arrow)

        # Where they do not fit inside the arc, arrowheads point in from outside it, with the text
        # past its end
        tail = 0.0 if is_inside else arrow * 2.0 / radius
        gap = half / radius if is_inside else 0.0
        low = start - tail
        high = start + sweep + tail
        for a, b in ((low, middle - gap), (middle + gap, high)):
            steps = max(1, math.ceil((b - a) / _ARC_STEP))
            self.add_polyline(
                vertex.translate(_unit_at(a + (b - a) * i / steps).scale(radius))
                for i in range(steps + 1)
            )
        turn = math.pi / 2.0 if is_inside else -math.pi / 2.0
        for a, side in ((start, -turn), (start + sweep, turn)):
            self.add_arrow(vertex.translate(_unit_at(a).scale(radius)), _unit_at(a + side))

        text_angle = middle if is_inside else high + half / radius
        at = vertex.translate(_unit_at(text_angle).scale(radius))
        self.add_text(at, text, align=TextAlign.CENTER)

        for point, a in ((p1, start), (p2, start + sweep)):
            reach = vertex.distance(point)
            clear = self._inches(_EXTENSION_GAP)
            overrun = self._inches(_EXTENSION_OVERRUN)
            limits = (
                (reach + clear, radius + overrun)
                if reach < radius
                else (reach - clear, radius - overrun)
            )
            if (limits[1] - limits[0]) * (radius - reach) > 0.0:
                unit = _unit_at(a)
                self.add_line(
                    vertex.translate(unit.scale(limits[0])), vertex.translate(unit.scale(limits[1]))
                )

    def add_center_mark(self, center: Point2D, radius: float) -> None:
        """
        Draw a small cross at the center of a circle, with center lines reaching past it.

        :param center: Center of the circle.
        :param radius: Radius of the circle.
        """
        arm = self._inches(_CENTER_MARK_ARM)
        start = arm * 2.0
        end = radius + self._inches(_EXTENSION_OVERRUN)
        for x, y in ((1.0, 0.0), (0.0, 1.0)):
            unit = Vector2D.by_xy(x, y)
            self.add_line(center.translate(unit.scale(-arm)), center.translate(unit.scale(arm)))
            if end > start:
                for sign in (1.0, -1.0):
                    self.add_line(
                        center.translate(unit.scale(sign * start)),
                        center.translate(unit.scale(sign * end)),
                    )

    def add_table(
        self,
        top_left: Point2D,
        rows: Iterable[Iterable[str]],
        column_widths: Iterable[float],
        row_height: float | None = None,
        height: float | None = None,
    ) -> None:
        """
        Draw a table of text, such as a revision block or a list of parts.

        :param top_left: Upper left corner.
        :param rows: Text of each cell of each row, from the top down.
        :param column_widths: Width of each column.
        :param row_height: Height of each row. Defaults to twice the letter height.
        :param height: Letter height. Defaults to the drafting height.
        """
        letter_height = self.text_height if height is None else height
        row_size = letter_height * 2.0 if row_height is None else row_height
        widths = list(column_widths)
        pad = self._inches(_TABLE_PAD)
        for r, row in enumerate(rows):
            x = top_left.x
            top = top_left.y - row_size * r
            for width, text in zip(widths, row, strict=True):
                self._add_rectangle(x, top - row_size, width, row_size)
                at = Point2D.by_xy(x + pad, top - row_size * 0.5)
                self.add_text(at, text, height=letter_height)
                x += width

    def add_feature_control_frame(self, at: Point2D, cells: Iterable[str]) -> None:
        """
        Draw a feature control frame for a geometric tolerance, such as a symbol, a tolerance and
        datums.

        :param at: Middle of the left side of the frame.
        :param cells: Text of each compartment.
        """
        height = self.text_height * 2.0
        pad = self._inches(_TABLE_PAD) * 1.5
        x = at.x
        for cell in cells:
            width = max(self.text_width(cell) + pad * 2.0, height)
            self._add_rectangle(x, at.y - height * 0.5, width, height)
            middle = Point2D.by_xy(x + width * 0.5, at.y)
            self.add_text(middle, cell, align=TextAlign.CENTER)
            x += width

    def add_datum_feature(self, tip: Point2D, at: Point2D, letter: str) -> None:
        """
        Draw a datum feature symbol: a filled triangle on a feature, joined to a boxed letter.

        :param tip: Middle of the side of the triangle that lies on the feature.
        :param at: Center of the box.
        :param letter: Letter of the datum.
        """
        unit = Vector2D.by_points(tip, at).normalize()
        side = Vector2D.by_xy(-unit.y, unit.x).scale(self._inches(_ARROW_LENGTH) * 0.5)
        apex = tip.translate(unit.scale(self._inches(_ARROW_LENGTH)))
        self.add_polygon([tip.translate(side), tip.translate(side.reverse()), apex])
        self.add_line(apex, at)

        half = self.text_height
        corners = [
            Point2D.by_xy(at.x + x * half, at.y + y * half)
            for x, y in ((-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0))
        ]
        self.add_polygon(corners, (1.0, 1.0, 1.0))
        self.add_polyline([*corners, corners[0]])
        self.add_text(at, letter, align=TextAlign.CENTER)

    def add_surface_finish(self, tip: Point2D, value: str) -> None:
        """
        Draw a machined surface finish symbol standing on a surface, with its roughness.

        :param tip: Point that touches the surface.
        :param value: Roughness.
        """
        size = self.text_height
        left = Point2D.by_xy(tip.x - size * 0.6, tip.y + size)
        middle = Point2D.by_xy(tip.x + size * 0.6, tip.y + size)
        right = Point2D.by_xy(tip.x + size * 1.3, tip.y + size * 2.2)
        self.add_polyline([left, tip, right])
        self.add_line(left, middle)
        at = Point2D.by_xy(tip.x - size * 0.2, tip.y + size * 1.9)
        self.add_text(at, value, height=size * 0.85, align=TextAlign.RIGHT)

    def write(self, path: str, dpi: int = _DEFAULT_DPI) -> None:
        """
        Write the page to a PNG, SVG or PDF file, chosen by the file's extension, at the size of the
        paper.

        :param path: File path.
        :param dpi: Pixels per inch of paper, which only applies to PNG.
        :raises ValueError: If the extension is not known or the page has no pixels at the dpi.
        :raises OSError: If the file cannot be written.
        """
        extension = Path(path).suffix.lower()
        if extension == ".png":
            self._write_png(path, dpi)
        elif extension == ".svg":
            self._write_svg(path)
        elif extension == ".pdf":
            self._write_pdf(path)
        else:
            raise ValueError(f"Expected a .png, .svg or .pdf path, got {path}.")

    def _inches(self, length: float) -> float:
        """
        Convert a length on the paper to the units of the canvas.

        :param length: Length in inches.
        :return: Length in units.
        """
        return length * self._units_per_inch

    def _add_rectangle(
        self, x: float, y: float, width: float, height: float, stroke: Stroke | None = None
    ) -> None:
        """
        Draw an axis-aligned rectangle.

        :param x: Left side.
        :param y: Bottom side.
        :param width: Width.
        :param height: Height.
        :param stroke: Appearance. Defaults to a thin solid black line.
        """
        corners = ((x, y), (x + width, y), (x + width, y + height), (x, y + height), (x, y))
        self.add_polyline((Point2D.by_xy(cx, cy) for cx, cy in corners), stroke)

    def _add_path(self, points: list[tuple[float, float]], stroke: Stroke) -> None:
        """
        Add a line to the page, split into dashes if its pattern has any.

        :param points: Points along the line.
        :param stroke: Appearance.
        """
        width = self.thin_width if stroke.width is None else stroke.width
        pattern = stroke.pattern.value
        if not pattern:
            self._items.append(_Polyline(points, stroke.color, width))
            return
        lengths = tuple(self._inches(length) for length in pattern)
        for dash in _dashes(points, lengths):
            self._items.append(_Polyline(dash, stroke.color, width))

    def _add_shoulder(self, at: Point2D, side: float, text: str) -> None:
        """
        Draw the horizontal end of a leader with its text.

        :param at: Point where the shoulder starts.
        :param side: 1 for a shoulder to the right, or -1 to the left.
        :param text: Text after the shoulder.
        """
        end = at.translate(Vector2D.by_xy(side * self._inches(_LEADER_SHOULDER), 0.0))
        self.add_line(at, end)
        align = TextAlign.LEFT if side > 0.0 else TextAlign.RIGHT
        start = end.translate(Vector2D.by_xy(side * self._inches(_TEXT_GAP), 0.0))
        self.add_text(start, text, align=align)

    def _add_extension(self, point: Point2D, end: Point2D, outward: Vector2D) -> None:
        """
        Draw an extension line from a little beyond a point to a little past a dimension line.

        :param point: Point being dimensioned.
        :param end: End of the dimension line.
        :param outward: Unit direction from the point to the dimension line.
        """
        gap = self._inches(_EXTENSION_GAP)
        overrun = self._inches(_EXTENSION_OVERRUN)
        if point.distance(end) > gap:
            self.add_line(
                point.translate(outward.scale(gap)), end.translate(outward.scale(overrun))
            )

    def _text_clearance(self, text: str, unit: Vector2D) -> float:
        """
        Get how far horizontal text reaches from its center along a direction, with a small gap.

        :param text: Text.
        :param unit: Unit direction.
        :return: Distance.
        """
        gap = self._inches(_TEXT_GAP)
        half_width = self.text_width(text) * 0.5 + gap
        half_height = self.text_height * 0.5 + gap
        reaches = []
        if abs(unit.x) > _PARALLEL_TOLERANCE:
            reaches.append(half_width / abs(unit.x))
        if abs(unit.y) > _PARALLEL_TOLERANCE:
            reaches.append(half_height / abs(unit.y))
        return min(reaches)

    def _add_dimension_line(self, end1: Point2D, end2: Point2D, text: str) -> None:
        """
        Draw a dimension line, with its arrowheads and text inside it where they fit, and otherwise
        outside it.

        :param end1: First end.
        :param end2: Second end.
        :param text: Text of the dimension.
        """
        between = Vector2D.by_points(end1, end2)
        length = between.magnitude
        unit = between.normalize()
        half = self._text_clearance(text, unit)
        tail = self._inches(_ARROW_LENGTH)

        if length >= 2.0 * (half + tail):
            middle = end1.translate(unit.scale(length * 0.5))
            self.add_line(end1, middle.translate(unit.scale(-half)))
            self.add_line(middle.translate(unit.scale(half)), end2)
            self.add_arrow(end1, unit.reverse())
            self.add_arrow(end2, unit)
            self.add_text(middle, text, align=TextAlign.CENTER)
            return

        self.add_line(
            end1.translate(unit.scale(-tail * 2.0)), end2.translate(unit.scale(tail * 2.0))
        )
        self.add_arrow(end1, unit)
        self.add_arrow(end2, unit.reverse())
        at = end2.translate(unit.scale(tail * 2.0 + half))
        self.add_text(at, text, align=TextAlign.CENTER)

    def _write_png(self, path: str, dpi: int) -> None:
        """
        Write the page to a PNG file.

        :param path: File path.
        :param dpi: Pixels per inch of paper.
        :raises ValueError: If the page has no pixels at the dpi.
        """
        scale = dpi / self._units_per_inch
        width = round(self._width * scale)
        height = round(self._height * scale)
        if width < 1 or height < 1:
            raise ValueError(f"Expected an image size in pixels, got {width} by {height}.")

        itool = RenderICanvas(width, height)
        for item in self._items:
            r, g, b = item.color
            coords = [c for x, y in item.points for c in (x * scale, height - y * scale)]
            if isinstance(item, _Polyline):
                itool.AddPolyline(coords, r, g, b, max(item.width * scale, 1.0))
            else:
                itool.FillPolygon(coords, r, g, b)
        _write_png(path, itool.Render(), width, height)

    def _write_svg(self, path: str) -> None:
        """
        Write the page to an SVG file.

        :param path: File path.
        """

        def color_of(color: Color) -> str:
            r, g, b = (round(c * 255.0) for c in color)
            return f"rgb({r},{g},{b})"

        def points_of(points: list[tuple[float, float]]) -> str:
            return " ".join(f"{x:.4f},{self._height - y:.4f}" for x, y in points)

        inches = (self._width / self._units_per_inch, self._height / self._units_per_inch)
        lines = [
            '<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{inches[0]:g}in" height="{inches[1]:g}in" '
            f'viewBox="0 0 {self._width:g} {self._height:g}">',
            f'<rect width="{self._width:g}" height="{self._height:g}" fill="white"/>',
            '<g fill="none" stroke-linecap="round" stroke-linejoin="round">',
        ]
        for item in self._items:
            points = points_of(item.points)
            if isinstance(item, _Polyline):
                lines.append(
                    f'<polyline points="{points}" stroke="{color_of(item.color)}" '
                    f'stroke-width="{item.width:.4f}"/>'
                )
            else:
                lines.append(f'<polygon points="{points}" fill="{color_of(item.color)}"/>')
        lines += ["</g>", "</svg>", ""]
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _write_pdf(self, path: str) -> None:
        """
        Write the page to a one-page PDF file.

        :param path: File path.
        """
        scale = _POINTS_PER_INCH / self._units_per_inch
        commands = [f"{scale:.6f} 0 0 {scale:.6f} 0 0 cm", "1 J", "1 j"]
        for item in self._items:
            r, g, b = item.color
            path_commands = [f"{item.points[0][0]:.4f} {item.points[0][1]:.4f} m"]
            path_commands += [f"{x:.4f} {y:.4f} l" for x, y in item.points[1:]]
            if isinstance(item, _Polyline):
                commands += [f"{r:.3f} {g:.3f} {b:.3f} RG", f"{item.width:.4f} w"]
                commands += [*path_commands, "S"]
            else:
                commands += [f"{r:.3f} {g:.3f} {b:.3f} rg", *path_commands, "h f"]
        content = zlib.compress("\n".join(commands).encode("ascii"))

        media_width = self._width * scale
        media_height = self._height * scale
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            (
                "<< /Type /Page /Parent 2 0 R "
                f"/MediaBox [0 0 {media_width:.3f} {media_height:.3f}] "
                "/Contents 4 0 R /Resources << >> >>"
            ).encode("ascii"),
            (f"<< /Length {len(content)} /Filter /FlateDecode >>\nstream\n").encode("ascii")
            + content
            + b"\nendstream",
        ]

        data = bytearray(b"%PDF-1.4\n")
        offsets = []
        for number, body in enumerate(objects, start=1):
            offsets.append(len(data))
            data += f"{number} 0 obj\n".encode("ascii") + body + b"\nendobj\n"
        xref = len(data)
        data += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii")
        for offset in offsets:
            data += f"{offset:010d} 00000 n \n".encode("ascii")
        data += (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
        ).encode("ascii")
        with open(path, "wb") as f:
            f.write(data)


class SheetView:
    """
    A projected view placed on a sheet, which annotates the sheet using points on the part.

    :ivar sheet: Sheet the view is on.
    :ivar shape: Shape in the view.
    :ivar camera: Direction of the view.
    :ivar scale: Length on the sheet for each length on the part.
    :ivar origin: Position on the sheet of the global origin.
    :ivar min_point: Lower left corner of the view on the sheet.
    :ivar max_point: Upper right corner of the view on the sheet.
    """

    def __init__(
        self,
        sheet: Sheet,
        shape: Shape,
        camera: Camera,
        scale: float,
        origin: Point2D,
        min_point: Point2D,
        max_point: Point2D,
        lines: list[_ViewLine] | None = None,
    ):
        """
        Initialize from named parts, without drawing anything.

        :param sheet: Sheet the view is on.
        :param shape: Shape in the view.
        :param camera: Direction of the view.
        :param scale: Length on the sheet for each length on the part.
        :param origin: Position on the sheet of the global origin.
        :param min_point: Lower left corner of the view on the sheet.
        :param max_point: Upper right corner of the view on the sheet.
        :param lines: Lines in the plane of the view, which a detail view enlarges.
        """
        self._sheet = sheet
        self._shape = shape
        self._camera = camera
        self._scale = scale
        self._origin = origin
        self._min_point = min_point
        self._max_point = max_point
        self._lines = [] if lines is None else lines

    @property
    def sheet(self) -> Sheet:
        """
        Sheet the view is on.

        :return: Sheet.
        """
        return self._sheet

    @property
    def shape(self) -> Shape:
        """
        Shape in the view.

        :return: Shape.
        """
        return self._shape

    @property
    def camera(self) -> Camera:
        """
        Direction of the view.

        :return: Camera.
        """
        return self._camera

    @property
    def scale(self) -> float:
        """
        Scale of the view.

        :return: Length on the sheet for each length on the part.
        """
        return self._scale

    @property
    def origin(self) -> Point2D:
        """
        Position on the sheet of the global origin.

        :return: Position.
        """
        return self._origin

    @property
    def min_point(self) -> Point2D:
        """
        Lower left corner of the view on the sheet.

        :return: Corner.
        """
        return self._min_point

    @property
    def max_point(self) -> Point2D:
        """
        Upper right corner of the view on the sheet.

        :return: Corner.
        """
        return self._max_point

    @property
    def lines(self) -> list[_ViewLine]:
        """
        Lines in the plane of the view.

        :return: Lines.
        """
        return self._lines

    def to_sheet(self, point: Point) -> Point2D:
        """
        Get where a point on the part appears on the sheet.

        :param point: Point on the part.
        :return: Position on the sheet.
        """
        projected = self._camera.project(point)
        return Point2D.by_xy(
            self._origin.x + projected.x * self._scale, self._origin.y + projected.y * self._scale
        )

    def add_dimension(
        self,
        p1: Point,
        p2: Point,
        offset: float,
        along: Vector2D | None = None,
        text: str | None = None,
        prefix: str = "",
        suffix: str = "",
        decimals: int = 2,
    ) -> None:
        """
        Dimension the distance between two points on the part, as measured in the view.

        :param p1: First point.
        :param p2: Second point.
        :param offset: Distance on the sheet of the dimension line from the farther point, toward
            the left of the measuring direction if positive.
        :param along: Direction on the sheet to measure in. Defaults to the direction between the
            points.
        :param text: Text of the dimension. Defaults to the measured length.
        :param prefix: Text before a measured length, such as a diameter symbol.
        :param suffix: Text after a measured length, such as a tolerance.
        :param decimals: Number of decimal places of a measured length.
        :raises ValueError: If the points coincide along the measuring direction.
        """
        s1 = self.to_sheet(p1)
        s2 = self.to_sheet(p2)
        if text is None:
            between = Vector2D.by_points(s1, s2)
            measured = between.magnitude if along is None else abs(between.dot(along.normalize()))
            text = f"{prefix}{_format_length(measured / self._scale, decimals)}{suffix}"
        self._sheet.add_linear_dimension(s1, s2, offset, text, along)

    def add_radius(
        self,
        edge: Edge,
        angle: float = math.pi / 4.0,
        text: str | None = None,
        suffix: str = "",
        decimals: int = 2,
    ) -> None:
        """
        Dimension the radius of a circular edge facing the view.

        :param edge: Circular edge.
        :param angle: Direction on the sheet from the center to the arrowhead, in radians.
        :param text: Text of the dimension. Defaults to R and the measured radius.
        :param suffix: Text after a measured radius, such as a tolerance.
        :param decimals: Number of decimal places of a measured radius.
        :raises ValueError: If the edge is not a circle facing the view.
        """
        circle = self._facing_circle(edge)
        if text is None:
            text = f"R{_format_length(circle.radius, decimals)}{suffix}"
        self._sheet.add_radial_dimension(
            self.to_sheet(circle.frame.origin), circle.radius * self._scale, text, angle
        )

    def add_diameter(
        self,
        edge: Edge,
        angle: float = math.pi / 4.0,
        text: str | None = None,
        prefix: str = "",
        suffix: str = "",
        decimals: int = 2,
    ) -> None:
        """
        Dimension the diameter of a circular edge facing the view with a leader.

        :param edge: Circular edge.
        :param angle: Direction on the sheet from the center to the arrowhead, in radians.
        :param text: Text of the dimension. Defaults to a diameter symbol and the measured diameter.
        :param prefix: Text before the diameter symbol, such as a count of holes.
        :param suffix: Text after a measured diameter, such as a tolerance or a further line.
        :param decimals: Number of decimal places of a measured diameter.
        :raises ValueError: If the edge is not a circle facing the view.
        """
        circle = self._facing_circle(edge)
        if text is None:
            diameter = _format_length(circle.radius * 2.0, decimals)
            text = f"{prefix}{Symbol.DIAMETER}{diameter}{suffix}"
        unit = _unit_at(angle)
        center = self.to_sheet(circle.frame.origin)
        tip = center.translate(unit.scale(circle.radius * self._scale))
        at = tip.translate(unit.scale(_LEADER_LENGTH * self._sheet.units_per_inch))
        self._sheet.add_leader(tip, at, text)

    def add_center_line(self, p1: Point, p2: Point) -> None:
        """
        Draw a center line between two points on the part, reaching a little past both.

        :param p1: First point.
        :param p2: Second point.
        """
        s1 = self.to_sheet(p1)
        s2 = self.to_sheet(p2)
        unit = Vector2D.by_points(s1, s2).normalize()
        overrun = _EXTENSION_OVERRUN * self._sheet.units_per_inch
        self._sheet.add_line(
            s1.translate(unit.scale(-overrun)),
            s2.translate(unit.scale(overrun)),
            Stroke(pattern=LinePattern.CENTER),
        )

    def add_cutting_plane(self, origin: Point, normal: Vector, label: str) -> None:
        """
        Mark a plane that the view sees edge-on, with arrows pointing in the direction of sight.

        :param origin: Point on the plane.
        :param normal: Normal of the plane, pointing to the side that is removed.
        :param label: Letter at each end.
        :raises ValueError: If the normal is along the view.
        """
        right = self._camera.right
        up = self._camera.direction.normalize().cross(right)
        across = Vector2D.by_xy(normal.dot(right), normal.dot(up))
        if across.magnitude < _PARALLEL_TOLERANCE:
            raise ValueError("Expected a plane that the view sees edge-on.")
        sight = across.normalize().reverse()
        along = Vector2D.by_xy(-sight.y, sight.x)

        inch = self._sheet.units_per_inch
        center = self.to_sheet(origin)
        corners = [
            Vector2D.by_xy(x - center.x, y - center.y).dot(along)
            for x in (self._min_point.x, self._max_point.x)
            for y in (self._min_point.y, self._max_point.y)
        ]
        overrun = _CUTTING_PLANE_OVERRUN * inch
        ends = [
            center.translate(along.scale(min(corners) - overrun)),
            center.translate(along.scale(max(corners) + overrun)),
        ]
        thick = self._sheet.thick_width
        self._sheet.add_line(ends[0], ends[1], Stroke(width=thick, pattern=LinePattern.PHANTOM))
        for end in ends:
            tip = end.translate(sight.scale(_CUTTING_PLANE_ARROW * inch))
            self._sheet.add_line(end, tip, Stroke(width=thick))
            self._sheet.add_arrow(tip, sight)
            at = tip.translate(sight.scale(self._sheet.text_height * 1.5))
            self._sheet.add_text(
                at, label, height=self._sheet.text_height * 1.5, align=TextAlign.CENTER
            )

    def add_label(self, text: str, gap: float | None = None) -> None:
        """
        Draw a title below the view, such as the name of a section and its scale.

        :param text: Text of the title.
        :param gap: Distance on the sheet below the view. Defaults to a quarter of an inch.
        """
        distance = 0.25 * self._sheet.units_per_inch if gap is None else gap
        height = self._sheet.text_height * 1.25
        at = Point2D.by_xy(
            (self._min_point.x + self._max_point.x) * 0.5, self._min_point.y - distance
        )
        self._sheet.add_text(at, text, height=height, align=TextAlign.CENTER)

    def add_angle(
        self, vertex: Point, p1: Point, p2: Point, radius: float, text: str | None = None
    ) -> None:
        """
        Dimension the angle seen in the view, counterclockwise from one point to another around a
        vertex.

        :param vertex: Point on the part at the corner of the angle.
        :param p1: Point on the side the angle starts from.
        :param p2: Point on the side the angle ends at.
        :param radius: Radius of the arc on the sheet.
        :param text: Text of the dimension. Defaults to the measured angle in degrees.
        """
        center = self.to_sheet(vertex)
        s1 = self.to_sheet(p1)
        s2 = self.to_sheet(p2)
        if text is None:
            sweep = _sweep(_angle_to(center, s1), _angle_to(center, s2))
            text = f"{math.degrees(sweep):.1f}{Symbol.DEGREE}"
        self._sheet.add_angular_dimension(center, s1, s2, radius, text)

    def add_center_mark(self, edge: Edge) -> None:
        """
        Mark the center of a circular edge facing the view.

        :param edge: Circular edge.
        :raises ValueError: If the edge is not a circle facing the view.
        """
        circle = self._facing_circle(edge)
        self._sheet.add_center_mark(self.to_sheet(circle.frame.origin), circle.radius * self._scale)

    def _facing_circle(self, edge: Edge) -> Circle:
        """
        Get the circle of an edge, which must appear round in the view.

        :param edge: Edge to check.
        :return: Circle of the edge.
        :raises ValueError: If the edge is not a circle facing the view.
        """
        curve = edge.curve
        if not isinstance(curve, Circle):
            raise ValueError("Expected a circular edge.")
        direction = self._camera.direction.normalize()
        if curve.frame.z_direction.normalize().cross(direction).magnitude > _PARALLEL_TOLERANCE:
            raise ValueError("Expected a circle facing the view.")
        return curve


class Sheet(Canvas):
    """
    Tool to make an engineering drawing on standard paper, with a border, projected views and a
    title block. Coordinates use the part's length unit, so that a view's scale is true, and
    annotations follow ASME conventions with third-angle projection.
    """

    def __init__(self, paper: Paper = Paper.B, units_per_inch: float = 1.0):
        """
        Initialize with the paper, drawing its border.

        :param paper: Paper size.
        :param units_per_inch: Length units of the part in an inch, such as 25.4 for millimeters.
        :raises ValueError: If the units per inch is not positive.
        """
        width, height = paper.value
        super().__init__(width * units_per_inch, height * units_per_inch, units_per_inch)
        self._paper = paper
        self._views: list[SheetView] = []

        margin = self._inches(_BORDER_MARGIN)
        self._add_rectangle(
            margin,
            margin,
            self.width - margin * 2.0,
            self.height - margin * 2.0,
            Stroke(width=self.thick_width),
        )

    @property
    def paper(self) -> Paper:
        """
        Paper size.

        :return: Paper.
        """
        return self._paper

    def add_view(
        self,
        shape: Shape,
        view: View | Camera,
        at: Point2D,
        scale: float = 1.0,
        hidden: bool = True,
    ) -> SheetView:
        """
        Draw a view with its visible and smooth edges, and optionally its hidden edges.

        :param shape: Shape to draw.
        :param view: Direction of the view, where any target and span of a camera are not used.
        :param at: Position of the center of the view on the sheet.
        :param scale: Length on the sheet for each length on the part.
        :param hidden: Whether to draw hidden edges.
        :return: New view.
        :raises ValueError: If the scale is not positive.
        """
        if scale <= 0.0:
            raise ValueError(f"Expected a positive scale, got {scale}.")
        camera = view if isinstance(view, Camera) else Camera.by_view(view)
        tool, low, high = self._project(shape, camera)
        origin = Point2D.by_xy(
            at.x - (low.x + high.x) * 0.5 * scale,
            at.y - (low.y + high.y) * 0.5 * scale,
        )
        lines = self._view_lines(tool, scale, hidden)
        return self._draw_view(shape, camera, scale, origin, lines, low, high)

    def add_projected_view(
        self, parent: SheetView, view: View, gap: float, hidden: bool = True
    ) -> SheetView:
        """
        Draw another view of a view's shape at the same scale, in third-angle projection: on the
        side of the parent that it looks from, and aligned with the parent.

        :param parent: View to project from.
        :param view: Direction of the new view, which must be at a right angle to the parent's.
        :param gap: Distance on the sheet between the two views.
        :param hidden: Whether to draw hidden edges.
        :return: New view.
        :raises ValueError: If the view is not at a right angle to the parent or does not line up
            with it.
        """
        camera = Camera.by_view(view)
        tool, low, high = self._project(parent.shape, camera)
        origin = self._aligned_origin(parent, camera, low, high, gap)
        lines = self._view_lines(tool, parent.scale, hidden)
        return self._draw_view(parent.shape, camera, parent.scale, origin, lines, low, high)

    def add_section_view(
        self, parent: SheetView, origin: Point, normal: Vector, gap: float, label: str = "A"
    ) -> SheetView:
        """
        Draw the view of a view's shape cut by a plane, with its cut area hatched, in third-angle
        projection at the same scale, and mark the plane on the parent.

        :param parent: View to project from, which must see the plane edge-on.
        :param origin: Point on the plane.
        :param normal: Normal of the plane, pointing to the side that is removed, which is the side
            the new view looks from.
        :param gap: Distance on the sheet between the two views.
        :param label: Letter of the section.
        :return: New view.
        :raises ValueError: If the parent does not see the plane edge-on along one of its axes, or
            the plane misses the shape.
        """
        unit = normal.normalize()
        right = parent.camera.right
        parent_up = parent.camera.direction.normalize().cross(right)
        if abs(abs(unit.dot(parent_up)) - 1.0) < _PARALLEL_TOLERANCE:
            up = unit.cross(right)
        elif abs(abs(unit.dot(right)) - 1.0) < _PARALLEL_TOLERANCE:
            up = parent_up
        else:
            raise ValueError("Expected a plane that the parent sees edge-on along one of its axes.")
        camera = Camera.by_direction(unit, up)

        shape = parent.shape
        box = shape.bounding_box
        size = _CUT_TOOL_SIZE * math.hypot(box.dx, box.dy, box.dz)
        x_direction = camera.right
        y_direction = unit.cross(x_direction)
        corner = origin.translate(
            x_direction.scale(-size * 0.5).add(y_direction.scale(-size * 0.5))
        )
        kept = shape.cut(Box.by_size(size, size, size, Frame.by_vectors(corner, x_direction, unit)))
        section = shape.intersect(self._plane_face(corner, x_direction, y_direction, size))
        if len(section.faces()) == 0:
            raise ValueError("Expected a plane that cuts the shape.")

        tool, low, high = self._project(kept, camera)
        scale = parent.scale
        lines = self._hatch_lines(section, camera, scale)
        lines += self._view_lines(tool, scale, False)
        placed = self._aligned_origin(parent, camera, low, high, gap)
        parent.add_cutting_plane(origin, normal, label)
        return self._draw_view(shape, camera, scale, placed, lines, low, high)

    def add_detail_view(
        self,
        parent: SheetView,
        center: Point,
        radius: float,
        at: Point2D,
        scale: float,
        label: str = "B",
    ) -> SheetView:
        """
        Draw a circular part of a view at a larger scale, and mark that part on the parent.

        :param parent: View to enlarge.
        :param center: Point on the part at the center of the circle.
        :param radius: Radius of the circle, as a length on the part.
        :param at: Position of the center of the detail on the sheet.
        :param scale: Length on the sheet for each length on the part.
        :param label: Letter of the detail.
        :return: New view.
        :raises ValueError: If the scale is not positive.
        """
        if scale <= 0.0:
            raise ValueError(f"Expected a positive scale, got {scale}.")
        projected = parent.camera.project(center)
        lines = [
            _ViewLine(part, line.stroke)
            for line in parent.lines
            for part in _clip_to_circle(line.points, (projected.x, projected.y), radius)
        ]
        origin = Point2D.by_xy(at.x - projected.x * scale, at.y - projected.y * scale)
        low = Point2D.by_xy(projected.x - radius, projected.y - radius)
        high = Point2D.by_xy(projected.x + radius, projected.y + radius)
        detail = self._draw_view(parent.shape, parent.camera, scale, origin, lines, low, high)
        self.add_curve(Circle2D.by_radius(radius * scale, Frame2D.by_origin(at)))

        # Mark the part on the parent, with its letter outside the circle
        marked = parent.to_sheet(center)
        mark_radius = radius * parent.scale
        self.add_curve(
            Circle2D.by_radius(mark_radius, Frame2D.by_origin(marked)),
            Stroke(pattern=LinePattern.PHANTOM),
        )
        reach = mark_radius + self.text_height
        unit = _unit_at(math.pi / 4.0)
        self.add_text(marked.translate(unit.scale(reach)), label, align=TextAlign.CENTER)
        return detail

    def add_zones(self, columns: int, rows: int) -> None:
        """
        Divide the border into zones, with numbers from the right and letters from the bottom.

        :param columns: Number of numbered columns.
        :param rows: Number of lettered rows.
        """
        margin = self._inches(_BORDER_MARGIN)
        tick = self._inches(_ZONE_TICK)
        band = margin * 0.5
        width = self.width - margin * 2.0
        height = self.height - margin * 2.0
        for i in range(columns + 1):
            x = margin + width * i / columns
            self.add_line(Point2D.by_xy(x, margin), Point2D.by_xy(x, margin - tick))
            self.add_line(
                Point2D.by_xy(x, self.height - margin),
                Point2D.by_xy(x, self.height - margin + tick),
            )
            if i < columns:
                name = str(columns - i)
                middle = x + width / columns * 0.5
                for y in (band, self.height - band):
                    self.add_text(Point2D.by_xy(middle, y), name, align=TextAlign.CENTER)
        for i in range(rows + 1):
            y = margin + height * i / rows
            self.add_line(Point2D.by_xy(margin, y), Point2D.by_xy(margin - tick, y))
            self.add_line(
                Point2D.by_xy(self.width - margin, y), Point2D.by_xy(self.width - margin + tick, y)
            )
            if i < rows:
                name = chr(ord("A") + i)
                middle = y + height / rows * 0.5
                for x in (band, self.width - band):
                    self.add_text(Point2D.by_xy(x, middle), name, align=TextAlign.CENTER)

    def add_title_block(
        self,
        title: str,
        number: str = "",
        revision: str = "",
        date: str = "",
        drawn_by: str = "",
        scale: float | None = None,
    ) -> None:
        """
        Draw a title block in the lower right corner, with the third-angle projection symbol.

        :param title: Title of the drawing.
        :param number: Drawing number.
        :param revision: Revision.
        :param date: Date.
        :param drawn_by: Who drew it.
        :param scale: Scale to show. Defaults to the scale of the first view, or none without views.
        """
        if scale is None and self._views:
            scale = self._views[0].scale
        scale_text = "" if scale is None else _format_scale(scale)

        inch = self._units_per_inch
        margin = _BORDER_MARGIN * inch
        block_width = 6.25 * inch
        row = 0.75 * inch
        left = self.width - margin - block_width
        bottom = margin
        side = 2.0 * inch
        main = left + side

        self._add_symbol_cell(left, bottom + row, side, row)
        self._add_cell(left, bottom, 1.25 * inch, row, "DRAWN BY", drawn_by, 0.12)
        self._add_cell(left + 1.25 * inch, bottom, 0.75 * inch, row, "DATE", date, 0.1)
        self._add_cell(main, bottom + row, 4.25 * inch, row, "TITLE", title, 0.2)
        self._add_cell(main, bottom, 0.5 * inch, row, "SIZE", self._paper.name, 0.16)
        self._add_cell(main + 0.5 * inch, bottom, 2.25 * inch, row, "DWG NO", number, 0.16)
        self._add_cell(main + 2.75 * inch, bottom, 0.5 * inch, row, "REV", revision, 0.16)
        self._add_cell(main + 3.25 * inch, bottom, 1.0 * inch, row, "SCALE", scale_text, 0.14)

    def _project(self, shape: Shape, camera: Camera) -> tuple[HiddenLineShape, Point2D, Point2D]:
        """
        Find the visible and hidden lines of a shape in a view.

        :param shape: Source shape.
        :param camera: Direction of the view.
        :return: Tool with the lines, and the lower left and upper right corners of its edges in the
            plane of the view.
        """
        tool = HiddenLineShape(shape, camera.direction, camera.up)
        box = Compound.by_shapes([tool.visible(), tool.hidden()]).bounding_box
        low = Point2D.by_xy(box.min_point.x, box.min_point.y)
        high = Point2D.by_xy(box.max_point.x, box.max_point.y)
        return tool, low, high

    def _aligned_origin(
        self, parent: SheetView, camera: Camera, low: Point2D, high: Point2D, gap: float
    ) -> Point2D:
        """
        Find where a view goes to be aligned with a parent, on the side of it that it looks from.

        :param parent: View to align with.
        :param camera: Direction of the view.
        :param low: Lower left corner of the view's lines in the plane of the view.
        :param high: Upper right corner of the view's lines in the plane of the view.
        :param gap: Distance on the sheet between the two views.
        :return: Position on the sheet of the global origin.
        :raises ValueError: If the view is not at a right angle to the parent or does not line up
            with it.
        """
        scale = parent.scale
        toward = camera.direction.normalize()
        parent_right = parent.camera.right
        parent_up = parent.camera.direction.normalize().cross(parent_right)
        across = toward.dot(parent_right)
        upward = toward.dot(parent_up)

        def is_same(a: Vector, b: Vector) -> bool:
            return a.cross(b).magnitude <= _PARALLEL_TOLERANCE and a.dot(b) > 0.0

        if abs(abs(across) - 1.0) < _PARALLEL_TOLERANCE:
            if not is_same(toward.cross(camera.right), parent_up):
                raise ValueError("Expected a view that lines up with the parent.")
            x = (
                parent.max_point.x + gap - low.x * scale
                if across > 0.0
                else parent.min_point.x - gap - high.x * scale
            )
            return Point2D.by_xy(x, parent.origin.y)
        if abs(abs(upward) - 1.0) < _PARALLEL_TOLERANCE:
            if not is_same(camera.right, parent_right):
                raise ValueError("Expected a view that lines up with the parent.")
            y = (
                parent.max_point.y + gap - low.y * scale
                if upward > 0.0
                else parent.min_point.y - gap - high.y * scale
            )
            return Point2D.by_xy(parent.origin.x, y)
        raise ValueError("Expected a view at a right angle to the parent.")

    def _plane_face(
        self, corner: Point, x_direction: Vector, y_direction: Vector, size: float
    ) -> Face:
        """
        Make a square planar face.

        :param corner: One corner.
        :param x_direction: Unit direction of one side.
        :param y_direction: Unit direction of the other side.
        :param size: Length of a side.
        :return: New face.
        """
        along_x = x_direction.scale(size)
        along_y = y_direction.scale(size)
        corners = [
            corner,
            corner.translate(along_x),
            corner.translate(along_x.add(along_y)),
            corner.translate(along_y),
        ]
        edges = [Edge.by_points(a, b) for a, b in zip(corners, [*corners[1:], corner], strict=True)]
        return Face.by_wire(Wire.by_edges(edges))

    def _edge_lines(
        self, edges: Shape, camera: Camera | None, scale: float, stroke: Stroke
    ) -> list[_ViewLine]:
        """
        Get the lines of a view from edges.

        :param edges: Shape whose edges to use.
        :param camera: View to project the edges with, or None if they are already in its plane.
        :param scale: Scale of the view, which sets how closely lines follow curves.
        :param stroke: Appearance.
        :return: Lines in the plane of the view.
        """
        deflection = self._inches(_SAMPLE_DEFLECTION) / scale
        lines = []
        for edge in edges.edges():
            points = edge.points(deflection)
            projected = (
                [(p.x, p.y) for p in points]
                if camera is None
                else [(q.x, q.y) for q in (camera.project(p) for p in points)]
            )
            lines.append(_ViewLine(projected, stroke))
        return lines

    def _view_lines(self, tool: HiddenLineShape, scale: float, hidden: bool) -> list[_ViewLine]:
        """
        Get the lines of a view, with visible edges last so that they go over any hidden edges they
        coincide with.

        :param tool: Tool with the lines of the shape.
        :param scale: Scale of the view.
        :param hidden: Whether to include hidden edges.
        :return: Lines in the plane of the view.
        """
        lines = []
        if hidden:
            lines += self._edge_lines(
                tool.hidden(), None, scale, Stroke(pattern=LinePattern.HIDDEN)
            )
        lines += self._edge_lines(tool.visible_smooth(), None, scale, Stroke(_SMOOTH_EDGE_COLOR))
        lines += self._edge_lines(tool.visible(), None, scale, Stroke(width=self.thick_width))
        return lines

    def _hatch_lines(self, section: Shape, camera: Camera, scale: float) -> list[_ViewLine]:
        """
        Get the lines that hatch a cut area, at 45 degrees on the sheet.

        :param section: Faces of the cut area, in the plane of the view.
        :param camera: Direction of the view.
        :param scale: Scale of the view.
        :return: Lines in the plane of the view.
        """
        right = camera.right
        up = camera.direction.normalize().cross(right)
        along = right.add(up).normalize()
        across = right.subtract(up).normalize()
        box = section.bounding_box
        center = box.center
        reach = math.hypot(box.dx, box.dy, box.dz)
        step = self._inches(_HATCH_SPACING) / scale
        hatch = [
            Edge.by_points(
                center.translate(across.scale(i * step).add(along.scale(-reach))),
                center.translate(across.scale(i * step).add(along.scale(reach))),
            )
            for i in range(-math.ceil(reach / step), math.ceil(reach / step) + 1)
        ]
        clipped = Compound.by_shapes(hatch).intersect(section)
        return self._edge_lines(clipped, camera, scale, Stroke())

    def _draw_view(
        self,
        shape: Shape,
        camera: Camera,
        scale: float,
        origin: Point2D,
        lines: list[_ViewLine],
        low: Point2D,
        high: Point2D,
    ) -> SheetView:
        """
        Draw the lines of a view.

        :param shape: Shape in the view.
        :param camera: Direction of the view.
        :param scale: Length on the sheet for each length on the part.
        :param origin: Position on the sheet of the global origin.
        :param lines: Lines in the plane of the view.
        :param low: Lower left corner of the view in its plane.
        :param high: Upper right corner of the view in its plane.
        :return: New view.
        """
        for line in lines:
            self.add_polyline(
                (Point2D.by_xy(origin.x + x * scale, origin.y + y * scale) for x, y in line.points),
                line.stroke,
            )
        min_point = Point2D.by_xy(origin.x + low.x * scale, origin.y + low.y * scale)
        max_point = Point2D.by_xy(origin.x + high.x * scale, origin.y + high.y * scale)
        sheet_view = SheetView(self, shape, camera, scale, origin, min_point, max_point, lines)
        self._views.append(sheet_view)
        return sheet_view

    def _add_cell(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        label: str,
        value: str,
        value_height: float,
    ) -> None:
        """
        Draw a title block cell with a small label and a value, which shrinks to fit the cell.

        :param x: Left side.
        :param y: Bottom side.
        :param width: Width.
        :param height: Height.
        :param label: Name of the cell.
        :param value: Value of the cell.
        :param value_height: Largest letter height of the value, in inches.
        """
        inch = self._units_per_inch
        pad = 0.05 * inch
        self._add_rectangle(x, y, width, height)
        self.add_text(
            Point2D.by_xy(x + pad, y + height - pad - 0.04 * inch), label, height=0.07 * inch
        )

        if value:
            letter_height = value_height * inch
            value_width = self.text_width(value, letter_height)
            room = width - pad * 2.0
            if value_width > room:
                letter_height *= room / value_width
            self.add_text(
                Point2D.by_xy(x + pad, y + (height - 0.12 * inch) * 0.5),
                value,
                height=letter_height,
            )

    def _add_symbol_cell(self, x: float, y: float, width: float, height: float) -> None:
        """
        Draw a title block cell with the third-angle projection symbol: concentric circles on the
        left of a cone whose small end faces them.

        :param x: Left side.
        :param y: Bottom side.
        :param width: Width.
        :param height: Height.
        """
        inch = self._units_per_inch
        self._add_rectangle(x, y, width, height)
        middle_x = x + width * 0.5
        middle_y = y + height * 0.5

        center = Point2D.by_xy(middle_x - 0.4 * inch, middle_y)
        steps = math.ceil(2.0 * math.pi / _ARC_STEP)
        for radius in (0.1 * inch, 0.2 * inch):
            self.add_polyline(
                center.translate(_unit_at(2.0 * math.pi * i / steps).scale(radius))
                for i in range(steps + 1)
            )
        cone_left = middle_x + 0.05 * inch
        cone_right = middle_x + 0.65 * inch
        small = 0.1 * inch
        large = 0.2 * inch
        self.add_polyline(
            Point2D.by_xy(px, py)
            for px, py in (
                (cone_left, middle_y - small),
                (cone_right, middle_y - large),
                (cone_right, middle_y + large),
                (cone_left, middle_y + small),
                (cone_left, middle_y - small),
            )
        )
