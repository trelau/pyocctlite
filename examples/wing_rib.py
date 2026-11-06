# A single-sided machined wing rib, modeled the way it is made: draw construction curves on the rib
# plane, offset them into walls, take what is left as pockets, and dig those out of a billet.
# Proportions loosely follow a narrow-body airliner wing and are not engineering data. Lengths are
# mm.
from __future__ import annotations

import math
from collections.abc import Iterable

from pyocctlite.geometry import Circle, Frame, Point, Vector
from pyocctlite.primitives import Box, Cylinder
from pyocctlite.rendering import Camera, Styled, render_image, render_views
from pyocctlite.topology import Edge, ExtrudeShape, Face, FilletShape, Shape, Solid, Wire

# Wing, with world axes x aft, y outboard and z up
semispan = 17170.0
leading_edge_sweep = math.radians(27.0)
dihedral = math.radians(6.0)
skin_thickness = 6.0
front_spar = 0.15
rear_spar = 0.60
rib_station = 0.25 * semispan

# Spanwise position, chord, thickness ratio and twist of each wing section
root = (0.0, 7320.0, 0.15, math.radians(2.0))
yehudi = (5900.0, 4400.0, 0.127, math.radians(0.5))
tip = (semispan, 1250.0, 0.105, math.radians(-1.0))

# Rib
depth = 60.0
web_thickness = 3.0
wall_thickness = 4.0
cap_thickness = 4.0
tab_height = 70.0
row_inset = 195.0
hole_radius = 165.0
hole_land = 14.0
hole_corner_radius = 15.0
boss_radius = 48.0
bore_radius = 26.0

# Stringers pass through the cap between the tabs
stringer_pitch = 150.0
tab_stem = 8.0
stringer_neck = 60.0

# Cutter
corner_radius = 8.0
floor_radius = 3.0
blend_radius = 3.0

# Tools overshoot the billet so that they do not end on one of its faces
overshoot = 1.0

# Offsets of splines can leave edges of about 1e-5, too short for a boolean's default tolerance
cut_tolerance = 1.0e-3


def chord_point(section: tuple[float, float, float, float], x: float, z: float = 0.0) -> Point:
    """
    Get a world point from coordinates relative to the chord of a wing section.

    :param tuple[float, float, float, float] section: Position, chord, thickness and twist.
    :param float x: Fraction of the chord behind the leading edge.
    :param float z: Fraction of the chord above the chord line.
    :return: World point.
    :rtype: Point
    """
    y, chord, _, twist = section
    cos, sin = math.cos(twist), math.sin(twist)
    return Point.by_xyz(
        y * math.tan(leading_edge_sweep) + chord * (x * cos + z * sin),
        y,
        y * math.tan(dihedral) + chord * (z * cos - x * sin),
    )


def airfoil(section: tuple[float, float, float, float], count: int = 41) -> Wire:
    """
    Create a closed section from the NACA 4-digit formula with 2% camber at 40% chord.

    :param tuple[float, float, float, float] section: Position, chord, thickness and twist.
    :param int count: Number of points on each of the upper and lower surfaces.
    :return: One spline around the leading edge, closed by a blunt trailing edge.
    :rtype: Wire
    """
    camber, crest, thickness = 0.02, 0.4, section[2]
    upper, lower = [], []
    for i in range(count):
        x = (1.0 - math.cos(math.pi * i / (count - 1))) / 2.0
        half = (
            5.0
            * thickness
            * (0.2969 * math.sqrt(x) - 0.126 * x - 0.3516 * x**2 + 0.2843 * x**3 - 0.1015 * x**4)
        )
        span = crest if x < crest else 1.0 - crest
        base = 0.0 if x < crest else 1.0 - 2.0 * crest
        line = camber / span**2 * (base + 2.0 * crest * x - x**2)
        slope = math.atan(2.0 * camber / span**2 * (crest - x))
        dx, dz = half * math.sin(slope), half * math.cos(slope)
        upper.append(chord_point(section, x - dx, line + dz))
        lower.append(chord_point(section, x + dx, line - dz))
    points = upper[::-1] + lower[1:]
    return Wire.by_edges([Edge.by_interpolation(points), Edge.by_points(points[-1], points[0])])


# The outer mold line (OML) is the whole wing. The inner mold line (IML) is what the skin leaves for
# the rib, and only the bay around the rib is needed.
root_section, yehudi_section, tip_section = airfoil(root), airfoil(yehudi), airfoil(tip)
oml = Solid.by_loft([root_section, yehudi_section, tip_section], is_ruled=True)
iml = Solid.by_loft(
    [s.offset(-skin_thickness).wires()[0] for s in (root_section, yehudi_section)], is_ruled=True
)

# The rib plane is normal to the rear spar, with x aft, y up and z pointing inboard, where the
# cutter comes from. The local origin is on the rear spar and on the chord line.
spar0, spar1 = chord_point(root, rear_spar), chord_point(yehudi, rear_spar)
spar_direction = Vector.by_points(spar0, spar1)
origin = spar0.translate(spar_direction.scale(rib_station / spar1.y))
frame = Frame.by_vectors(
    origin, Vector.by_xyz(1.0, 0.0, 0.0), spar_direction.normalize().scale(-1.0)
)
x_dir, y_dir, z_dir = frame.x_direction, frame.y_direction, frame.z_direction


def local(x: float, y: float, z: float = 0.0) -> Point:
    """
    Get a world point from coordinates in the rib frame.

    :param float x: Distance aft of the rear spar.
    :param float y: Distance above the chord line.
    :param float z: Distance inboard of the rib plane.
    :return: World point.
    :rtype: Point
    """
    return origin.translate(x_dir.scale(x)).translate(y_dir.scale(y)).translate(z_dir.scale(z))


def polygon(points: Iterable[tuple[float, float]]) -> Wire:
    """
    Create a closed wire on the rib plane.

    :param Iterable[tuple[float, float]] points: Corners in rib frame coordinates.
    :return: New wire.
    :rtype: Wire
    """
    p = [local(x, y) for x, y in points]
    return Wire.by_edges([Edge.by_points(a, b) for a, b in zip(p, p[1:] + p[:1], strict=True)])


def rectangle(x0: float, x1: float, y0: float = -1500.0, y1: float = 1500.0) -> Face:
    """
    Create a rectangle on the rib plane, tall enough by default to cross the whole wing.

    :param float x0: First x.
    :param float x1: Second x.
    :param float y0: First y.
    :param float y1: Second y.
    :return: New face.
    :rtype: Face
    """
    return Face.by_wire(polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]))


# The front spar crosses the rib plane where its distance along z changes sign
front0, front1 = chord_point(root, front_spar), chord_point(yehudi, front_spar)
d0 = Vector.by_points(origin, front0).dot(z_dir)
d1 = Vector.by_points(origin, front1).dot(z_dir)
front = front0.translate(Vector.by_points(front0, front1).scale(d0 / (d0 - d1)))
length = -Vector.by_points(origin, front).dot(x_dir)

# Start from a billet and trim it to the skin and the spars, so the caps pick up the skin's bevel
billet_y = -240.0
billet_height = 720.0
billet_frame = Frame.by_vectors(local(-length, billet_y), x_dir, z_dir)
billet = Box.by_size(length, billet_height, depth, billet_frame)
blank = billet.intersect(iml)

# Section the IML with the plane. The rib outline stops at the spars. The longer contour runs past
# them, so that curves offset from it reach the spars at full depth.
outline = iml.intersect(rectangle(-length, 0.0)).wires()[0]
contour = iml.intersect(rectangle(-length - 400.0, 400.0)).wires()[0]


def inset(distance: float) -> Face:
    """
    Create the region inside the contour at a distance.

    :param float distance: Distance inside the contour.
    :return: New face.
    :rtype: Face
    """
    return Face.by_wire(contour.offset(-distance).wires()[0])


# Construction curves: the stiffener centerlines. Vertical ones sit on every other tab stem.
tab_count = int(length // stringer_pitch)
first_stem = -length + (length - (tab_count - 1) * stringer_pitch) / 2.0
stems = [first_stem + i * stringer_pitch for i in range(tab_count)]
vertical_stems = stems[1::2]
holes = [(stems[3], 120.0), (stems[9], 120.0)]
bosses = [(stems[1], 150.0), (stems[7], 110.0), (stems[13], 90.0)]
centerlines = [
    Wire.by_edge(Edge.by_points(local(x, -300.0), local(x, 550.0))) for x in vertical_stems
]
for hx, hy in holes:
    for angle in (67.5, 112.5, 247.5, 292.5):
        c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        centerlines.append(
            Wire.by_edge(
                Edge.by_points(
                    local(hx + hole_radius * c, hy + hole_radius * s),
                    local(hx + 380.0 * c, hy + 380.0 * s),
                )
            )
        )

# Offset every centerline into a wall. Walls may overlap, so nothing has to line up yet. A straight
# line doesn't define a plane, so it needs a spine face. The spine's boundary is offset too and
# comes first in the result, so the wall is the last wire.
spine = rectangle(-length - 1000.0, 1000.0)
walls: list[Shape] = [
    Face.by_wire(w.offset(-wall_thickness / 2.0, spine).wires()[-1]) for w in centerlines
]

# The curved stiffeners are the band between two offsets of the contour
run_outer = inset(tab_height - wall_thickness / 2.0)
run_inner = inset(tab_height + wall_thickness / 2.0)
walls.append(inset(row_inset - wall_thickness / 2.0).cut(inset(row_inset + wall_thickness / 2.0)))

# Lightening holes keep a land around them. Bosses are round lands on a stiffener.
octagons = [
    polygon(
        (
            x + hole_radius * math.cos(math.pi / 8.0 + i * math.pi / 4.0),
            y + hole_radius * math.sin(math.pi / 8.0 + i * math.pi / 4.0),
        )
        for i in range(8)
    )
    for x, y in holes
]
walls += [Face.by_wire(o.offset(hole_land).wires()[0]) for o in octagons]
boss_frames = [Frame.by_vectors(local(x, y), x_dir, z_dir) for x, y in bosses]
walls += [
    Face.by_wire(Wire.by_edge(Edge.by_curve(Circle.by_radius(boss_radius, f)))) for f in boss_frames
]

# Trim: what is left of the region inside the spar walls and the run stiffener is the pockets
inside_spars = rectangle(-length + wall_thickness, -wall_thickness)
pocket_regions = list(run_inner.intersect(inside_spars).faces()[0].cut(walls).faces())

# The band outside the run stiffener holds the tabs. Its ends stay solid as spar attach pads.
band = (
    Face.by_wire(outline.offset(-cap_thickness).wires()[0]).intersect(inside_spars).cut(run_outer)
)

# Between the stems a window goes through the web, and a narrower neck goes through the cap, which
# leaves T-shaped tabs with flared feet
gaps = [(a + b) / 2.0 for a, b in zip(stems, stems[1:], strict=False)]
window_regions = [
    f
    for x in gaps
    for f in band.intersect(
        rectangle(x - (stringer_pitch - tab_stem) / 2.0, x + (stringer_pitch - tab_stem) / 2.0)
    ).faces()
]
neck_regions = [
    f
    for x in gaps
    for f in rectangle(x - stringer_neck / 2.0, x + stringer_neck / 2.0).cut(run_outer).faces()
]


def cutter_path(face: Face, radius: float) -> list[Face]:
    """
    Reduce a region to what a cutter can reach, as an inset for the path of the cutter's center and
    an offset back out for what it sweeps. Corners become the cutter radius, and slivers that the
    cutter does not fit in disappear. A small blend first rounds the corners that point into the
    region, so that the floor fillet can run around a smooth boundary.

    :param Face face: Region with no islands.
    :param float radius: Cutter radius.
    :return: Faces the cutter sweeps. A narrow neck in the region splits it into several.
    :rtype: list[Face]
    """
    wire = face.wires()[0]
    blended = wire.offset(blend_radius).wires()[0].offset(-blend_radius).wires()[0]
    return [Face.by_wire(w.offset(radius).wires()[0]) for w in blended.offset(-radius).wires()]


def pocket_tool(face: Face) -> Shape:
    """
    Create the solid a pocket removes, down to the web and with the cutter's floor radius.

    :param Face face: Pocket region on the rib plane.
    :return: New solid.
    :rtype: Shape
    """
    tool = ExtrudeShape(
        face.translate(z_dir.scale(web_thickness)),
        z_dir.scale(depth - web_thickness + overshoot),
    )
    fillet = FilletShape(tool.shape())
    for edge in tool.first_shape().edges():
        fillet.add_edge(edge, floor_radius)
    return fillet.shape()


def through_tool(face: Face) -> Shape:
    """
    Create the solid a through cut removes.

    :param Face face: Region on the rib plane.
    :return: New solid.
    :rtype: Shape
    """
    start = face.translate(z_dir.scale(-overshoot))
    return start.extrude(z_dir.scale(depth + 2.0 * overshoot))


pockets = [f for region in pocket_regions for f in cutter_path(region, corner_radius)]
windows = [f for region in window_regions for f in cutter_path(region, corner_radius)]
hole_faces = [
    Face.by_wire(w.offset(hole_corner_radius).wires()[0])
    for o in octagons
    for w in o.offset(-hole_corner_radius).wires()
]
bores = [
    Cylinder.by_size(
        bore_radius,
        depth + 2.0 * overshoot,
        Frame.by_vectors(f.origin.translate(z_dir.scale(-overshoot)), x_dir, z_dir),
    )
    for f in boss_frames
]

# Dig everything out of the blank. Necks open into windows, so they are a separate cut.
pocket_tools = [pocket_tool(f) for f in pockets]
through_tools = [through_tool(f) for f in windows + hole_faces]
machined = blank.cut(pocket_tools + through_tools + bores, cut_tolerance)
rib = machined.cut([through_tool(f) for f in neck_regions], cut_tolerance)

# Export STEP
rib.export_step("outputs/wing_rib.step")

# Render the layout on the plane, a sheet of views, a view into the pockets and the rib in the wing
gray = (0.8, 0.8, 0.8)
red = (0.9, 0.3, 0.2)
blue = (0.2, 0.45, 0.85)
face_on = Camera.by_direction(z_dir, y_dir, span=1.5 * length)
render_image(
    [Styled(Face.by_wire(outline), gray, 0.6)]
    + [Styled(w, red) for w in centerlines]
    + [Styled(contour.offset(-d), red) for d in (tab_height, row_inset)],
    "outputs/wing_rib_layout.png",
    face_on,
    width=1600,
    height=700,
)
render_image(
    [Styled(s, blue) for s in pockets + windows + hole_faces + neck_regions]
    + [Styled(Face.by_wire(outline), gray, 0.6)],
    "outputs/wing_rib_pockets.png",
    face_on,
    width=1600,
    height=700,
)
render_views(rib, "outputs/wing_rib_views.png")
into_pockets = Camera.by_direction(
    Vector.by_xyz(
        z_dir.x + 0.3 * x_dir.x + 0.5 * y_dir.x,
        z_dir.y + 0.3 * x_dir.y + 0.5 * y_dir.y,
        z_dir.z + 0.3 * x_dir.z + 0.5 * y_dir.z,
    ),
    y_dir,
    span=1.15 * length,
)
render_image(rib, "outputs/wing_rib.png", into_pockets, width=1800, height=900)
render_image(
    [Styled(oml, (0.6, 0.7, 0.85), 0.75), Styled(rib, red)],
    "outputs/wing_rib_in_wing.png",
    width=1600,
    height=900,
)
