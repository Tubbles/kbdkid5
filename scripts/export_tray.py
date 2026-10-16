"""Export a half's 3D-printable tray shell and joint (STL) from the layout.

tray_shape.py builds the tray (see its docstring): walls, floor, ledge
and joint block, standoffs bored for M2 heat-set inserts, the dowel pin
and parking bosses with their fills, the ledge cut-aways and the
sockets' cuts as layout.py gives them, the magnet slots, the
flat-topped teardrop pin holes and parking hole, and the joint face's
bottom chamfer. This script mirrors it for the right half, measures it
and prints what it found against DESIGN.md's figures, which it
transcribes itself (the DESIGN_* constants below), never against the
constants the tray is built from: the outside's size, the walls, the
floor, the ledge and the joint block, the standoffs and their bores,
the joint face's angle, place and bottom chamfer, the pin holes (depth,
diameter, the plastic behind and over them, the flat top, the lead-in),
the magnet slots and the parking hole. Then it builds the other half
too and joins them as DESIGN.md describes, each half turned 17.74
degrees so the outer slant faces touch, and checks that the trays do
not overlap, that the pin holes line up into one channel at least 1.0
longer than the pin, and that the magnet slots face each other. Last,
it writes the tray as built, floor on the bed, as one closed mesh.

Runs headless under FreeCAD's console interpreter (see
freecad_common.py for the freecadcmd quirks that shape the
invocation):

    freecadcmd scripts/export_tray.py --pass <tray.stl> [right] [pin_hole_diameter=<mm>]

The word "right" makes the right half: the tray built with that half's
socket cuts and its slip fit pin holes, mirrored across the layout's
right-half mirror line. pin_hole_diameter overrides the half's pin
hole fit (layout.py: the left half's snug, the right half's slip, as
modelled), for a test print. The measured diameter is then checked
against it instead of DESIGN.md's, and the flat top and the plastic
over the holes, which follow from it, are only printed.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import FreeCAD as App
import Part

import layout
from freecad_common import check_closed_mesh, export_stl, run_and_exit, script_arguments
from tray_shape import UP, build_tray, mirror_for_right_half

# DESIGN.md's figures, transcribed independently of layout.py, each
# compared within half its last digit.
DESIGN_TRAY_OUTSIDE_MM = (134.8, 85.0, 13.1)  # along x, along y, tall
DESIGN_FLOOR_UNDERSIDE_Z_MM = -1.2
DESIGN_RIM_Z_MM = 11.9
DESIGN_GAP_MM = 0.4
DESIGN_WALL_MM = 0.8
DESIGN_FLOOR_MM = 1.2
DESIGN_LEDGE_WIDTH_MM = 1.0
DESIGN_LEDGE_UNDER_PCB_MM = 0.6
DESIGN_LEDGE_TOP_Z_MM = 8.0  # the PCB's underside, also the standoffs' and the block's tops
DESIGN_STANDOFF_DIAMETER_MM = 5.8
DESIGN_STANDOFF_BORE_MM = 3.2
DESIGN_MOUNTING_DRILLS_MM = (
    (18.574, 18.732),
    (18.574, 37.782),
    (76.041, 43.260),
    (94.774, 60.404),
    (114.141, 19.765),
)
DESIGN_MIRROR_LINE_X_MM = 66.199
DESIGN_SLANT_ENDS_MM = ((132.398, 18.335), (113.348, 77.867))  # south, north
DESIGN_SLANT_ANGLE_FROM_NORTH_DEGREES = 17.74
DESIGN_JOINT_FACE_OUT_OF_SLANT_MM = 1.2
DESIGN_JOINT_FACE_BOTTOM_CHAMFER_MM = 0.4
DESIGN_JOINT_BLOCK_THICKNESS_MM = 4.0
DESIGN_DOWEL_PIN_ALONGS_MM = (3.5, 59.0)
DESIGN_DOWEL_PIN_SPACING_MM = 55.5
DESIGN_DOWEL_PIN_Z_MM = 3.4
# Per half, False the left one, True the right one: the left half's
# holes snug and the pin's stop, the right half's slip.
DESIGN_DOWEL_HOLE_DIAMETER_MM = {False: 4.4, True: 4.5}
DESIGN_DOWEL_HOLE_DEPTH_MM = {False: 8.2, True: 9.0}
DESIGN_DOWEL_BOSS_BEHIND_HOLE_MM = {False: 1.2, True: 1.0}
DESIGN_DOWEL_BOSS_REACH_MM = {False: 9.4, True: 10.0}
DESIGN_DOWEL_HOLE_LEAD_IN_MM = {False: 0.0, True: 0.3}
DESIGN_DOWEL_HOLE_FLAT_MM = {False: 1.82, True: 1.86}  # the flat top's width
DESIGN_PLASTIC_OVER_DOWEL_HOLES_MM = {False: 2.4, True: 2.35}
DESIGN_DOWEL_BOSS_ACROSS_MM = 7.0
DESIGN_DOWEL_PIN_LENGTH_MM = 16.0
DESIGN_PIN_CHANNEL_MARGIN_MM = 1.0  # the joined channel's length past the pin's, as modelled
DESIGN_MAGNET_ALONGS_MM = (14.24, 25.58, 36.92, 48.26)
DESIGN_MAGNET_SLOT_MM = (8.5, 3.5)  # along the slant, across it
DESIGN_MAGNET_SLOT_BOTTOM_Z_MM = -0.7
DESIGN_MAGNET_SKIN_MM = 0.5
DESIGN_MAGNETS_APART_JOINED_MM = 1.0
DESIGN_THUMB_EAST_EDGE_X_MM = 132.398
DESIGN_PARKING_HOLE_DIAMETER_MM = 4.5
DESIGN_PARKING_HOLE_FLAT_MM = 1.86
DESIGN_PLASTIC_OVER_PARKING_HOLE_MM = 2.35
DESIGN_PARKING_HOLE_Y_MM = 13.1
DESIGN_PARKING_HOLE_Z_MM = 3.4
DESIGN_PARKING_HOLE_DEPTH_MM = 16.5  # the pin's 14.5 and the magnet's 2.0
DESIGN_PARKING_BOSS_ACROSS_MM = 7.0
DESIGN_PARKING_BOSS_BEHIND_HOLE_MM = 1.5
DESIGN_SOCKET_BOTTOM_Z_MM = 5.98
# The least any socket keeps from the tray as cut: the ledge relief's
# and the tab pocket's clearance.
DESIGN_LEAST_SOCKET_CLEARANCE_MM = 0.5

# The walls are measured at these points of DESIGN.md's outline, (where,
# point on an outline edge, outward unit vector), at WALL_PROBE_Z_MM,
# above the ledge and clear of every cut. The slant's is its middle,
# between two magnet slots. The ledge is measured at the west one.
WALL_PROBE_Z_MM = 10.0
LEDGE_PROBE_Z_MM = 4.0
FLOOR_PROBE_MM = (60.0, 40.0)  # open floor, clear of every standoff and boss
SLANT_PROBE_ALONG_MM = 31.25

# How far a measuring line reaches either side of its point.
PROBE_REACH_MM = 30.0
# The plastic over a horizontal hole is sampled this far apart along it.
HOLE_SAMPLE_STEP_MM = 0.25
# Two places count as the same within this.
SAME_PLACE_MM = 1e-6
# The joined trays overlap or part by less than this.
JOINED_TOLERANCE_MM = 1e-6
JOINED_OVERLAP_TOLERANCE_MM3 = 1e-3

USAGE = f"""\
usage: freecadcmd scripts/export_tray.py --pass <tray.stl> [right]
           [pin_hole_diameter=<mm>]

  right              export the right half: cut for its own sockets, its pin
                     holes the slip fit, mirrored across the layout's right-half
                     mirror line, x = {layout.RIGHT_HALF_MIRROR_X_MM:.3f}
  pin_hole_diameter  the dowel pin holes' diameter as modelled, mm, instead of
                     the half's fit ({layout.DOWEL_HOLE_SNUG_DIAMETER_MM:.1f} snug on the left, \
{layout.DOWEL_HOLE_SLIP_DIAMETER_MM:.1f} slip
                     on the right, both less {layout.PRINT_SWELLING_PER_SIDE_MM} per side once \
printed)\
"""


class Arguments:
    def __init__(self):
        self.stl_file = None
        self.right = False
        self.pin_hole_diameter = None


def parse_arguments(argument_list):
    arguments = Arguments()
    positionals = []
    for argument in argument_list:
        if argument == "right":
            arguments.right = True
        elif "=" in argument:
            key, _, value = argument.partition("=")
            if key != "pin_hole_diameter":
                raise SystemExit(f"error: unknown option '{key}'\n{USAGE}")
            try:
                arguments.pin_hole_diameter = float(value)
            except ValueError:
                raise SystemExit(f"error: '{key}' needs a number, got '{value}'")
        else:
            positionals.append(argument)
    if len(positionals) != 1:
        raise SystemExit(USAGE)
    arguments.stl_file = positionals[0]
    return arguments


# DESIGN.md's geometry on either half.


def half_point(point, right):
    """A left-half DESIGN.md point on the given half."""
    return (2.0 * DESIGN_MIRROR_LINE_X_MM - point[0], point[1]) if right else point


def half_vector(vector, right):
    return (-vector[0], vector[1]) if right else vector


def design_slant_frame(right):
    """(south end, unit direction north, unit outward normal) of
    DESIGN.md's slant on the given half."""
    (south_x, south_y), (north_x, north_y) = DESIGN_SLANT_ENDS_MM
    length = math.hypot(north_x - south_x, north_y - south_y)
    direction = ((north_x - south_x) / length, (north_y - south_y) / length)
    outward = (direction[1], -direction[0])  # the outline runs counter-clockwise
    south = half_point((south_x, south_y), right)
    return south, half_vector(direction, right), half_vector(outward, right)


def slant_place(right, along, outward, z):
    """The point along and outward of DESIGN.md's slant on the given
    half, at height z."""
    south, direction, normal = design_slant_frame(right)
    return App.Vector(
        south[0] + along * direction[0] + outward * normal[0],
        south[1] + along * direction[1] + outward * normal[1],
        z,
    )


def vector(plan, z=0.0):
    return App.Vector(plan[0], plan[1], z)


def wall_probes(right):
    """(where, point on DESIGN.md's outline, outward unit vector), named
    on the given half."""
    probes = [
        (("west", "east"), (0.0, 34.0), (-1.0, 0.0)),
        (("south", "south"), (18.8, 0.0), (0.0, -1.0)),
        (("north of column 4", "north of column 4"), (85.249, 80.248), (0.0, 1.0)),
        (("thumb's east", "thumb's west"), (DESIGN_THUMB_EAST_EDGE_X_MM, 10.0), (1.0, 0.0)),
    ]
    probes = [
        (names[right], half_point(point, right), half_vector(outward, right))
        for names, point, outward in probes
    ]
    _south, _direction, normal = design_slant_frame(right)
    middle = slant_place(right, SLANT_PROBE_ALONG_MM, 0.0, 0.0)
    probes.append(("slant", (middle.x, middle.y), normal))
    return probes


# Measuring along lines.


def material_intervals(shape, start, direction, length):
    """The sorted (low, high) stretches, as distances from start along
    the unit direction, where the segment lies inside the shape."""
    edge = Part.LineSegment(start, start.add(direction * length)).toShape()
    intervals = []
    for piece in shape.common(edge).Edges:
        ends = [vertex.Point.sub(start).dot(direction) for vertex in piece.Vertexes]
        intervals.append((min(ends), max(ends)))
    intervals.sort()
    merged = []
    for low, high in intervals:
        if merged and low <= merged[-1][1] + SAME_PLACE_MM:
            merged[-1] = (merged[-1][0], max(merged[-1][1], high))
        else:
            merged.append((low, high))
    return merged


def run_through(shape, point, direction, material):
    """(low, high) of the material (or, with material False, the empty)
    stretch through point along the unit direction, as signed distances
    from point. An open end reads as PROBE_REACH_MM."""
    start = point.sub(direction * PROBE_REACH_MM)
    intervals = [
        (low - PROBE_REACH_MM, high - PROBE_REACH_MM)
        for low, high in material_intervals(shape, start, direction, 2.0 * PROBE_REACH_MM)
    ]
    if material:
        for low, high in intervals:
            if low <= 0.0 <= high:
                return low, high
        raise SystemExit(f"error: no plastic at {format_vector(point)} to measure")
    low, high = -PROBE_REACH_MM, PROBE_REACH_MM
    for interval_low, interval_high in intervals:
        if interval_low <= 0.0 <= interval_high:
            raise SystemExit(f"error: plastic at {format_vector(point)}, where a gap was measured")
        if interval_high < 0.0:
            low = max(low, interval_high)
        if interval_low > 0.0:
            high = min(high, interval_low)
    return low, high


def format_vector(point):
    return f"({point.x:.3f}, {point.y:.3f}, {point.z:.3f})"


class Figures:
    """Measured figures against DESIGN.md's, each within half its last
    digit. A figure off DESIGN.md stops the export."""

    def __init__(self):
        self.problems = []

    def check(self, label, measured, stated, decimals):
        tolerance = 0.5 * 10.0**-decimals + 1e-6
        shown = round(measured, decimals + 2) + 0.0  # no "-0.00"
        text = f"{label} {shown:.{decimals + 2}f} (DESIGN.md {stated})"
        if abs(measured - stated) > tolerance:
            self.problems.append(text)
        return text

    def at_least(self, label, measured, minimum, decimals):
        shown = round(measured, decimals + 2) + 0.0
        text = f"{label} {shown:.{decimals + 2}f} (DESIGN.md at least {minimum})"
        if measured < minimum - 1e-6:
            self.problems.append(text)
        return text

    def report(self, label, measured, decimals):
        """A figure DESIGN.md does not give (a test print's)."""
        return f"{label} {measured:.{decimals + 2}f}"

    def stop_on_problems(self):
        if self.problems:
            raise SystemExit("error: off DESIGN.md's figures:\n  " + "\n  ".join(self.problems))


# The measurements.


def measure_outside(tray, figures):
    box = tray.BoundBox
    texts = [
        figures.check(f"{what} outside", length, stated, 1)
        for what, length, stated in zip(
            ("x", "y", "z"), (box.XLength, box.YLength, box.ZLength), DESIGN_TRAY_OUTSIDE_MM
        )
    ]
    texts.append(figures.check("floor underside z", box.ZMin, DESIGN_FLOOR_UNDERSIDE_Z_MM, 1))
    texts.append(figures.check("rim z", box.ZMax, DESIGN_RIM_Z_MM, 1))
    return f"outside:    {', '.join(texts)} (x {box.XMin:.3f} to {box.XMax:.3f})"


def wall_middle(point, outward, z):
    """The point halfway through DESIGN.md's wall out of an outline
    point."""
    return vector(point, z).add(vector(outward) * (DESIGN_GAP_MM + DESIGN_WALL_MM / 2.0))


def measure_walls(tray, right, figures):
    lines = []
    for where, point, outward in wall_probes(right):
        middle = wall_middle(point, outward, WALL_PROBE_Z_MM)
        low, high = run_through(tray, middle, vector(outward), True)
        inner = DESIGN_GAP_MM + DESIGN_WALL_MM / 2.0 + low
        texts = [
            figures.check("inner face out of the outline", inner, DESIGN_GAP_MM, 1),
            figures.check("thick", high - low, DESIGN_WALL_MM, 1),
        ]
        lines.append(f"wall:       {where}: {', '.join(texts)}")
    return lines


def measure_floor(tray, right, figures):
    plan = half_point(FLOOR_PROBE_MM, right)
    point = vector(plan, DESIGN_FLOOR_UNDERSIDE_Z_MM / 2.0)
    low, high = run_through(tray, point, UP, True)
    bottom, top = point.z + low, point.z + high
    texts = [
        figures.check("thick", top - bottom, DESIGN_FLOOR_MM, 1),
        figures.check("top z", top, 0.0, 1),
    ]
    return f"floor:      at ({plan[0]:.3f}, {plan[1]:.3f}): {', '.join(texts)}"


def measure_ledge(tray, right, figures):
    where, point, outward = wall_probes(right)[0]
    direction = vector(outward)
    low, high = run_through(tray, wall_middle(point, outward, LEDGE_PROBE_Z_MM), direction, True)
    reach = -(DESIGN_GAP_MM + DESIGN_WALL_MM / 2.0 + low)
    in_ledge = vector(point, 0.0).sub(direction * (DESIGN_LEDGE_UNDER_PCB_MM / 2.0))
    _bottom, top = run_through(tray, in_ledge, UP, True)
    texts = [
        figures.check("under the PCB", reach, DESIGN_LEDGE_UNDER_PCB_MM, 1),
        figures.check("wide", reach + DESIGN_GAP_MM, DESIGN_LEDGE_WIDTH_MM, 1),
        figures.check("top z", top, DESIGN_LEDGE_TOP_Z_MM, 1),
    ]
    return f"ledge:      {where}: {', '.join(texts)}"


def measure_block(tray, right, figures):
    _south, _direction, normal = design_slant_frame(right)
    point = slant_place(right, SLANT_PROBE_ALONG_MM, 0.0, LEDGE_PROBE_Z_MM)
    low, high = run_through(tray, point, vector(normal), True)
    in_block = slant_place(right, SLANT_PROBE_ALONG_MM, -1.6, 0.0)
    _bottom, top = run_through(tray, in_block, UP, True)
    texts = [
        figures.check("thick", high - low, DESIGN_JOINT_BLOCK_THICKNESS_MM, 1),
        figures.check("outer face out of the slant", high, DESIGN_JOINT_FACE_OUT_OF_SLANT_MM, 1),
        figures.check("top z", top, DESIGN_LEDGE_TOP_Z_MM, 1),
    ]
    return f"block:      at {SLANT_PROBE_ALONG_MM} along the slant: {', '.join(texts)}"


def vertical_cylinders(tray, radius):
    """{rounded (x, y): (x, y, z low, z high)} of the vertical
    cylindrical faces of the given radius, merged per axis."""
    found = {}
    for face in tray.Faces:
        surface = face.Surface
        if not isinstance(surface, Part.Cylinder) or abs(surface.Radius - radius) > 1e-6:
            continue
        if abs(abs(surface.Axis.z) - 1.0) > 1e-9:
            continue
        key = (round(surface.Center.x, 3), round(surface.Center.y, 3))
        box = face.BoundBox
        low, high = box.ZMin, box.ZMax
        if key in found:
            low, high = min(low, found[key][2]), max(high, found[key][3])
        found[key] = (surface.Center.x, surface.Center.y, low, high)
    return found


def nearest_found(found, target, what):
    """The one found (x, y, ...) entry within 0.01 of target."""
    near = [entry for entry in found.values() if math.dist(entry[:2], target) < 0.01]
    if len(near) != 1:
        raise SystemExit(f"error: found {len(near)} {what}s at {target}, expected one")
    return near[0]


def measure_standoffs(tray, right, figures):
    bores = vertical_cylinders(tray, DESIGN_STANDOFF_BORE_MM / 2.0)
    posts = vertical_cylinders(tray, DESIGN_STANDOFF_DIAMETER_MM / 2.0)
    drills = [half_point(drill, right) for drill in DESIGN_MOUNTING_DRILLS_MM]
    if len(bores) != len(drills) or len(posts) != len(drills):
        raise SystemExit(
            f"error: {len(bores)} bores and {len(posts)} standoffs for {len(drills)} drills"
        )
    worst = 0.0
    bore_lows, bore_highs, post_highs, floors = [], [], [], []
    for drill in drills:
        bore = nearest_found(bores, drill, "bore")
        post = nearest_found(posts, drill, "standoff")
        worst = max(worst, math.dist(bore[:2], drill), math.dist(post[:2], drill))
        bore_lows.append(bore[2])
        bore_highs.append(bore[3])
        post_highs.append(post[3])
        low, high = run_through(tray, App.Vector(drill[0], drill[1], -0.6), UP, True)
        floors.append(high - low)
    texts = [
        f"{len(drills)} on DESIGN.md's drills within {worst:.6f}",
        figures.check("bore bottoms z", max(bore_lows, key=abs), 0.0, 1),
        figures.check("tops z", min(post_highs), DESIGN_LEDGE_TOP_Z_MM, 1),
        figures.check("plastic under the inserts", min(floors), DESIGN_FLOOR_MM, 1),
        f"{DESIGN_STANDOFF_DIAMETER_MM} across, {DESIGN_STANDOFF_BORE_MM} bores (by radius)",
    ]
    return f"standoffs:  {', '.join(texts)}"


def joint_face(tray, right):
    """The planar face of the tray whose outward normal is the slant's,
    farthest out: (face, its distance out of DESIGN.md's slant)."""
    south, _direction, normal = design_slant_frame(right)
    candidates = []
    for face in tray.Faces:
        if not isinstance(face.Surface, Part.Plane):
            continue
        face_normal = face.normalAt(*face.Surface.parameter(face.CenterOfMass))
        if face_normal.x * normal[0] + face_normal.y * normal[1] < 1.0 - 1e-9:
            continue
        point = face.Vertexes[0].Point
        offset = (point.x - south[0]) * normal[0] + (point.y - south[1]) * normal[1]
        candidates.append((offset, face))
    if not candidates:
        raise SystemExit("error: the tray has no face along the slant")
    offset, face = max(candidates, key=lambda candidate: candidate[0])
    return face, offset


def measure_joint_face(tray, right, figures):
    face, offset = joint_face(tray, right)
    face_normal = face.normalAt(*face.Surface.parameter(face.CenterOfMass))
    angle = math.degrees(math.atan2(abs(face_normal.y), abs(face_normal.x)))
    south, direction, _normal = design_slant_frame(right)
    alongs = [
        (vertex.Point.x - south[0]) * direction[0] + (vertex.Point.y - south[1]) * direction[1]
        for vertex in face.Vertexes
    ]
    box = face.BoundBox
    holes = len(face.Wires) - 1
    texts = [
        figures.check("out of the slant", offset, DESIGN_JOINT_FACE_OUT_OF_SLANT_MM, 1),
        figures.check("degrees from north", angle, DESIGN_SLANT_ANGLE_FROM_NORTH_DEGREES, 2),
        f"flat from {min(alongs):.4f} to {max(alongs):.4f} along the slant, z {box.ZMin:.3f} to "
        f"{box.ZMax:.3f}, {holes} openings",
    ]
    if holes != len(DESIGN_DOWEL_PIN_ALONGS_MM):
        raise SystemExit(f"error: the joint face has {holes} openings, expected the pin holes")
    lowest_boss = min(DESIGN_DOWEL_PIN_ALONGS_MM) - DESIGN_DOWEL_BOSS_ACROSS_MM / 2.0
    highest_boss = max(DESIGN_DOWEL_PIN_ALONGS_MM) + DESIGN_DOWEL_BOSS_ACROSS_MM / 2.0
    if lowest_boss < min(alongs) or highest_boss > max(alongs):
        raise SystemExit(
            f"error: the bosses span {lowest_boss} to {highest_boss} along the slant, past the "
            "joint face's flat part"
        )
    return f"joint face: {', '.join(texts)}, the bosses' {lowest_boss} to {highest_boss} on it"


def horizontal_cylinders(tray, radius, axis):
    """Axis points of the cylindrical faces of the given radius whose
    axis lies along the horizontal unit axis, one per axis line."""
    found = []
    for face in tray.Faces:
        surface = face.Surface
        if not isinstance(surface, Part.Cylinder) or abs(surface.Radius - radius) > 1e-6:
            continue
        if abs(abs(surface.Axis.dot(axis)) - 1.0) > 1e-9:
            continue
        center = surface.Center
        side = App.Vector(-axis.y, axis.x, 0.0)  # square to the axis, so it tells axes apart
        key = (center.dot(side), center.z)
        if all(math.dist(key, other) > 1e-3 for other, _center in found):
            found.append((key, center))
    return [center for _key, center in found]


def sample_depths(start, end):
    """Depths from start to end, HOLE_SAMPLE_STEP_MM apart."""
    count = int((end - start) / HOLE_SAMPLE_STEP_MM)
    return [start + index * HOLE_SAMPLE_STEP_MM for index in range(count + 1)]


def least_plastic_over(tray, mouth, axis, depths):
    """(the least plastic over a horizontal hole, the depth from its
    mouth along the unit axis where it lies) over the given depths."""
    least = (math.inf, None)
    for depth in depths:
        point = mouth.add(axis * depth)
        _down, up = run_through(tray, point, UP, False)
        _low, high = run_through(tray, point.add(UP * (up + 0.01)), UP, True)
        least = min(least, (high + 0.01, depth))
    return least


def flat_top(tray, point, side):
    """(how far a flat-topped teardrop's top lies above the point on its
    axis, the flat's width, measured along side just under it)."""
    _down, up = run_through(tray, point, UP, False)
    low, high = run_through(tray, point.add(UP * (up - 0.001)), side, False)
    return up, high - low - 0.002


def hole_design(right, pin_hole_diameter):
    """(diameter, flat width, plastic over) DESIGN.md gives the half's
    dowel holes, or for a test print's pin_hole_diameter that diameter
    and no other figures."""
    if pin_hole_diameter is None:
        return (
            DESIGN_DOWEL_HOLE_DIAMETER_MM[right],
            DESIGN_DOWEL_HOLE_FLAT_MM[right],
            DESIGN_PLASTIC_OVER_DOWEL_HOLES_MM[right],
        )
    return (pin_hole_diameter, None, None)


def check_or_report(figures, label, measured, stated, decimals):
    if stated is None:
        return figures.report(label, measured, decimals)
    return figures.check(label, measured, stated, decimals)


def measure_pin_hole(tray, right, along, radius, design, figures):
    """The figures of the dowel hole found at `along`: its depth and
    diameter, the boss behind it, its flat top, the plastic over it and
    its mouth's lead-in."""
    _south, direction, normal = design_slant_frame(right)
    outward = vector(normal)
    face = DESIGN_JOINT_FACE_OUT_OF_SLANT_MM
    z = DESIGN_DOWEL_PIN_Z_MM
    diameter, flat_stated, over_stated = design
    bottom_low, _ = run_through(tray, slant_place(right, along, face - 1.0, z), outward, False)
    bottom = face - 1.0 + bottom_low
    back_low, _ = run_through(tray, slant_place(right, along, bottom - 0.1, z), outward, True)
    boss_end = bottom - 0.1 + back_low
    inside = slant_place(right, along, (face + bottom) / 2.0, z)
    across_low, across_high = run_through(tray, inside, vector(direction), False)
    top, flat = flat_top(tray, inside, vector(direction))
    mouth = slant_place(right, along, face, z)
    depths = sample_depths(0.1, face - bottom - 0.1)
    over, where = least_plastic_over(tray, mouth, outward * -1.0, depths)
    at_face = slant_place(right, along, face - 0.05, z)
    face_low, face_high = run_through(tray, at_face, vector(direction), False)
    widening = (face_high - face_low) / 2.0 - radius
    lead_in = widening + 0.05 if widening > 1e-6 else 0.0
    over_text = check_or_report(figures, "least plastic over it", over, over_stated, 2)
    return [
        figures.check("deep", face - bottom, DESIGN_DOWEL_HOLE_DEPTH_MM[right], 1),
        check_or_report(figures, "across", across_high - across_low, diameter, 1),
        figures.check(
            "plastic behind", bottom - boss_end, DESIGN_DOWEL_BOSS_BEHIND_HOLE_MM[right], 1
        ),
        figures.check("boss reach", face - boss_end, DESIGN_DOWEL_BOSS_REACH_MM[right], 1),
        f"top {top:.3f} above the axis ({top / radius:.4f} radii)",
        check_or_report(figures, "flat top", flat, flat_stated, 2),
        f"{over_text} (at {where:.2f} in)",
        figures.check("lead-in", lead_in, DESIGN_DOWEL_HOLE_LEAD_IN_MM[right], 1),
    ]


def measure_pin_holes(tray, right, radius, design, figures):
    south, direction, normal = design_slant_frame(right)
    centers = horizontal_cylinders(tray, radius, vector(normal))
    if len(centers) != len(DESIGN_DOWEL_PIN_ALONGS_MM):
        raise SystemExit(f"error: found {len(centers)} pin holes of radius {radius}, expected two")
    alongs = sorted(
        (center.x - south[0]) * direction[0] + (center.y - south[1]) * direction[1]
        for center in centers
    )
    heights = [center.z for center in centers]
    lines = []
    for along, stated in zip(alongs, DESIGN_DOWEL_PIN_ALONGS_MM):
        texts = [figures.check("at", along, stated, 1)]
        texts.extend(measure_pin_hole(tray, right, along, radius, design, figures))
        lines.append(f"pin hole:   {', '.join(texts)}")
    texts = [
        figures.check("pin holes apart", alongs[1] - alongs[0], DESIGN_DOWEL_PIN_SPACING_MM, 1),
        figures.check(
            "axes z",
            max(heights, key=lambda height: abs(height - DESIGN_DOWEL_PIN_Z_MM)),
            DESIGN_DOWEL_PIN_Z_MM,
            1,
        ),
        "axes square to the joint face (by their direction)",
    ]
    lines.append(f"pin holes:  {', '.join(texts)}")
    return lines


def measure_magnet_slots(tray, right, figures):
    _south, direction, normal = design_slant_frame(right)
    face = DESIGN_JOINT_FACE_OUT_OF_SLANT_MM
    slot_middle = face - DESIGN_MAGNET_SKIN_MM - DESIGN_MAGNET_SLOT_MM[1] / 2.0
    block_inner_face = face - DESIGN_JOINT_BLOCK_THICKNESS_MM
    in_floor_z = DESIGN_MAGNET_SLOT_BOTTOM_Z_MM / 2.0
    lines = []
    for stated in DESIGN_MAGNET_ALONGS_MM:
        point = slant_place(right, stated, slot_middle, LEDGE_PROBE_Z_MM)
        along_low, along_high = run_through(tray, point, vector(direction), False)
        inward_low, face_high = run_through(tray, point, vector(normal), False)
        if slot_middle + inward_low > block_inner_face - 1.0:
            raise SystemExit(f"error: the magnet slot at {stated} is not open toward the cavity")
        recess = slant_place(right, stated, slot_middle, in_floor_z)
        across_low, across_high = run_through(tray, recess, vector(normal), False)
        bottom, _top = run_through(tray, point, UP, False)
        cutback = slant_place(right, stated, face - 0.05, WALL_PROBE_Z_MM)
        wall_low, wall_high = run_through(tray, cutback, vector(normal), True)
        texts = [
            figures.check("at", stated + (along_low + along_high) / 2.0, stated, 2),
            figures.check("long", along_high - along_low, DESIGN_MAGNET_SLOT_MM[0], 1),
            figures.check(
                "across in the floor", across_high - across_low, DESIGN_MAGNET_SLOT_MM[1], 1
            ),
            figures.check("skin", face - (slot_middle + face_high), DESIGN_MAGNET_SKIN_MM, 1),
            figures.check("bottom z", point.z + bottom, DESIGN_MAGNET_SLOT_BOTTOM_Z_MM, 1),
            "open toward the cavity from the block's inner face",
            figures.check(
                "wall left above the block", wall_high - wall_low, DESIGN_MAGNET_SKIN_MM, 1
            ),
        ]
        lines.append(f"magnet:     {', '.join(texts)}")
    return lines


def measure_parking_hole(tray, right, figures):
    inward = vector(half_vector((-1.0, 0.0), right))
    across = App.Vector(0, 1, 0)
    face_x = DESIGN_THUMB_EAST_EDGE_X_MM + DESIGN_GAP_MM + DESIGN_WALL_MM
    mouth_plan = half_point((face_x, DESIGN_PARKING_HOLE_Y_MM), right)
    mouth = vector(mouth_plan, DESIGN_PARKING_HOLE_Z_MM)
    _, to_bottom = run_through(tray, mouth.add(inward * 0.5), inward, False)
    depth = to_bottom + 0.5
    middle = mouth.add(inward * (depth / 2.0))
    across_low, across_high = run_through(tray, middle, across, False)
    down, _up = run_through(tray, middle, UP, False)
    top, flat = flat_top(tray, middle, across)
    back_low, back_high = run_through(tray, mouth.add(inward * (depth + 0.1)), inward, True)
    over, where = least_plastic_over(tray, mouth, inward, sample_depths(0.1, depth - 0.1))
    # The boss's own width 1.0 short of the hole's bottom: nearer the
    # mouth it merges with the lower dowel boss.
    beside = mouth.add(inward * (depth - 1.0)).add(
        UP * (DESIGN_PARKING_HOLE_DIAMETER_MM / 2.0 + 0.5)
    )
    boss_low, boss_high = run_through(tray, beside, across, True)
    _boss_bottom, boss_top = run_through(tray, beside, UP, True)
    over_text = figures.check("least plastic over it", over, DESIGN_PLASTIC_OVER_PARKING_HOLE_MM, 2)
    texts = [
        figures.check("deep", depth, DESIGN_PARKING_HOLE_DEPTH_MM, 1),
        figures.check("across", across_high - across_low, DESIGN_PARKING_HOLE_DIAMETER_MM, 1),
        figures.check(
            "at y", middle.y + (across_low + across_high) / 2.0, DESIGN_PARKING_HOLE_Y_MM, 1
        ),
        figures.check(
            "axis z",
            middle.z + down + DESIGN_PARKING_HOLE_DIAMETER_MM / 2.0,
            DESIGN_PARKING_HOLE_Z_MM,
            1,
        ),
        f"top {top:.3f} above the axis",
        figures.check("flat top", flat, DESIGN_PARKING_HOLE_FLAT_MM, 2),
        f"{over_text} (at {where:.2f} in)",
        figures.check(
            "boss behind the bottom",
            back_high - back_low,
            DESIGN_PARKING_BOSS_BEHIND_HOLE_MM,
            1,
        ),
        figures.check("boss across", boss_high - boss_low, DESIGN_PARKING_BOSS_ACROSS_MM, 1),
        figures.check("boss top z", beside.z + boss_top, DESIGN_LEDGE_TOP_Z_MM, 1),
    ]
    return f"parking:    {', '.join(texts)}"


def measure_joint_face_chamfer(tray, right, figures):
    """The joint face's bottom edge chamfer at the slant's middle: how
    far it reaches in along the bed and up the face."""
    _south, _direction, normal = design_slant_frame(right)
    face = DESIGN_JOINT_FACE_OUT_OF_SLANT_MM
    bed = DESIGN_FLOOR_UNDERSIDE_Z_MM
    on_bed = slant_place(right, SLANT_PROBE_ALONG_MM, face - 1.0, bed + 0.001)
    _low, high = run_through(tray, on_bed, vector(normal), True)
    on_face = slant_place(right, SLANT_PROBE_ALONG_MM, face - 0.001, bed + 1.0)
    low, _high = run_through(tray, on_face, UP, True)
    size = DESIGN_JOINT_FACE_BOTTOM_CHAMFER_MM
    texts = [
        figures.check("in along the bed", 1.0 - high + 0.001, size, 1),
        figures.check("up the face", 1.0 + low + 0.001, size, 1),
    ]
    return (
        f"chamfer:    the joint face's bottom edge at {SLANT_PROBE_ALONG_MM} along the slant: "
        f"{', '.join(texts)}"
    )


def half_sockets(right):
    """(key, polygon) of every socket polygon of the given half in its
    own frame: on the right half the left footprint at the mirrored key
    center (layout.py's module docstring)."""
    for name, center in layout.KEY_CENTERS_MM.items():
        placed = layout.mirror_for_right_half(center) if right else center
        for polygon in layout.socket_polygons(placed):
            yield name, polygon


def measure_socket_clearance(tray, right, figures):
    """Every socket of the half, a prism from its bottom to the PCB's
    underside, against the exported tray itself: the end to end check
    that the cuts landed where the sockets are, mirroring included."""
    closest = (math.inf, "nothing")
    count = 0
    for name, polygon in half_sockets(right):
        points = [App.Vector(x, y, DESIGN_SOCKET_BOTTOM_Z_MM) for x, y in polygon]
        prism = Part.Face(Part.makePolygon(points + [points[0]])).extrude(
            UP * (DESIGN_LEDGE_TOP_Z_MM - DESIGN_SOCKET_BOTTOM_Z_MM)
        )
        distance = prism.distToShape(tray)[0]
        count += 1
        if distance < closest[0]:
            closest = (distance, name)
    if closest[0] < DESIGN_LEAST_SOCKET_CLEARANCE_MM - 1e-6:
        raise SystemExit(
            f"error: {closest[1]}'s socket comes {closest[0]:.4f} from the tray, DESIGN.md "
            f"keeps {DESIGN_LEAST_SOCKET_CLEARANCE_MM}"
        )
    text = figures.check("least clearance", closest[0], DESIGN_LEAST_SOCKET_CLEARANCE_MM, 1)
    return (
        f"sockets:    {count} socket polygons of {len(layout.KEY_CENTERS_MM)} keys (z "
        f"{DESIGN_SOCKET_BOTTOM_Z_MM} to {DESIGN_LEDGE_TOP_Z_MM}) against the tray as cut: "
        f"{text}, at {closest[1]}'s"
    )


def measure(tray, right, pin_hole_radius, design):
    """Print every measured figure against DESIGN.md's, stopping on any
    that is off."""
    figures = Figures()
    lines = [measure_outside(tray, figures)]
    lines.extend(measure_walls(tray, right, figures))
    lines.append(measure_floor(tray, right, figures))
    lines.append(measure_ledge(tray, right, figures))
    lines.append(measure_block(tray, right, figures))
    lines.append(measure_standoffs(tray, right, figures))
    lines.append(measure_joint_face(tray, right, figures))
    lines.append(measure_joint_face_chamfer(tray, right, figures))
    lines.extend(measure_pin_holes(tray, right, pin_hole_radius, design, figures))
    lines.extend(measure_magnet_slots(tray, right, figures))
    lines.append(measure_parking_hole(tray, right, figures))
    lines.append(measure_socket_clearance(tray, right, figures))
    for line in lines:
        print(line)
    figures.stop_on_problems()


# The joined check.


def design_slant_angle_degrees():
    (south_x, south_y), (north_x, north_y) = DESIGN_SLANT_ENDS_MM
    return math.degrees(math.atan2(south_x - north_x, north_y - south_y))


def joined_pair(left, right):
    """The left and right trays (each as exported) turned as DESIGN.md
    joins them: the left one clockwise and the right one anticlockwise
    by the slant's angle about their slant's south ends, so both slants
    run north, then the right one moved so its outer slant face lies on
    the left one's and the slants' south ends are level. Returns (left,
    right, the face's x)."""
    angle = design_slant_angle_degrees()
    left_south, _, _ = design_slant_frame(False)
    right_south, _, _ = design_slant_frame(True)
    left_turned = left.copy()
    left_turned.rotate(vector(left_south), UP, -angle)
    right_turned = right.copy()
    right_turned.rotate(vector(right_south), UP, angle)
    face_x = left_south[0] + DESIGN_JOINT_FACE_OUT_OF_SLANT_MM
    shift = App.Vector(
        face_x - (right_south[0] - DESIGN_JOINT_FACE_OUT_OF_SLANT_MM),
        left_south[1] - right_south[1],
        0.0,
    )
    right_turned.translate(shift)
    return left_turned, right_turned, face_x


def outermost_face_x(tray, sign):
    """The x of the planar face with outward normal (sign, 0, 0) lying
    farthest that way."""
    xs = []
    for face in tray.Faces:
        if not isinstance(face.Surface, Part.Plane):
            continue
        normal = face.normalAt(*face.Surface.parameter(face.CenterOfMass))
        if normal.x * sign > 1.0 - 1e-9:
            xs.append(face.Vertexes[0].Point.x)
    return max(xs) if sign > 0 else min(xs)


def pin_axes_along_x(tray, radius):
    """(y, z) of the pin holes' axes, running along x once joined."""
    centers = horizontal_cylinders(tray, radius, App.Vector(1.0, 0.0, 0.0))
    return sorted((center.y, center.z) for center in centers)


def joined_contact_problems(left_joined, right_joined, face_x):
    """(problems, overlap, apart) of the joined trays, which must touch
    without overlapping, both joint faces at face_x."""
    overlap = left_joined.common(right_joined).Volume
    apart = left_joined.distToShape(right_joined)[0]
    left_face = outermost_face_x(left_joined, 1.0)
    right_face = outermost_face_x(right_joined, -1.0)
    problems = []
    if overlap > JOINED_OVERLAP_TOLERANCE_MM3:
        problems.append(f"the joined trays overlap by {overlap:.4f} mm3")
    if apart > JOINED_TOLERANCE_MM:
        problems.append(f"the joined trays stand {apart:.6f} apart")
    if max(abs(left_face - face_x), abs(right_face - face_x)) > JOINED_TOLERANCE_MM:
        problems.append(
            f"the joint faces lie at x {left_face:.6f} and {right_face:.6f}, not {face_x:.6f}"
        )
    return problems, overlap, apart


def joined_pin_channels(left_joined, right_joined, face_x, radii, figures):
    """(problems, how far apart the pin holes' axes lie across the
    joint, the channels' text): each left hole coaxial with its right
    one, the two a channel at least the pin plus DESIGN.md's margin
    long."""
    left_axes = pin_axes_along_x(left_joined, radii[0])
    right_axes = pin_axes_along_x(right_joined, radii[1])
    if len(left_axes) != 2 or len(right_axes) != 2:
        raise SystemExit(f"error: joined: {len(left_axes)} and {len(right_axes)} pin holes found")
    axis_offset = max(math.dist(first, second) for first, second in zip(left_axes, right_axes))
    problems = []
    if axis_offset > SAME_PLACE_MM:
        problems.append(f"the pin holes' axes lie {axis_offset:.6f} apart across the joint")
    both = Part.makeCompound([left_joined, right_joined])
    channels = []
    for y, z in left_axes:
        low, high = run_through(both, App.Vector(face_x, y, z), App.Vector(1, 0, 0), False)
        channels.append(high - low)
    text = figures.at_least(
        "pin channels",
        min(channels),
        DESIGN_DOWEL_PIN_LENGTH_MM + DESIGN_PIN_CHANNEL_MARGIN_MM,
        1,
    )
    return problems, axis_offset, text


def joined_magnet_slots(left_joined, right_joined, face_x, figures):
    """(problems, how far apart the slots lie along the joint, the
    gap's text): each left slot facing its right one, DESIGN.md's gap
    between the opposing magnets."""
    slot_offset = 0.0
    gaps = []
    left_south, _, _ = design_slant_frame(False)
    slot_middle = DESIGN_MAGNET_SKIN_MM + DESIGN_MAGNET_SLOT_MM[1] / 2.0
    for along in DESIGN_MAGNET_ALONGS_MM:
        y = left_south[1] + along
        runs = []
        for side, tray in ((-1.0, left_joined), (1.0, right_joined)):
            point = App.Vector(face_x + side * slot_middle, y, LEDGE_PROBE_Z_MM)
            runs.append(
                (
                    run_through(tray, point, App.Vector(0, 1, 0), False),
                    run_through(tray, point, App.Vector(1, 0, 0), False),
                    point,
                )
            )
        (left_along, left_across, left_point), (right_along, right_across, right_point) = runs
        slot_offset = max(
            slot_offset,
            abs(left_along[0] - right_along[0]),
            abs(left_along[1] - right_along[1]),
        )
        gaps.append((right_point.x + right_across[0]) - (left_point.x + left_across[1]))
    text = figures.check(
        "between opposing magnet slots",
        max(gaps, key=lambda gap: abs(gap - DESIGN_MAGNETS_APART_JOINED_MM)),
        DESIGN_MAGNETS_APART_JOINED_MM,
        1,
    )
    problems = []
    if slot_offset > SAME_PLACE_MM:
        problems.append(f"the magnet slots lie {slot_offset:.6f} apart along the joint")
    return problems, slot_offset, text


def check_joined(left, right, left_radius, right_radius):
    """Join the trays and check them: no overlap, the faces touching,
    the pin holes coaxial in a channel longer than the pin, the magnet
    slots facing each other with DESIGN.md's gap. Returns the line to
    print."""
    left_joined, right_joined, face_x = joined_pair(left, right)
    figures = Figures()
    problems, overlap, apart = joined_contact_problems(left_joined, right_joined, face_x)
    pin_problems, axis_offset, channel_text = joined_pin_channels(
        left_joined, right_joined, face_x, (left_radius, right_radius), figures
    )
    slot_problems, slot_offset, gap_text = joined_magnet_slots(
        left_joined, right_joined, face_x, figures
    )
    problems.extend(pin_problems + slot_problems + figures.problems)
    if problems:
        raise SystemExit("error: joined:\n  " + "\n  ".join(problems))
    return (
        f"joined:     each half turned {design_slant_angle_degrees():.4f} degrees, the outer slant "
        f"faces both at x {face_x:.3f}: overlap {overlap:.6f} mm3, apart {apart:.6f}, pin hole "
        f"axes {axis_offset:.6f} apart, {channel_text}, magnet slots {slot_offset:.6f} apart "
        f"along the joint, {gap_text}"
    )


# The build.


def half_tray(right, pin_hole_diameter):
    """(build, the tray on its half as exported)."""
    build = build_tray(right, pin_hole_diameter)
    solid = mirror_for_right_half(build.solid) if right else build.solid
    return build, solid


def print_build(build):
    print(f"tray:       {'right' if build.right else 'left'} half, gap {layout.TRAY_GAP_MM}, wall "
          f"{layout.TRAY_WALL_MM}, floor {layout.TRAY_FLOOR_MM}, rim at z {layout.TRAY_RIM_Z_MM}, "
          f"volume {build.solid.Volume / 1000.0:.3f} cm3")
    print(f"corners:    every bend {build.corner_radius - layout.TRAY_WALL_MM:.2f} inside / "
          f"{build.corner_radius:.2f} outside, concentric")
    for label, removed in build.cuts:
        print(f"cut:        {label}, {removed:.3f} mm3")
    for label in build.skipped_cuts:
        print(f"skipped:    {label}, nothing left to remove")
    lead_in = f"{build.pin_hole_lead_in} lead-in" if build.pin_hole_lead_in else "no lead-in"
    print(f"pins:       holes {build.pin_hole_diameter} across "
          f"({'slip' if build.right else 'snug'} fit), {build.pin_hole_depth} deep, {lead_in}")


def main():
    arguments = parse_arguments(script_arguments(sys.argv))
    right = arguments.right
    build, tray = half_tray(right, arguments.pin_hole_diameter)
    print_build(build)
    if right:
        print(f"half:       right, mirrored across x = {layout.RIGHT_HALF_MIRROR_X_MM:.3f} (the "
              "lines above are its build in the left half's frame, the lines below the right "
              "half's)")
    else:
        print("half:       left")
    design = hole_design(right, arguments.pin_hole_diameter)
    measure(tray, right, build.pin_hole_diameter / 2.0, design)
    _other_build, other = half_tray(not right, None)
    left, right_tray = (other, tray) if right else (tray, other)
    left_diameter = layout.dowel_hole_diameter(False)
    right_diameter = layout.dowel_hole_diameter(True)
    if right:
        right_diameter = build.pin_hole_diameter
    else:
        left_diameter = build.pin_hole_diameter
    print(check_joined(left, right_tray, left_diameter / 2.0, right_diameter / 2.0))
    mesh = export_stl(tray, arguments.stl_file)
    check_closed_mesh(arguments.stl_file)
    print(f"wrote:      {arguments.stl_file} ({mesh.CountFacets} facets), floor on the bed, one "
          "closed manifold shell")


run_and_exit(main)
