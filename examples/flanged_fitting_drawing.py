# Makes a dimensioned engineering drawing of the part from flanged_fitting.py, written as
# outputs/flanged_fitting_drawing.png, .svg and .pdf. Every measured value comes from the part, so
# the drawing follows it when its dimensions change.
from __future__ import annotations

import math
import runpy
from pathlib import Path

from pyocctlite.drawing import LinePattern, Paper, Sheet, Stroke, Symbol
from pyocctlite.geometry import Circle, Circle2D, Frame2D, Point, Point2D, Vector, Vector2D
from pyocctlite.rendering import View
from pyocctlite.topology import Edge, Shape

# Build the part with its own example, which also gives its dimensions
part = runpy.run_path(str(Path(__file__).with_name("flanged_fitting.py")))
fitting: Shape = part["fitting"]
bore_radius: float = part["bore_radius"]
raised_face_radius: float = part["raised_face_radius"]
raised_face_height: float = part["raised_face_height"]
flange_radius: float = part["flange_radius"]
flange_thickness: float = part["flange_thickness"]
hub_base_radius: float = part["hub_base_radius"]
hub_end_radius: float = part["hub_end_radius"]
hub_fillet_radius: float = part["hub_fillet_radius"]
total_height: float = part["total_height"]
weld_bevel: float = part["weld_bevel"]
bolt_circle_radius: float = part["bolt_circle_radius"]
bolt_hole_radius: float = part["bolt_hole_radius"]
bolt_hole_chamfer: float = part["bolt_hole_chamfer"]

SCALE = 1.5
HORIZONTAL = Vector2D.by_xy(1.0, 0.0)
VERTICAL = Vector2D.by_xy(0.0, 1.0)


def at_radius(radius: float, z: float) -> Point:
    """
    Get a point of the half profile in the plane of the section, on the right of the axis.

    :param radius: Distance from the axis.
    :param z: Height.
    :return: Point on the part.
    """
    return Point.by_xyz(radius, 0.0, z)


def circular_edges(radius: float) -> list[Edge]:
    """
    Find the circular edges of the part with a radius, by geometry since edge order can vary.

    :param radius: Radius to look for.
    :return: Matching edges.
    """
    found = []
    for edge in fitting.edges():
        curve = edge.curve
        if isinstance(curve, Circle) and math.isclose(curve.radius, radius, abs_tol=1.0e-6):
            found.append(edge)
    return found


# Each hole has a circular edge at each end of its bore, and the hub's fillet has others of the
# same radius elsewhere, so holes are told apart by where they are
bolt_holes: dict[tuple[float, float], Edge] = {}
for edge in circular_edges(bolt_hole_radius):
    curve = edge.curve
    assert isinstance(curve, Circle)
    center = curve.frame.origin
    if math.isclose(math.hypot(center.x, center.y), bolt_circle_radius, abs_tol=1.0e-6):
        bolt_holes[(round(center.x, 6), round(center.y, 6))] = edge
hole_count = len(bolt_holes)

# The part is in millimeters, so the sheet's coordinates are too
sheet = Sheet(Paper.C, units_per_inch=25.4)
sheet.add_zones(columns=8, rows=6)

# The plan view shows the flange's face, and a full section below it shows everything inside
plan = sheet.add_view(fitting, View.TOP, Point2D.by_xy(175.0, 300.0), SCALE)
section = sheet.add_section_view(
    plan, Point.by_xyz(0.0, 0.0, 0.0), Vector.by_xyz(0.0, -1.0, 0.0), gap=52.0, label="A"
)
section.add_label("SECTION A-A", gap=38.0)
detail = sheet.add_detail_view(
    section,
    at_radius(hub_end_radius - weld_bevel, total_height - weld_bevel),
    radius=7.0,
    at=Point2D.by_xy(350.0, 130.0),
    scale=5.0,
    label="B",
)
detail.add_label("DETAIL B\nSCALE 5:1", gap=14.0)
iso = sheet.add_view(fitting, View.ISO, Point2D.by_xy(455.0, 275.0), scale=1.0, hidden=False)
iso.add_label("ISOMETRIC\nSCALE 1:1", gap=12.0)

# The plan view locates the holes on their bolt circle, with a center mark on each
plan.add_center_mark(circular_edges(flange_radius)[0])
bolt_circle = Circle2D.by_radius(
    bolt_circle_radius * SCALE, Frame2D.by_origin(plan.to_sheet(Point.by_xyz(0.0, 0.0, 0.0)))
)
sheet.add_curve(bolt_circle, Stroke(pattern=LinePattern.CENTER))
for edge in bolt_holes.values():
    plan.add_center_mark(edge)

first_hole = bolt_holes[max(bolt_holes, key=lambda xy: xy[0] + xy[1])]
countersink = 2.0 * (bolt_hole_radius + bolt_hole_chamfer)
plan.add_diameter(
    first_hole,
    angle=math.radians(45.0),
    prefix=f"{hole_count}X ",
    suffix=(
        f" THRU\n{Symbol.COUNTERSINK}{Symbol.DIAMETER}{countersink:.0f} X 90{Symbol.DEGREE}"
        f"\nEQ SP ON {Symbol.DIAMETER}{bolt_circle_radius * 2.0:.0f} B.C."
    ),
    decimals=0,
)
sheet.add_feature_control_frame(
    Point2D.by_xy(237.5, 369.0),
    [
        str(Symbol.POSITION),
        f"{Symbol.DIAMETER}0.5{Symbol.MAX_MATERIAL}",
        "A",
        f"B{Symbol.MAX_MATERIAL}",
    ],
)

# The section's diameters stack below it and above it, from the smallest out
bottom = -raised_face_height
section.add_dimension(
    at_radius(-raised_face_radius, bottom),
    at_radius(raised_face_radius, bottom),
    offset=-12.0,
    along=HORIZONTAL,
    prefix=str(Symbol.DIAMETER),
    decimals=0,
)
section.add_dimension(
    at_radius(-flange_radius, 0.0),
    at_radius(flange_radius, 0.0),
    offset=-24.0,
    along=HORIZONTAL,
    prefix=str(Symbol.DIAMETER),
    suffix=f" {Symbol.PLUS_MINUS}0.5",
    decimals=0,
)
section.add_dimension(
    at_radius(-hub_end_radius, total_height - weld_bevel),
    at_radius(hub_end_radius, total_height - weld_bevel),
    offset=18.0,
    along=HORIZONTAL,
    prefix=str(Symbol.DIAMETER),
    decimals=0,
)
section.add_dimension(
    at_radius(-bore_radius, total_height),
    at_radius(bore_radius, total_height),
    offset=8.0,
    along=HORIZONTAL,
    prefix=str(Symbol.DIAMETER),
    suffix=f" {Symbol.PLUS_MINUS}0.1",
    decimals=0,
)

# Heights chain up the side from the raised face, which is the primary datum
section.add_dimension(
    at_radius(-flange_radius, bottom),
    at_radius(-hub_end_radius, total_height),
    offset=26.0,
    along=VERTICAL,
    decimals=0,
)
section.add_dimension(
    at_radius(flange_radius, 0.0),
    at_radius(flange_radius, flange_thickness),
    offset=-10.0,
    along=VERTICAL,
    decimals=0,
)
section.add_dimension(
    at_radius(flange_radius, bottom),
    at_radius(flange_radius, 0.0),
    offset=-24.0,
    along=VERTICAL,
    decimals=0,
)

# The hub's root fillet, seen only in the section
fillet_middle = at_radius(
    hub_base_radius + hub_fillet_radius * (1.0 - math.cos(math.pi / 4.0)) * 0.72,
    flange_thickness + hub_fillet_radius * (1.0 - math.sin(math.pi / 4.0)) * 0.72,
)
tip = section.to_sheet(fillet_middle)
sheet.add_leader(tip, tip.translate(Vector2D.by_xy(26.0, 22.0)), f"R{hub_fillet_radius:.0f} TYP")

# Datums and geometric tolerances hang off the faces and the bore they control
raised_left = section.to_sheet(at_radius(-30.0, bottom))
sheet.add_datum_feature(raised_left, raised_left.translate(Vector2D.by_xy(0.0, -9.0)), "A")
bore_wall = section.to_sheet(at_radius(-bore_radius, total_height - 18.0))
sheet.add_datum_feature(bore_wall, bore_wall.translate(Vector2D.by_xy(14.0, 0.0)), "B")

flatness_tip = section.to_sheet(at_radius(30.0, bottom))
flatness_at = flatness_tip.translate(Vector2D.by_xy(62.0, -19.0))
sheet.add_leader(flatness_tip, flatness_at, "")
sheet.add_feature_control_frame(
    flatness_at.translate(Vector2D.by_xy(7.0, 0.0)), [str(Symbol.FLATNESS), "0.05"]
)
runout_tip = section.to_sheet(at_radius(hub_end_radius, total_height - weld_bevel - 12.0))
runout_at = runout_tip.translate(Vector2D.by_xy(26.0, 14.0))
sheet.add_leader(runout_tip, runout_at, "")
sheet.add_feature_control_frame(
    runout_at.translate(Vector2D.by_xy(7.0, 0.0)), [str(Symbol.RUNOUT), "0.2", "A", "B"]
)
sheet.add_surface_finish(section.to_sheet(at_radius(-48.0, flange_thickness)), "3.2")

# The axis of the part runs through its section
section.add_center_line(Point.by_xyz(0.0, 0.0, bottom), Point.by_xyz(0.0, 0.0, total_height))

# The detail shows the bevel that a weld will fill
detail.add_dimension(
    at_radius(hub_end_radius - weld_bevel, total_height),
    at_radius(hub_end_radius, total_height - weld_bevel),
    offset=10.0,
    along=HORIZONTAL,
    decimals=0,
)
detail.add_dimension(
    at_radius(hub_end_radius - weld_bevel, total_height),
    at_radius(hub_end_radius, total_height - weld_bevel),
    offset=-10.0,
    along=VERTICAL,
    decimals=0,
)

# A table lists where each hole is, read from the part, with a letter for each going around
holes = sorted(bolt_holes, key=lambda xy: math.atan2(xy[1], xy[0]) % (2.0 * math.pi))
sheet.add_table(
    Point2D.by_xy(290.0, 262.0),
    [
        ["HOLE", "X", "Y"],
        *[[chr(ord("A") + i), f"{x:.2f}", f"{y:.2f}"] for i, (x, y) in enumerate(holes)],
    ],
    column_widths=[18.0, 24.0, 24.0],
)

# The revision block goes in the upper right corner, against the border
right = sheet.width - 12.7
sheet.add_table(
    Point2D.by_xy(right - 150.0, sheet.height - 12.7),
    [
        ["REV", "DESCRIPTION", "DATE", "BY"],
        ["A", "INITIAL RELEASE", "2026-10-12", "PY"],
        ["B", "ADD WELD BEVEL DETAIL", "2026-11-07", "PY"],
    ],
    column_widths=[14.0, 86.0, 32.0, 18.0],
)

# Notes and the general tolerances, above the title block
sheet.add_text(
    Point2D.by_xy(400.0, 133.0),
    "NOTES:\n"
    "1. INTERPRET PER ASME Y14.5-2018.\n"
    "2. DIMENSIONS ARE IN MILLIMETERS.\n"
    "3. BREAK SHARP EDGES 0.2 MAX.\n"
    "4. SURFACE ROUGHNESS 6.3 MAX UNLESS NOTED.\n"
    "5. INSPECT THE BORE AND RAISED FACE 100%.",
    height=3.0,
)
sheet.add_table(
    Point2D.by_xy(right - 159.0, 83.0),
    [
        ["MATERIAL", "ASTM A105 FORGED CARBON STEEL"],
        ["FINISH", "ZINC PHOSPHATE, OIL"],
        [
            "TOLERANCES",
            f"X {Symbol.PLUS_MINUS}0.5   X.X {Symbol.PLUS_MINUS}0.2   "
            f"ANGLES {Symbol.PLUS_MINUS}1{Symbol.DEGREE}",
        ],
    ],
    column_widths=[34.0, 125.0],
    row_height=10.7,
)
sheet.add_title_block(
    title="WELD NECK FLANGE",
    number="FF-1042",
    revision="B",
    date="2026-11-07",
    drawn_by="PYOCCTLITE",
    scale=SCALE,
)

for extension in ("png", "svg", "pdf"):
    sheet.write(f"outputs/flanged_fitting_drawing.{extension}")
