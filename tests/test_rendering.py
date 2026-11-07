from __future__ import annotations

import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from pyocctlite.errors import BuildFailed
from pyocctlite.geometry import Frame, Line, Point, Vector
from pyocctlite.primitives import Box, Cylinder
from pyocctlite.rendering import (
    Callout,
    Camera,
    RenderShapes,
    Section,
    Shading,
    Styled,
    View,
    render_edges,
    render_faces,
    render_image,
    render_views,
)
from pyocctlite.topology import Compound, CutShapes, Edge, Shape, UniteShapes, Vertex, Wire

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

    def render(
        self, shapes, view: View | Camera = View.ISO, width: int = 800, height: int = 800
    ) -> Image:
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

    def test_many_styled_shapes_do_not_show_through_each_other(self):
        # holes close to the front wall, with enough faces that an offset per shape would add up
        holes = [
            Cylinder.by_size(5.0, 22.0, Frame.by_origin(Point.by_xyz(10.0 + 11.0 * i, 7.0, -1.0)))
            for i in range(8)
        ]
        part = CutShapes(Box.by_size(100.0, 100.0, 20.0), holes).shape()

        colors = [(0.9, 0.3, 0.3), (0.3, 0.6, 0.95), (0.35, 0.8, 0.4), (0.98, 0.75, 0.2)]
        styled = [Styled(f, color=colors[i % 4]) for i, f in enumerate(part.faces())]
        forward = self.render(styled)
        backward = self.render(styled[::-1])

        pixels = forward.part_pixels()
        changed = [p for p in pixels if backward.pixel(p[0], p[1]) != p[2]]
        self.assertLess(len(changed), len(pixels) * 0.01)

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


class TestCamera(RenderingTest):
    def test_by_view_matches_the_view(self):
        box = Box.by_size(1.0, 2.0, 3.0)
        expected = self.render(box, View.RIGHT).rows
        self.assertEqual(self.render(box, Camera.by_view(View.RIGHT)).rows, expected)

    def test_by_direction_matches_a_standard_view(self):
        box = Box.by_size(1.0, 2.0, 3.0)
        expected = self.render(box, View.FRONT).part_pixels()
        camera = Camera.by_direction(Vector.by_xyz(0.0, -1.0, 0.0))
        self.assertEqual(self.render(box, camera).part_pixels(), expected)

    def test_up_defaults_to_y_when_looking_along_z(self):
        box = Box.by_size(1.0, 2.0, 3.0)
        expected = self.render(box, View.TOP).part_pixels()
        camera = Camera.by_direction(Vector.by_xyz(0.0, 0.0, 1.0))
        self.assertEqual(self.render(box, camera).part_pixels(), expected)

    def test_distance_has_no_effect(self):
        box = Box.by_size(1.0, 2.0, 3.0)
        target = Point.by_xyz(0.5, 1.0, 1.5)
        near = Camera.by_position(Point.by_xyz(2.0, 3.0, 4.0), target)
        far = Camera.by_position(Point.by_xyz(15.5, 21.0, 26.5), target)
        self.assertEqual(self.render(box, near).rows, self.render(box, far).rows)

    def test_span_sets_the_scale(self):
        # the span covers 92 percent of the image, so a unit box is half of that with a span of 2
        camera = Camera.by_view(View.FRONT, Point.by_xyz(0.5, 0.0, 0.5), span=2.0)
        x_min, y_min, x_max, y_max = self.render(Box.by_size(1, 1, 1), camera).part_bounds()
        self.assertAlmostEqual(x_max - x_min, 800 * 0.92 / 2.0, delta=3)
        self.assertAlmostEqual(y_max - y_min, 800 * 0.92 / 2.0, delta=3)

    def test_target_is_at_the_center(self):
        camera = Camera.by_view(View.FRONT, Point.by_xyz(0.0, 0.0, 0.0), span=4.0)
        image = self.render(Box.by_size(1, 1, 1), camera)

        # the corner at the origin is at the center, with the box up and to the right
        self.assertNotEqual(image.pixel(420, 380), WHITE)
        self.assertEqual(image.pixel(380, 380), WHITE)
        self.assertEqual(image.pixel(420, 420), WHITE)

    def test_extreme_zoom_is_safe(self):
        box = Box.by_size(1, 1, 1)
        for span in (1.0e-6, 1.0e-9, 1.0e-15):
            camera = Camera.by_view(View.FRONT, Point.by_xyz(0.5, 0.0, 0.5), span=span)
            self.assertNotEqual(self.render(box, camera).pixel(400, 400), WHITE)

        # an edge far from the view
        camera = Camera.by_view(View.FRONT, Point.by_xyz(0.0, 0.0, 0.0), span=1.0e-9)
        self.assertEqual(len(self.render(box, camera).rows), 800 * (800 * 3 + 1))

    def test_label_is_drawn(self):
        box = Box.by_size(1, 1, 1)
        direction = Vector.by_xyz(1.0, 1.0, 1.0)
        one = self.render(box, Camera(direction, label="A"))
        two = self.render(box, Camera(direction, label="B"))
        self.assertNotEqual(one.rows, two.rows)
        self.assertEqual(one.part_pixels(), two.part_pixels())

    def test_invalid_values_raise(self):
        z = Vector.by_xyz(0.0, 0.0, 1.0)
        origin = Point.by_xyz(0.0, 0.0, 0.0)
        with self.assertRaises(ValueError):
            Camera.by_direction(Vector.by_xyz(0.0, 0.0, 0.0))
        with self.assertRaises(ValueError):
            Camera.by_direction(z, up=z)
        with self.assertRaises(ValueError):
            Camera.by_direction(z, up=Vector.by_xyz(0.0, 0.0, 0.0))
        with self.assertRaises(ValueError):
            Camera.by_position(origin, origin)
        with self.assertRaises(ValueError):
            Camera.by_view(View.ISO, span=0.0)


class TestRenderFaces(RenderingTest):
    def render_faces(self, shape, view: View | Camera = View.ISO) -> tuple[Image, dict[int, int]]:
        path = self.directory / "faces.png"
        visible = render_faces(shape, str(path), view, 800, 800)
        return Image(path), visible

    def test_numbers_match_the_faces_of_the_shape(self):
        box = Box.by_size(1.0, 1.0, 1.0)
        faces = box.faces()
        named = {
            View.FRONT: box.front_face,
            View.BACK: box.back_face,
            View.LEFT: box.left_face,
            View.RIGHT: box.right_face,
            View.TOP: box.top_face,
            View.BOTTOM: box.bottom_face,
        }
        for view, face in named.items():
            _, visible = self.render_faces(box, view)
            self.assertEqual(len(visible), 1, view)
            self.assertEqual(faces[next(iter(visible))], face, view)

    def test_iso_shows_three_faces(self):
        box = Box.by_size(1.0, 1.0, 1.0)
        _, visible = self.render_faces(box)
        faces = list(box.faces())
        expected = {faces.index(f) for f in (box.front_face, box.right_face, box.top_face)}
        self.assertEqual(set(visible), expected)

    def test_visible_pixels_match_the_size_on_the_image(self):
        box = Box.by_size(1.0, 1.0, 1.0)
        _, visible = self.render_faces(box, View.FRONT)
        side = 800 * 0.92 / 3.0**0.5
        self.assertAlmostEqual(next(iter(visible.values())), side * side, delta=side * 4)

    def test_faces_have_different_colors(self):
        two = Compound.by_shapes([_box_at(0, 0, 0, 1, 1, 1), _box_at(1.5, 0, 0, 1, 1, 1)])
        image, visible = self.render_faces(two, View.FRONT)
        self.assertEqual(len(visible), 2)

        # sample away from the numbers at the center of each face
        x_min, y_min, x_max, _ = image.part_bounds()
        first = image.pixel(x_min + 10, y_min + 10)
        second = image.pixel(x_max - 10, y_min + 10)
        self.assertNotEqual(first, second)

    def test_colors_repeat_for_many_faces(self):
        boxes = [_box_at(2.0 * i, 0, 0, 1, 1, 1) for i in range(5)]
        _, visible = self.render_faces(Compound.by_shapes(boxes))
        self.assertGreater(len(visible), 12)

    def test_shape_without_faces_has_no_visible_faces(self):
        edge = Edge.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0))
        _, visible = self.render_faces(edge)
        self.assertEqual(visible, {})

    def test_small_face_is_numbered_at_the_side(self):
        # a thin plate has a side face too small to hold its number
        image, visible = self.render_faces(Box.by_size(10.0, 10.0, 0.05), View.FRONT)
        self.assertEqual(len(visible), 1)
        at_sides = [p for p in image.part_pixels() if p[0] < 40 or p[0] > 760]
        self.assertTrue(at_sides)


class TestRenderEdges(RenderingTest):
    def render_edges(self, shape, view: View | Camera = View.ISO) -> tuple[Image, dict[int, int]]:
        path = self.directory / "edges.png"
        visible = render_edges(shape, str(path), view, 800, 800)
        return Image(path), visible

    def test_numbers_match_the_edges_of_the_shape(self):
        box = Box.by_size(1.0, 1.0, 1.0)
        _, visible = self.render_edges(box, View.FRONT)

        # the four edges around the front face, not those behind it or seen end-on
        edges = box.edges()
        expected = {
            i
            for i, edge in enumerate(edges)
            if edge.bounding_box.max_point.y < 0.5 and edge.bounding_box.dy < 0.5
        }
        self.assertEqual(len(expected), 4)
        self.assertEqual(set(visible), expected)

    def test_visible_length_matches_the_size_on_the_image(self):
        _, visible = self.render_edges(Box.by_size(1.0, 1.0, 1.0), View.FRONT)
        side = 800 * 0.92 / 3.0**0.5
        for length in visible.values():
            self.assertAlmostEqual(length, side, delta=8)

    def test_iso_shows_the_nine_outer_edges(self):
        _, visible = self.render_edges(Box.by_size(1.0, 1.0, 1.0))
        self.assertEqual(len(visible), 9)

    def test_partly_hidden_edge_has_its_visible_length(self):
        # the post hides most of the edge behind it in the front view
        base = Box.by_size(6.0, 3.0, 1.0)
        post = _box_at(0.0, 0.0, 1.0, 5.0, 1.0, 2.0)
        part = UniteShapes(base, post).shape()
        _, visible = self.render_edges(part, View.TOP)
        edges = list(part.edges())
        lengths = {round(edges[i].length): length for i, length in visible.items()}
        self.assertGreater(lengths[6], lengths[1])

    def test_shape_without_edges_has_no_visible_edges(self):
        _, visible = self.render_edges(Vertex.by_point(Point.by_xyz(1.0, 2.0, 3.0)))
        self.assertEqual(visible, {})

    def test_free_edge_is_numbered(self):
        edge = Edge.by_points(Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0))
        _, visible = self.render_edges(edge, View.FRONT)
        self.assertEqual(set(visible), {0})


class TestShading(RenderingTest):
    def setUp(self) -> None:
        super().setUp()

        # A low base with a tall block, whose tops face the same way at different heights
        self.part = UniteShapes(
            Box.by_size(4.0, 4.0, 1.0), _box_at(0.0, 0.0, 0.0, 2.0, 2.0, 3.0)
        ).shape()
        self.tall = Point.by_xyz(1.0, 1.0, 3.0)

    def tops(self, shading: Shading) -> tuple[Pixel, Pixel]:
        path = self.directory / "shaded.png"
        render_image(self.part, str(path), View.TOP, 800, 800, shading=shading)
        image = Image(path)
        x_min, y_min, x_max, y_max = image.part_bounds()

        # the tall block is at the lower left in the top view, and the base at the upper right
        near = image.pixel(x_min + 20, y_max - 20)
        far = image.pixel(x_max - 20, y_min + 20)
        return near, far

    def test_light_shades_parallel_faces_alike(self):
        near, far = self.tops(Shading.LIGHT)
        self.assertEqual(near, far)

    def test_depth_darkens_the_farther_face(self):
        near, far = self.tops(Shading.DEPTH)
        self.assertGreater(sum(near), sum(far) + 30)

    def test_depth_keeps_the_nearest_face_as_with_light(self):
        self.assertEqual(self.tops(Shading.DEPTH)[0], self.tops(Shading.LIGHT)[0])

    def test_every_render_function_takes_shading(self):
        box = self.part
        path = str(self.directory / "shaded.png")
        results = []
        for render in (render_image, render_views, render_faces, render_edges):
            render(box, path, shading=Shading.LIGHT)
            light = Path(path).read_bytes()
            render(box, path, shading=Shading.DEPTH)
            results.append(light != Path(path).read_bytes())
        self.assertEqual(results, [True, True, True, True])


class TestLabels(RenderingTest):
    def setUp(self) -> None:
        super().setUp()
        self.box = Box.by_size(1.0, 1.0, 1.0)
        self.path = self.directory / "labels.png"

    def non_white_in_corners(self, image: Image) -> int:
        return sum(
            1
            for y in range(image.height)
            for x in range(110)
            if (y < 40 or y >= image.height - 110) and image.pixel(x, y) != WHITE
        )

    def test_render_image_leaves_out_the_view_name_and_axes(self):
        render_image(self.box, str(self.path), View.FRONT, 800, 800)
        with_labels = Image(self.path)
        render_image(self.box, str(self.path), View.FRONT, 800, 800, labels=False)
        without = Image(self.path)

        self.assertGreater(self.non_white_in_corners(with_labels), 0)
        self.assertEqual(self.non_white_in_corners(without), 0)

        # the view itself is the same
        self.assertEqual(with_labels.part_pixels(), without.part_pixels())

    def test_render_views_leaves_them_out_of_every_tile(self):
        render_views(self.box, str(self.path), 800, 800, labels=False)
        image = Image(self.path)
        for left, top in ((0, 0), (400, 0), (0, 400), (400, 400)):
            for x, y in ((left + 5, top + 5), (left + 48, top + 352)):
                self.assertEqual(image.pixel(x, y), WHITE)

    def test_render_faces_leaves_out_numbers_but_still_reports(self):
        visible = render_faces(self.box, str(self.path), View.ISO, 800, 800)
        numbered = Image(self.path)
        same = render_faces(self.box, str(self.path), View.ISO, 800, 800, labels=False)
        plain = Image(self.path)

        self.assertEqual(same, visible)

        # no white boxes remain on the faces
        whites = [p for p in plain.part_pixels() if min(p[2]) > 250]
        self.assertEqual(whites, [])
        self.assertNotEqual(numbered.rows, plain.rows)

    def test_render_edges_leaves_out_numbers_but_still_reports(self):
        visible = render_edges(self.box, str(self.path), View.FRONT, 800, 800)
        same = render_edges(self.box, str(self.path), View.FRONT, 800, 800, labels=False)
        image = Image(self.path)

        self.assertEqual(same, visible)
        self.assertEqual(sum(1 for x, _, _ in image.part_pixels() if x < 150 or x >= 650), 0)

    def test_callouts_are_still_drawn(self):
        render_image(
            self.box,
            str(self.path),
            View.FRONT,
            800,
            800,
            Callout(self.box.front_face, "x"),
            labels=False,
        )
        image = Image(self.path)
        self.assertLess(max(image.pixel(400, 400)), 120)


class TestCallout(RenderingTest):
    def margin_pixels(self, image: Image) -> int:
        """
        Count the pixels in the side columns, where a unit box leaves room for text boxes.
        """
        return sum(1 for x, _, _ in image.part_pixels() if x < 150 or x >= 650)

    def render_callouts(self, shapes, callouts, view: View | Camera = View.FRONT) -> Image:
        path = self.directory / "callouts.png"
        render_image(shapes, str(path), view, 800, 800, callouts)
        return Image(path)

    def test_line_ends_on_the_target(self):
        box = Box.by_size(1.0, 1.0, 1.0)
        image = self.render_callouts(box, Callout(box.front_face, "front"))

        # the dot at the end of the line is at the middle of the visible face
        self.assertLess(max(image.pixel(400, 400)), 120)
        self.assertGreater(self.margin_pixels(image), 0)

    def test_point_target(self):
        box = Box.by_size(1.0, 1.0, 1.0)
        image = self.render_callouts(box, Callout(Point.by_xyz(0.25, 0.0, 0.75), "here"))
        side = 800 * 0.92 / 3.0**0.5
        x = round(400 - side / 4)
        y = round(400 - side / 4)
        self.assertLess(max(image.pixel(x, y)), 120)

    def test_edge_target_points_at_the_middle_of_its_visible_part(self):
        box = Box.by_size(1.0, 1.0, 1.0)
        edge = Edge.by_points(Point.by_xyz(0, 0, 1), Point.by_xyz(1, 0, 1))
        image = self.render_callouts(box, Callout(edge, "edge"))
        side = 800 * 0.92 / 3.0**0.5
        self.assertLess(max(image.pixel(400, round(400 - side / 2))), 120)

    def test_many_callouts_in_an_iterable(self):
        box = Box.by_size(1.0, 1.0, 1.0)
        one = self.render_callouts(box, Callout(box.front_face, "a"))
        two = self.render_callouts(
            box, iter([Callout(box.front_face, "a"), Callout(Point.by_xyz(0, 0, 0), "b")])
        )
        self.assertGreater(self.margin_pixels(two), self.margin_pixels(one))

    def test_hidden_target_says_so(self):
        box = Box.by_size(1.0, 1.0, 1.0)
        shown = self.render_callouts(box, Callout(box.front_face, "x"))
        hidden = self.render_callouts(box, Callout(box.back_face, "x"))
        self.assertGreater(self.margin_pixels(hidden), self.margin_pixels(shown))

    def test_hidden_edge_on_the_outline_says_so(self):
        # half of a line on the outline lies over the background, which must not make it visible
        box = Box.by_size(1.0, 1.0, 1.0)
        front = Edge.by_points(Point.by_xyz(0, 0, 1), Point.by_xyz(1, 0, 1))
        back = Edge.by_points(Point.by_xyz(0, 1, 1), Point.by_xyz(1, 1, 1))
        shown = self.render_callouts(box, Callout(front, "x"))
        hidden = self.render_callouts(box, Callout(back, "x"))
        self.assertGreater(self.margin_pixels(hidden), self.margin_pixels(shown))

    def test_target_outside_the_image_says_so_and_has_no_line(self):
        box = Box.by_size(1.0, 1.0, 1.0)
        plain = self.render(box, View.FRONT)
        far = self.render_callouts(box, Callout(Point.by_xyz(100.0, 0.0, 0.0), "far"))
        self.assertGreater(self.margin_pixels(far), 0)

        # it does not change the view, and the part is untouched
        self.assertEqual(far.pixel(400, 400), plain.pixel(400, 400))
        self.assertEqual(far.pixel(300, 300), plain.pixel(300, 300))

    def test_target_need_not_be_in_the_image(self):
        box = Box.by_size(1.0, 1.0, 1.0)
        other = _box_at(0.25, -1.0, 0.25, 0.5, 0.5, 0.5)
        image = self.render_callouts(box, Callout(other.front_face, "x"))
        self.assertLess(max(image.pixel(400, 400)), 120)

    def test_every_printable_character_draws_something(self):
        box = Box.by_size(1.0, 1.0, 1.0)
        path = self.directory / "letter.png"

        def margin(text: str) -> int:
            render_image(box, str(path), View.FRONT, 400, 400, Callout(box.front_face, text))
            image = Image(path)
            return sum(1 for y in range(100, 300) for x in range(60) if image.pixel(x, y) != WHITE)

        blank = margin(" ")
        for code in range(33, 127):
            self.assertGreater(margin(chr(code)), blank, chr(code))

    def test_other_characters_are_drawn_as_a_question_mark(self):
        box = Box.by_size(1.0, 1.0, 1.0)
        one = self.render_callouts(box, Callout(box.front_face, "\t"))
        two = self.render_callouts(box, Callout(box.front_face, "?"))
        self.assertEqual(one.rows, two.rows)

    def test_tiny_image_is_safe(self):
        box = Box.by_size(1.0, 1.0, 1.0)
        path = str(self.directory / "tiny.png")
        callouts = [Callout(box.front_face, "a"), Callout(box.back_face, "b")]
        for size in (1, 20, 100):
            render_image(box, path, View.FRONT, size, size, callouts)
            self.assertEqual(Image(Path(path)).width, size)

    def test_new_line_makes_a_taller_box(self):
        box = Box.by_size(1.0, 1.0, 1.0)
        one = self.render_callouts(box, Callout(box.front_face, "ab cd"))
        two = self.render_callouts(box, Callout(box.front_face, "ab\ncd"))

        def height(image: Image) -> int:
            rows = [y for x, y, _ in image.part_pixels() if x < 40 or x > 760]
            return max(rows) - min(rows)

        self.assertGreater(height(two), height(one))


class TestSection(RenderingTest):
    ORIGIN = Point.by_xyz(0.0, 0.0, 0.0)
    TO_FRONT = Vector.by_xyz(0.0, -1.0, 0.0)
    TO_RIGHT = Vector.by_xyz(1.0, 0.0, 0.0)
    PURE_RED = (255, 0, 0)
    HATCH_SPACING = 8

    def setUp(self) -> None:
        super().setUp()
        self.box = _box_at(-1.0, -1.0, -1.0, 2.0, 2.0, 2.0)
        self.front_half = Section.by_plane(self.ORIGIN, self.TO_FRONT, RED)

    def render_section(self, shapes, section, view=View.FRONT, callouts=(), shading=Shading.LIGHT):
        path = self.directory / "section.png"
        render_image(shapes, str(path), view, 800, 800, callouts, shading, section=section)
        return Image(path)

    def fill(self, image: Image, x: int, y: int) -> Pixel:
        """
        Get the color between hatch lines, from a run of pixels long enough to pass between them.
        """
        return max((image.pixel(x + i, y) for i in range(self.HATCH_SPACING)), key=sum)

    def test_cut_area_has_the_color(self):
        for shading in Shading:
            image = self.render_section(self.box, self.front_half, shading=shading)
            self.assertEqual(self.fill(image, 400, 400), self.PURE_RED)
            self.assertEqual(self.fill(image, 300, 300), self.PURE_RED)

    def test_cut_area_is_hatched(self):
        image = self.render_section(self.box, self.front_half)
        darkest = min((image.pixel(400 + i, 400) for i in range(self.HATCH_SPACING)), key=sum)
        self.assertLess(max(darkest), 120)

        # lines are diagonal, so they move along a row from one row to the next
        self.assertEqual(image.pixel(400, 400), image.pixel(399, 401))
        self.assertNotEqual(
            [image.pixel(400 + i, 400) for i in range(self.HATCH_SPACING)],
            [image.pixel(400 + i, 402) for i in range(self.HATCH_SPACING)],
        )

    def test_default_color_is_a_tint_of_the_shape(self):
        section = Section.by_plane(self.ORIGIN, self.TO_FRONT)
        self.assertIsNone(section.color)

        r, g, b = self.fill(self.render_section(self.box, section), 400, 400)
        self.assertGreater(min(r, g, b), 215)
        self.assertNotEqual((r, g, b), WHITE)

        r, g, b = self.fill(self.render_section(Styled(self.box, RED), section), 400, 400)
        self.assertEqual(r, 255)
        self.assertGreater(g, 150)
        self.assertLess(g, 200)

    def test_each_shape_has_its_own_tint(self):
        left = _box_at(-2.0, -1.0, -1.0, 2.0, 2.0, 2.0)
        right = _box_at(0.0, -1.0, -1.0, 2.0, 2.0, 2.0)
        section = Section.by_plane(self.ORIGIN, self.TO_FRONT)
        image = self.render_section([left, Styled(right, RED)], section)

        # the default color of shapes is slightly blue
        r, _, b = self.fill(image, 300, 400)
        self.assertLess(r, b)
        r, g, _ = self.fill(image, 500, 400)
        self.assertGreater(r, g + 50)

    def test_color_applies_to_every_shape(self):
        left = _box_at(-2.0, -1.0, -1.0, 2.0, 2.0, 2.0)
        right = _box_at(0.0, -1.0, -1.0, 2.0, 2.0, 2.0)
        image = self.render_section([left, Styled(right, (0.0, 0.0, 1.0))], self.front_half)
        self.assertEqual(self.fill(image, 300, 400), self.PURE_RED)
        self.assertEqual(self.fill(image, 500, 400), self.PURE_RED)

    def test_cut_is_only_visible_from_the_removed_side(self):
        image = self.render_section(self.box, self.front_half, View.BACK)
        self.assertFalse(image.has_reddish_pixel())
        self.assertNotEqual(image.pixel(400, 400), WHITE)

    def test_cavity_is_not_cut_area(self):
        cavity = _box_at(-0.5, -0.5, -0.5, 1.0, 1.0, 1.0)
        image = self.render_section(self.box.cut(cavity), self.front_half)
        self.assertEqual(self.fill(image, 250, 400), self.PURE_RED)

        # looking into the cavity shows its far wall, in front of the outside of the part
        r, g, b = self.fill(image, 400, 400)
        self.assertNotEqual((r, g, b), self.PURE_RED)
        self.assertNotEqual((r, g, b), WHITE)

    def test_mirrored_solid_has_the_cut_in_the_same_place(self):
        mirrored = self.box.mirror(self.ORIGIN, self.TO_RIGHT)
        image = self.render_section(mirrored, self.front_half)
        self.assertEqual(self.fill(image, 400, 400), self.PURE_RED)

    def test_plane_clear_of_the_part_changes_nothing(self):
        for shape in (self.box, self.box.mirror(self.ORIGIN, self.TO_RIGHT)):
            beyond = Section.by_plane(Point.by_xyz(0.0, -5.0, 0.0), self.TO_FRONT, RED)
            image = self.render_section(shape, beyond, View.ISO)
            self.assertEqual(image.rows, self.render(shape).rows)

    def test_removing_everything_leaves_a_blank_image(self):
        behind = Section.by_plane(Point.by_xyz(0.0, 5.0, 0.0), self.TO_FRONT, RED)
        self.assertEqual(self.render_section(self.box, behind).part_pixels(), [])

    def test_part_stays_in_place(self):
        whole = self.render(self.box, View.FRONT)
        section = Section.by_plane(self.ORIGIN, self.TO_RIGHT, RED)
        image = self.render_section(self.box, section)
        self.assertEqual(image.pixel(300, 400), whole.pixel(300, 400))
        self.assertEqual(image.pixel(500, 400), WHITE)

    def test_edges_behind_the_cut_are_hidden(self):
        # the plate's edges are on the far side of the part, and would show if the cut were not in
        # front of them
        plate = _box_at(-0.25, 1.0, -0.25, 0.5, 0.25, 0.5)
        part = self.box.unite(plate)
        image = self.render_section(part, self.front_half)
        for x in range(300, 500):
            self.assertEqual(image.pixel(x, 400), image.pixel(x + self.HATCH_SPACING, 400))

    def test_open_shape_is_only_clipped(self):
        # the back face is seen from behind, which would be a cut on a solid
        plane = Section.by_plane(Point.by_xyz(0.0, 1.0, 0.0), Vector.by_xyz(1.0, -1.0, 0.0), RED)
        image = self.render_section(Box.by_size(2.0, 2.0, 2.0).back_face, plane)
        self.assertFalse(image.has_reddish_pixel())
        self.assertNotEqual(image.pixel(300, 400), WHITE)
        self.assertEqual(image.pixel(500, 400), WHITE)

    def test_transparent_solid_is_only_clipped(self):
        styled = Styled(self.box, transparency=0.5)
        image = self.render_section(styled, self.front_half)
        self.assertFalse(image.has_reddish_pixel())
        self.assertNotEqual(image.pixel(400, 400), WHITE)

    def test_free_edge_is_clipped(self):
        edge = Edge.by_points(Point.by_xyz(-1.0, 0.0, 0.0), Point.by_xyz(1.0, 0.0, 0.0))
        section = Section.by_plane(self.ORIGIN, self.TO_RIGHT, RED)
        image = self.render_section(edge, section)
        self.assertNotEqual(image.pixel(300, 400), WHITE)
        self.assertEqual(image.pixel(500, 400), WHITE)

    def test_callout_on_the_cut_points_at_it(self):
        plain = self.render_section(self.box, self.front_half)
        callout = Callout(self.ORIGIN, "here")
        image = self.render_section(self.box, self.front_half, callouts=callout)
        self.assertNotEqual(image.pixel(400, 400), plain.pixel(400, 400))
        self.assertLess(max(image.pixel(400, 400)), 120)

    def test_callout_on_a_removed_target_has_no_line(self):
        plain = self.render_section(self.box, self.front_half)
        callout = Callout(Point.by_xyz(0.0, -1.0, 0.0), "gone")
        image = self.render_section(self.box, self.front_half, callouts=callout)
        self.assertEqual(image.pixel(400, 400), plain.pixel(400, 400))

    def test_render_views_cuts_every_view(self):
        path = self.directory / "sheet.png"
        render_views(self.box, str(path), section=self.front_half)
        image = Image(path)
        tile_width = image.width // 2
        tile_height = image.height // 2

        # the cut faces FRONT, and TOP shows only the half that is kept
        self.assertEqual(self.fill(image, tile_width // 2, tile_height * 3 // 2), self.PURE_RED)
        self.assertEqual(image.pixel(tile_width // 2, tile_height // 2 + 60), WHITE)
        self.assertNotEqual(image.pixel(tile_width // 2, tile_height // 2 - 60), WHITE)

    def test_input_is_unchanged(self):
        self.render_section(self.box, self.front_half)
        self.assertAlmostEqual(self.box.volume, 8.0)

    def test_properties(self):
        section = Section.by_plane(self.ORIGIN, self.TO_FRONT, RED)
        self.assertEqual(section.origin, self.ORIGIN)
        self.assertEqual(section.normal, self.TO_FRONT)
        self.assertEqual(section.color, RED)

    def test_invalid_values_raise(self):
        with self.assertRaises(ValueError):
            Section.by_plane(self.ORIGIN, Vector.by_xyz(0.0, 0.0, 0.0))
        with self.assertRaises(ValueError):
            Section.by_plane(self.ORIGIN, self.TO_FRONT, (2.0, 0.0, 0.0))


class TestRenderShapes(RenderingTest):
    BOX = Box.by_size(1.0, 2.0, 3.0)
    SECTION = Section.by_plane(Point.by_xyz(0.5, 1.0, 1.5), Vector.by_xyz(0.0, -1.0, 0.0))

    def setUp(self) -> None:
        super().setUp()
        self.actual = str(self.directory / "actual.png")
        self.expected = str(self.directory / "expected.png")

    def assert_same_image(self) -> None:
        self.assertEqual(Path(self.actual).read_bytes(), Path(self.expected).read_bytes())

    def test_each_view_matches_render_image(self):
        tool = RenderShapes(400, 300)
        tool.add_shape(Styled(self.BOX, RED))
        for view in (View.ISO, View.TOP, View.ISO):
            tool.render(self.actual, view)
            render_image(Styled(self.BOX, RED), self.expected, view, 400, 300)
            self.assert_same_image()

    def test_render_views_is_twice_the_image_size(self):
        tool = RenderShapes(300, 200)
        tool.add_shape(self.BOX)
        tool.render_views(self.actual)
        render_views(self.BOX, self.expected, 600, 400)
        self.assert_same_image()

    def test_adding_after_a_render_matches_a_new_tool(self):
        other = _box_at(5.0, 0.0, 0.0, 1.0, 1.0, 1.0)
        callout = Callout(other, "other")
        tool = RenderShapes(400, 300)
        tool.add_shape(self.BOX)
        tool.render(self.actual)
        tool.add_shape(other)
        tool.add_callout(callout)
        tool.set_section(self.SECTION)
        tool.render(self.actual)
        render_image(
            [self.BOX, other],
            self.expected,
            width=400,
            height=300,
            callouts=callout,
            section=self.SECTION,
        )
        self.assert_same_image()

    def test_section_before_shapes_matches_section_after(self):
        tool = RenderShapes(400, 300)
        tool.set_section(self.SECTION)
        tool.add_shape(Styled(self.BOX, RED))
        tool.render(self.actual)
        styled = Styled(self.BOX, RED)
        render_image(styled, self.expected, width=400, height=300, section=self.SECTION)
        self.assert_same_image()

    def test_visible_pixels_follow_the_latest_view(self):
        tool = RenderShapes(400, 400)
        tool.add_numbered_faces(self.BOX)
        self.assertEqual(tool.visible_pixels(), {})
        for view in (View.TOP, View.ISO):
            tool.render(self.actual, view)
            expected = render_faces(self.BOX, self.expected, view, 400, 400)
            self.assertEqual(tool.visible_pixels(), expected)

    def test_only_one_shape_can_be_numbered(self):
        for first in ("add_numbered_faces", "add_numbered_edges"):
            for second in ("add_numbered_faces", "add_numbered_edges"):
                tool = RenderShapes(400, 400)
                getattr(tool, first)(self.BOX)
                with self.assertRaises(ValueError):
                    getattr(tool, second)(self.BOX)

    def test_plain_shapes_can_join_a_numbered_shape(self):
        tool = RenderShapes(400, 400)
        tool.add_shape(_box_at(5.0, 0.0, 0.0, 1.0, 1.0, 1.0))
        tool.add_numbered_edges(self.BOX)
        tool.render(self.actual)
        self.assertTrue(tool.visible_pixels())

    def test_invalid_size_raises(self):
        with self.assertRaises(ValueError):
            RenderShapes(0, 300)


class TestNumberedSubShapes(RenderingTest):
    BOX = Box.by_size(1.0, 1.0, 1.0)

    def faces(self, faces=None, labels: bool = True) -> tuple[Image, dict[int, int]]:
        path = self.directory / "faces.png"
        visible = render_faces(
            self.BOX, str(path), width=400, height=400, labels=labels, faces=faces
        )
        return Image(path), visible

    def test_chosen_face_keeps_its_index(self):
        index = self.BOX.faces().find_index(self.BOX.top_face)
        _, visible = self.faces(self.BOX.top_face)
        self.assertEqual(list(visible), [index])

    def test_chosen_face_has_its_full_count(self):
        index = self.BOX.faces().find_index(self.BOX.top_face)
        _, every = self.faces()
        _, chosen = self.faces([self.BOX.top_face])
        self.assertEqual(chosen[index], every[index])

    def test_hidden_chosen_face_is_not_visible(self):
        _, visible = self.faces(self.BOX.bottom_face)
        self.assertEqual(visible, {})

    def test_other_faces_stay_in_context(self):
        everything, _ = self.faces(labels=False)
        chosen, _ = self.faces(self.BOX.top_face, labels=False)
        self.assertEqual(chosen.part_bounds(), everything.part_bounds())

        def neutral_pixels(image: Image) -> int:
            return sum(max(pixel) - min(pixel) < 16 for _, _, pixel in image.part_pixels())

        self.assertGreater(neutral_pixels(chosen), neutral_pixels(everything))

    def test_all_faces_match_the_default(self):
        everything, visible = self.faces()
        chosen, chosen_visible = self.faces(self.BOX.faces())
        self.assertEqual(chosen.rows, everything.rows)
        self.assertEqual(chosen_visible, visible)

    def test_no_faces_draws_the_shape_without_numbers(self):
        image, visible = self.faces([])
        self.assertEqual(visible, {})
        self.assertTrue(image.part_pixels())

    def test_chosen_edges_keep_their_index_and_length(self):
        path = str(self.directory / "edges.png")
        every = render_edges(self.BOX, path, width=400, height=400)
        index = next(iter(every))
        edge = self.BOX.edges()[index]
        chosen = render_edges(self.BOX, path, width=400, height=400, edges=edge)
        self.assertEqual(list(chosen), [index])
        # wider numbered neighbors can cover a pixel or so of an edge
        self.assertAlmostEqual(chosen[index], every[index], delta=5)

    def test_other_free_edges_stay_visible(self):
        p = [Point.by_xyz(0, 0, 0), Point.by_xyz(1, 0, 0), Point.by_xyz(1, 1, 0)]
        wire = Wire.by_edges([Edge.by_points(p[0], p[1]), Edge.by_points(p[1], p[2])])
        path = self.directory / "wire.png"
        render_edges(wire, str(path), View.TOP, 400, 400, labels=False)
        everything = Image(path)
        chosen = render_edges(
            wire, str(path), View.TOP, 400, 400, labels=False, edges=wire.edges()[0]
        )
        self.assertEqual(len(chosen), 1)
        image = Image(path)
        self.assertEqual(image.part_bounds(), everything.part_bounds())
        self.assertTrue(any(max(pixel) < 200 for _, _, pixel in image.part_pixels()))

    def test_chosen_faces_with_a_section(self):
        section = Section.by_plane(Point.by_xyz(0.5, 0.5, 0.5), Vector.by_xyz(1.0, 0.0, 0.0))
        tool = RenderShapes(400, 400)
        tool.add_numbered_faces(self.BOX, self.BOX.top_face)
        tool.set_section(section)
        tool.render(str(self.directory / "section.png"))
        self.assertEqual(
            list(tool.visible_pixels()), [self.BOX.faces().find_index(self.BOX.top_face)]
        )

    def test_sub_shape_of_another_shape_raises_and_leaves_the_tool_usable(self):
        tool = RenderShapes(400, 400)
        with self.assertRaises(ValueError):
            tool.add_numbered_faces(self.BOX, Box.by_size(2.0, 2.0, 2.0).top_face)
        with self.assertRaises(ValueError):
            tool.add_numbered_edges(self.BOX, Box.by_size(2.0, 2.0, 2.0).edges()[0])
        tool.add_numbered_faces(self.BOX, self.BOX.top_face)


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
