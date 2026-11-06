from __future__ import annotations

import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from pyocctlite.errors import BuildFailed
from pyocctlite.geometry import Frame, Line, Point
from pyocctlite.primitives import Box
from pyocctlite.rendering import Styled, View, render_image, render_views
from pyocctlite.topology import Compound, Edge, Shape, UniteShapes, Vertex

Pixel = tuple[int, int, int]

WHITE = (255, 255, 255)
RED = (1.0, 0.0, 0.0)


class Image:
    """
    Decoded PNG, limited to the format that the renderer writes.
    """

    def __init__(self, path: Path):
        data = path.read_bytes()
        assert data[:8] == b"\x89PNG\r\n\x1a\n"

        compressed = b""
        position = 8
        while position < len(data):
            length = struct.unpack(">I", data[position : position + 4])[0]
            kind = data[position + 4 : position + 8]
            body = data[position + 8 : position + 8 + length]
            crc = struct.unpack(">I", data[position + 8 + length : position + 12 + length])[0]
            assert crc == zlib.crc32(kind + body)
            if kind == b"IHDR":
                self.width, self.height = struct.unpack(">II", body[:8])
                assert body[8:] == bytes((8, 2, 0, 0, 0))
            elif kind == b"IDAT":
                compressed += body
            position += 12 + length

        self.rows = zlib.decompress(compressed)
        self.stride = self.width * 3 + 1

    def pixel(self, x: int, y: int) -> Pixel:
        start = y * self.stride + 1 + x * 3
        r, g, b = self.rows[start : start + 3]
        return r, g, b

    def is_overlay(self, x: int, y: int) -> bool:
        """
        Check for the corners that hold the label and axes, which a part never reaches.
        """
        return x < 110 and (y < 40 or y >= self.height - 110)

    def part_pixels(self) -> list[tuple[int, int, Pixel]]:
        return [
            (x, y, self.pixel(x, y))
            for y in range(self.height)
            for x in range(self.width)
            if not self.is_overlay(x, y) and self.pixel(x, y) != WHITE
        ]

    def part_bounds(self) -> tuple[int, int, int, int]:
        pixels = self.part_pixels()
        xs = [x for x, _, _ in pixels]
        ys = [y for _, y, _ in pixels]
        return min(xs), min(ys), max(xs), max(ys)

    def has_reddish_pixel(self) -> bool:
        return any(r > 200 and g < 60 and b < 60 for _, _, (r, g, b) in self.part_pixels())


def _box_at(x: float, y: float, z: float, dx: float, dy: float, dz: float) -> Shape:
    return Box.by_size(dx, dy, dz, Frame.by_origin(Point.by_xyz(x, y, z)))


class RenderingTest(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)

    def render(self, shapes, view: View = View.ISO, width: int = 800, height: int = 800) -> Image:
        path = self.directory / "image.png"
        render_image(shapes, str(path), view, width, height)
        return Image(path)


class TestRenderImage(RenderingTest):
    def test_size_background_and_part(self):
        image = self.render(Box.by_size(1.0, 1.0, 1.0), width=320, height=200)
        self.assertEqual((image.width, image.height), (320, 200))
        self.assertEqual(image.pixel(319, 199), WHITE)
        self.assertNotEqual(image.pixel(160, 100), WHITE)

    def test_part_is_centered(self):
        # far from the origin, and a large size, should make no difference
        box = _box_at(1000.0, -2000.0, 3000.0, 500.0, 500.0, 500.0)
        image = self.render(box, View.FRONT)
        self.assertNotEqual(image.pixel(400, 400), WHITE)
        self.assertEqual(image.pixel(799, 799), WHITE)

    def test_same_input_gives_same_image(self):
        box = Box.by_size(1.0, 2.0, 3.0)
        self.assertEqual(self.render(box).rows, self.render(box).rows)

    def test_input_is_unchanged(self):
        box = Box.by_size(1.0, 2.0, 3.0)
        self.render(box)
        self.assertAlmostEqual(box.volume, 6.0)
        self.assertAlmostEqual(box.area, 22.0)
        self.assertTrue(box.is_valid)

    def test_iterable_of_shapes(self):
        shapes = iter([_box_at(0, 0, 0, 1, 1, 1), _box_at(3, 0, 0, 1, 1, 1)])
        image = self.render(shapes, View.FRONT)
        self.assertEqual(image.pixel(400, 400), WHITE)


class TestViews(RenderingTest):
    def setUp(self) -> None:
        super().setUp()

        # A long block along x with a tall post at its +x end and a tab on its +y side
        base = Box.by_size(6.0, 3.0, 1.0)
        post = _box_at(5.0, 0.0, 1.0, 1.0, 1.0, 2.0)
        tab = _box_at(2.5, 3.0, 0.0, 1.0, 1.5, 1.0)
        self.part = UniteShapes(base, [post, tab]).shape()

    def test_front_looks_along_positive_y_with_z_up(self):
        image = self.render(self.part, View.FRONT)
        x_min, y_min, x_max, y_max = image.part_bounds()

        # the post is at +x (right) and goes up, leaving the upper left corner empty
        self.assertNotEqual(image.pixel(x_max - 5, y_min + 5), WHITE)
        self.assertEqual(image.pixel(x_min + 5, y_min + 5), WHITE)
        self.assertNotEqual(image.pixel(x_min + 5, y_max - 5), WHITE)

    def test_back_is_mirrored_front(self):
        image = self.render(self.part, View.BACK)
        x_min, y_min, _, _ = image.part_bounds()
        self.assertNotEqual(image.pixel(x_min + 5, y_min + 5), WHITE)

    def test_right_looks_along_negative_x_with_y_to_the_right(self):
        image = self.render(self.part, View.RIGHT)
        x_min, y_min, x_max, y_max = image.part_bounds()

        # the post is at y=0 (left) and the tab at +y (right), with the tab low
        self.assertNotEqual(image.pixel(x_min + 5, y_min + 5), WHITE)
        self.assertEqual(image.pixel(x_max - 5, y_min + 5), WHITE)
        self.assertNotEqual(image.pixel(x_max - 5, y_max - 5), WHITE)

    def test_left_is_mirrored_right(self):
        image = self.render(self.part, View.LEFT)
        _, y_min, x_max, _ = image.part_bounds()
        self.assertNotEqual(image.pixel(x_max - 5, y_min + 5), WHITE)

    def test_top_has_x_to_the_right_and_y_up(self):
        image = self.render(self.part, View.TOP)
        x_min, y_min, x_max, _ = image.part_bounds()

        # the tab at +y points up in the middle of the block
        center = (x_min + x_max) // 2
        self.assertNotEqual(image.pixel(center, y_min + 5), WHITE)
        self.assertEqual(image.pixel(x_min + 5, y_min + 5), WHITE)
        self.assertEqual(image.pixel(x_max - 5, y_min + 5), WHITE)

    def test_bottom_has_x_to_the_right_and_y_down(self):
        image = self.render(self.part, View.BOTTOM)
        x_min, _, x_max, y_max = image.part_bounds()
        center = (x_min + x_max) // 2
        self.assertNotEqual(image.pixel(center, y_max - 5), WHITE)
        self.assertEqual(image.pixel(x_min + 5, y_max - 5), WHITE)

    def test_views_share_a_scale(self):
        box = Box.by_size(4.0, 1.0, 2.0)
        front = self.render(box, View.FRONT).part_bounds()
        right = self.render(box, View.RIGHT).part_bounds()

        # the z size is the same in both views, and sizes keep their ratio between views
        self.assertAlmostEqual(front[3] - front[1], right[3] - right[1], delta=1)
        self.assertAlmostEqual((front[2] - front[0]) / (right[2] - right[0]), 4.0, delta=0.1)


class TestStyled(RenderingTest):
    def test_color(self):
        image = self.render(Styled(Box.by_size(1, 1, 1), color=RED), View.FRONT)
        r, g, b = image.pixel(400, 400)
        self.assertGreater(r, 100)
        self.assertEqual((g, b), (0, 0))

    def test_highlighted_edge_is_drawn_over_the_part(self):
        box = Box.by_size(1.0, 1.0, 1.0)
        plain = self.render(box)
        self.assertFalse(plain.has_reddish_pixel())

        edge = box.top_face.edges()[0]
        self.assertTrue(self.render([box, Styled(edge, color=RED)]).has_reddish_pixel())

    def test_coincident_shape_draws_over_earlier_one(self):
        box = Box.by_size(1.0, 1.0, 1.0)
        image = self.render([box, Styled(box.front_face, color=RED)], View.FRONT)
        self.assertTrue(image.has_reddish_pixel())

    def test_transparency_shows_what_is_inside(self):
        outer = Box.by_size(3.0, 3.0, 3.0)
        inner = Styled(_box_at(1.0, 1.0, 1.0, 1.0, 1.0, 1.0), color=RED)

        opaque = self.render([outer, inner], View.FRONT)
        self.assertFalse(opaque.has_reddish_pixel())

        clear = self.render([Styled(outer, transparency=0.8), inner], View.FRONT)
        r, g, _ = clear.pixel(400, 400)
        self.assertGreater(r, g + 50)

    def test_fully_transparent_faces_leave_edges(self):
        image = self.render(Styled(Box.by_size(1, 1, 1), transparency=1.0), View.FRONT)
        self.assertEqual(image.pixel(400, 400), WHITE)
        x_min, y_min, x_max, y_max = image.part_bounds()
        self.assertGreater(x_max - x_min, 100)
        self.assertGreater(y_max - y_min, 100)

    def test_invalid_values_raise(self):
        box = Box.by_size(1.0, 1.0, 1.0)
        with self.assertRaises(ValueError):
            Styled(box, color=(1.5, 0.0, 0.0))
        with self.assertRaises(ValueError):
            Styled(box, color=(1.0, 0.0))  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            Styled(box, transparency=-0.1)
        with self.assertRaises(ValueError):
            Styled(box, transparency=1.1)


class TestFreeShapes(RenderingTest):
    def test_free_edge(self):
        edge = Edge.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0))
        image = self.render(Styled(edge, color=RED), View.FRONT)
        self.assertTrue(image.has_reddish_pixel())

    def test_vertex_has_no_size_but_is_drawn(self):
        vertex = Vertex.by_point(Point.by_xyz(1.0, 2.0, 3.0))
        image = self.render(Styled(vertex, color=RED), View.FRONT)
        self.assertEqual(image.pixel(400, 400), (255, 0, 0))


class TestRenderViews(RenderingTest):
    def render_sheet(self, shapes, width: int = 600, height: int = 400) -> Image:
        path = self.directory / "sheet.png"
        render_views(shapes, str(path), width, height)
        return Image(path)

    def test_size(self):
        image = self.render_sheet(Box.by_size(1, 1, 1))
        self.assertEqual((image.width, image.height), (600, 400))

    def test_odd_size_rounds_down(self):
        image = self.render_sheet(Box.by_size(1, 1, 1), 601, 401)
        self.assertEqual((image.width, image.height), (600, 400))

    def test_layout_matches_individual_views(self):
        box = Box.by_size(1.0, 2.0, 3.0)
        sheet = self.render_sheet(box)

        tiles = {View.TOP: (0, 0), View.ISO: (300, 0), View.FRONT: (0, 200), View.RIGHT: (300, 200)}
        for view, (left, top) in tiles.items():
            tile = self.render(box, view, 300, 200)
            for x, y in [(150, 100), (100, 60), (200, 140)]:
                self.assertEqual(sheet.pixel(left + x, top + y), tile.pixel(x, y), view)


class TestFailures(RenderingTest):
    def test_empty_raises(self):
        for shapes in ([], Compound.by_shapes([])):
            with self.assertRaises(BuildFailed):
                self.render(shapes)

    def test_unbounded_raises(self):
        line = Line.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0))
        with self.assertRaises(BuildFailed):
            self.render(Edge.by_curve(line))

    def test_invalid_size_raises(self):
        box = Box.by_size(1.0, 1.0, 1.0)
        with self.assertRaises(ValueError):
            self.render(box, width=0)
        with self.assertRaises(ValueError):
            render_views(box, str(self.directory / "sheet.png"), 1, 400)

    def test_missing_folder_raises(self):
        with self.assertRaises(OSError):
            render_image(Box.by_size(1, 1, 1), str(self.directory / "missing" / "image.png"))


if __name__ == "__main__":
    unittest.main()
