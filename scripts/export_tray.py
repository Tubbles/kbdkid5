"""Export a half's 3D-printable tray shell and joint (STL) from the layout.

tray_shape.py builds the tray (see its docstring): walls, floor, ledge
and joint block, standoffs bored for M2 heat-set inserts, the dowel pin
and parking bosses with their fills, the ledge cut-aways and the
sockets' cuts as layout.py gives them, the parts' mounts, the magnet
slots, the flat-topped teardrop pin holes and parking hole, and the
joint face's bottom chamfer. This script mirrors it for the right half,
measures it and prints what it found against DESIGN.md's figures, which
it transcribes itself (the DESIGN_* constants below), never against the
constants the tray is built from: the outside's size, the walls, the
floor, the ledge and the joint block, the standoffs and their bores,
the joint face's angle, place and bottom chamfer, the pin holes (depth,
diameter, the plastic behind and over them, the flat top, the lead-in),
the magnet slots, the parking hole, the sockets' clearance from the
tray as built, and the mounts: the USB shell's channel and the USB
window, the hold-down bar on its posts, the snap hook (its blade,
slots, bed chamfers, lip, and from what was measured the strain at its
root and its free end's swing, which must stay inside its room as
printed whatever is overridden), the east ribs, the solder grooves, the pry recess, the
lever slot and the cradle, the reset pin hole and the back wall, the battery
header's pocket and the battery's ribs, and that the PCB connector's
zone (as printed) and layout.py's wire rooms hold no plastic. Then it builds the
other half too and joins them as DESIGN.md describes, each half turned
17.74 degrees so the outer slant faces touch, and checks that the trays
do not overlap, that the pin holes line up into one channel at least
1.0 longer than the pin, and that the magnet slots face each other.
Last, it writes the tray as built, floor on the bed, as one closed mesh.

Runs headless under FreeCAD's console interpreter (see
freecad_common.py for the freecadcmd quirks that shape the
invocation):

    freecadcmd scripts/export_tray.py --pass <tray.stl> [right] [key=value ...]

The word "right" makes the right half: the tray built with that half's
socket cuts and its slip fit pin holes, mirrored across the layout's
right-half mirror line. The key=value words (USAGE lists them) override
a fit for a test print: pin_hole_diameter the half's pin hole fit
(layout.py: the left half's snug, the right half's slip, as modelled),
the others the mounts' fits that wait on a caliper or a test print
(layout.MountFits).
A measured figure that is an override is then checked against it
instead of DESIGN.md's, and the figures that follow from it (the pin
holes' flat top and the plastic over them, the hook's top, strain and
swing) are only printed. The other half, built for the joined check, keeps
the defaults.
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
# The parts' mounts (DESIGN.md, "Parts in the tray"), the left half's,
# placed on either half by half_point(). The nice!nano's mounts follow
# the board, so they are given from its edges, and the board from its
# fixed corner (the west edge and the USB end), its size DESIGN.md's
# unless a key=value word overrides it.
DESIGN_PRINT_SWELLING_PER_SIDE_MM = 0.2  # a 45 degree face: this times the square root of 2
DESIGN_NANO_WEST_X_MM = 0.9
DESIGN_NANO_USB_END_Y_MM = 75.316
DESIGN_NANO_SIZE_MM = (18.0, 33.3)  # along x, along y
DESIGN_NANO_TOP_Z_MM = 1.6
DESIGN_SHELL_WIDTH_MM = 8.94
DESIGN_SHELL_TOP_Z_MM = 3.16
DESIGN_SHELL_PAST_BOARD_MM = 0.87  # the shell's mouth past the board's USB end
DESIGN_WEST_LEDGE_FACE_X_MM = 0.6
DESIGN_NORTH_EDGES_Y_MM = {"nice!nano": 75.486, "power switch": 80.248, "reset button": 82.629}
DESIGN_USB_WINDOW_MM = (10.5, 4.5)  # along x, along z
DESIGN_USB_WINDOW_CENTER_Z_MM = 1.58
DESIGN_USB_WINDOW_CORNER_RADIUS_MM = 1.95
DESIGN_USB_WINDOW_CHAMFER_MM = {"outer": 0.2, "inner": 0.0}
DESIGN_NANO_END_GAP_MM = 0.25  # at each end of the board, to the bar's posts and the hook
DESIGN_NANO_BAR_OPENING_MM = 9.44
DESIGN_NANO_BAR_POST_WIDTH_MM = 1.0
DESIGN_NANO_BAR_CLEARANCE_MM = 0.1  # over the shell's top, as printed
DESIGN_NANO_BAR_HEIGHT_MM = 1.5
DESIGN_NANO_BAR_DEPTH_MM = 0.62  # to the shell's mouth
DESIGN_USB_CHANNEL_PAST_MOUTH_MM = 0.25  # its width the bar's opening, its top the bar's underside
DESIGN_HOOK_ROOT_X_MM = DESIGN_WEST_LEDGE_FACE_X_MM
DESIGN_HOOK_BENDING_LENGTH_MM = 11.0
DESIGN_HOOK_LIP_X_MM = (11.6, 14.4)
DESIGN_HOOK_BLADE_THICKNESS_MM = 0.8
DESIGN_HOOK_LIP_REACH_MM = 0.8  # onto the board
DESIGN_HOOK_LIP_OVER_EDGE_MM = 0.1  # over the board's top edge, as printed
DESIGN_HOOK_SIDES_DEGREES = 45.0
DESIGN_HOOK_TOP_Z_MM = 3.83
DESIGN_HOOK_SLOTS_MM = {"south": 2.0, "north": 0.8, "end": 0.8}  # as modelled
DESIGN_HOOK_BED_CHAMFERS_MM = {"slots": 0.4, "blade": 0.2}
DESIGN_HOOK_STRAIN_PERCENT = 1.61  # as printed
DESIGN_HOOK_SWING_MM = 1.50  # the free end's, as printed
DESIGN_HOOK_MAXIMUM_STRAIN_PERCENT = 2.0
DESIGN_HOOK_UNDER_SOCKET_MM = 2.15
DESIGN_NANO_RIB_FROM_BOARD_MM = 0.2  # the ribs' face from the board's east edge
DESIGN_NANO_RIB_MM = (0.6, 3.0, 1.0)  # thick, long, tall
DESIGN_NANO_RIB_FROM_BOARD_ENDS_MM = 2.0
DESIGN_NANO_GROOVE_DEPTH_MM = 0.4
# Each groove's (x from the board's west edge, or from its east edge for
# the east row, or either side of its center line for the tab slots, y
# from the board's USB end), on both halves seen from above, since the
# right half's nice!nano lies the same side up.
DESIGN_NANO_ROW_GROOVES_MM = ((0.195, 2.555), (0.46, 32.965))
DESIGN_NANO_P1_GROOVE_MM = ((2.735, 10.175), (25.685, 27.915))
DESIGN_NANO_TAB_GROOVES_MM = ((4.54, 6.215), (0.02, 6.42))
# The pry recess beside and under the board's east edge north of the
# battery: its reach from the board's edge and its width as printed, its
# place along y as modelled.
DESIGN_NANO_PRY_RECESS_ACROSS_PRINTED_MM = 4.1
DESIGN_NANO_PRY_RECESS_Y_MM = (61.43, 65.93)
DESIGN_NANO_PRY_RECESS_UNDER_BOARD_PRINTED_MM = 1.0
DESIGN_NANO_PRY_RECESS_BESIDE_BOARD_PRINTED_MM = 4.0
DESIGN_NANO_PRY_RECESS_DEPTH_MM = 0.8
DESIGN_NANO_PRY_RECESS_FLOOR_UNDER_MM = 0.4  # as modelled
DESIGN_NANO_PRY_TOOL_ROOM_PRINTED_MM = 0.6  # the bottom raised by the swelling
DESIGN_POWER_SWITCH_CENTER_X_MM = 47.149
DESIGN_LEVER_SLOT_MM = (4.0, 2.0)  # along x, along z
DESIGN_LEVER_SLOT_CENTER_Z_MM = 1.95
DESIGN_CRADLE_OPENING_MM = 9.2
DESIGN_CRADLE_DEPTH_MM = 3.9  # from the wall's inner face to the back arms
DESIGN_CRADLE_PIN_SLOT_MM = 6.0
DESIGN_CRADLE_END_MM = 1.2
DESIGN_CRADLE_ARM_MM = 0.8
DESIGN_CRADLE_TOP_Z_MM = 3.0
DESIGN_RESET_CENTER_X_MM = 66.199
DESIGN_RESET_PIN_HOLE_MM = 3.0
DESIGN_RESET_PIN_HOLE_AXIS_Z_MM = 1.75
DESIGN_RESET_PIN_HOLE_FLAT_MM = 1.24
DESIGN_RESET_BACK_WALL_DEPTH_MM = 4.9  # from the wall's inner face
DESIGN_RESET_BACK_WALL_MM = 1.2
DESIGN_RESET_BACK_WALL_TOP_Z_MM = 3.5
DESIGN_RESET_NOTCH_WIDTH_MM = 1.55
DESIGN_RESET_NOTCH_FROM_CENTER_MM = 3.425  # each notch's middle
DESIGN_RESET_NOTCH_BOTTOM_Z_MM = 0.9
DESIGN_RESET_BACK_WALL_BEYOND_NOTCHES_MM = 1.0
DESIGN_BATTERY_HEADER_X_MM = (85.0, 91.0)
DESIGN_BATTERY_HEADER_MIDDLE_Y_MM = 74.6
DESIGN_BATTERY_POCKET_MM = (6.4, 6.3)  # inside, along x, along y
DESIGN_BATTERY_POCKET_WALL_MM = 1.2
DESIGN_BATTERY_POCKET_TOP_Z_MM = 4.5
DESIGN_BATTERY_POST_SLOT_MM = 3.14
DESIGN_BATTERY_POST_SLOT_BOTTOM_Z_MM = 1.21
DESIGN_BATTERY_X_MM = (22.0, 56.37)
DESIGN_BATTERY_Y_MM = (8.1, 59.63)
DESIGN_BATTERY_RIB_CLEARANCE_MM = 0.5
DESIGN_BATTERY_RIB_MM = (0.8, 6.0, 1.0)  # thick, arm from the pocket's corner, tall
DESIGN_BATTERY_RIB_CORNERS = ((-1, -1), (-1, 1), (1, -1))  # (east, north): all but the northeast
DESIGN_PCB_CONNECTOR_ZONE_MM = ((20.0, 37.0), (65.5, 74.5))

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
           [pin_hole_diameter=<mm>] [nano_length=<mm>] [nano_width=<mm>]
           [hook_lip=<mm>] [bar_clearance=<mm>] [hook_room=<mm>]
           [battery_shoulder=<mm>]

  right              export the right half: cut for its own sockets, its pin
                     holes the slip fit, mirrored across the layout's right-half
                     mirror line, x = {layout.RIGHT_HALF_MIRROR_X_MM:.3f}
  pin_hole_diameter  the dowel pin holes' diameter as modelled, mm, instead of
                     the half's fit ({layout.DOWEL_HOLE_SNUG_DIAMETER_MM:.1f} snug on the left, \
{layout.DOWEL_HOLE_SLIP_DIAMETER_MM:.1f} slip
                     on the right, both less {layout.PRINT_SWELLING_PER_SIDE_MM} per side once \
printed)
  nano_length        the nice!nano's board length the mounts are fitted to
                     (default {layout.NANO_LENGTH_MM}), its USB end staying put
  nano_width         its width (default {layout.NANO_WIDTH_MM}), its west edge staying put
  hook_lip           how far the snap hook's lip reaches onto the board
                     (default {layout.NANO_HOOK_LIP_MM})
  bar_clearance      the hold-down bar's clearance over the USB-C shell as
                     printed (default {layout.NANO_BAR_CLEARANCE_MM})
  hook_room          the room south of the hook's blade as printed, which its
                     free end swings through (default {layout.NANO_HOOK_DEFLECTION_ROOM_MM})
  battery_shoulder   how far front lips reach onto the battery header's rim
                     (default {layout.BATTERY_HEADER_SHOULDER_MM}, none)\
"""

# The key=value words, each a number: the pin holes' diameter and the
# mounts' fits (layout.MountFits' fields).
OPTION_KEYS = (
    "pin_hole_diameter",
    "nano_length",
    "nano_width",
    "hook_lip",
    "bar_clearance",
    "hook_room",
    "battery_shoulder",
)


class Arguments:
    def __init__(self):
        self.stl_file = None
        self.right = False
        for key in OPTION_KEYS:
            setattr(self, key, None)

    def mount_fits(self):
        """layout.MountFits with the overrides given."""
        given = {
            key: getattr(self, key) for key in OPTION_KEYS[1:] if getattr(self, key) is not None
        }
        return layout.MountFits(**given)


def parse_arguments(argument_list):
    arguments = Arguments()
    positionals = []
    for argument in argument_list:
        if argument == "right":
            arguments.right = True
        elif "=" in argument:
            key, _, value = argument.partition("=")
            if key not in OPTION_KEYS:
                raise SystemExit(f"error: unknown option '{key}'\n{USAGE}")
            try:
                setattr(arguments, key, float(value))
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


# The parts' mounts.


class Board:
    """The nice!nano's board where DESIGN.md places it, its size
    DESIGN.md's or a test print's: its edges in the left half's frame.
    The west edge and the USB end stay put whatever the size."""

    def __init__(self, width, length):
        self.west = DESIGN_NANO_WEST_X_MM
        self.east = DESIGN_NANO_WEST_X_MM + width
        self.north = DESIGN_NANO_USB_END_Y_MM
        self.south = DESIGN_NANO_USB_END_Y_MM - length
        self.center = (self.west + self.east) / 2.0


class MountDesign:
    """What the mounts are measured against: DESIGN.md's figures, a test
    print's key=value overrides in their place. A figure that is an
    override is checked against it, one that follows from an override
    only printed."""

    def __init__(self, arguments):
        width = DESIGN_NANO_SIZE_MM[0] if arguments.nano_width is None else arguments.nano_width
        length = DESIGN_NANO_SIZE_MM[1] if arguments.nano_length is None else arguments.nano_length
        self.board = Board(width, length)
        self.hook_lip_overridden = arguments.hook_lip is not None
        self.hook_lip = arguments.hook_lip if self.hook_lip_overridden else DESIGN_HOOK_LIP_REACH_MM
        self.bar_clearance = (
            DESIGN_NANO_BAR_CLEARANCE_MM
            if arguments.bar_clearance is None
            else arguments.bar_clearance
        )
        # The hook's slots as modelled, the south one a hook_room
        # override's as printed plus the swelling on both sides.
        self.hook_slots = dict(DESIGN_HOOK_SLOTS_MM)
        if arguments.hook_room is not None:
            self.hook_slots["south"] = (
                arguments.hook_room + 2.0 * DESIGN_PRINT_SWELLING_PER_SIDE_MM
            )
        self.battery_shoulder = arguments.battery_shoulder or 0.0


def half_place(right, point):
    """A left half's (x, y, z) on the given half."""
    x, y, z = point
    return vector(half_point((x, y), right), z)


def run_span(tray, right, point, axis, material):
    """(low, high) along "x", "y" or "z" in the left half's frame of the
    material (or, with material False, the empty) run through the left
    half's point, measured on the given half. An open end reads
    PROBE_REACH_MM away."""
    direction = {"x": App.Vector(1, 0, 0), "y": App.Vector(0, 1, 0), "z": UP}[axis]
    if axis == "x" and right:
        direction = direction * -1.0
    low, high = run_through(tray, half_place(right, point), direction, material)
    origin = point["xyz".index(axis)]
    return origin + low, origin + high


def span_length(span):
    return span[1] - span[0]


def span_middle(span):
    return (span[0] + span[1]) / 2.0


def worst_offset(measured, expected):
    """The measured edge farthest from its expected place, signed."""
    offsets = [got - want for got, want in zip(measured, expected)]
    return max(offsets, key=abs)


def north_wall_faces(part):
    """(inner, outer) y of DESIGN.md's north wall behind the part."""
    edge = DESIGN_NORTH_EDGES_Y_MM[part]
    return edge + DESIGN_GAP_MM, edge + DESIGN_GAP_MM + DESIGN_WALL_MM


def opening_chamfer(tray, right, point, width):
    """A 45 degree chamfer's size from an opening's width along x 0.05
    inside a face, as measure_pin_hole() reads a lead-in."""
    widening = (span_length(run_span(tray, right, point, "x", False)) - width) / 2.0
    return widening + 0.05 if widening > 1e-6 else 0.0


def window_corner_radius(tray, right, x, y, top, half_width):
    """The window's corner radius from its half width 0.2 under its top:
    a corner of radius r takes a off the width and b off the height
    where (r - a)^2 + (r - b)^2 = r^2."""
    below_top = 0.2
    across = run_span(tray, right, (x, y, top - below_top), "x", False)
    off_width = half_width - span_length(across) / 2.0
    return off_width + below_top + math.sqrt(2.0 * off_width * below_top)


def shell_mouth_y(board):
    return board.north + DESIGN_SHELL_PAST_BOARD_MM


def channel_top_z(design):
    return DESIGN_SHELL_TOP_Z_MM + DESIGN_PRINT_SWELLING_PER_SIDE_MM + design.bar_clearance


def measure_usb_window(tray, right, design, figures):
    """The window between the shell's channel and the outer chamfer,
    where it is the opening alone, and its chamfers."""
    board = design.board
    _inner, outer = north_wall_faces("nice!nano")
    mouth = shell_mouth_y(board)
    width, height = DESIGN_USB_WINDOW_MM
    channel_end = mouth + DESIGN_USB_CHANNEL_PAST_MOUTH_MM
    alone_y = (channel_end + outer - DESIGN_USB_WINDOW_CHAMFER_MM["outer"]) / 2.0
    middle = (board.center, alone_y, DESIGN_USB_WINDOW_CENTER_Z_MM)
    across = run_span(tray, right, middle, "x", False)
    up = run_span(tray, right, middle, "z", False)
    half_width = span_length(across) / 2.0
    radius = window_corner_radius(tray, right, middle[0], middle[1], up[1], half_width)
    outer_chamfer = opening_chamfer(tray, right, (middle[0], outer - 0.05, middle[2]), width)
    inner_chamfer = opening_chamfer(tray, right, (middle[0], mouth + 0.05, middle[2]), width)
    texts = [
        figures.check("wide", span_length(across), width, 1),
        figures.check("tall", span_length(up), height, 1),
        figures.check("off the shell's middle", span_middle(across) - board.center, 0.0, 2),
        figures.check("middle z", span_middle(up), DESIGN_USB_WINDOW_CENTER_Z_MM, 2),
        figures.check(
            "into the floor", -up[0], round(height / 2.0 - DESIGN_USB_WINDOW_CENTER_Z_MM, 2), 2
        ),
        figures.check("corners", radius, DESIGN_USB_WINDOW_CORNER_RADIUS_MM, 2),
        figures.check("outer chamfer", outer_chamfer, DESIGN_USB_WINDOW_CHAMFER_MM["outer"], 1),
        figures.check("inner chamfer", inner_chamfer, DESIGN_USB_WINDOW_CHAMFER_MM["inner"], 1),
    ]
    return f"USB window: {', '.join(texts)}"


def measure_usb_channel(tray, right, design, figures):
    """The shell's channel through the wall's inner part: across and up
    in the wall, its end past the shell's mouth at a top corner, where
    it reaches out of the window's corner round."""
    board = design.board
    inner, _outer = north_wall_faces("nice!nano")
    mouth = shell_mouth_y(board)
    in_wall = (board.center, (inner + mouth) / 2.0, 1.0)
    across = run_span(tray, right, in_wall, "x", False)
    up = run_span(tray, right, in_wall, "z", False)
    corner = (board.center + DESIGN_NANO_BAR_OPENING_MM / 2.0 - 0.1, in_wall[1],
              channel_top_z(design) - 0.05)
    end = run_span(tray, right, corner, "y", False)[1]
    over_shell = up[1] - DESIGN_PRINT_SWELLING_PER_SIDE_MM - DESIGN_SHELL_TOP_Z_MM
    texts = [
        figures.check("wide", span_length(across), DESIGN_NANO_BAR_OPENING_MM, 2),
        figures.check("off the shell's middle", span_middle(across) - board.center, 0.0, 2),
        figures.check("from z", up[0], 0.0, 2),
        figures.check("over the shell as printed", over_shell, design.bar_clearance, 2),
        figures.check("past the shell's mouth", end - mouth, DESIGN_USB_CHANNEL_PAST_MOUTH_MM, 2),
    ]
    return f"channel:    {', '.join(texts)}"


def measure_nano_bar(tray, right, design, figures):
    board = design.board
    inner, _outer = north_wall_faces("nice!nano")
    y = inner - 0.1
    opening = run_span(tray, right, (board.center, y, 1.0), "x", False)
    posts = [
        run_span(tray, right, (opening[0] - 0.1, y, 1.0), "x", True),
        run_span(tray, right, (opening[1] + 0.1, y, 1.0), "x", True),
    ]
    under = run_span(tray, right, (board.center, y, 1.0), "z", False)
    in_bar = (board.center, y, under[1] + 0.1)
    bar = run_span(tray, right, in_bar, "z", True)
    south_faces = [run_span(tray, right, in_bar, "y", True)[0]] + [
        run_span(tray, right, (span_middle(post), y, 1.0), "y", True)[0] for post in posts
    ]
    south_gap = worst_offset(south_faces, [board.north] * 3)
    mouth = shell_mouth_y(board)
    over_channel = (channel_top_z(design) + DESIGN_USB_WINDOW_CENTER_Z_MM
                    + DESIGN_USB_WINDOW_MM[1] / 2.0) / 2.0
    deep = run_span(tray, right, (board.center, mouth - 0.1, over_channel), "y", True)
    texts = [
        figures.check("posts' opening", span_length(opening), DESIGN_NANO_BAR_OPENING_MM, 2),
        figures.check("off the shell's middle", span_middle(opening) - board.center, 0.0, 2),
        figures.check("west post", span_length(posts[0]), DESIGN_NANO_BAR_POST_WIDTH_MM, 1),
        figures.check("east post", span_length(posts[1]), DESIGN_NANO_BAR_POST_WIDTH_MM, 1),
        figures.check(
            "bar over the shell as printed",
            under[1] - DESIGN_PRINT_SWELLING_PER_SIDE_MM - DESIGN_SHELL_TOP_Z_MM,
            design.bar_clearance,
            2,
        ),
        figures.check("bar tall", span_length(bar), DESIGN_NANO_BAR_HEIGHT_MM, 1),
        figures.check("deep", span_length(deep), DESIGN_NANO_BAR_DEPTH_MM, 2),
        figures.check("to the shell's mouth", deep[1] - mouth, 0.0, 2),
        figures.check(
            "bar and posts from the board's USB end", south_gap, DESIGN_NANO_END_GAP_MM, 2
        ),
    ]
    return f"bar:        {', '.join(texts)}"


def hook_side_degrees(tray, right, x, ys, z, toward):
    """The angle from horizontal of the lip's underside (toward 1, read
    upward from below it) or its top (toward -1, read downward from above
    it) between two y."""
    heights = []
    for y in ys:
        low, high = run_span(tray, right, (x, y, z), "z", False)
        heights.append(high if toward > 0 else low)
    return math.degrees(math.atan2(abs(heights[1] - heights[0]), abs(ys[1] - ys[0])))


def swelling_at_45_degrees():
    return DESIGN_PRINT_SWELLING_PER_SIDE_MM * math.sqrt(2.0)


def hook_strain_percent(reach, thickness, length):
    """DESIGN.md's bending strain at the blade's root, as printed: the
    print's swelling grows the blade and moves the lip's tip, where its
    45 degree sides meet, out by the swelling at 45 degrees."""
    printed_thickness = thickness + 2.0 * DESIGN_PRINT_SWELLING_PER_SIDE_MM
    printed_reach = reach + swelling_at_45_degrees()
    return 100.0 * 3.0 * printed_reach * printed_thickness / (2.0 * length**2)


def hook_swing(reach, length, lip_width):
    """DESIGN.md's swing of the blade's free end as printed while the
    lip's near end moves the lip's reach as printed: past the point load
    the blade runs on straight, turned by 3/2 the deflection over the
    length per mm."""
    deflection = reach + swelling_at_45_degrees()
    return deflection * (1.0 + 1.5 * lip_width / length)


def measure_nano_hook_blade(tray, right, design, figures):
    """The blade and its slots: (line, blade's thickness, its root's x,
    its north face's y, its top's z, the slot south of it)."""
    board = design.board
    blade_x = (DESIGN_HOOK_ROOT_X_MM + DESIGN_HOOK_LIP_X_MM[0]) / 2.0
    face_y = board.south - DESIGN_NANO_END_GAP_MM
    in_blade = (blade_x, face_y - DESIGN_HOOK_BLADE_THICKNESS_MM / 2.0, 2.0)
    blade = run_span(tray, right, in_blade, "y", True)
    height = run_span(tray, right, in_blade, "z", True)
    floor_z = DESIGN_FLOOR_UNDERSIDE_Z_MM / 2.0
    in_floor = run_span(tray, right, (blade_x, in_blade[1], floor_z), "y", True)
    south_slot = run_span(tray, right, (blade_x, blade[0] - 0.1, floor_z), "y", False)
    north_slot = run_span(tray, right, (blade_x, blade[1] + 0.1, floor_z), "y", False)
    slot_along = run_span(tray, right, (blade_x, blade[0] - 0.1, floor_z), "x", False)
    blade_end = run_span(tray, right, in_blade, "x", True)[1]
    end_slot = run_span(tray, right, (blade_end + 0.1, in_blade[1], floor_z), "x", False)
    texts = [
        figures.check("blade thick", span_length(blade), DESIGN_HOOK_BLADE_THICKNESS_MM, 1),
        figures.check(
            "as thick in the floor", span_length(in_floor), DESIGN_HOOK_BLADE_THICKNESS_MM, 1
        ),
        figures.check("north face from the board's south end", board.south - blade[1],
                      DESIGN_NANO_END_GAP_MM, 2),
        figures.check("bottom z", height[0], DESIGN_FLOOR_UNDERSIDE_Z_MM, 1),
        figures.check("root x", slot_along[0], DESIGN_HOOK_ROOT_X_MM, 1),
        figures.check("end x", blade_end, DESIGN_HOOK_LIP_X_MM[1], 1),
        figures.check("slot south", span_length(south_slot), design.hook_slots["south"], 1),
        figures.check("north", span_length(north_slot), design.hook_slots["north"], 1),
        figures.check("past the end", span_length(end_slot), design.hook_slots["end"], 1),
    ]
    return (f"hook:       {', '.join(texts)}", span_length(blade), slot_along[0], blade[1],
            height[1], span_length(south_slot))


def bed_chamfer(tray, right, edge, axis, into, inside):
    """(in along the bed, up the face) of a 45 degree chamfer at the bed
    edge of a vertical face: edge the (x, y) of a point on the face, the
    material on the `into` (1 or -1) side along axis, `inside` deep."""
    bed = DESIGN_FLOOR_UNDERSIDE_Z_MM
    index = "xy".index(axis)

    def place(depth, z):
        point = [edge[0], edge[1], z]
        point[index] += into * depth
        return tuple(point)

    along = run_span(tray, right, place(inside, bed + 0.001), axis, True)
    bed_edge = along[0] if into > 0 else along[1]
    up = run_span(tray, right, place(0.001, bed + 0.6), "z", True)
    return abs(bed_edge - edge[index]) + 0.001, up[0] - bed + 0.001


def measure_nano_hook_bed_chamfers(tray, right, design, figures):
    """The floor's bed edges on the slots' south, north and east sides
    and the blade's on its south and north faces and its free end."""
    face_y = design.board.south - DESIGN_NANO_END_GAP_MM
    back_y = face_y - DESIGN_HOOK_BLADE_THICKNESS_MM
    end_x = DESIGN_HOOK_LIP_X_MM[1]
    slots = design.hook_slots
    middle_x = (DESIGN_HOOK_ROOT_X_MM + end_x) / 2.0
    blade_y = (back_y + face_y) / 2.0
    edges = {
        "slots": [
            ((middle_x, back_y - slots["south"]), "y", -1),
            ((middle_x, face_y + slots["north"]), "y", 1),
            ((end_x + slots["end"], blade_y), "x", 1),
        ],
        "blade": [((middle_x, back_y), "y", 1), ((middle_x, face_y), "y", -1),
                  ((end_x, blade_y), "x", -1)],
    }
    inside = {"slots": 0.6, "blade": DESIGN_HOOK_BLADE_THICKNESS_MM / 2.0}
    labels = {"slots": "the slots' floor edges", "blade": "the blade's edges"}
    texts = []
    for what, stated in DESIGN_HOOK_BED_CHAMFERS_MM.items():
        sizes = [size for edge, axis, into in edges[what]
                 for size in bed_chamfer(tray, right, edge, axis, into, inside[what])]
        worst = max(sizes, key=lambda size: abs(size - stated))
        texts.append(figures.check(labels[what], worst, stated, 1))
    return f"hook bed:   chamfered along the bed and up the faces, {', '.join(texts)}"


def unless(overridden, stated):
    """A DESIGN.md figure to check against, or None (only print it) when
    it follows from a test print's override."""
    return None if overridden else stated


def measure_nano_hook(tray, right, design, figures):
    """The blade and its slots, then the lip, its sides, the strain the
    lip's reach and the blade make at the root and the free end's swing
    in the room south of the blade."""
    board = design.board
    blade_line, thickness, root, face_y, top, south_slot = measure_nano_hook_blade(
        tray, right, design, figures
    )
    lip_x = span_middle(DESIGN_HOOK_LIP_X_MM)
    over_edge = run_span(tray, right, (lip_x, board.south, 1.0), "z", False)[1]
    tip_z = over_edge + design.hook_lip
    tip = run_span(tray, right, (lip_x, face_y - 0.4, tip_z), "y", True)[1]
    reach = tip - board.south
    lip = run_span(tray, right, (lip_x, board.south, (over_edge + tip_z) / 2.0), "x", True)
    sides_y = (face_y + 0.15, tip - 0.4)
    underside = hook_side_degrees(tray, right, lip_x, sides_y, 1.0, 1)
    lead_in = hook_side_degrees(tray, right, lip_x, sides_y, top + 1.0, -1)
    bending_length = lip[0] - root
    strain = hook_strain_percent(reach, thickness, bending_length)
    swing = hook_swing(reach, bending_length, span_length(lip))
    room = south_slot - 2.0 * DESIGN_PRINT_SWELLING_PER_SIDE_MM
    under_socket = DESIGN_SOCKET_BOTTOM_Z_MM - top
    follows = design.hook_lip_overridden
    texts = [
        figures.check("lip onto the board", reach, design.hook_lip, 2),
        figures.check("over the board's edge as printed",
                      over_edge - swelling_at_45_degrees() - DESIGN_NANO_TOP_Z_MM,
                      DESIGN_HOOK_LIP_OVER_EDGE_MM, 2),
        figures.check("from x", lip[0], DESIGN_HOOK_LIP_X_MM[0], 1),
        figures.check("to", lip[1], DESIGN_HOOK_LIP_X_MM[1], 1),
        figures.check("underside degrees", underside, DESIGN_HOOK_SIDES_DEGREES, 0),
        figures.check("lead-in degrees", lead_in, DESIGN_HOOK_SIDES_DEGREES, 0),
        figures.check("bending length", bending_length, DESIGN_HOOK_BENDING_LENGTH_MM, 1),
        check_or_report(figures, "top z", top, unless(follows, DESIGN_HOOK_TOP_Z_MM), 2),
        check_or_report(figures, "under the sockets' bottoms", under_socket,
                        unless(follows, DESIGN_HOOK_UNDER_SOCKET_MM), 2),
        check_or_report(figures, "root strain as printed %", strain,
                        unless(follows, DESIGN_HOOK_STRAIN_PERCENT), 2),
        check_or_report(figures, "free end swings", swing, unless(follows, DESIGN_HOOK_SWING_MM),
                        2),
        figures.report("in room as printed", room, 1),
    ]
    if strain > DESIGN_HOOK_MAXIMUM_STRAIN_PERCENT:
        figures.problems.append(
            f"the hook's root strain {strain:.2f} % is over {DESIGN_HOOK_MAXIMUM_STRAIN_PERCENT} %"
        )
    if swing > room:
        figures.problems.append(
            f"the hook's free end swings {swing:.3f}, its room leaves {room:.3f} as printed"
        )
    return [blade_line, measure_nano_hook_bed_chamfers(tray, right, design, figures),
            f"hook lip:   {', '.join(texts)}"]


def measure_nano_ribs(tray, right, design, figures):
    board = design.board
    thickness, length, height = DESIGN_NANO_RIB_MM
    rib_x = board.east + DESIGN_NANO_RIB_FROM_BOARD_MM + thickness / 2.0
    ends = DESIGN_NANO_RIB_FROM_BOARD_ENDS_MM + length / 2.0
    texts = []
    for name, middle_y in (("south", board.south + ends), ("north", board.north - ends)):
        point = (rib_x, middle_y, 0.5)
        across = run_span(tray, right, point, "x", True)
        along = run_span(tray, right, point, "y", True)
        up = run_span(tray, right, point, "z", True)
        from_end = along[0] - board.south if name == "south" else board.north - along[1]
        texts.append(
            f"{name}: "
            + ", ".join([
                figures.check("face from the board", across[0] - board.east,
                              DESIGN_NANO_RIB_FROM_BOARD_MM, 2),
                figures.check("thick", span_length(across), thickness, 1),
                figures.check("long", span_length(along), length, 1),
                figures.check("tall", up[1], height, 1),
                figures.check(
                    "from the board's end", from_end, DESIGN_NANO_RIB_FROM_BOARD_ENDS_MM, 1
                ),
            ])
        )
    return f"ribs:       {'; '.join(texts)}"


def nano_groove_places(board, right):
    """(label, x range, y range) of DESIGN.md's grooves on the given half,
    in the left half's frame. The P1.01/P1.02/P1.07 groove lies at the
    board's west edge seen from above, which in the left half's frame is
    the east edge on the right half."""
    (row_near, row_far), row_y = DESIGN_NANO_ROW_GROOVES_MM
    (p1_near, p1_far), p1_y = DESIGN_NANO_P1_GROOVE_MM
    (tab_near, tab_far), tab_y = DESIGN_NANO_TAB_GROOVES_MM

    def from_usb_end(offsets):
        return (board.north - offsets[1], board.north - offsets[0])

    if right:
        p1_x = (board.east - p1_far, board.east - p1_near)
    else:
        p1_x = (board.west + p1_near, board.west + p1_far)
    return [
        ("west row", (board.west + row_near, board.west + row_far), from_usb_end(row_y)),
        ("east row", (board.east - row_far, board.east - row_near), from_usb_end(row_y)),
        ("P1.01/P1.02/P1.07", p1_x, from_usb_end(p1_y)),
        ("west tab slots", (board.center - tab_far, board.center - tab_near), from_usb_end(tab_y)),
        ("east tab slots", (board.center + tab_near, board.center + tab_far), from_usb_end(tab_y)),
    ]


def measure_nano_grooves(tray, right, design, figures):
    """Each groove's edges against DESIGN.md's and its depth. Where the
    hook's north slot reaches north past the west row's groove's south
    end (DESIGN.md's board), the groove runs on into it, so that end
    reads as the blade's face."""
    board = design.board
    blade_face = board.south - DESIGN_NANO_END_GAP_MM
    north_slot_end = blade_face + DESIGN_HOOK_SLOTS_MM["north"]
    offsets, depths = [], []
    for label, x_range, y_range in nano_groove_places(board, right):
        middle = (span_middle(x_range), span_middle(y_range), -DESIGN_NANO_GROOVE_DEPTH_MM / 2.0)
        across = run_span(tray, right, middle, "x", False)
        along = run_span(tray, right, middle, "y", False)
        depths.append(-run_span(tray, right, middle, "z", False)[0])
        if label == "west row" and north_slot_end >= y_range[0]:
            y_range = (blade_face, y_range[1])
        offsets.append(worst_offset(across + along, x_range + y_range))
    texts = [
        figures.check("edges off DESIGN.md's by", max(offsets, key=abs), 0.0, 2),
        figures.check(
            "deep",
            max(depths, key=lambda depth: abs(depth - DESIGN_NANO_GROOVE_DEPTH_MM)),
            DESIGN_NANO_GROOVE_DEPTH_MM,
            1,
        ),
    ]
    p1 = nano_groove_places(board, right)[2][1]
    return (
        f"grooves:    {len(offsets)}, {', '.join(texts)}, P1.01/P1.02/P1.07's from x "
        f"{p1[0]:.3f} to {p1[1]:.3f} in the left half's frame"
    )


def measure_nano_pry_recess(tray, right, design, figures):
    """The recess below the east pin row's groove, where it is alone:
    its place along y, across and along x as printed from the board's
    east edge, its depth, the tip's room over its bottom as printed and
    the floor under it. At the groove's depth
    it runs on west to the groove's west edge."""
    board = design.board
    swelling = DESIGN_PRINT_SWELLING_PER_SIDE_MM
    beside = DESIGN_NANO_PRY_RECESS_BESIDE_BOARD_PRINTED_MM + swelling
    x = board.east + beside / 2.0
    y = span_middle(DESIGN_NANO_PRY_RECESS_Y_MM)
    below_groove = (x, y, -(DESIGN_NANO_GROOVE_DEPTH_MM + DESIGN_NANO_PRY_RECESS_DEPTH_MM) / 2.0)
    along_x = run_span(tray, right, below_groove, "x", False)
    along_y = run_span(tray, right, below_groove, "y", False)
    bottom = run_span(tray, right, below_groove, "z", False)[0]
    floor = run_span(tray, right, (x, y, (bottom + DESIGN_FLOOR_UNDERSIDE_Z_MM) / 2.0), "z", True)
    in_groove = run_span(tray, right, (x, y, -DESIGN_NANO_GROOVE_DEPTH_MM / 2.0), "x", False)
    groove_west = board.east - DESIGN_NANO_ROW_GROOVES_MM[0][1]
    texts = [
        figures.check("across as printed", span_length(along_y) - 2.0 * swelling,
                      DESIGN_NANO_PRY_RECESS_ACROSS_PRINTED_MM, 1),
        figures.check("under the board", board.east - along_x[0] - swelling,
                      DESIGN_NANO_PRY_RECESS_UNDER_BOARD_PRINTED_MM, 1),
        figures.check("beside it", along_x[1] - board.east - swelling,
                      DESIGN_NANO_PRY_RECESS_BESIDE_BOARD_PRINTED_MM, 1),
        figures.check("from y", along_y[0], DESIGN_NANO_PRY_RECESS_Y_MM[0], 2),
        figures.check("to", along_y[1], DESIGN_NANO_PRY_RECESS_Y_MM[1], 2),
        figures.check("deep", -bottom, DESIGN_NANO_PRY_RECESS_DEPTH_MM, 1),
        figures.check("the tip's room as printed", -bottom - swelling,
                      DESIGN_NANO_PRY_TOOL_ROOM_PRINTED_MM, 1),
        figures.check("floor under it", span_length(floor),
                      DESIGN_NANO_PRY_RECESS_FLOOR_UNDER_MM, 1),
        figures.check("into the east row's groove, off its west edge by",
                      in_groove[0] - groove_west, 0.0, 2),
    ]
    return f"recess:     {', '.join(texts)}"


def measure_power_switch(tray, right, figures):
    center = DESIGN_POWER_SWITCH_CENTER_X_MM
    inner, outer = north_wall_faces("power switch")
    in_slot = (center, (inner + outer) / 2.0, DESIGN_LEVER_SLOT_CENTER_Z_MM)
    across = run_span(tray, right, in_slot, "x", False)
    up = run_span(tray, right, in_slot, "z", False)
    through = run_span(tray, right, in_slot, "y", False)
    if through[0] > inner or through[1] < outer:
        figures.problems.append("the lever slot does not pass through the wall")
    body_y = inner - 2.0
    opening = run_span(tray, right, (center, body_y, 1.5), "x", False)
    ends = [
        run_span(tray, right, (opening[0] - 0.1, body_y, 1.5), "x", True),
        run_span(tray, right, (opening[1] + 0.1, body_y, 1.5), "x", True),
    ]
    beside_pins = (opening[0] + 0.5, body_y, 1.5)
    depth = run_span(tray, right, beside_pins, "y", False)
    arm = run_span(tray, right, (beside_pins[0], depth[0] - 0.1, 1.5), "y", True)
    pin_slot = run_span(tray, right, (center, depth[0] - 0.1, 1.5), "x", False)
    top = run_span(tray, right, (span_middle(ends[0]), body_y, 1.5), "z", True)[1]
    slot_texts = [
        figures.check("wide", span_length(across), DESIGN_LEVER_SLOT_MM[0], 1),
        figures.check("tall", span_length(up), DESIGN_LEVER_SLOT_MM[1], 1),
        figures.check("off x", span_middle(across) - center, 0.0, 2),
        figures.check("middle z", span_middle(up), DESIGN_LEVER_SLOT_CENTER_Z_MM, 2),
    ]
    cradle_texts = [
        figures.check("opening", span_length(opening), DESIGN_CRADLE_OPENING_MM, 1),
        figures.check("off x", span_middle(opening) - center, 0.0, 2),
        figures.check("ends", min(span_length(end) for end in ends), DESIGN_CRADLE_END_MM, 1),
        figures.check("deep to the back arms", depth[1] - depth[0], DESIGN_CRADLE_DEPTH_MM, 1),
        figures.check("back arms", span_length(arm), DESIGN_CRADLE_ARM_MM, 1),
        figures.check("pin slot", span_length(pin_slot), DESIGN_CRADLE_PIN_SLOT_MM, 1),
        figures.check("top z", top, DESIGN_CRADLE_TOP_Z_MM, 1),
    ]
    return [f"lever slot: {', '.join(slot_texts)}", f"cradle:     {', '.join(cradle_texts)}"]


def measure_reset_button(tray, right, figures):
    center = DESIGN_RESET_CENTER_X_MM
    inner, outer = north_wall_faces("reset button")
    in_hole = (center, (inner + outer) / 2.0, DESIGN_RESET_PIN_HOLE_AXIS_Z_MM)
    across = run_span(tray, right, in_hole, "x", False)
    up = run_span(tray, right, in_hole, "z", False)
    through = run_span(tray, right, in_hole, "y", False)
    if through[0] > inner or through[1] < outer:
        figures.problems.append("the reset pin hole does not pass through the wall")
    radius = span_length(across) / 2.0
    _top, flat = flat_top(tray, half_place(right, in_hole), App.Vector(1, 0, 0))
    in_front = run_span(tray, right, (center, inner - 1.0, DESIGN_RESET_BACK_WALL_TOP_Z_MM - 0.1),
                        "y", False)
    in_wall = (center, in_front[0] - DESIGN_RESET_BACK_WALL_MM / 2.0, 2.0)
    wall = run_span(tray, right, in_wall, "y", True)
    wall_top = run_span(tray, right, in_wall, "z", True)[1]
    notch_texts = []
    for side in (-1.0, 1.0):
        notch_point = (center + side * DESIGN_RESET_NOTCH_FROM_CENTER_MM, in_wall[1], 2.0)
        notch = run_span(tray, right, notch_point, "x", False)
        bottom = run_span(tray, right, notch_point, "z", False)[0]
        outer_edge = notch[1] if side > 0 else notch[0]
        end = run_span(tray, right, (outer_edge + side * 0.1, in_wall[1], 2.0), "x", True)
        notch_texts.extend([
            figures.check("notch", span_length(notch), DESIGN_RESET_NOTCH_WIDTH_MM, 2),
            figures.check("from the middle", abs(span_middle(notch) - center),
                          DESIGN_RESET_NOTCH_FROM_CENTER_MM, 2),
            figures.check("bottom z", bottom, DESIGN_RESET_NOTCH_BOTTOM_Z_MM, 1),
            figures.check("wall beyond", span_length(end), DESIGN_RESET_BACK_WALL_BEYOND_NOTCHES_MM,
                          1),
        ])
    hole_texts = [
        figures.check("pin hole across", span_length(across), DESIGN_RESET_PIN_HOLE_MM, 1),
        figures.check("off x", span_middle(across) - center, 0.0, 2),
        figures.check("axis z", up[0] + radius, DESIGN_RESET_PIN_HOLE_AXIS_Z_MM, 2),
        f"top {up[1] - up[0] - radius:.3f} above the axis",
        figures.check("flat top", flat, DESIGN_RESET_PIN_HOLE_FLAT_MM, 2),
    ]
    wall_texts = [
        figures.check("back wall from the wall's inner face", in_front[1] - in_front[0],
                      DESIGN_RESET_BACK_WALL_DEPTH_MM, 1),
        figures.check("thick", span_length(wall), DESIGN_RESET_BACK_WALL_MM, 1),
        figures.check("top z", wall_top, DESIGN_RESET_BACK_WALL_TOP_Z_MM, 1),
    ] + notch_texts
    return [f"reset:      {', '.join(hole_texts)}", f"back wall:  {', '.join(wall_texts)}"]


def measure_battery_pocket(tray, right, design, figures):
    """The pocket, its mouth where the side walls end, or with a test
    print's front lips, which run on from the side walls, at the lips'
    faces."""
    middle_y = DESIGN_BATTERY_HEADER_MIDDLE_Y_MM
    header_x = DESIGN_BATTERY_HEADER_X_MM
    in_pocket = (span_middle(header_x), middle_y, 2.0)
    across = run_span(tray, right, in_pocket, "y", False)
    beside_post_slot = (in_pocket[0], across[0] + 0.1, 2.0)
    back = run_span(tray, right, beside_post_slot, "x", False)[1]
    walls = [
        run_span(tray, right, (in_pocket[0], across[0] - 0.1, 2.0), "y", True),
        run_span(tray, right, (in_pocket[0], across[1] + 0.1, 2.0), "y", True),
    ]
    side = run_span(tray, right, (in_pocket[0], across[0] - 0.1, 2.0), "x", True)
    if design.battery_shoulder > 0.0:
        mouth_x = run_span(tray, right, beside_post_slot, "x", False)[0]
    else:
        mouth_x = side[0]
    top = run_span(tray, right, (in_pocket[0], across[0] - 0.1, 2.0), "z", True)[1]
    back_wall = run_span(tray, right, (back + 0.1, beside_post_slot[1], 2.0), "x", True)
    in_post_slot = (back + 0.1, middle_y, DESIGN_BATTERY_POCKET_TOP_Z_MM - 0.1)
    post_slot = run_span(tray, right, in_post_slot, "y", False)
    slot_bottom = run_span(tray, right, in_post_slot, "z", False)[0]
    pocket_width, pocket_across = DESIGN_BATTERY_POCKET_MM
    mouth = run_span(tray, right, (mouth_x - 0.5, middle_y, 2.0), "y", False)
    texts = [
        figures.check("inside along x", back - mouth_x, pocket_width, 1),
        figures.check("across", span_length(across), pocket_across, 1),
        figures.check("middle y", span_middle(across), middle_y, 2),
        figures.check("mouth before the header", header_x[0] - mouth_x,
                      round((pocket_width - (header_x[1] - header_x[0])) / 2.0, 2), 2),
        figures.check("side walls", min(span_length(wall) for wall in walls),
                      DESIGN_BATTERY_POCKET_WALL_MM, 1),
        figures.check("back wall", span_length(back_wall), DESIGN_BATTERY_POCKET_WALL_MM, 1),
        figures.check("top z", top, DESIGN_BATTERY_POCKET_TOP_Z_MM, 1),
        figures.check("post slot", span_length(post_slot), DESIGN_BATTERY_POST_SLOT_MM, 2),
        figures.check("down to z", slot_bottom, DESIGN_BATTERY_POST_SLOT_BOTTOM_Z_MM, 2),
    ]
    if design.battery_shoulder > 0.0:
        texts.append(figures.report("front lips' opening", span_length(mouth), 1))
    elif span_length(mouth) < pocket_across:
        figures.problems.append(f"the battery pocket's mouth is {span_length(mouth):.3f} across, "
                                "DESIGN.md leaves it open")
    else:
        texts.append("open toward the plug")
    return f"pocket:     {', '.join(texts)}"


def battery_rib_pocket():
    clearance = DESIGN_BATTERY_RIB_CLEARANCE_MM
    return (
        (DESIGN_BATTERY_X_MM[0] - clearance, DESIGN_BATTERY_X_MM[1] + clearance),
        (DESIGN_BATTERY_Y_MM[0] - clearance, DESIGN_BATTERY_Y_MM[1] + clearance),
    )


def battery_rib_arm(tray, right, corner, outward, axis):
    """(thickness, arm from the pocket's corner, top z) of the rib arm
    running along axis from the pocket's corner, (east, north) outward."""
    (corner_x, corner_y), (east, north) = corner, outward
    thickness, arm, _height = DESIGN_BATTERY_RIB_MM
    if axis == "x":
        point = (corner_x - east * arm / 2.0, corner_y + north * thickness / 2.0, 0.5)
        across, along_index, sign = "y", 0, east
    else:
        point = (corner_x + east * thickness / 2.0, corner_y - north * arm / 2.0, 0.5)
        across, along_index, sign = "x", 1, north
    width = span_length(run_span(tray, right, point, across, True))
    along = run_span(tray, right, point, axis, True)
    free_end = along[0] if sign > 0 else along[1]
    top = run_span(tray, right, point, "z", True)[1]
    return width, abs(free_end - corner[along_index]), top


def measure_battery_ribs(tray, right, figures):
    (low_x, high_x), (low_y, high_y) = battery_rib_pocket()
    thickness, arm, height = DESIGN_BATTERY_RIB_MM
    widths, arms, tops = [], [], []
    for east, north in DESIGN_BATTERY_RIB_CORNERS:
        corner = (high_x if east > 0 else low_x, high_y if north > 0 else low_y)
        for axis in ("x", "y"):
            width, reach, top = battery_rib_arm(tray, right, corner, (east, north), axis)
            widths.append(width)
            arms.append(reach)
            tops.append(top)
    inside_x = run_span(tray, right, ((low_x + high_x) / 2.0, low_y + arm / 2.0, 0.5), "x", False)
    inside_y = run_span(tray, right, (low_x + arm / 2.0, (low_y + high_y) / 2.0, 0.5), "y", False)
    for point in ((high_x - arm / 2.0, high_y + thickness / 2.0, 0.5),
                  (high_x + thickness / 2.0, high_y - arm / 2.0, 0.5)):
        if tray.isInside(half_place(right, point), SAME_PLACE_MM, True):
            figures.problems.append(
                "a battery rib stands at the northeast corner, which DESIGN.md leaves free"
            )
    measured_middle = (span_middle(inside_x), span_middle(inside_y))
    battery_middle = (span_middle(DESIGN_BATTERY_X_MM), span_middle(DESIGN_BATTERY_Y_MM))
    texts = [
        figures.check("inside", span_length(inside_x), round(high_x - low_x, 2), 1),
        figures.check("by", span_length(inside_y), round(high_y - low_y, 2), 1),
        figures.check("off the battery's middle", worst_offset(measured_middle, battery_middle),
                      0.0, 2),
        figures.check("thick", max(widths, key=lambda width: abs(width - thickness)), thickness, 1),
        figures.check("arms", max(arms, key=lambda reach: abs(reach - arm)), arm, 1),
        figures.check("tall", max(tops, key=lambda top: abs(top - height)), height, 1),
        "no rib at the northeast corner",
    ]
    return f"battery:    {len(widths)} rib arms at 3 corners, {', '.join(texts)}"


def half_box(right, x_range, y_range, z_range):
    """A box given in the left half's frame, on the given half."""
    corners = [half_point((x, y), right) for x in x_range for y in y_range]
    low_x, high_x = min(x for x, _ in corners), max(x for x, _ in corners)
    low_y, high_y = min(y for _, y in corners), max(y for _, y in corners)
    return Part.makeBox(
        high_x - low_x,
        high_y - low_y,
        z_range[1] - z_range[0],
        App.Vector(low_x, low_y, z_range[0]),
    )


def measure_kept_clear(tray, right, fits, figures):
    """The PCB connector's zone above the floor holds no plastic of the
    tray as printed (the zone grown by the swelling holds none as
    built), and every wire room (layout.py's, the rooms DESIGN.md asks
    for behind every lead) none as built."""
    x_range, y_range = (
        (low - DESIGN_PRINT_SWELLING_PER_SIDE_MM, high + DESIGN_PRINT_SWELLING_PER_SIDE_MM)
        for low, high in DESIGN_PCB_CONNECTOR_ZONE_MM
    )
    zone = half_box(right, x_range, y_range, (0.0, DESIGN_LEDGE_TOP_Z_MM)).common(tray).Volume
    rooms = layout.wire_rooms(fits, right)
    in_rooms = sum(
        half_box(right, room.x_range, room.y_range, room.z_range).common(tray).Volume
        for room in rooms
    )
    texts = [
        figures.check("plastic in the PCB connector's zone as printed, mm3", zone, 0.0, 3),
        figures.check(f"in the {len(rooms)} wire rooms, mm3", in_rooms, 0.0, 3),
    ]
    return f"kept clear: {', '.join(texts)}"


def measure_mounts(tray, right, design, fits, figures):
    lines = [
        measure_usb_window(tray, right, design, figures),
        measure_usb_channel(tray, right, design, figures),
        measure_nano_bar(tray, right, design, figures),
    ]
    lines.extend(measure_nano_hook(tray, right, design, figures))
    lines.append(measure_nano_ribs(tray, right, design, figures))
    lines.append(measure_nano_grooves(tray, right, design, figures))
    lines.append(measure_nano_pry_recess(tray, right, design, figures))
    lines.extend(measure_power_switch(tray, right, figures))
    lines.extend(measure_reset_button(tray, right, figures))
    lines.append(measure_battery_pocket(tray, right, design, figures))
    lines.append(measure_battery_ribs(tray, right, figures))
    lines.append(measure_kept_clear(tray, right, fits, figures))
    return lines


def measure(tray, right, pin_hole_radius, design, mount_design, fits):
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
    lines.extend(measure_mounts(tray, right, mount_design, fits, figures))
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


def half_tray(right, pin_hole_diameter, fits=None):
    """(build, the tray on its half as exported)."""
    build = build_tray(right, pin_hole_diameter, fits)
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
    fits = build.fits
    lips = f"{fits.battery_shoulder} onto the rim" if fits.battery_shoulder > 0.0 else "none"
    print(f"mounts:     fitted to a nice!nano {fits.nano_width} x {fits.nano_length}, the hook's "
          f"lip {fits.hook_lip} onto it with {fits.hook_room} of room, the bar "
          f"{fits.bar_clearance} over its shell, the battery header's front lips {lips}")
    for label, added in build.mounts:
        print(f"added:      {label}, {added:.3f} mm3")


def main():
    arguments = parse_arguments(script_arguments(sys.argv))
    right = arguments.right
    fits = arguments.mount_fits()
    build, tray = half_tray(right, arguments.pin_hole_diameter, fits)
    print_build(build)
    if right:
        print(f"half:       right, mirrored across x = {layout.RIGHT_HALF_MIRROR_X_MM:.3f} (the "
              "lines above are its build in the left half's frame, the lines below the right "
              "half's)")
    else:
        print("half:       left")
    design = hole_design(right, arguments.pin_hole_diameter)
    measure(tray, right, build.pin_hole_diameter / 2.0, design, MountDesign(arguments), fits)
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
