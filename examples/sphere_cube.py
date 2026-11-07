from __future__ import annotations

from pyocctlite.geometry import Frame, Point
from pyocctlite.primitives import Box, Sphere
from pyocctlite.rendering import render_views
from pyocctlite.topology import UniteShapes

# Dimensions for the sphere-cube
size = 10.0
radius = size / 2.0
fillet_radius = size / 50.0

# Create the cube with its minimum corner at the origin
cube = Box.by_size(size, size, size)

# Create the sphere centered at the maximum corner of the cube
o = Point.by_xyz(size, size, size)
frame = Frame.by_origin(o)
sphere = Sphere.by_size(radius, frame)

# Unite the cube and sphere, then fillet the edges where they intersect
tool = UniteShapes(cube, sphere)
sphere_cube = tool.shape().fillet(tool.intersection_edges(), fillet_radius)

# Export STEP
sphere_cube.export_step("outputs/sphere_cube.step")

# Render a sheet of views
render_views(sphere_cube, "outputs/sphere_cube.png")
