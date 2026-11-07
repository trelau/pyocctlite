from __future__ import annotations

import math
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path
from unittest.mock import patch

from test_rendering import Image

from pyocctlite.drawing import Canvas, LinePattern, Paper, Sheet, Stroke, Symbol, TextAlign
from pyocctlite.geometry import (
    Ellipse2D,
    Frame,
    Line2D,
    Point,
    Point2D,
    TrimmedCurve2D,
    Vector,
    Vector2D,
)
from pyocctlite.primitives import Box, Cylinder
from pyocctlite.rendering import Camera, View
from pyocctlite.topology import Edge

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (1.0, 0.0, 0.0)
RED_PIXEL = (255, 0, 0)
SVG = "{http://www.w3.org/2000/svg}"


def xy(x: float, y: float) -> Point2D:
    return Point2D.by_xy(x, y)


class CanvasTestCase(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)

    def png(self, canvas: Canvas, dpi: int = 100) -> Image:
        path = self.folder / "image.png"
        canvas.write(str(path), dpi)
        return Image(path)

    def svg(self, canvas: Canvas) -> ET.Element:
        path = self.folder / "image.svg"
        canvas.write(str(path))
        return ET.parse(path).getroot()

    def pdf(self, canvas: Canvas) -> bytes:
        path = self.folder / "image.pdf"
        canvas.write(str(path))
        return path.read_bytes()


class TestCanvasPng(CanvasTestCase):
    def test_size_follows_the_paper_and_dpi(self):
        image = self.png(Canvas(4.0, 2.0), dpi=50)
        self.assertEqual((image.width, image.height), (200, 100))

    def test_units_per_inch_keep_the_paper_size(self):
        image = self.png(Canvas(101.6, 50.8, units_per_inch=25.4), dpi=50)
        self.assertEqual((image.width, image.height), (200, 100))

    def test_y_points_up(self):
        canvas = Canvas(4.0, 2.0)
        canvas.add_line(xy(1.0, 1.5), xy(3.0, 1.5), Stroke(RED, width=0.04))
        image = self.png(canvas)
        self.assertEqual(image.pixel(200, 50), RED_PIXEL)
        self.assertEqual(image.pixel(200, 150), WHITE)

    def test_polygon_fills_with_its_color(self):
        canvas = Canvas(4.0, 2.0)
        corners = [xy(1.0, 0.5), xy(3.0, 0.5), xy(3.0, 1.5), xy(1.0, 1.5)]
        canvas.add_polygon(corners, RED)
        image = self.png(canvas)
        self.assertEqual(image.pixel(200, 100), RED_PIXEL)
        self.assertEqual(image.pixel(50, 100), WHITE)

    def test_later_drawing_goes_on_top(self):
        canvas = Canvas(4.0, 2.0)
        corners = [xy(1.0, 0.5), xy(3.0, 0.5), xy(3.0, 1.5), xy(1.0, 1.5)]
        canvas.add_line(xy(0.0, 1.0), xy(4.0, 1.0), Stroke(width=0.1))
        canvas.add_polygon(corners, RED)
        image = self.png(canvas)
        self.assertEqual(image.pixel(200, 100), RED_PIXEL)
        self.assertEqual(image.pixel(50, 100), BLACK)

    def test_hidden_pattern_leaves_gaps(self):
        canvas = Canvas(4.0, 2.0)
        canvas.add_line(xy(0.0, 1.0), xy(4.0, 1.0), Stroke(width=0.02, pattern=LinePattern.HIDDEN))
        image = self.png(canvas)
        row = [image.pixel(x, 100) for x in range(400)]
        self.assertIn(BLACK, row)
        self.assertIn(WHITE, row)

    def test_patterns_continue_around_corners(self):
        canvas = Canvas(4.0, 2.0)
        points = [xy(1.0, 0.5), xy(1.05, 0.5), xy(1.05, 1.5)]
        canvas.add_polyline(points, Stroke(pattern=LinePattern.HIDDEN))
        image = self.png(canvas)
        self.assertTrue(any(image.pixel(105, y) == WHITE for y in range(55, 145)))

    def test_curve(self):
        canvas = Canvas(4.0, 2.0)
        frame_center = TrimmedCurve2D.by_points(xy(1.0, 1.0), xy(3.0, 1.0))
        canvas.add_curve(frame_center, Stroke(RED, width=0.04))
        self.assertEqual(self.png(canvas).pixel(200, 100), RED_PIXEL)

    def test_unbounded_curve_raises(self):
        with self.assertRaises(ValueError):
            Canvas(4.0, 2.0).add_curve(Line2D.by_points(xy(0.0, 0.0), xy(1.0, 0.0)))

    def test_edges_use_their_x_and_y(self):
        canvas = Canvas(4.0, 2.0)
        edge = Edge.by_points(Point.by_xyz(1.0, 1.0, 5.0), Point.by_xyz(3.0, 1.0, -5.0))
        canvas.add_edges(edge, Stroke(RED, width=0.04))
        self.assertEqual(self.png(canvas).pixel(200, 100), RED_PIXEL)

    def test_text_alignment(self):
        def extent(align: TextAlign) -> tuple[int, int]:
            canvas = Canvas(4.0, 2.0)
            canvas.add_text(xy(2.0, 1.0), "TEXT", height=0.2, align=align)
            image = self.png(canvas)
            xs = [x for x in range(400) for y in range(200) if image.pixel(x, y) != WHITE]
            return min(xs), max(xs)

        self.assertGreaterEqual(extent(TextAlign.LEFT)[0], 198)
        self.assertLessEqual(extent(TextAlign.RIGHT)[1], 202)
        low, high = extent(TextAlign.CENTER)
        self.assertLess(abs((low + high) * 0.5 - 200.0), 3.0)

    def test_text_rotates(self):
        canvas = Canvas(2.0, 4.0)
        canvas.add_text(xy(1.0, 1.0), "TEXT", height=0.2, angle=math.pi / 2.0)
        image = self.png(canvas)
        points = [(x, y) for x in range(200) for y in range(400) if image.pixel(x, y) != WHITE]
        xs = [x for x, _ in points]
        ys = [y for _, y in points]
        self.assertGreater(max(ys) - min(ys), max(xs) - min(xs))

    def test_symbols_are_not_question_marks(self):
        def strokes(text: str) -> bytes:
            canvas = Canvas(2.0, 1.0)
            canvas.add_text(xy(0.5, 0.5), text, height=0.3)
            return self.png(canvas).rows

        unknown = strokes("?")
        for symbol in ("⌀", "Ø", "°", "±"):
            self.assertNotEqual(strokes(symbol), unknown)
        self.assertEqual(strokes("中"), unknown)

    def test_unknown_extension_raises(self):
        with self.assertRaises(ValueError):
            Canvas(1.0, 1.0).write(str(self.folder / "image.bmp"))

    def test_bad_inputs_raise(self):
        with self.assertRaises(ValueError):
            Canvas(0.0, 1.0)
        with self.assertRaises(ValueError):
            Stroke((2.0, 0.0, 0.0))
        with self.assertRaises(ValueError):
            Stroke(width=0.0)
        with self.assertRaises(ValueError):
            Canvas(1.0, 1.0).add_text(xy(0.0, 0.0), "A", height=0.0)


class TestCanvasVectorFormats(CanvasTestCase):
    def canvas(self) -> Canvas:
        canvas = Canvas(101.6, 50.8, units_per_inch=25.4)
        canvas.add_line(xy(10.0, 40.0), xy(90.0, 40.0), Stroke(RED, width=0.5))
        canvas.add_polygon([xy(10.0, 10.0), xy(20.0, 10.0), xy(20.0, 20.0)])
        return canvas

    def test_svg_has_the_physical_size(self):
        root = self.svg(self.canvas())
        self.assertEqual(root.get("width"), "4in")
        self.assertEqual(root.get("height"), "2in")
        self.assertEqual(root.get("viewBox"), "0 0 101.6 50.8")

    def test_svg_flips_y_and_keeps_colors(self):
        root = self.svg(self.canvas())
        polyline = next(root.iter(f"{SVG}polyline"))
        self.assertEqual(polyline.get("stroke"), "rgb(255,0,0)")
        self.assertEqual(polyline.get("points"), "10.0000,10.8000 90.0000,10.8000")
        self.assertEqual(len(list(root.iter(f"{SVG}polygon"))), 1)

    def test_pdf_has_the_page_size(self):
        data = self.pdf(self.canvas())
        self.assertTrue(data.startswith(b"%PDF-"))
        self.assertIn(b"/MediaBox [0 0 288.000 144.000]", data)

    def test_pdf_cross_reference_points_at_its_objects(self):
        data = self.pdf(self.canvas())
        start = int(re.search(rb"startxref\n(\d+)", data).group(1))
        self.assertEqual(data[start : start + 4], b"xref")
        offsets = re.findall(rb"(\d{10}) 00000 n", data)
        self.assertEqual(len(offsets), 4)
        for number, offset in enumerate(offsets, start=1):
            obj = f"{number} 0 obj".encode()
            self.assertEqual(data[int(offset) : int(offset) + len(obj)], obj)

    def test_pdf_content_has_the_drawing(self):
        data = self.pdf(self.canvas())
        stream = data[data.index(b"stream\n") + 7 : data.index(b"\nendstream")]
        content = zlib.decompress(stream).decode("ascii")
        self.assertIn("1.000 0.000 0.000 RG", content)
        self.assertIn("10.0000 40.0000 m", content)
        self.assertIn("h f", content)


class TestCanvasAnnotations(CanvasTestCase):
    def lines(self, canvas: Canvas) -> list[tuple[tuple[float, float], tuple[float, float]]]:
        # Reads the drawing back through its SVG, which has y pointing down from the page height
        root = self.svg(canvas)
        found = []
        for polyline in root.iter(f"{SVG}polyline"):
            points = [
                tuple(float(v) for v in pair.split(",")) for pair in polyline.get("points").split()
            ]
            if len(points) == 2:
                found.append((points[0], points[1]))
        return found

    def test_arrow_points_along_its_direction(self):
        canvas = Canvas(4.0, 2.0)
        canvas.add_arrow(xy(2.0, 1.0), Vector2D.by_xy(1.0, 0.0), RED)
        image = self.png(canvas)
        self.assertEqual(image.pixel(190, 100), RED_PIXEL)
        self.assertEqual(image.pixel(205, 100), WHITE)

    def test_linear_dimension_clears_both_points(self):
        canvas = Canvas(8.0, 4.0)
        canvas.add_linear_dimension(
            xy(2.0, 1.0), xy(6.0, 2.0), 0.5, "4.00", Vector2D.by_xy(1.0, 0.0)
        )
        # The dimension line is above the higher point, with y measured down from the top
        heights = [a[1] for a, b in self.lines(canvas) if a[1] == b[1]]
        self.assertTrue(heights)
        self.assertAlmostEqual(min(heights), 4.0 - 2.5, places=3)

    def test_small_dimension_puts_its_arrows_outside(self):
        canvas = Canvas(8.0, 4.0)
        canvas.add_linear_dimension(
            xy(4.0, 1.0), xy(4.1, 1.0), -0.5, "0.10", Vector2D.by_xy(1.0, 0.0)
        )
        spans = [abs(b[0] - a[0]) for a, b in self.lines(canvas) if a[1] == b[1]]
        self.assertGreater(max(spans), 0.1)

    def test_coincident_dimension_points_raise(self):
        with self.assertRaises(ValueError):
            Canvas(8.0, 4.0).add_linear_dimension(xy(1.0, 1.0), xy(1.0, 1.0), 0.5, "0")
        with self.assertRaises(ValueError):
            Canvas(8.0, 4.0).add_linear_dimension(
                xy(1.0, 1.0), xy(1.0, 2.0), 0.5, "0", Vector2D.by_xy(1.0, 0.0)
            )

    def test_leader_points_at_its_tip(self):
        canvas = Canvas(4.0, 2.0)
        canvas.add_leader(xy(1.0, 1.0), xy(2.0, 1.0), "NOTE")
        image = self.png(canvas)
        self.assertEqual(image.pixel(105, 100), BLACK)
        self.assertEqual(image.pixel(95, 100), WHITE)

    def test_center_mark_reaches_past_the_circle(self):
        canvas = Canvas(4.0, 4.0)
        canvas.add_center_mark(xy(2.0, 2.0), 1.0)
        reach = max(abs(b[0] - 2.0) for _, b in self.lines(canvas))
        self.assertAlmostEqual(reach, 1.125, places=3)

    def test_angular_dimension_draws_its_arc(self):
        canvas = Canvas(4.0, 4.0)
        canvas.add_angular_dimension(xy(1.0, 1.0), xy(3.0, 1.0), xy(1.0, 3.0), 1.5, "90.0")
        image = self.png(canvas)
        # along the arc, away from the text at its middle
        angle = math.radians(15.0)
        x = round(100.0 + 150.0 * math.cos(angle))
        y = round(300.0 - 150.0 * math.sin(angle))
        window = [image.pixel(x + i, y + j) for i in range(-2, 3) for j in range(-2, 3)]
        self.assertTrue(any(pixel != WHITE for pixel in window))


class TestSmallAngle(CanvasTestCase):
    def test_text_goes_past_the_arc_clear_of_its_sides(self):
        canvas = Canvas(8.0, 4.0)
        vertex = xy(2.0, 1.0)
        with patch.object(Canvas, "add_text") as add:
            canvas.add_angular_dimension(vertex, xy(4.0, 1.0), xy(4.0, 1.2), 1.0, "5.7")
        at = add.call_args.args[0]
        self.assertGreater(math.atan2(at.y - vertex.y, at.x - vertex.x), math.radians(5.7) + 0.1)

    def test_arrows_point_in_from_outside(self):
        canvas = Canvas(8.0, 4.0)
        with patch.object(Canvas, "add_arrow") as add:
            canvas.add_angular_dimension(xy(2.0, 1.0), xy(4.0, 1.0), xy(4.0, 1.2), 1.0, "5.7")
        first, second = (call.args[1] for call in add.call_args_list)
        self.assertGreater(first.y, 0.9)
        self.assertLess(second.y, -0.9)

    def test_arrows_point_out_where_they_fit(self):
        canvas = Canvas(8.0, 4.0)
        with patch.object(Canvas, "add_arrow") as add:
            canvas.add_angular_dimension(xy(2.0, 1.0), xy(4.0, 1.0), xy(2.0, 3.0), 1.5, "90.0")
        first, second = (call.args[1] for call in add.call_args_list)
        self.assertLess(first.y, -0.9)
        self.assertLess(second.x, -0.9)


class SheetTestCase(CanvasTestCase):
    def setUp(self):
        super().setUp()
        self.box = Box.by_size(40.0, 20.0, 10.0)
        self.sheet = Sheet(Paper.B, units_per_inch=25.4)
        self.front = self.sheet.add_view(self.box, View.FRONT, xy(100.0, 80.0), scale=2.0)


class TestSheet(SheetTestCase):
    def test_paper_sets_the_size(self):
        self.assertAlmostEqual(self.sheet.width, 17.0 * 25.4)
        self.assertAlmostEqual(self.sheet.height, 11.0 * 25.4)
        image = self.png(Sheet(Paper.A), dpi=20)
        self.assertEqual((image.width, image.height), (220, 170))

    def test_border_is_drawn(self):
        image = self.png(Sheet(Paper.A), dpi=100)
        self.assertEqual(image.pixel(50, 400), BLACK)
        self.assertEqual(image.pixel(20, 400), WHITE)

    def test_view_is_centered_at_its_position(self):
        self.assertAlmostEqual(self.front.min_point.x, 60.0, delta=0.1)
        self.assertAlmostEqual(self.front.max_point.x, 140.0, delta=0.1)
        self.assertAlmostEqual(self.front.min_point.y, 70.0, delta=0.1)
        self.assertAlmostEqual(self.front.max_point.y, 90.0, delta=0.1)

    def test_to_sheet_follows_the_scale(self):
        a = self.front.to_sheet(Point.by_xyz(0.0, 0.0, 0.0))
        b = self.front.to_sheet(Point.by_xyz(40.0, 0.0, 10.0))
        self.assertAlmostEqual(a.x, 60.0, delta=0.1)
        self.assertAlmostEqual(a.y, 70.0, delta=0.1)
        self.assertAlmostEqual(b.x - a.x, 80.0)
        self.assertAlmostEqual(b.y - a.y, 20.0)

    def test_view_draws_the_part(self):
        image = self.png(self.sheet, dpi=100)
        scale = 100.0 / 25.4
        x = round(100.0 * scale)
        y = round((self.sheet.height - 90.0) * scale)
        self.assertTrue(any(image.pixel(x, y + i) != WHITE for i in range(-3, 4)))

    def test_bad_scale_raises(self):
        with self.assertRaises(ValueError):
            self.sheet.add_view(self.box, View.FRONT, xy(0.0, 0.0), scale=0.0)

    def test_top_view_is_above_and_aligned(self):
        top = self.sheet.add_projected_view(self.front, View.TOP, gap=10.0)
        self.assertAlmostEqual(top.min_point.y, self.front.max_point.y + 10.0, delta=0.1)
        a = Point.by_xyz(15.0, 3.0, 4.0)
        self.assertAlmostEqual(top.to_sheet(a).x, self.front.to_sheet(a).x)
        self.assertAlmostEqual(top.scale, 2.0)

    def test_bottom_view_is_below(self):
        bottom = self.sheet.add_projected_view(self.front, View.BOTTOM, gap=10.0)
        self.assertAlmostEqual(bottom.max_point.y, self.front.min_point.y - 10.0, delta=0.1)
        a = Point.by_xyz(15.0, 3.0, 4.0)
        self.assertAlmostEqual(bottom.to_sheet(a).x, self.front.to_sheet(a).x)

    def test_right_view_is_on_the_right_and_aligned(self):
        right = self.sheet.add_projected_view(self.front, View.RIGHT, gap=10.0)
        self.assertAlmostEqual(right.min_point.x, self.front.max_point.x + 10.0, delta=0.1)
        a = Point.by_xyz(15.0, 3.0, 4.0)
        self.assertAlmostEqual(right.to_sheet(a).y, self.front.to_sheet(a).y)

    def test_left_view_is_on_the_left(self):
        left = self.sheet.add_projected_view(self.front, View.LEFT, gap=10.0)
        self.assertAlmostEqual(left.max_point.x, self.front.min_point.x - 10.0, delta=0.1)

    def test_view_not_at_a_right_angle_raises(self):
        with self.assertRaises(ValueError):
            self.sheet.add_projected_view(self.front, View.ISO, gap=10.0)
        with self.assertRaises(ValueError):
            self.sheet.add_projected_view(self.front, View.BACK, gap=10.0)

    def test_view_that_does_not_line_up_raises(self):
        top = self.sheet.add_projected_view(self.front, View.TOP, gap=10.0)
        with self.assertRaises(ValueError):
            self.sheet.add_projected_view(top, View.RIGHT, gap=10.0)

    def test_camera_target_and_span_do_not_move_a_view(self):
        camera = Camera.by_view(View.FRONT, Point.by_xyz(5.0, 5.0, 5.0), 1.0)
        view = self.sheet.add_view(self.box, camera, xy(100.0, 80.0), scale=2.0)
        self.assertAlmostEqual(view.min_point.x, self.front.min_point.x)

    def test_inputs_are_unchanged(self):
        before = self.box.volume
        self.png(self.sheet)
        self.assertEqual(self.box.volume, before)


class TestSheetDimensions(SheetTestCase):
    def setUp(self):
        super().setUp()
        self.cylinder = Cylinder.by_size(10.0, 30.0, Frame.by_origin(Point.by_xyz(5.0, 6.0, 0.0)))
        self.top = self.sheet.add_view(self.cylinder, View.TOP, xy(100.0, 180.0), scale=2.0)
        circles = [e for e in self.cylinder.edges() if e.curve.__class__.__name__ == "Circle"]
        self.circle = circles[0]

    def test_dimension_measures_the_part_at_any_scale(self):
        with patch.object(self.sheet, "add_linear_dimension") as add:
            self.front.add_dimension(
                Point.by_xyz(0.0, 0.0, 0.0), Point.by_xyz(40.0, 0.0, 0.0), offset=-5.0
            )
        self.assertEqual(add.call_args.args[3], "40.00")

    def test_dimension_measures_along_a_direction(self):
        with patch.object(self.sheet, "add_linear_dimension") as add:
            self.front.add_dimension(
                Point.by_xyz(0.0, 0.0, 0.0),
                Point.by_xyz(40.0, 0.0, 10.0),
                offset=5.0,
                along=Vector2D.by_xy(0.0, 1.0),
            )
        self.assertEqual(add.call_args.args[3], "10.00")

    def test_dimension_ignores_depth_along_the_view(self):
        with patch.object(self.sheet, "add_linear_dimension") as add:
            self.front.add_dimension(
                Point.by_xyz(0.0, 0.0, 0.0), Point.by_xyz(40.0, 20.0, 0.0), offset=5.0
            )
        self.assertEqual(add.call_args.args[3], "40.00")

    def test_dimension_text_can_be_replaced(self):
        with patch.object(self.sheet, "add_linear_dimension") as add:
            self.front.add_dimension(
                Point.by_xyz(0.0, 0.0, 0.0),
                Point.by_xyz(40.0, 0.0, 0.0),
                offset=5.0,
                text="40 REF",
            )
        self.assertEqual(add.call_args.args[3], "40 REF")

    def test_radius_is_measured_and_placed(self):
        with patch.object(self.sheet, "add_radial_dimension") as add:
            self.top.add_radius(self.circle)
        center, radius, text, _ = add.call_args.args
        expected = self.top.to_sheet(Point.by_xyz(5.0, 6.0, 0.0))
        self.assertAlmostEqual(center.x, expected.x)
        self.assertAlmostEqual(center.y, expected.y)
        self.assertAlmostEqual(radius, 20.0)
        self.assertEqual(text, "R10.00")

    def test_diameter_is_measured_and_touches_the_circle(self):
        with patch.object(self.sheet, "add_leader") as add:
            self.top.add_diameter(self.circle, angle=0.0)
        tip, _, text = add.call_args.args
        expected = self.top.to_sheet(Point.by_xyz(15.0, 6.0, 0.0))
        self.assertAlmostEqual(tip.x, expected.x)
        self.assertAlmostEqual(tip.y, expected.y)
        self.assertEqual(text, "⌀20.00")

    def test_angle_is_measured_in_degrees(self):
        with patch.object(self.sheet, "add_angular_dimension") as add:
            self.front.add_angle(
                Point.by_xyz(0.0, 0.0, 0.0),
                Point.by_xyz(40.0, 0.0, 0.0),
                Point.by_xyz(40.0, 0.0, 40.0),
                radius=20.0,
            )
        self.assertEqual(add.call_args.args[4], "45.0°")

    def test_center_mark_uses_the_center_and_scale(self):
        with patch.object(self.sheet, "add_center_mark") as add:
            self.top.add_center_mark(self.circle)
        center, radius = add.call_args.args
        expected = self.top.to_sheet(Point.by_xyz(5.0, 6.0, 0.0))
        self.assertAlmostEqual(center.x, expected.x)
        self.assertAlmostEqual(radius, 20.0)

    def test_circle_seen_from_the_side_raises(self):
        with self.assertRaises(ValueError):
            self.front.add_diameter(self.circle)

    def test_edge_that_is_not_a_circle_raises(self):
        line = Edge.by_points(Point.by_xyz(0.0, 0.0, 0.0), Point.by_xyz(1.0, 0.0, 0.0))
        with self.assertRaises(ValueError):
            self.top.add_radius(line)

    def test_a_drawing_with_everything_writes_every_format(self):
        self.front.add_dimension(
            Point.by_xyz(0.0, 0.0, 0.0), Point.by_xyz(40.0, 0.0, 0.0), offset=-8.0
        )
        self.top.add_radius(self.circle)
        self.top.add_diameter(self.circle, angle=math.pi)
        self.top.add_center_mark(self.circle)
        self.sheet.add_title_block("A PART WITH A VERY LONG TITLE", "1", "A", "2026", "ME")
        self.png(self.sheet, dpi=30)
        self.svg(self.sheet)
        self.assertTrue(self.pdf(self.sheet).endswith(b"%%EOF\n"))


class TestTitleBlock(CanvasTestCase):
    def fields(self, sheet: Sheet) -> dict[str, str]:
        found = {}
        with patch.object(Canvas, "add_text") as add:
            sheet.add_title_block("TITLE TEXT", "NUMBER")
        for call in add.call_args_list:
            found[call.args[1]] = call
        return found

    def test_scale_comes_from_the_first_view(self):
        sheet = Sheet(Paper.B)
        sheet.add_view(Box.by_size(1.0, 1.0, 1.0), View.FRONT, xy(4.0, 4.0), scale=0.5)
        sheet.add_view(Box.by_size(1.0, 1.0, 1.0), View.TOP, xy(9.0, 4.0), scale=4.0)
        self.assertIn("1:2", self.fields(sheet))

    def test_scale_larger_than_full_size(self):
        sheet = Sheet(Paper.B)
        sheet.add_view(Box.by_size(1.0, 1.0, 1.0), View.FRONT, xy(4.0, 4.0), scale=2.0)
        self.assertIn("2:1", self.fields(sheet))

    def test_paper_size_is_shown(self):
        self.assertIn("C", self.fields(Sheet(Paper.C)))

    def test_long_value_shrinks_to_its_cell(self):
        with patch.object(Canvas, "add_text") as add:
            Sheet(Paper.B).add_title_block("T", number="X" * 200)
        call = next(c for c in add.call_args_list if c.args[1] == "X" * 200)
        self.assertLess(call.kwargs["height"], 0.16)


class TestSectionView(CanvasTestCase):
    def setUp(self):
        super().setUp()
        block = Box.by_size(40.0, 40.0, 20.0, Frame.by_origin(Point.by_xyz(-20.0, -20.0, 0.0)))
        hole = Cylinder.by_size(5.0, 20.0)
        self.part = block.cut(hole)
        self.volume = self.part.volume
        self.sheet = Sheet(Paper.C, units_per_inch=25.4)
        self.plan = self.sheet.add_view(self.part, View.TOP, xy(150.0, 300.0))
        self.section = self.sheet.add_section_view(
            self.plan, Point.by_xyz(0, 0, 0), Vector.by_xyz(0, -1, 0), gap=30.0
        )

    def test_section_is_placed_like_the_view_it_looks_from(self):
        self.assertLess(self.section.max_point.y, self.plan.min_point.y)
        a = Point.by_xyz(7.0, 0.0, 3.0)
        self.assertAlmostEqual(self.section.to_sheet(a).x, self.plan.to_sheet(a).x)

    def test_section_keeps_the_side_behind_the_plane(self):
        # The hole's far wall stays, and the near half of the part is gone
        direction = self.section.camera.direction
        self.assertAlmostEqual(direction.y, -1.0)

    def test_section_hatches_the_cut_only(self):
        image = self.png(self.sheet, dpi=254)
        center = self.section.to_sheet(Point.by_xyz(0.0, 0.0, 10.0))
        cut = self.section.to_sheet(Point.by_xyz(12.0, 0.0, 10.0))
        height = image.height

        def is_marked(point: Point2D) -> bool:
            x = round(point.x * 10.0)
            y = height - round(point.y * 10.0)
            return any(
                image.pixel(x + i, y + j) != WHITE for i in range(-25, 26) for j in range(-25, 26)
            )

        self.assertTrue(is_marked(cut))
        self.assertFalse(is_marked(center.translate(Vector2D.by_xy(2.0, 0.0))))

    def test_shape_is_unchanged(self):
        self.assertAlmostEqual(self.part.volume, self.volume)

    def test_plane_that_misses_raises(self):
        with self.assertRaises(ValueError):
            self.sheet.add_section_view(
                self.plan, Point.by_xyz(0, 500, 0), Vector.by_xyz(0, -1, 0), gap=30.0
            )

    def test_plane_not_edge_on_raises(self):
        with self.assertRaises(ValueError):
            self.sheet.add_section_view(
                self.plan, Point.by_xyz(0, 0, 0), Vector.by_xyz(1, -1, 0), gap=30.0
            )
        with self.assertRaises(ValueError):
            self.sheet.add_section_view(
                self.plan, Point.by_xyz(0, 0, 10), Vector.by_xyz(0, 0, 1), gap=30.0
            )

    def test_hidden_edges_can_be_left_out(self):
        without = Sheet(Paper.C, units_per_inch=25.4)
        view = without.add_view(self.part, View.FRONT, xy(100.0, 100.0), hidden=False)
        self.assertFalse(any(line.stroke.pattern is LinePattern.HIDDEN for line in view.lines))
        full = self.sheet.add_view(self.part, View.FRONT, xy(100.0, 100.0))
        self.assertTrue(any(line.stroke.pattern is LinePattern.HIDDEN for line in full.lines))


class TestDetailView(CanvasTestCase):
    def setUp(self):
        super().setUp()
        self.box = Box.by_size(40.0, 20.0, 10.0)
        self.sheet = Sheet(Paper.C, units_per_inch=25.4)
        self.front = self.sheet.add_view(self.box, View.FRONT, xy(100.0, 100.0))
        self.corner = Point.by_xyz(40.0, 0.0, 10.0)
        self.detail = self.sheet.add_detail_view(
            self.front, self.corner, 5.0, xy(300.0, 100.0), scale=4.0
        )

    def test_center_goes_to_its_position(self):
        at = self.detail.to_sheet(self.corner)
        self.assertAlmostEqual(at.x, 300.0)
        self.assertAlmostEqual(at.y, 100.0)

    def test_lines_stay_inside_the_circle(self):
        projected = self.front.camera.project(self.corner)
        self.assertTrue(self.detail.lines)
        for line in self.detail.lines:
            for x, y in line.points:
                self.assertLessEqual(math.hypot(x - projected.x, y - projected.y), 5.0 + 1.0e-9)

    def test_dimension_measures_the_part_at_the_larger_scale(self):
        with patch.object(self.sheet, "add_linear_dimension") as add:
            self.detail.add_dimension(
                Point.by_xyz(38.0, 0.0, 10.0), self.corner, offset=5.0, decimals=0
            )
        self.assertEqual(add.call_args.args[3], "2")

    def test_scale_must_be_positive(self):
        with self.assertRaises(ValueError):
            self.sheet.add_detail_view(self.front, self.corner, 5.0, xy(0.0, 0.0), scale=0.0)


class TestAdditionalAnnotations(CanvasTestCase):
    def test_measured_text_takes_a_prefix_and_suffix(self):
        sheet = Sheet(Paper.B)
        part = Box.by_size(4.0, 2.0, 1.0)
        view = sheet.add_view(part, View.FRONT, xy(8.0, 5.0))
        with patch.object(sheet, "add_linear_dimension") as add:
            view.add_dimension(
                Point.by_xyz(0, 0, 0),
                Point.by_xyz(4, 0, 0),
                offset=1.0,
                prefix="2X ",
                suffix=f" {Symbol.PLUS_MINUS}0.1",
                decimals=1,
            )
        self.assertEqual(add.call_args.args[3], f"2X 4.0 {Symbol.PLUS_MINUS}0.1")

    def test_table_draws_a_grid_with_every_cell(self):
        canvas = Canvas(8.0, 4.0)
        with patch.object(Canvas, "add_text") as add:
            canvas.add_table(xy(1.0, 3.0), [["A", "B"], ["C", "D"]], [1.0, 2.0])
        self.assertEqual([c.args[1] for c in add.call_args_list], ["A", "B", "C", "D"])
        self.assertTrue(self.lines_exist(canvas))

    def lines_exist(self, canvas: Canvas) -> bool:
        return bool(list(self.svg(canvas).iter(f"{SVG}polyline")))

    def test_table_row_needs_a_cell_for_each_column(self):
        with self.assertRaises(ValueError):
            Canvas(8.0, 4.0).add_table(xy(1.0, 3.0), [["A"]], [1.0, 2.0])

    def test_frame_grows_with_its_text(self):
        def right_edge(cells: list[str]) -> float:
            canvas = Canvas(8.0, 4.0)
            canvas.add_feature_control_frame(xy(1.0, 2.0), cells)
            return max(
                float(pair.split(",")[0])
                for polyline in self.svg(canvas).iter(f"{SVG}polyline")
                for pair in polyline.get("points").split()
            )

        self.assertGreater(right_edge(["A", "LONGER TEXT"]), right_edge(["A", "B"]))

    def test_datum_triangle_is_on_the_feature(self):
        canvas = Canvas(8.0, 4.0)
        canvas.add_datum_feature(xy(2.0, 2.0), xy(2.0, 1.0), "A")
        image = self.png(canvas)
        # The triangle is filled just below its base, and nothing is above the feature
        self.assertEqual(image.pixel(200, 201), BLACK)
        self.assertEqual(image.pixel(200, 190), WHITE)

    def test_datum_box_hides_what_is_behind_it(self):
        canvas = Canvas(8.0, 4.0)
        canvas.add_line(xy(0.0, 1.0), xy(4.0, 1.0), Stroke(RED, width=0.03))
        canvas.add_datum_feature(xy(2.0, 2.0), xy(2.0, 1.0), "A")
        image = self.png(canvas)
        self.assertEqual(image.pixel(100, 300), RED_PIXEL)
        self.assertNotEqual(image.pixel(204, 300), RED_PIXEL)

    def test_surface_finish_stands_on_its_tip(self):
        canvas = Canvas(4.0, 2.0)
        canvas.add_surface_finish(xy(2.0, 1.0), "3.2")
        image = self.png(canvas)
        above = [image.pixel(x, y) for x in range(180, 230) for y in range(70, 99)]
        below = [image.pixel(x, y) for x in range(180, 230) for y in range(103, 130)]
        self.assertTrue(any(pixel != WHITE for pixel in above))
        self.assertTrue(all(pixel == WHITE for pixel in below))

    def test_every_symbol_has_its_own_strokes(self):
        def strokes(text: str) -> bytes:
            canvas = Canvas(2.0, 1.0)
            canvas.add_text(xy(0.5, 0.5), text, height=0.3)
            return self.png(canvas).rows

        drawn = [strokes(symbol) for symbol in Symbol]
        self.assertEqual(len(set(drawn)), len(Symbol))
        self.assertNotIn(strokes("?"), drawn)

    def test_center_line_reaches_past_its_points(self):
        sheet = Sheet(Paper.B)
        view = sheet.add_view(Box.by_size(4.0, 2.0, 1.0), View.FRONT, xy(8.0, 5.0))
        with patch.object(sheet, "add_line") as add:
            view.add_center_line(Point.by_xyz(0, 0, 0), Point.by_xyz(4, 0, 0))
        start, end, stroke = add.call_args.args
        self.assertAlmostEqual(end.x - start.x, 4.25)
        self.assertIs(stroke.pattern, LinePattern.CENTER)

    def test_cutting_plane_arrows_point_along_the_sight(self):
        sheet = Sheet(Paper.B)
        view = sheet.add_view(Box.by_size(4.0, 2.0, 1.0), View.TOP, xy(8.0, 5.0))
        with patch.object(sheet, "add_arrow") as add:
            view.add_cutting_plane(Point.by_xyz(2, 1, 0), Vector.by_xyz(0, -1, 0), "A")
        self.assertEqual(add.call_count, 2)
        for call in add.call_args_list:
            self.assertAlmostEqual(call.args[1].y, 1.0)

    def test_cutting_plane_along_the_view_raises(self):
        sheet = Sheet(Paper.B)
        view = sheet.add_view(Box.by_size(4.0, 2.0, 1.0), View.TOP, xy(8.0, 5.0))
        with self.assertRaises(ValueError):
            view.add_cutting_plane(Point.by_xyz(0, 0, 0), Vector.by_xyz(0, 0, 1), "A")

    def test_zones_label_from_the_right_and_bottom(self):
        sheet = Sheet(Paper.B)
        with patch.object(Canvas, "add_text") as add:
            sheet.add_zones(4, 2)
        positions = {}
        for call in add.call_args_list:
            positions.setdefault(call.args[1], []).append(call.args[0])
        self.assertGreater(positions["1"][0].x, positions["4"][0].x)
        self.assertLess(positions["A"][0].y, positions["B"][0].y)

    def test_label_goes_below_the_view(self):
        sheet = Sheet(Paper.B)
        view = sheet.add_view(Box.by_size(4.0, 2.0, 1.0), View.FRONT, xy(8.0, 5.0))
        with patch.object(sheet, "add_text") as add:
            view.add_label("VIEW", gap=1.0)
        at = add.call_args.args[0]
        self.assertAlmostEqual(at.x, 8.0, delta=0.01)
        self.assertAlmostEqual(at.y, view.min_point.y - 1.0)


class TestDirectionsAndPoints(unittest.TestCase):
    def test_camera_projects_like_the_hidden_lines(self):
        camera = Camera.by_direction(Vector.by_xyz(0.0, -1.0, 0.0))
        projected = camera.project(Point.by_xyz(1.0, 2.0, 3.0))
        self.assertAlmostEqual(projected.x, 1.0)
        self.assertAlmostEqual(projected.y, 3.0)

    def test_ellipse_points_stay_on_it(self):
        points = Ellipse2D.by_radii(2.0, 1.0).points(0.001)
        self.assertGreater(len(points), 8)
        for p in points:
            self.assertAlmostEqual((p.x / 2.0) ** 2 + p.y**2, 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
