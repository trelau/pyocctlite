# Builds the same bottle as bottle.py, with a numbered image after each step of its construction
from __future__ import annotations

import math
from collections.abc import Iterable
from itertools import count
from pathlib import Path

from pyocctlite.geometry import (
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
from pyocctlite.rendering import Camera, Section, Styled, View, render_image, render_views
from pyocctlite.topology import Edge, Face, Shape, Solid, Wire

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

folder = Path("outputs/bottle_history")
folder.mkdir(exist_ok=True)
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
    path = str(folder / f"{next(numbers):02d}_{name}.png")
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

# Finish with a sheet of views
render_views(bottle, str(folder / f"{next(numbers):02d}_finished_views.png"))
