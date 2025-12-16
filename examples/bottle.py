# https://dev.opencascade.org/doc/overview/html/occt__tutorial.html
import math

from pyocctlite.geometry import (CylindricalSurface, Ellipse2D, Frame, Frame2D, Point, Point2D,
                                 TrimmedCurve2D, Vector, Vector2D)
from pyocctlite.mesh import Mesh, MeshControl
from pyocctlite.primitives import Cylinder
from pyocctlite.topology import Edge, Face, Solid, Wire

height = 70
width = 50
thickness = 30
neck_radius = thickness / 4.
neck_height = height / 10.

p1 = Point.by_xyz(-width / 2., 0., 0.)
p2 = Point.by_xyz(-width / 2., -thickness / 4., 0.)
p3 = Point.by_xyz(0., -thickness / 2., 0.)
p4 = Point.by_xyz(width / 2., -thickness / 4., 0.)
p5 = Point.by_xyz(width / 2., 0., 0.)

e1 = Edge.by_points(p1, p2)
e2 = Edge.by_points(p4, p5)
e3 = Edge.by_circular_arc(p2, p3, p4)
w1 = Wire.by_edges([e1, e2, e3])

origin = Point.by_xyz(0, 0, 0)
normal = Vector.by_xyz(0, 1, 0)
w2 = w1.mirror(origin, normal)

w3 = w1.combine(w2)

bottom_face = Face.by_wire(w3)
v = Vector.by_xyz(0, 0, height)
extruded = bottom_face.extrude(v)

filleted = extruded.fillet(extruded.edges(), thickness / 12.)

o = Point.by_xyz(0, 0, height)
frame = Frame.by_origin(o)
neck = Cylinder.by_size(neck_radius, neck_height, frame)
bottle = filleted.unite(neck)
bottle = bottle.fillet(neck.bottom_face.edges(), 1.5 * thickness / 50.)

bottle = bottle.thicken(-thickness / 50., 1.0e-3, [neck.top_face])

cs1 = CylindricalSurface.by_radius(frame, neck_radius * 0.99)
cs2 = CylindricalSurface.by_radius(frame, neck_radius * 1.05)
p2d = Point2D.by_xy(2. * math.pi, neck_height / 2.)
v2d = Vector2D.by_xy(2. * math.pi, neck_height / 4.)
f2d = Frame2D.by_vector(p2d, v2d)
rmajor = 2. * math.pi
rminor = neck_height / 10.
ellipse1 = Ellipse2D.by_radii(f2d, rmajor, rminor)
ellipse2 = Ellipse2D.by_radii(f2d, rmajor, rminor / 4.)
arc1 = TrimmedCurve2D.by_curve(ellipse1, 0, math.pi)
arc2 = TrimmedCurve2D.by_curve(ellipse2, 0., math.pi)
ep1 = ellipse1.evaluate(0.)
ep2 = ellipse2.evaluate(math.pi)
aseg = TrimmedCurve2D.by_points(ep1, ep2)
e1s1 = Edge.by_curve2d(arc1, cs1)
e2s1 = Edge.by_curve2d(aseg, cs1)
e1s2 = Edge.by_curve2d(arc1, cs2)
e2s2 = Edge.by_curve2d(aseg, cs2)
w1 = Wire.by_edges([e1s1, e2s1])
w2 = Wire.by_edges([e1s2, e2s2])
threads = Solid.by_loft([w1, w2])
bottle = bottle.unite(threads)

# Export STEP
bottle.export_step('bottle.step')

# Mesh
control3d = MeshControl.by_control_3d(bottle, 1.0)
mesh = Mesh.generate(bottle, control3d)

# Export mesh
print(mesh.num_nodes, mesh.num_tetras)
mesh.export_unv('bottle.unv')
