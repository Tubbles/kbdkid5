"""Export a 3D-printable mock of the PCB (STL) from the layout.

kbdkid5 has no PCB design yet. Until it does, this printed stand-in
for the bare board carries the switches for a feel and test-fits the
tray and the plate: the outline from layout.py extruded to the PCB's
thickness, with every key's Choc hotswap footprint holes and the
mounting drills, and nothing else (no sockets). FDM prints come out
slightly larger than modelled (the extruded bead spreads, and the
first layer squashes wider still), so the mock is pulled in from all
sides: the outline moves inward by pull_in and every hole grows
outward by pull_in, so the printed part measures like the real board
instead of binding in the tray or refusing the switches. The thickness
stays as modelled, since a print's height follows its layer count and
does not swell the same way.

The outline and the holes move in opposite directions, so they are
built separately: FreeCAD's makeOffset2D on the whole face would
shrink the holes along with the outline. The outline's sharp polygon
moves in with sharp joins and is then rounded with the layout's corner
radius less pull_in at its convex corners and plus pull_in at its
concave ones, which is the rounded outline moved in (the arcs stay
concentric). Each hole is made pull_in larger in radius.

Runs headless under FreeCAD's console interpreter (see
freecad_common.py for the freecadcmd quirks that shape the
invocation):

    freecadcmd scripts/export_pcb.py --pass <mock.stl> [right] [pull_in=0.2]

The mock's x and y are the layout's, its bottom face on z = 0, while
in the layout's frame z = 0 is the tray floor's top (the PCB's
underside sits at z 8.0 there): a print lies on the bed. The word
"right" mirrors it across the layout's right-half mirror line (see
layout.py) for the right half: a bare board turned over is its own
mirror image, but a print is not, since its bed side and its top side
come out with different surfaces.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import FreeCAD as App
import Part

import layout
from freecad_common import (
    check_closed_mesh,
    export_stl,
    offset_outline,
    run_and_exit,
    script_arguments,
)
from tray_shape import MINIMUM_FILLET_RADIUS_MM, fillet_prism_corners

# How far the printed part is expected to swell per side, in mm: the
# outline moves inward and every hole grows outward by this much.
DEFAULT_PULL_IN_MM = 0.2

# Implementation tuning, rarely worth touching.
CUT_EXTRA_MM = 1.0  # hole cutters overshoot both faces for a clean cut
VOLUME_RELATIVE_TOLERANCE = 1e-6  # against the analytic volume

UP = App.Vector(0.0, 0.0, 1.0)

USAGE = f"""\
usage: freecadcmd scripts/export_pcb.py --pass <mock.stl> [right] [pull_in={DEFAULT_PULL_IN_MM}]

  right      export the right half: the mock mirrored across the layout's
             right-half mirror line, x = {layout.RIGHT_HALF_MIRROR_X_MM:.3f}
  pull_in    swelling allowance per side, mm: the outline moves inward and
             every hole grows outward by this much\
"""


class Arguments:
    def __init__(self):
        self.stl_file = None
        self.pull_in = DEFAULT_PULL_IN_MM
        self.right = False


def parse_arguments(argument_list):
    arguments = Arguments()
    positionals = []
    for argument in argument_list:
        if argument == "right":
            arguments.right = True
        elif "=" in argument:
            key, _, value = argument.partition("=")
            if key != "pull_in":
                raise SystemExit(f"error: unknown option '{key}'\n{USAGE}")
            try:
                arguments.pull_in = float(value)
            except ValueError:
                raise SystemExit(f"error: '{key}' needs a number, got '{value}'")
        else:
            positionals.append(argument)
    if len(positionals) != 1:
        raise SystemExit(USAGE)
    arguments.stl_file = positionals[0]
    return arguments


def all_holes():
    """Every hole of the bare board as (center, diameter): each key's
    footprint holes, then the mounting drills."""
    holes = [
        hole
        for center in layout.KEY_CENTERS_MM.values()
        for hole in layout.footprint_holes(center)
    ]
    holes.extend(
        (center, layout.MOUNTING_DRILL_DIAMETER_MM)
        for center in layout.MOUNTING_DRILL_CENTERS_MM
    )
    return holes


def corner_radii(pull_in):
    """(convex, concave) corner radii of the outline moved in by
    pull_in: concentric with the layout's rounds."""
    return (
        max(layout.OUTLINE_CORNER_RADIUS_MM - pull_in, 0.0),
        layout.OUTLINE_CORNER_RADIUS_MM + pull_in,
    )


def rounded_polygon_area(polygon, convex_radius, concave_radius):
    """The area of a counter-clockwise polygon with its corners rounded,
    as fillet_prism_corners() rounds them: a round of radius r at a
    corner turning by t takes r^2 (tan(t / 2) - t / 2) off a convex
    corner and adds as much at a concave one."""
    area = layout.polygon_signed_area(polygon)
    for turn in layout.corner_turn_angles(polygon):
        radius = convex_radius if turn > 0.0 else concave_radius
        if radius < MINIMUM_FILLET_RADIUS_MM:
            continue
        half_turn = abs(turn) / 2.0
        corner_area = radius**2 * (math.tan(half_turn) - half_turn)
        area += -corner_area if turn > 0.0 else corner_area
    return area


def analytic_mock_area(pull_in):
    """The mock's area from the layout alone, without FreeCAD's offset
    or fillets: the outline moved in, rounded, less the grown holes."""
    moved = layout.offset_polygon(layout.OUTLINE_VERTICES_MM, -pull_in)
    outline_area = rounded_polygon_area(moved, *corner_radii(pull_in))
    holes_area = sum(
        math.pi * (diameter / 2.0 + pull_in) ** 2 for _center, diameter in all_holes()
    )
    return outline_area - holes_area


def outline_polygon_wire():
    points = [App.Vector(x, y, 0.0) for x, y in layout.OUTLINE_VERTICES_MM]
    return Part.makePolygon(points + [points[0]])


def outline_body(pull_in, thickness):
    """The outline moved in by pull_in, rounded, extruded upward."""
    polygon = outline_polygon_wire()
    moved = polygon if pull_in == 0 else offset_outline(polygon, -pull_in)
    prism = Part.Face(moved).extrude(UP * thickness)
    convex_radius, concave_radius = corner_radii(pull_in)
    return fillet_prism_corners(prism, moved, UP, convex_radius, concave_radius)


def hole_cutter(center, diameter, pull_in, thickness):
    circle = Part.Wire(
        Part.makeCircle(diameter / 2.0 + pull_in, App.Vector(center[0], center[1], 0.0))
    )
    cutter = Part.Face(circle).extrude(UP * (thickness + 2.0 * CUT_EXTRA_MM))
    cutter.translate(UP * -CUT_EXTRA_MM)
    return cutter


def build_mock(pull_in, thickness):
    """(mock, its analytic volume)."""
    body = outline_body(pull_in, thickness)
    cutters = [
        hole_cutter(center, diameter, pull_in, thickness) for center, diameter in all_holes()
    ]
    mock = body.cut(Part.makeCompound(cutters))
    return mock, validate_mock(mock, pull_in, thickness)


def bottom_face(mock):
    """The mock's face on z = 0."""
    faces = [
        face
        for face in mock.Faces
        if isinstance(face.Surface, Part.Plane)
        and abs(face.Surface.Axis.z) > 0.999
        and abs(face.CenterOfMass.z) < 1e-6
    ]
    if len(faces) != 1:
        raise SystemExit(f"error: the mock has {len(faces)} faces on z = 0, expected one")
    return faces[0]


def rounded_corner_count(pull_in):
    """How many of the mock outline's corners fillet_prism_corners()
    rounds: all but those whose radius it skips as moot."""
    convex_radius, concave_radius = corner_radii(pull_in)
    return sum(
        1
        for turn in layout.corner_turn_angles(layout.OUTLINE_VERTICES_MM)
        if (convex_radius if turn > 0.0 else concave_radius) >= MINIMUM_FILLET_RADIUS_MM
    )


def validate_mock(mock, pull_in, thickness):
    """Check the mock against the layout and return its analytic
    volume."""
    if not mock.isValid() or len(mock.Solids) != 1:
        raise SystemExit("error: cutting the holes broke the mock solid")
    expected_volume = analytic_mock_area(pull_in) * thickness
    deviation = abs(mock.Volume - expected_volume)
    if deviation > VOLUME_RELATIVE_TOLERANCE * expected_volume:
        raise SystemExit(
            f"error: mock volume {mock.Volume:.4f} mm3 deviates from the analytic "
            f"{expected_volume:.4f} mm3 by {deviation:.4f}; geometry is off"
        )
    face = bottom_face(mock)
    hole_count = len(face.Wires) - 1
    if hole_count != len(all_holes()):
        raise SystemExit(
            f"error: the mock has {hole_count} holes, the layout {len(all_holes())}"
        )
    # The volume only just tells a missing round at the default pull_in
    # (a right-angle corner rounded with 0.276 loses 0.026 mm3, against a
    # tolerance of 0.013 mm3) and misses smaller rounds, so count them.
    arc_count = sum(1 for edge in face.OuterWire.Edges if isinstance(edge.Curve, Part.Circle))
    if arc_count != rounded_corner_count(pull_in):
        raise SystemExit(
            f"error: the mock's outline has {arc_count} rounded corners, the layout "
            f"{rounded_corner_count(pull_in)}"
        )
    return expected_volume


def mirror_for_right_half(mock):
    """Mirror the mock across the layout's right-half mirror line."""
    volume_before = mock.Volume
    mirrored = mock.mirror(
        App.Vector(layout.RIGHT_HALF_MIRROR_X_MM, 0.0, 0.0), App.Vector(1.0, 0.0, 0.0)
    )
    if not mirrored.isValid() or abs(mirrored.Volume - volume_before) > 1e-6 * volume_before:
        raise SystemExit("error: mirroring the mock changed its volume")
    return mirrored


def hole_census():
    """{diameter: count} of the layout's holes."""
    counts = {}
    for _center, diameter in all_holes():
        counts[diameter] = counts.get(diameter, 0) + 1
    return counts


def main():
    arguments = parse_arguments(script_arguments(sys.argv))
    thickness = layout.PCB_THICKNESS_MM

    mock, expected_volume = build_mock(arguments.pull_in, thickness)
    if arguments.right:
        mock = mirror_for_right_half(mock)
    mesh = export_stl(mock, arguments.stl_file)
    check_closed_mesh(arguments.stl_file)

    outline = layout.OUTLINE_VERTICES_MM
    width = max(x for x, _ in outline) - min(x for x, _ in outline)
    height = max(y for _, y in outline) - min(y for _, y in outline)
    box = mock.BoundBox
    print(f"layout:     outline {width:.2f} x {height:.2f} mm, "
          f"{len(outline)} corners rounded {layout.OUTLINE_CORNER_RADIUS_MM} mm, "
          f"{len(layout.KEY_CENTERS_MM)} keys, {len(layout.MOUNTING_DRILL_CENTERS_MM)} "
          f"mounting drills, {thickness} mm thick")
    print(f"mock:       {box.XLength:.2f} x {box.YLength:.2f} x {box.ZLength:.2f} mm "
          f"(x {box.XMin:.3f} to {box.XMax:.3f}), pulled in {arguments.pull_in} mm per "
          f"side, volume {mock.Volume:.3f} mm3 (analytic {expected_volume:.3f} mm3)")
    for diameter, count in sorted(hole_census().items()):
        print(f"holes:      {count:3d} x {diameter:.2f} mm -> "
              f"{diameter + 2.0 * arguments.pull_in:.2f} mm")
    half = "left"
    if arguments.right:
        half = f"right, mirrored across x = {layout.RIGHT_HALF_MIRROR_X_MM:.3f}"
    print(f"half:       {half}")
    print(f"wrote:      {arguments.stl_file} ({mesh.CountFacets} facets), "
          "one closed manifold shell")


run_and_exit(main)
