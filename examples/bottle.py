# https://dev.opencascade.org/doc/overview/html/occt__tutorial.html
from __future__ import annotations

import math

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
from pyocctlite.rendering import render_views
from pyocctlite.topology import Edge, Face, Solid, Wire

# Dimensions for the bottle
height = 70
width = 50
thickness = 30
neck_radius = thickness / 4.0
neck_height = height / 10.0

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
w1 = Wire.by_edges([e1, e2, e3])

# Mirror the profile to create the full symmetric base
origin = Point.by_xyz(0, 0, 0)
normal = Vector.by_xyz(0, 1, 0)
w2 = w1.mirror(origin, normal)

# Combine the two halves into a single closed wire
w3 = w1.combine(w2)

# Create the bottle body by extruding the base face
bottom_face = Face.by_wire(w3)
v = Vector.by_xyz(0, 0, height)
extruded = bottom_face.extrude(v)

# Fillet all edges for a smooth finish
filleted = extruded.fillet(extruded.edges(), thickness / 12.0)

# Add the neck of the bottle and fillet the junction
o = Point.by_xyz(0, 0, height)
frame = Frame.by_origin(o)
neck = Cylinder.by_size(neck_radius, neck_height, frame)
bottle = filleted.unite(neck)
bottle = bottle.fillet(neck.bottom_face.edges(), 1.5 * thickness / 50.0)

# Create a hollow shell by thickening the solid and removing the top face
bottle = bottle.thicken(-thickness / 50.0, neck.top_face)

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

# Create wires and loft them to form the solid threads
w1 = Wire.by_edges([e1s1, e2s1])
w2 = Wire.by_edges([e1s2, e2s2])
threads = Solid.by_loft([w1, w2])

# Unite threads with the bottle
bottle = bottle.unite(threads)

# Export STEP
bottle.export_step("outputs/bottle.step")

# Render a sheet of views
render_views(bottle, "outputs/bottle.png")
