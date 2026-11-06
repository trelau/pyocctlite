from __future__ import annotations

import math

from pyocctlite.geometry import Axis, Frame, Point, Vector
from pyocctlite.primitives import Cylinder
from pyocctlite.rendering import render_views
from pyocctlite.topology import CutShapes, Edge, Face, RevolveShape, Vertex, Wire

# Dimensions for the fitting
bore_radius = 20.0
raised_face_radius = 45.0
raised_face_height = 2.0
flange_radius = 60.0
flange_thickness = 14.0
hub_base_radius = 34.0
hub_end_radius = 28.0
total_height = 60.0
hub_fillet_radius = 6.0
weld_bevel = 2.0
bolt_count = 6
bolt_circle_radius = 52.5
bolt_hole_radius = 6.0
bolt_hole_chamfer = 1.0

# The fitting is symmetric about the z-axis
origin = Point.by_xyz(0.0, 0.0, 0.0)
axis = Axis.by_vector(origin, Vector.by_xyz(0.0, 0.0, 1.0))

# Define the half-profile in the xz-plane as (radius, height)
hub_root = Vertex.by_point(Point.by_xyz(hub_base_radius, 0.0, flange_thickness))
hub_end = Vertex.by_point(Point.by_xyz(hub_end_radius, 0.0, total_height))
vertices = [
    Vertex.by_point(Point.by_xyz(bore_radius, 0.0, -raised_face_height)),
    Vertex.by_point(Point.by_xyz(raised_face_radius, 0.0, -raised_face_height)),
    Vertex.by_point(Point.by_xyz(raised_face_radius, 0.0, 0.0)),
    Vertex.by_point(Point.by_xyz(flange_radius, 0.0, 0.0)),
    Vertex.by_point(Point.by_xyz(flange_radius, 0.0, flange_thickness)),
    hub_root,
    hub_end,
    Vertex.by_point(Point.by_xyz(bore_radius, 0.0, total_height)),
]

# Share the vertices between edges so that the revolve can trace them
edges = [
    Edge.by_vertices(v1, v2) for v1, v2 in zip(vertices, vertices[1:] + vertices[:1], strict=True)
]
profile = Face.by_wire(Wire.by_edges(edges))

# Revolve the profile into the body, where each profile vertex generates a circular edge
tool = RevolveShape(profile, axis)
body = tool.shape()
hub_root_edge = tool.generated_shapes(hub_root)[0]
hub_end_edge = tool.generated_shapes(hub_end)[0]
assert isinstance(hub_root_edge, Edge)
assert isinstance(hub_end_edge, Edge)

# Fillet the root of the hub and bevel its end for welding
filleted = body.fillet(hub_root_edge, hub_fillet_radius)
beveled = filleted.chamfer(hub_end_edge, weld_bevel)

# Pattern a through-hole around the axis, starting and ending clear of the flange
o = Point.by_xyz(bolt_circle_radius, 0.0, -1.0)
hole = Cylinder.by_size(bolt_hole_radius, flange_thickness + 2.0, Frame.by_origin(o))
holes = [hole.rotate(axis, i * 2.0 * math.pi / bolt_count) for i in range(bolt_count)]

# Drill the holes and break the edges where they meet the flange faces
drill = CutShapes(beveled, holes)
fitting = drill.shape().chamfer(drill.intersection_edges(), bolt_hole_chamfer)

# Export STEP
fitting.export_step("outputs/flanged_fitting.step")

# Render a sheet of views
render_views(fitting, "outputs/flanged_fitting.png")
