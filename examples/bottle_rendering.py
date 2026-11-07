# Builds the same bottle as bottle.py, with a numbered image after each step of its construction
# in outputs/bottle_rendering/history, then shows what else the renderer can do in
# outputs/bottle_rendering/gallery.
from __future__ import annotations

import math
from collections.abc import Iterable
from itertools import count
from pathlib import Path

from pyocctlite.geometry import (
    Circle,
    CylindricalSurface,
    Ellipse2D,
    Frame,
    Frame2D,
    Point,
    Point2D,
    TrimmedCurve2D,
    Vector,
    Vector2D,
)
from pyocctlite.primitives import Cylinder
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
from pyocctlite.topology import Compound, Edge, Face, Shape, Solid, Wire

# Dimensions for the bottle
height = 70
width = 50
thickness = 30
neck_radius = thickness / 4.0
neck_height = height / 10.0

# New geometry is highlighted, on top of what it was built from
NEW = (0.90, 0.35, 0.20)
OTHER = (0.20, 0.45, 0.85)
THIRD = (0.20, 0.70, 0.35)

# The same camera throughout, so that the part stays still from one image to the next
WHOLE = Camera.by_view(View.ISO, Point.by_xyz(0.0, 0.0, 38.0), 100.0)
NECK = Camera.by_view(View.ISO, Point.by_xyz(0.0, 0.0, height + neck_height / 2.0), 28.0)

folder = Path("outputs/bottle_rendering")
history = folder / "history"
gallery = folder / "gallery"
history.mkdir(parents=True, exist_ok=True)
gallery.mkdir(exist_ok=True)
numbers = count(1)


def snapshot(
    name: str,
    shapes: Shape | Styled | Iterable[Shape | Styled],
    camera: Camera,
    section: Section | None = None,
) -> None:
    """
    Write the next numbered image of the construction history.

    :param name: What the step did, used in the file name.
    :param shapes: Shape(s) to draw.
    :param camera: View to render.
    :param section: Plane to cut the image with, if any.
    """
    path = str(history / f"{next(numbers):02d}_{name}.png")
    render_image(shapes, path, camera, section=section)


# Define points for the bottom profile (one half)
p1 = Point.by_xyz(-width / 2.0, 0.0, 0.0)
p2 = Point.by_xyz(-width / 2.0, -thickness / 4.0, 0.0)
p3 = Point.by_xyz(0.0, -thickness / 2.0, 0.0)
p4 = Point.by_xyz(width / 2.0, -thickness / 4.0, 0.0)
p5 = Point.by_xyz(width / 2.0, 0.0, 0.0)

# Create edges and a wire for the first half of the profile
e1 = Edge.by_points(p1, p2)
e2 = Edge.by_points(p4, p5)
e3 = Edge.by_circular_arc(p2, p3, p4)
snapshot("profile_edges", [Styled(e1, NEW), Styled(e2, OTHER), Styled(e3, THIRD)], WHOLE)
w1 = Wire.by_edges([e1, e2, e3])
snapshot("half_profile_wire", Styled(w1, NEW), WHOLE)

# Mirror the profile to create the full symmetric base
origin = Point.by_xyz(0, 0, 0)
normal = Vector.by_xyz(0, 1, 0)
w2 = w1.mirror(origin, normal)
snapshot("mirrored_profile", [Styled(w1, OTHER), Styled(w2, NEW)], WHOLE)

# Combine the two halves into a single closed wire
w3 = w1.combine(w2)
snapshot("closed_profile_wire", Styled(w3, NEW), WHOLE)

# Create the bottle body by extruding the base face
bottom_face = Face.by_wire(w3)
snapshot("bottom_face", Styled(bottom_face, NEW), WHOLE)
v = Vector.by_xyz(0, 0, height)
extruded = bottom_face.extrude(v)
snapshot("extruded_body", extruded, WHOLE)

# Fillet all edges for a smooth finish
filleted = extruded.fillet(extruded.edges(), thickness / 12.0)
snapshot("filleted_body", filleted, WHOLE)

# Add the neck of the bottle and fillet the junction
o = Point.by_xyz(0, 0, height)
frame = Frame.by_origin(o)
neck = Cylinder.by_size(neck_radius, neck_height, frame)
snapshot("neck_cylinder", [filleted, Styled(neck, NEW)], WHOLE)
bottle = filleted.unite(neck)
snapshot("neck_united", bottle, WHOLE)
bottle = bottle.fillet(neck.bottom_face.edges(), 1.5 * thickness / 50.0)
snapshot("neck_filleted", bottle, NECK)

# Create a hollow shell by thickening the solid and removing the top face
bottle = bottle.thicken(-thickness / 50.0, neck.top_face)
snapshot("hollowed_neck_opening", bottle, NECK)

# Look at the walls through a section that removes the front half from the image
section = Section.by_plane(origin, Vector.by_xyz(0, -1, 0))
snapshot("hollowed_section", bottle, WHOLE, section)

# Create thread surfaces (inner and outer radii)
cs1 = CylindricalSurface.by_radius(neck_radius * 0.99, frame)
cs2 = CylindricalSurface.by_radius(neck_radius * 1.05, frame)

# Define thread geometry in 2D (parametric space)
p2d = Point2D.by_xy(2.0 * math.pi, neck_height / 2.0)
v2d = Vector2D.by_xy(2.0 * math.pi, neck_height / 4.0)
f2d = Frame2D.by_vector(p2d, v2d)
rmajor = 2.0 * math.pi
rminor = neck_height / 10.0
ellipse1 = Ellipse2D.by_radii(rmajor, rminor, f2d)
ellipse2 = Ellipse2D.by_radii(rmajor, rminor / 4.0, f2d)
arc1 = TrimmedCurve2D.by_curve(ellipse1, 0, math.pi)
arc2 = TrimmedCurve2D.by_curve(ellipse2, 0.0, math.pi)
ep1 = ellipse1.evaluate(0.0)
ep2 = ellipse2.evaluate(math.pi)
aseg = TrimmedCurve2D.by_points(ep1, ep2)

# Map 2D curves to the cylindrical surfaces to create 3D edges
e1s1 = Edge.by_curve2d(arc1, cs1)
e2s1 = Edge.by_curve2d(aseg, cs1)
e1s2 = Edge.by_curve2d(arc2, cs2)
e2s2 = Edge.by_curve2d(aseg, cs2)
snapshot("thread_edges", [Styled(e, NEW) for e in (e1s1, e2s1, e1s2, e2s2)], NECK)

# Create wires and loft them to form the solid threads
w1 = Wire.by_edges([e1s1, e2s1])
w2 = Wire.by_edges([e1s2, e2s2])
snapshot("thread_wires", [Styled(w1, OTHER), Styled(w2, NEW)], NECK)
threads = Solid.by_loft([w1, w2])
snapshot("thread_solid", Styled(threads, NEW), NECK)
snapshot("thread_on_neck", [bottle, Styled(threads, NEW)], NECK)

# Unite threads with the bottle
bottle = bottle.unite(threads)
snapshot("threads_united", bottle, NECK)
snapshot("finished_bottle", bottle, WHOLE)

# Finish the history with a sheet of views, and export STEP
render_views(bottle, str(history / f"{next(numbers):02d}_finished_views.png"))
bottle.export_step(str(folder / "bottle.step"))


def image(name: str) -> str:
    """
    Get the path of an image in the gallery.

    :param name: Name of the image.
    :return: File path.
    """
    return str(gallery / f"{name}.png")


# Sub-shapes to color, point at and number, found by where they are
faces = bottle.faces()
edges = bottle.edges()
front_face = max((f for f in faces if f.centroid.y < 0.0), key=lambda f: f.area)
back_face = max((f for f in faces if f.centroid.y > 0.0), key=lambda f: f.area)
neck_faces = [f for f in faces if f.centroid.z > height]
neck_edges = [e for e in edges if e.centroid.z > height]
front_edges = [e for e in edges if e.centroid.y < 0.0 and e.centroid.z < height]

# A tool keeps its mesh between renders, so each view after the first is quick. These are all of the
# standard views.
tool = RenderShapes(800, 600)
tool.add_shape(bottle)
for view in View:
    tool.render(image(f"view_{view.name.lower()}"), view)

# It also writes a sheet of views, with each view at the tool's image size
tool.render_views(image("view_sheet"))

# A camera looks from any direction, from any position, or closer at a standard view
low = Camera.by_direction(Vector.by_xyz(2.0, -3.0, -1.0))
high = Camera.by_position(Point.by_xyz(-90.0, -150.0, 220.0), Point.by_xyz(0.0, 0.0, 38.0))
close = Camera.by_view(View.FRONT, Point.by_xyz(0.0, 0.0, height), 30.0)
tilted = Camera.by_direction(Vector.by_xyz(1.0, -1.0, 0.2), Vector.by_xyz(0.3, 0.0, 1.0))
render_image(bottle, image("camera_from_below"), low)
render_image(bottle, image("camera_from_position"), high)
render_image(bottle, image("camera_close_up"), close)
render_image(bottle, image("camera_tilted_up_direction"), tilted)

# An image can be any size, with the part fit to its smaller side
render_image(bottle, image("size_banner"), View.FRONT, width=1600, height=400)
render_image(bottle, image("size_portrait"), View.RIGHT, width=500, height=1000)

# Shading by depth darkens what is farther away, and labels can be left out for a clean image
render_image(bottle, image("shading_depth"), View.TOP, shading=Shading.DEPTH)
render_image(bottle, image("no_labels"), WHOLE, labels=False)

# Any shape can have its own color, and later shapes draw over earlier ones
GREEN = (0.15, 0.55, 0.35)
GLASS = (0.45, 0.70, 0.90)
render_image(Styled(bottle, GREEN), image("color_whole_part"), WHOLE)
render_image([bottle, Styled(front_face, NEW)], image("color_one_face"), WHOLE)
render_image(
    [bottle, *[Styled(f, OTHER) for f in neck_faces]],
    image("color_chosen_faces"),
    NECK,
)
render_image(
    [bottle, *[Styled(e, NEW) for e in front_edges]],
    image("color_chosen_edges"),
    WHOLE,
)

# Transparency shows what is inside, down to fully transparent faces that leave only the edges
render_image(Styled(bottle, GLASS, 0.6), image("transparent_glass"), WHOLE)
render_image(
    [Styled(bottle, GLASS, 0.8), Styled(threads, NEW)],
    image("transparent_showing_threads"),
    NECK,
)
render_image(Styled(bottle, GLASS, 1.0), image("transparent_edges_only"), WHOLE)

# A section cuts the image without changing the shapes, tinted from each shape or in one color
to_front = Vector.by_xyz(0.0, -1.0, 0.0)
to_top = Vector.by_xyz(0.0, 0.0, 1.0)
through_middle = Section.by_plane(origin, to_front)
render_image(bottle, image("section_tint"), View.FRONT, section=through_middle)
render_image(
    Styled(bottle, GREEN),
    image("section_tint_of_color"),
    WHOLE,
    section=through_middle,
)
render_image(
    bottle,
    image("section_one_color"),
    WHOLE,
    section=Section.by_plane(origin, to_front, (0.95, 0.75, 0.20)),
)
render_image(
    bottle,
    image("section_from_above"),
    View.TOP,
    section=Section.by_plane(Point.by_xyz(0.0, 0.0, 35.0), to_top),
)
render_views(bottle, image("section_sheet"), section=through_middle)

# A callout points at a shape or a point with lines of text, and says when its target is hidden
render_image(
    bottle,
    image("callouts"),
    WHOLE,
    width=1200,
    callouts=[
        Callout(front_face, "Front wall\nof the body"),
        Callout(max(neck_faces, key=lambda f: f.area), "Neck"),
        Callout(Point.by_xyz(width / 2.0, 0.0, height / 2.0), "Widest point"),
        Callout(back_face, "Back wall"),
    ],
)
render_image(
    bottle,
    image("callouts_with_section"),
    View.FRONT,
    callouts=Callout(Point.by_xyz(0.0, 0.0, 35.0), "Hollow inside"),
    section=through_middle,
)

# Numbering faces or edges finds their indices, and returns what is visible in the view
print("Visible faces:", render_faces(bottle, image("numbered_faces"), WHOLE))
print("Visible edges:", render_edges(bottle, image("numbered_edges"), WHOLE))

# Numbering chosen ones keeps their indices, and shows them in the context of the whole part
print("Neck faces:", render_faces(bottle, image("numbered_chosen_faces"), NECK, faces=neck_faces))
print("Neck edges:", render_edges(bottle, image("numbered_chosen_edges"), NECK, edges=neck_edges))

# A sub-shape finds its number, and a number finds its sub-shape
index = faces.find_index(front_face)
assert index is not None
print(f"The front wall is face {index}, with an area of {faces[index].area:.1f}")

# Parts in a compound are numbered together, so that their numbers do not clash
pair = Compound.by_shapes([threads, neck])
render_faces(pair, image("numbered_compound"), NECK)

# Hidden lines replace the shading with exact edges and silhouettes, dashing what is behind them,
# in any view and at any size. A sheet shows the part as line work from every side. The view from
# above is the slow one, since every thread's edges overlap in it.
lines = RenderShapes(1000, 800)
lines.add_shape(bottle)
lines.render(image("hidden_lines_iso"), WHOLE, Shading.HIDDEN_LINE)
lines.render(image("hidden_lines_front"), View.FRONT, Shading.HIDDEN_LINE)
lines.render(image("hidden_lines_neck"), NECK, Shading.HIDDEN_LINE)
lines.render_views(image("hidden_lines_sheet"), Shading.HIDDEN_LINE)

# Hidden lines still point at what is hidden, here the threads on the far side of the neck
render_image(
    bottle,
    image("hidden_lines_with_callouts"),
    NECK,
    callouts=[Callout(threads, "Threads"), Callout(front_face, "Front wall")],
    shading=Shading.HIDDEN_LINE,
)

RED = (0.80, 0.10, 0.10)
BLUE = (0.10, 0.30, 0.80)
DARK_GREEN = (0.05, 0.50, 0.20)
WHITE = (1.0, 1.0, 1.0)


def add_measure(tool: RenderShapes, a: Point, b: Point, offset: Vector) -> None:
    """
    Mark a distance on an image, for checking a size at a glance.

    :param tool: Tool to add to.
    :param a: Start of what is measured.
    :param b: End of what is measured.
    :param offset: Distance from the points to the line that shows the measure.
    """
    start = a.translate(offset)
    end = b.translate(offset)
    tool.add_line(a, start, DARK_GREEN, width=1.0, dashed=True)
    tool.add_line(b, end, DARK_GREEN, width=1.0, dashed=True)
    tool.add_line(start, end, DARK_GREEN)
    middle = start.translate(Vector.by_points(start, end).scale(0.5))
    tool.add_text(middle, f"{a.distance(b):.1f}", height=16.0, color=DARK_GREEN, background=WHITE)


def box_edges(shape: Shape) -> list[Edge]:
    """
    Get the edges of a shape's bounding box.

    :param shape: Shape to bound.
    :return: The twelve edges.
    """
    box = shape.bounding_box
    corners = {
        (i, j, k): Point.by_xyz(
            box.min_point.x + i * box.dx, box.min_point.y + j * box.dy, box.min_point.z + k * box.dz
        )
        for i in (0, 1)
        for j in (0, 1)
        for k in (0, 1)
    }
    return [
        Edge.by_points(corner, corners[(i + di, j + dj, k + dk)])
        for (i, j, k), corner in corners.items()
        for di, dj, dk in ((1, 0, 0), (0, 1, 0), (0, 0, 1))
        if i + di < 2 and j + dj < 2 and k + dk < 2
    ]


# Sizes can be checked on the image itself, with the measures drawn from the part's own points
box = bottle.bounding_box
least = box.min_point
measured = RenderShapes(1000, 800)
measured.add_shape(bottle)
measured.add_edges(box_edges(bottle), BLUE, width=1.0, dashed=True)
add_measure(
    measured,
    Point.by_xyz(least.x, least.y, least.z),
    Point.by_xyz(least.x + box.dx, least.y, least.z),
    Vector.by_xyz(0.0, -12.0, 0.0),
)
add_measure(
    measured,
    Point.by_xyz(least.x + box.dx, least.y, least.z),
    Point.by_xyz(least.x + box.dx, least.y + box.dy, least.z),
    Vector.by_xyz(12.0, 0.0, 0.0),
)
add_measure(
    measured,
    Point.by_xyz(least.x, least.y + box.dy, least.z),
    Point.by_xyz(least.x, least.y + box.dy, least.z + box.dz),
    Vector.by_xyz(-12.0, 0.0, 0.0),
)
measured.render(image("measured_bounding_box"), View.ISO)
measured.render(image("measured_bounding_box_lines"), View.ISO, Shading.HIDDEN_LINE)

# Where a part's properties are can be seen against the part, here its center of mass and frame
frame = RenderShapes(1000, 800)
frame.add_shape(Styled(bottle, GLASS, 0.75))
center = bottle.centroid
for axis, color, name in (
    (Vector.by_xyz(1.0, 0.0, 0.0), RED, "X"),
    (Vector.by_xyz(0.0, 1.0, 0.0), DARK_GREEN, "Y"),
    (Vector.by_xyz(0.0, 0.0, 1.0), BLUE, "Z"),
):
    tip = center.translate(axis.scale(45.0))
    frame.add_line(center, tip, color, width=3.0)
    frame.add_text(tip.translate(axis.scale(4.0)), name, height=18.0, color=color)
frame.add_text(
    center.translate(Vector.by_xyz(0.0, 0.0, -9.0)),
    f"CENTROID\n{center.x:.2f}, {center.y:.2f}, {center.z:.2f}\nVOLUME {bottle.volume:.0f}",
    height=14.0,
    color=(0.0, 0.0, 0.0),
    background=WHITE,
)
frame.render(image("centroid_and_axes"), WHOLE)

# What a step will act on can be checked before it runs: here each neck edge in one color on a
# line view, and the fillet's edges that a selection by height would pick
selected = RenderShapes(1000, 800)
selected.add_shape(bottle)
selected.add_edges(neck_edges, BLUE, width=3.0)
selected.add_edges(front_edges, RED, width=3.0)
selected.add_text(Point.by_xyz(0.0, -15.0, 35.0), f"{len(front_edges)} EDGES", 18.0, RED, WHITE)
selected.add_text(
    Point.by_xyz(0.0, 0.0, height + 18.0), f"{len(neck_edges)} EDGES", 18.0, BLUE, WHITE
)
selected.render(image("selection_check_on_lines"), WHOLE, Shading.HIDDEN_LINE)

# A construction guide shows how a part relates to what it was built from, with the axis the neck
# was built on, the height it starts from and a curve of its own
guide = RenderShapes(1000, 800)
guide.add_shape(Styled(bottle, GLASS, 0.85))
neck_axis = (Point.by_xyz(0.0, 0.0, -5.0), Point.by_xyz(0.0, 0.0, height + neck_height + 8.0))
guide.add_line(*neck_axis, RED, dashed=True)
neck_frame = Frame.by_origin(Point.by_xyz(0.0, 0.0, height))
guide.add_edges(Edge.by_curve(Circle.by_radius(neck_radius, neck_frame)), BLUE, width=3.0)
guide.add_text(
    Point.by_xyz(0.0, 0.0, height + neck_height + 12.0),
    f"NECK \u2300{neck_radius * 2.0:.1f}",
    height=16.0,
    color=BLUE,
)
guide.render(image("construction_guide"), WHOLE)

# Lines and text are not removed by a section, so a section can carry its own measurements, like
# the wall that the thickening left behind
wall = RenderShapes(1000, 800)
wall.add_shape(bottle)
wall.set_section(through_middle)
wall_thickness = thickness / 50.0
wall_height = 35.0
inner_point = Point.by_xyz(width / 2.0 - wall_thickness, 0.0, wall_height)
outer_point = Point.by_xyz(width / 2.0, 0.0, wall_height)
wall.add_line(inner_point, outer_point, RED, width=4.0)
wall.add_text(
    Point.by_xyz(width / 2.0 - 2.0, 0.0, wall_height + 1.0),
    f"WALL {wall_thickness:.2f}",
    height=22.0,
    color=RED,
    background=WHITE,
)
wall.render(
    image("section_with_measurement"),
    Camera.by_view(View.FRONT, Point.by_xyz(width / 2.0 - 2.0, 0.0, wall_height), 8.0),
)

# Text carries drawing symbols, and a line can run anywhere, including beyond the part
symbols = RenderShapes(1000, 800)
symbols.add_shape(bottle)
symbols.add_text(
    Point.by_xyz(0.0, 0.0, height + neck_height + 14.0),
    f"\u2300{neck_radius * 2.0:.0f} \u00b10.1  \u27c2 0.05  \u2316 \u23002 \u24c2  90\u00b0",
    height=20.0,
    color=BLUE,
)
symbols.add_line(
    Point.by_xyz(-60.0, 0.0, height), Point.by_xyz(60.0, 0.0, height), DARK_GREEN, dashed=True
)
symbols.render(image("text_symbols_and_reference_line"), View.FRONT, Shading.HIDDEN_LINE)

# A tool can combine all of these, and take more after a render
tool = RenderShapes(1000, 800)
tool.add_numbered_faces(bottle, neck_faces)
tool.add_callout(Callout(Point.by_xyz(0.0, 0.0, 35.0), "Hollow inside"))
tool.set_section(through_middle)
tool.render(image("combined_cut_and_numbered"), View.FRONT)
cap_frame = Frame.by_origin(Point.by_xyz(0.0, 0.0, height + neck_height))
tool.add_shape(Styled(Cylinder.by_size(1.3 * neck_radius, 3.0, cap_frame), NEW))
tool.render(image("combined_with_a_cap"), WHOLE)
print("Visible in the latest view:", tool.visible_pixels())
