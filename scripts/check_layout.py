"""Check layout.py's geometry, and DESIGN.md's figures against it.

    python3 scripts/check_layout.py

Plain Python, no FreeCAD. The checks run in order. Each one prints a
line with the tightest margin it found; the first one that fails
prints every offending item it found, with the numbers, and the script
exits 1. A failure is a conflict in the design (or between DESIGN.md
and layout.py): fix the design, not the check.

layout.py holds the values the geometry is built from. The DESIGN_*
constants below are DESIGN.md's figures that follow from them,
transcribed independently, so a slip on either side fails here.

Every check that involves the sockets or the dowel bosses and holes
runs on both halves: the right half's sockets differ (layout.py's
module docstring), so its tray gets its own cuts, and its dowel holes
are a deeper slip fit in deeper bosses. The right half is checked in
the left half's frame, its sockets mirrored back across the mirror
line, against a tray whose outline, ledge, standoffs, magnet slots and
parking hole are the left half's there. The other checks would only
repeat the left half's numbers, so they run once.

The parts' mounts (work item 004) are layout.py's MountBoxes, the
bodies the tray adds and the voids it cuts, checked as boxes (the
hook's lip, the USB window and the reset pin hole lie inside theirs):
inside the tray, clear of the parts, the sockets, the standoffs and the
joint, the snap hook within its strain, and the openings around what
passes them as printed, the shell wherever its play lets it go. The
wire rooms behind the parts' leads must stay clear of
all of it. Those that meet the sockets, the joint or the nice!nano's
P1.01/P1.02/P1.07 groove, which is the only mount that differs between
the halves, run on both halves. The nice!nano's pry recess (work item
006) is checked in plan against everything whatever the heights, since
a tool comes down to it from above. The mount checks' problem functions
take a layout.MountFits (the default unless given), so
export_nano_bay_test.py runs them for each bay of its strip.

Distances are in plan. Two bodies are checked against each other only
where their z ranges overlap, since one can pass over the other. The
tray is modelled as layout.py's sharp-cornered polygons: the wall
between the cavity and the outer face (whole but for the sockets' tab
pockets, since its windows and the magnet slots' cut-backs only take
more away), the ledge (cut away where DESIGN.md says and where the
sockets get notches and reliefs, the joint block in its place along
the slant) and the standoffs (with the sockets' flats). The tray
rounds its convex corners inside with the wall's inner radius (0.4 on
kbdkid4's tray), so a part within that of a convex cavity corner has
less room than reported here.
"""

import itertools
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import layout

# Overlap below this counts as touching, not as a collision.
TOLERANCE_MM = 1e-6

# This check's own threshold, not DESIGN.md's: a key center, footprint
# hole or mounting drill closer than this to the outline would leave a
# sliver at the board edge.
INSIDE_OUTLINE_MINIMUM_MARGIN_MM = 0.5

# This check's own tolerance for the outline's edges against the key
# cells moved by the insets: DESIGN.md rounds both to 0.001, from
# kbdkid4's board.lp, whose north edge of columns 0 and 1, for
# example, lies at 75.485625, 0.396375 inside the cells' 75.882.
OUTLINE_ON_CELLS_TOLERANCE_MM = 0.0015

# This check's own threshold: a magnet drops into its slot from above,
# through what the wall leaves open there, with at least the least
# clearance DESIGN.md gives a slot as printed (3.1 across for the 3.0
# magnet).
MAGNET_DROP_IN_CLEARANCE_MM = 0.1

# DESIGN.md's figures, each compared within half its last digit.
DESIGN_SLANT_OFFSET_MM = 0.574
DESIGN_SLANT_LENGTH_MM = 62.51
DESIGN_SLANT_ANGLE_FROM_NORTH_DEGREES = 17.74
DESIGN_HALF_SIZE_MM = (132.4, 82.6)
DESIGN_MIRROR_LINE_X_MM = 66.199
DESIGN_HEIGHTS_Z_MM = (  # (what, z)
    ("socket bottoms", 5.98),
    ("PCB top", 9.6),
    ("plate top", 11.8),
    ("tray rim", 11.9),
)
DESIGN_TRAY_HEIGHT_MM = 13.1
DESIGN_MINIMUM_PCB_UNDERSIDE_Z_MM = 6.63
DESIGN_NANO_SIZE_MM = (18.0, 33.3)  # along x, along y
DESIGN_NANO_FROM_WEST_LEDGE_FACE_MM = 0.3
DESIGN_NANO_USB_MOUTH_BEHIND_OUTER_FACE_MM = 0.5
DESIGN_POWER_SWITCH_LEVER_PROUD_MM = {False: 2.2, True: 1.8}  # as modelled, as printed
DESIGN_BATTERY_SIZE_MM = (34.37, 51.53)  # along x, along y
DESIGN_BATTERY_FROM_STANDOFFS_MM = 0.53
DESIGN_BATTERY_FROM_LEDGE_MM = 0.36
DESIGN_BATTERY_BELOW_SOCKETS_MM = 1.87
DESIGN_BATTERY_COLUMNS = {1, 2}
DESIGN_PCB_CONNECTOR_CLEAR_ZONE_FROM_LEDGE_MM = 0.39
DESIGN_TAB_NOTCH_KEYS = {"S100", "S101", "S102", "S103"}
DESIGN_TAB_TIP_PAST_WEST_EDGE_MM = 0.231
DESIGN_TAB_TIP_FROM_CAVITY_WALL_MM = 0.169
DESIGN_TAB_POCKET_DEPTH_MM = 0.331
DESIGN_WALL_LEFT_AT_TAB_POCKETS_MM = 0.469
DESIGN_LEDGE_RELIEF_KEYS = {
    "S100",
    "S101",
    "S102",
    "S103",
    "S113",
    "S123",
    "S133",
    "S143",
    "S153",
    "S163",
}
DESIGN_LEDGE_RELIEF_BOTTOM_Z_MM = 5.48
DESIGN_BOTTOM_ROW_FROM_SOUTH_LEDGE_FACE_MM = 0.39
DESIGN_STANDOFF_FLATS = (
    # (key, standoff, its socket's clearance before the flat, plastic
    # the flat leaves around the bore)
    ("S141", (76.041, 43.260), 0.627, 0.927),
    ("S150", (94.774, 60.404), 0.487, 0.787),
)
DESIGN_STANDOFF_FLAT_BOTTOM_Z_MM = 4.98
# The right half's sockets (DESIGN.md, "Tray"): the thumb's tab past the
# thumb's outer edge, notched and pocketed like column 0's on the left
# (the same pocket figures), the bottom row's reliefs, and no flats.
DESIGN_RIGHT_TAB_NOTCH_KEYS = {"S163"}
DESIGN_RIGHT_TAB_TIP_PAST_THUMB_EDGE_MM = 0.231
DESIGN_RIGHT_LEDGE_RELIEF_KEYS = {"S103", "S113", "S123", "S133", "S143", "S153", "S163"}
DESIGN_RIGHT_STANDOFF_FLATS = ()
DESIGN_RIGHT_CLOSEST_SOCKET_TO_STANDOFF_MM = 1.391
# Along the slant: boss, four slots, boss.
DESIGN_BOSS_TO_SLOT_GAP_MM = 2.99
DESIGN_SLOT_TO_SLOT_GAP_MM = 2.84
DESIGN_DOWEL_PIN_SPACING_MM = 55.5
DESIGN_DOWEL_PIN_Z_MM = 3.4
# Per half, False the left one, True the right one: how close the
# dowel bosses and their fills come to a socket (S150's on both), and
# the least plastic between two of the joint's holes and slots (the
# lower dowel hole and the parking hole on both).
DESIGN_BOSSES_FROM_SOCKETS_MM = {False: 3.701, True: 1.144}
DESIGN_LEAST_PLASTIC_BETWEEN_VOIDS_MM = {False: 2.09, True: 1.80}
DESIGN_DOWEL_PIN_SLANT_Y_MM = (21.7, 74.5)
# How far the lower boss's south end and the upper boss's north end lie
# inside the outline slant's ends.
DESIGN_DOWEL_BOSSES_INSIDE_SLANT_ENDS_MM = (0.0, 0.006)
DESIGN_PARKING_PIN_PROUD_MM = 1.5
DESIGN_PARKING_BOSS_FROM_SOCKETS_MM = 1.763  # on both halves, the thumb's
DESIGN_MAGNET_SLOT_ABOVE_BED_MM = 0.5
DESIGN_PIN_OFF_HOLE_MM = 0.05  # each blade from its 3.0 hole, along footprint x
DESIGN_PULL_IN_MM = 0.2
DESIGN_DEFAULT_SLIT_MM = (0.6, 1.6)  # across the blade, along it
DESIGN_SLIT_CLEARANCE_MM = (0.2, 0.4)  # per side as modelled: across the blade, along it
# The parts' mounts (work item 004).
DESIGN_MOUNT_FROM_OTHER_PARTS_MM = 0.5  # every mount body from every part but its own
DESIGN_MOUNTS_LEAST_FROM_OTHER_PARTS_MM = 1.8  # the battery's northwest rib, from the nice!nano
DESIGN_MOUNT_VOIDS_FROM_STANDOFFS_MM = 0.5
DESIGN_HOOK_SLOT_FROM_STANDOFF_MM = 0.676  # the hook's deflection slot, the closest void
DESIGN_HOOK_BENDING_LENGTH_MM = 11.0
DESIGN_HOOK_MINIMUM_BENDING_LENGTH_MM = 10.0
DESIGN_HOOK_MAXIMUM_STRAIN_PERCENT = 2.0  # PLA
DESIGN_HOOK_STRAIN_PERCENT = {True: 1.61, False: 0.79}  # as printed, as modelled
DESIGN_HOOK_END_DEFLECTION_MM = 1.50
DESIGN_HOOK_DEFLECTION_ROOM_MM = 1.6  # as printed
DESIGN_HOOK_LIP_X_MM = (11.6, 14.4)
DESIGN_NANO_FREE_MIDDLE_X_MM = (3.105, 16.695)
DESIGN_HOOK_TOP_Z_MM = 3.83
DESIGN_HOOK_UNDER_SOCKET_MM = 2.15
DESIGN_HOOK_SOCKET_KEYS = {"S101"}
DESIGN_SOLE_CUTOUT_X_MM = {False: (0.6, 15.6), True: (116.798, 131.798)}  # per half
DESIGN_SOLE_CUTOUT_Y_MM = (38.566, 42.966)
DESIGN_SOLE_CUTOUT_FROM_STANDOFF_MM = 0.176  # the standoff at (18.574, 37.782)
DESIGN_LEVER_IN_SLOT_PRINTED_MM = 0.05  # per side
DESIGN_NANO_BAR_DEPTH_MM = 0.62
DESIGN_SHELL_PLAY_MM = {"west": 0.05, "east": 0.0, "north": 0.05}  # as printed
DESIGN_SHELL_IN_CHANNEL_PRINTED_MM = {"sides": 0.0, "top": 0.1, "end": 0.0}
DESIGN_RESET_PIN_HOLE_AXIS_MM = (66.199, 1.75)  # x, z
DESIGN_MOUNTS_FROM_PCB_ZONE_PRINTED_MM = 0.1  # the nice!nano's north rib
DESIGN_WIRE_ROOM_BEHIND_LEADS_MM = 3.0
DESIGN_WIRE_ROOM_OVER_PADS_MM = 3.0
DESIGN_WIRE_ROOM_LEAST_CLEARANCE_MM = 0.345
# The nice!nano's pry recess (work item 006), in plan whatever the
# heights: its size as printed, its place, its leverage, the slopes at
# which the tip gets under the board, per half (False the left one), and
# its least clearances, each with the rule's minimum, the clearance None
# where DESIGN.md gives only the minimum.
DESIGN_PRY_RECESS_ACROSS_PRINTED_MM = 4.1  # a 4.0 tip's slip fit
DESIGN_PRY_RECESS_UNDER_BOARD_PRINTED_MM = 1.0
DESIGN_PRY_RECESS_BESIDE_BOARD_PRINTED_MM = 4.0
DESIGN_PRY_RECESS_DEPTH_MM = 0.8
DESIGN_PRY_TOOL_ROOM_PRINTED_MM = 0.6  # its bottom counted 0.2 higher
DESIGN_PRY_RECESS_FLOOR_UNDER_MM = 0.4  # as modelled, also the least
DESIGN_PRY_RECESS_FROM_BATTERY_RIB_MM = 0.5  # north of the northwest rib
DESIGN_PRY_LEVER_RATIO = 2.73
DESIGN_PRY_LIFT_TO_RELEASE_MM = 0.43
DESIGN_PRY_TOOL_DEGREES = {False: (7.3, 10.9), True: (7.3, 10.9)}  # from, to
DESIGN_PRY_RECESS_CLEARANCES_MM = {  # what: (tightest, minimum)
    "the other parts": (1.8, 0.5),  # the battery
    "the standoffs": (None, 0.5),
    "the joint": (None, 1.0),
    "the mount bodies": (0.5, 0.5),  # the battery's northwest rib
    "the hook's slots and their bed chamfers": (None, 1.0),
}


class CheckFailure(Exception):
    pass


def require_figure(label, computed, stated, decimals):
    """A DESIGN.md figure, stated to `decimals` decimals, against the
    layout's: (ok, description)."""
    tolerance = 0.5 * 10.0**-decimals + TOLERANCE_MM
    ok = abs(computed - stated) <= tolerance
    shown = round(computed, decimals + 2) + 0.0  # no "-0.00"
    return ok, f"{label} {shown:.{decimals + 2}f} (DESIGN.md {stated})"


def require_figure_for_all(label, computed_values, stated, decimals):
    """require_figure on the value farthest from the stated one."""
    if not computed_values:
        return False, f"{label}: nothing to measure (DESIGN.md {stated})"
    worst = max(computed_values, key=lambda value: abs(value - stated))
    return require_figure(label, worst, stated, decimals)


def failed(figures):
    return [text for ok, text in figures if not ok]


def joined(figures):
    return ", ".join(text for _, text in figures)


def fail_on(problems, what):
    if problems:
        raise CheckFailure(f"{what}:\n  " + "\n  ".join(problems))


# Plane geometry.


def vector_between(start, end):
    return (end[0] - start[0], end[1] - start[1])


def cross(first, second):
    return first[0] * second[1] - first[1] * second[0]


def dot(first, second):
    return first[0] * second[0] + first[1] * second[1]


def edges(polygon):
    count = len(polygon)
    return [(polygon[index], polygon[(index + 1) % count]) for index in range(count)]


def point_segment_distance(point, start, end):
    segment = vector_between(start, end)
    length_squared = dot(segment, segment)
    if length_squared == 0.0:
        return math.dist(point, start)
    parameter = dot(vector_between(start, point), segment) / length_squared
    parameter = max(0.0, min(1.0, parameter))
    closest = (start[0] + parameter * segment[0], start[1] + parameter * segment[1])
    return math.dist(point, closest)


def segments_cross(first_start, first_end, second_start, second_end):
    """Whether two segments cross at a point inside both."""
    first = vector_between(first_start, first_end)
    second = vector_between(second_start, second_end)
    side_of_second_start = cross(first, vector_between(first_start, second_start))
    side_of_second_end = cross(first, vector_between(first_start, second_end))
    side_of_first_start = cross(second, vector_between(second_start, first_start))
    side_of_first_end = cross(second, vector_between(second_start, first_end))
    return (
        side_of_second_start * side_of_second_end < 0.0
        and side_of_first_start * side_of_first_end < 0.0
    )


def segment_distance(first_start, first_end, second_start, second_end):
    if segments_cross(first_start, first_end, second_start, second_end):
        return 0.0
    return min(
        point_segment_distance(first_start, second_start, second_end),
        point_segment_distance(first_end, second_start, second_end),
        point_segment_distance(second_start, first_start, first_end),
        point_segment_distance(second_end, first_start, first_end),
    )


def boundary_distance(first_polygon, second_polygon):
    return min(
        segment_distance(*first_edge, *second_edge)
        for first_edge in edges(first_polygon)
        for second_edge in edges(second_polygon)
    )


def point_boundary_distance(point, polygon):
    return min(point_segment_distance(point, *edge) for edge in edges(polygon))


def point_in_polygon(point, polygon):
    """Ray casting; a point on the boundary may land on either side."""
    inside = False
    for start, end in edges(polygon):
        if (start[1] > point[1]) != (end[1] > point[1]):
            fraction = (point[1] - start[1]) / (end[1] - start[1])
            if point[0] < start[0] + fraction * (end[0] - start[0]):
                inside = not inside
    return inside


def signed_point_distance(point, polygon):
    """Distance to the polygon's boundary, negative outside."""
    distance = point_boundary_distance(point, polygon)
    if distance <= TOLERANCE_MM or point_in_polygon(point, polygon):
        return distance
    return -distance


def is_convex(polygon):
    turns = [
        cross(vector_between(before, corner), vector_between(corner, after))
        for before, corner, after in zip(
            polygon[-1:] + polygon[:-1], polygon, polygon[1:] + polygon[:1]
        )
    ]
    return all(turn >= -TOLERANCE_MM for turn in turns) or all(
        turn <= TOLERANCE_MM for turn in turns
    )


def separating_axis_gap(first_polygon, second_polygon):
    """The widest gap between two convex polygons' projections onto any
    edge normal: positive when separated, its negative the overlap."""
    best = -math.inf
    for polygon in (first_polygon, second_polygon):
        for start, end in edges(polygon):
            edge = vector_between(start, end)
            length = math.hypot(*edge)
            axis = (edge[1] / length, -edge[0] / length)
            first_values = [dot(point, axis) for point in first_polygon]
            second_values = [dot(point, axis) for point in second_polygon]
            gap = max(
                min(second_values) - max(first_values),
                min(first_values) - max(second_values),
            )
            best = max(best, gap)
    return best


def convex_separation(first_polygon, second_polygon):
    """Clearance between two convex polygons: the distance between them,
    zero when they touch, negative (by how much) when they overlap."""
    gap = separating_axis_gap(first_polygon, second_polygon)
    if gap < -TOLERANCE_MM:
        return gap
    return boundary_distance(first_polygon, second_polygon)


def circle_separation(center, radius, convex_polygon):
    """Clearance between a circle and a convex polygon, negative when
    they overlap."""
    distance = point_boundary_distance(center, convex_polygon)
    if point_in_polygon(center, convex_polygon):
        distance = -distance
    return distance - radius


def containment_margin(inner_polygon, outer_polygon):
    """How far a convex polygon stays inside a simple one: its distance
    to the outer boundary, negative (by how much) when it pokes out."""
    corner_depths = [signed_point_distance(corner, outer_polygon) for corner in inner_polygon]
    if min(corner_depths) < -TOLERANCE_MM:
        return min(corner_depths)
    poking_in = [
        point_boundary_distance(vertex, inner_polygon)
        for vertex in outer_polygon
        if point_in_polygon(vertex, inner_polygon)
        and point_boundary_distance(vertex, inner_polygon) > TOLERANCE_MM
    ]
    if poking_in:
        return -max(poking_in)
    return boundary_distance(inner_polygon, outer_polygon)


def clip_to_half_plane(polygon, normal, limit):
    """The part of a convex polygon where dot(point, normal) <= limit."""
    clipped = []
    for start, end in edges(polygon):
        start_value = dot(start, normal) - limit
        end_value = dot(end, normal) - limit
        if start_value <= 0.0:
            clipped.append(start)
        if start_value * end_value < 0.0:
            fraction = start_value / (start_value - end_value)
            clipped.append(
                (
                    start[0] + fraction * (end[0] - start[0]),
                    start[1] + fraction * (end[1] - start[1]),
                )
            )
    return tuple(clipped)


def half_planes(polygon):
    """(normal, limit) of a counter-clockwise convex polygon's sides: a
    point inside has dot(point, normal) <= limit for each."""
    planes = []
    for start, end in edges(polygon):
        side = vector_between(start, end)
        length = math.hypot(*side)
        normal = (side[1] / length, -side[0] / length)
        planes.append((normal, dot(start, normal)))
    return planes


def split_cells(cells, normal, limit):
    """Convex cells cut in two along the line dot(point, normal) =
    limit, slivers dropped."""
    opposite = (-normal[0], -normal[1])
    halves = []
    for cell in cells:
        halves.append(clip_to_half_plane(cell, normal, limit))
        halves.append(clip_to_half_plane(cell, opposite, -limit))
    return [half for half in halves if len(half) >= 3 and polygon_area(half) > TOLERANCE_MM]


def polygon_area(polygon):
    return abs(layout.polygon_signed_area(polygon))


def polygon_centroid(polygon):
    """The vertices' mean: inside a convex polygon."""
    count = len(polygon)
    return (sum(x for x, _ in polygon) / count, sum(y for _, y in polygon) / count)


def box_polygon(envelope):
    (low_x, high_x), (low_y, high_y) = envelope.x_range, envelope.y_range
    return ((low_x, low_y), (high_x, low_y), (high_x, high_y), (low_x, high_y))


def ranges_overlap(first, second):
    return min(first[1], second[1]) - max(first[0], second[0]) > TOLERANCE_MM


def subtract_ranges(kept_range, removed_ranges):
    """What is left of a range with others taken out, as ranges."""
    remaining = [kept_range]
    for removed_low, removed_high in removed_ranges:
        split = []
        for low, high in remaining:
            split.append((low, min(high, removed_low)))
            split.append((max(low, removed_high), high))
        remaining = [(low, high) for low, high in split if high - low > TOLERANCE_MM]
    return remaining


def describe_envelope(envelope):
    return f"{envelope.part} {envelope.piece}"


def describe_piece(label, z_range):
    return f"{label} (z {z_range[0]:.2f} to {z_range[1]:.2f})"


def describe_extent(polygon):
    xs = [x for x, _ in polygon]
    ys = [y for _, y in polygon]
    return f"x {min(xs):.3f} to {max(xs):.3f}, y {min(ys):.3f} to {max(ys):.3f}"


class Tightest:
    """The smallest margin seen, and where."""

    def __init__(self):
        self.value = math.inf
        self.where = "nothing checked"

    def update(self, value, where):
        if value < self.value:
            self.value = value
            self.where = where

    def __str__(self):
        return f"{self.value:.3f} ({self.where})"


# The tray and the sockets as obstacles.


def socket_z_range():
    return (layout.SOCKET_BOTTOM_Z_MM, layout.PCB_UNDERSIDE_Z_MM)


def standoff_z_range():
    return (0.0, layout.STANDOFF_HEIGHT_MM)


def ledge_z_range():
    return (0.0, layout.PCB_UNDERSIDE_Z_MM)


def wall_z_range():
    return (layout.FLOOR_UNDERSIDE_Z_MM, layout.TRAY_RIM_Z_MM)


def half_label(right):
    """What starts a check's line for the right half."""
    return "right half: " if right else ""


def socket_footprints(right=False):
    """(key name, convex polygon) for every socket polygon on the given
    half, in the left half's frame."""
    return [
        (name, polygon)
        for name in layout.KEY_CENTERS_MM
        for polygon in layout.socket_polygons_on_half(name, right)
    ]


def ring_pieces(outer_polygon, inner_polygon):
    """The quadrilaterals between two offsets of the outline, one per
    outline edge: piece i lies between the polygons' edges i."""
    count = len(outer_polygon)
    return [
        (
            outer_polygon[index],
            outer_polygon[(index + 1) % count],
            inner_polygon[(index + 1) % count],
            inner_polygon[index],
        )
        for index in range(count)
    ]


def cutaway_cut(cutaway):
    """A ledge cut-away as layout.py cuts it."""
    try:
        return layout.ledge_cutaway_cut(cutaway)
    except ValueError as error:
        raise CheckFailure(str(error))


def cut_piece(label, polygon, z_range, cuts):
    """(label, convex polygon, z range) of what the cuts leave of a
    convex tray piece standing over z_range: the piece split along the
    sides of every cut reaching into it, each cell keeping z_range less
    the cuts over it."""
    rectangles = [(cut, layout.tray_cut_polygon(cut)) for cut in cuts]
    reaching = [
        (cut, rectangle)
        for cut, rectangle in rectangles
        if convex_separation(polygon, rectangle) < -TOLERANCE_MM
    ]
    cells = [polygon]
    for _cut, rectangle in reaching:
        for normal, limit in half_planes(rectangle):
            cells = split_cells(cells, normal, limit)
    pieces = []
    for cell in cells:
        middle = polygon_centroid(cell)
        removed = [
            cut.z_range for cut, rectangle in reaching if point_in_polygon(middle, rectangle)
        ]
        pieces.extend((label, cell, remaining) for remaining in subtract_ranges(z_range, removed))
    return pieces


def ledge_pieces(right=False):
    """(label, convex polygon, z range) of the given half's ledge and
    joint block as cut: DESIGN.md's cut-aways and the sockets' notches,
    pockets and reliefs taken out."""
    cuts = [cutaway_cut(cutaway) for cutaway in layout.LEDGE_CUTAWAYS]
    cuts.extend(layout.all_socket_tray_cuts(right))
    rings = ring_pieces(layout.tray_cavity_polygon(), layout.ledge_inner_polygon())
    pieces = []
    for index, ring_piece in enumerate(rings):
        if index == layout.SLANT_EDGE_INDEX:
            label = "joint block"
        else:
            label = f"ledge along outline edge {index}"
        pieces.extend(cut_piece(label, ring_piece, ledge_z_range(), cuts))
    return pieces


def wall_pieces(right=False):
    """(label, convex polygon, z range) of the given half's wall between
    the cavity and the outer face, the sockets' tab pockets taken out of
    it."""
    pockets = [cut for cut in layout.all_socket_tray_cuts(right) if cut.cuts_wall]
    rings = ring_pieces(layout.tray_outer_polygon(), layout.tray_cavity_polygon())
    pieces = []
    for index, ring_piece in enumerate(rings):
        label = f"wall along outline edge {index}"
        pieces.extend(cut_piece(label, ring_piece, wall_z_range(), pockets))
    return pieces


def standoff_bands(center, right=False):
    """(z range, flats) of a standoff's height bands on the given half,
    with the sockets' flats cut into each band."""
    flats = [
        flat
        for flat in layout.all_socket_standoff_flats(right)
        if flat.standoff_center == center
    ]
    bounds = sorted(set(standoff_z_range()) | {z for flat in flats for z in flat.z_range})
    return [
        (
            (low, high),
            [
                flat
                for flat in flats
                if flat.z_range[0] <= low + TOLERANCE_MM and high <= flat.z_range[1] + TOLERANCE_MM
            ],
        )
        for low, high in zip(bounds, bounds[1:])
    ]


def standoff_clearance(center, flats, convex_polygon):
    """The clearance between a convex polygon and a standoff with flats,
    bounded from below: the larger of the full circle's and, for each
    flat, how far the polygon lies beyond the flat's plane. Exact
    without flats, and where the polygon's nearest point faces a flat's
    middle, as the rule places each flat."""
    bound = circle_separation(center, layout.STANDOFF_DIAMETER_MM / 2.0, convex_polygon)
    for flat in flats:
        nearest = min(
            dot(vector_between(center, corner), flat.toward) for corner in convex_polygon
        )
        bound = max(bound, nearest - flat.plane_distance)
    return bound


def socket_clearances(obstacles, minimum, right=False):
    """(problems, tightest) of every socket polygon on the given half
    against (label, convex polygon, z range) obstacles wherever their z
    ranges overlap."""
    problems = []
    tightest = Tightest()
    for name, socket in socket_footprints(right):
        for label, polygon, z_range in obstacles:
            if not ranges_overlap(z_range, socket_z_range()):
                continue
            clearance = convex_separation(socket, polygon)
            where = f"{name}'s socket and the {describe_piece(label, z_range)}"
            tightest.update(clearance, where)
            if clearance < minimum - TOLERANCE_MM:
                problems.append(f"{where}: {clearance:.3f}, less than {minimum}")
    return problems, tightest


# The checks, in order.


def outline_shape_problems(polygon):
    """What keeps a polygon from being a closed counter-clockwise one
    with no zero-length edge and no doubling back."""
    problems = [f"only {len(polygon)} vertices"] if len(polygon) < 3 else []
    for index, (start, end) in enumerate(edges(polygon)):
        if math.dist(start, end) <= TOLERANCE_MM:
            problems.append(f"edge {index} has no length")
    for index, turn in enumerate(layout.corner_turn_angles(polygon)):
        if abs(abs(turn) - math.pi) < 1e-9:
            problems.append(f"the outline doubles back at vertex {index} {polygon[index]}")
    area = layout.polygon_signed_area(polygon)
    if area <= 0.0:
        problems.append(f"signed area {area:.3f}: not counter-clockwise")
    return problems


def non_adjacent_edge_problems(polygon):
    """(problems, tightest) over the pairs of edges that share no
    vertex: any that touch or cross."""
    all_edges = edges(polygon)
    count = len(all_edges)
    problems = []
    tightest = Tightest()
    for first, second in itertools.combinations(range(count), 2):
        if second - first == 1 or (first == 0 and second == count - 1):
            continue  # adjacent
        distance = segment_distance(*all_edges[first], *all_edges[second])
        tightest.update(distance, f"edges {first} and {second}")
        if distance <= TOLERANCE_MM:
            problems.append(f"edges {first} and {second} touch or cross")
    return problems, tightest


def check_outline():
    polygon = layout.OUTLINE_VERTICES_MM
    edge_problems, tightest = non_adjacent_edge_problems(polygon)
    fail_on(
        outline_shape_problems(polygon) + edge_problems,
        "the outline is not a simple closed polygon",
    )
    width = max(x for x, _ in polygon) - min(x for x, _ in polygon)
    height = max(y for _, y in polygon) - min(y for _, y in polygon)
    figures = [
        require_figure("width", width, DESIGN_HALF_SIZE_MM[0], 1),
        require_figure("height", height, DESIGN_HALF_SIZE_MM[1], 1),
        require_figure(
            "mirror line x", layout.RIGHT_HALF_MIRROR_X_MM, DESIGN_MIRROR_LINE_X_MM, 3
        ),
    ]
    fail_on(failed(figures), "the half's size or mirror line differs from DESIGN.md")
    area = layout.polygon_signed_area(polygon)
    return (
        f"outline:   simple, closed, counter-clockwise, {len(polygon)} corners, "
        f"{area:.1f} mm2, closest non-adjacent edges {tightest}; " + joined(figures)
    )


def key_cells():
    """(x range, y range) of every key's 19.05 square cell."""
    half = layout.KEY_PITCH_MM / 2.0
    return [
        ((x - half, x + half), (y - half, y + half)) for x, y in layout.KEY_CENTERS_MM.values()
    ]


def horizontal_edge_target(start, end):
    """(what, the edge's y moved by its inset, the cell y values it may
    meet) of a horizontal outline edge. The outline runs
    counter-clockwise, so a south edge runs east."""
    x_range = (min(start[0], end[0]), max(start[0], end[0]))
    y_ranges = [y_range for cell_x, y_range in key_cells() if ranges_overlap(cell_x, x_range)]
    if not y_ranges:
        return "a cell", start[1], []
    if end[0] > start[0]:
        lowest = min(low for low, _ in y_ranges)
        what = "the lowest cell's bottom moved in by the south inset"
        return what, start[1] - layout.CELL_INSET_SOUTH_MM, [lowest]
    highest = max(high for _, high in y_ranges)
    what = "the highest cell's top moved in by the north inset"
    return what, start[1] + layout.CELL_INSET_NORTH_MM, [highest]


def vertical_edge_target(start, end, outline_x_range):
    """(what, the edge's x moved by its inset, the cell x values it may
    meet) of a vertical outline edge: the west and east edges are inset,
    the risers between steps lie on a cell's side."""
    y_range = (min(start[1], end[1]), max(start[1], end[1]))
    x_ranges = [x_range for x_range, cell_y in key_cells() if ranges_overlap(cell_y, y_range)]
    if not x_ranges:
        return "a cell", start[0], []
    if abs(start[0] - outline_x_range[0]) <= TOLERANCE_MM:
        westmost = min(low for low, _ in x_ranges)
        what = "the westmost cell's west side moved in by the west inset"
        return what, start[0] - layout.CELL_INSET_WEST_MM, [westmost]
    if abs(start[0] - outline_x_range[1]) <= TOLERANCE_MM:
        eastmost = max(high for _, high in x_ranges)
        what = "the eastmost cell's east side moved in by the east inset"
        return what, start[0] + layout.CELL_INSET_EAST_MM, [eastmost]
    return "a cell's west or east side", start[0], [x for x_range in x_ranges for x in x_range]


def outline_edge_target(start, end, outline_x_range):
    if abs(start[1] - end[1]) <= TOLERANCE_MM:
        return horizontal_edge_target(start, end)
    if abs(start[0] - end[0]) <= TOLERANCE_MM:
        return vertical_edge_target(start, end, outline_x_range)
    return None


def check_outline_on_cells():
    """Every outline edge but the slant lies on the key cells moved in
    by DESIGN.md's insets (the slant has its own check)."""
    outline = layout.OUTLINE_VERTICES_MM
    outline_x_range = (min(x for x, _ in outline), max(x for x, _ in outline))
    problems = []
    worst_error, worst_where = 0.0, "no edge"
    for index, (start, end) in enumerate(edges(outline)):
        if index == layout.SLANT_EDGE_INDEX:
            continue
        where = f"edge {index} {start} to {end}"
        target = outline_edge_target(start, end, outline_x_range)
        if target is None:
            problems.append(f"{where} is neither the slant nor parallel to an axis")
            continue
        what, coordinate, candidates = target
        if not candidates:
            problems.append(f"{where} has no key cell beside it")
            continue
        error = min(abs(coordinate - candidate) for candidate in candidates)
        if error > worst_error:
            worst_error, worst_where = error, where
        if error > OUTLINE_ON_CELLS_TOLERANCE_MM:
            problems.append(f"{where} lies {error:.4f} off {what}")
    fail_on(problems, "the outline does not follow the key cells and DESIGN.md's insets")
    return (
        f"cells:     every outline edge but the slant on the key cells moved in by the insets, "
        f"off by {worst_error:.4f} at most ({worst_where})"
    )


def check_slant():
    thumb_corner = layout.key_cell_top_right_corner(layout.THUMB_KEY_CENTER_MM)
    column_5_corner = layout.key_cell_top_right_corner(
        layout.KEY_CENTERS_MM[layout.TOP_ROW_KEY_OF_COLUMN_5]
    )
    inset = (-layout.CELL_INSET_EAST_MM, -layout.CELL_INSET_NORTH_MM)
    problems = []
    worst_end_error = 0.0
    for label, corner, end in (
        ("south", thumb_corner, layout.SLANT_SOUTH_END_MM),
        ("north", column_5_corner, layout.SLANT_NORTH_END_MM),
    ):
        expected = (corner[0] + inset[0], corner[1] + inset[1])
        error = math.dist(expected, end)
        worst_end_error = max(worst_end_error, error)
        if error > 0.0005:
            problems.append(
                f"the {label} end {end} is {error:.4f} from the cell corner {corner} "
                f"moved in by the insets, {expected}"
            )
    corner_line = vector_between(thumb_corner, column_5_corner)
    slant = layout.slant_vector()
    sine = cross(corner_line, slant) / (math.hypot(*corner_line) * math.hypot(*slant))
    if abs(sine) > 1e-9:
        problems.append(f"the slant is not parallel to the corner to corner line (sine {sine:.2e})")
    offset = -dot(
        vector_between(thumb_corner, layout.SLANT_SOUTH_END_MM), layout.slant_outward_normal()
    )
    angle = math.degrees(math.atan2(-slant[0], slant[1]))
    figures = [
        require_figure(
            "offset inside the corner to corner line", offset, DESIGN_SLANT_OFFSET_MM, 3
        ),
        require_figure("length", layout.slant_length(), DESIGN_SLANT_LENGTH_MM, 2),
        require_figure("degrees from north", angle, DESIGN_SLANT_ANGLE_FROM_NORTH_DEGREES, 2),
    ]
    fail_on(problems + failed(figures), "the slant does not run as DESIGN.md states")
    return (
        f"slant:     ends at the cell corners less the insets (off by {worst_end_error:.4f} at "
        f"most), " + joined(figures)
    )


def check_keys_and_holes():
    outline = layout.OUTLINE_VERTICES_MM
    minimum = INSIDE_OUTLINE_MINIMUM_MARGIN_MM
    problems = []
    centers = Tightest()
    holes = Tightest()
    hole_count = 0
    for name, center in layout.KEY_CENTERS_MM.items():
        margin = signed_point_distance(center, outline)
        centers.update(margin, name)
        if margin < minimum:
            problems.append(f"{name}'s center {center} is {margin:.3f} inside the outline")
        for hole_center, diameter in layout.footprint_holes(center):
            hole_count += 1
            margin = signed_point_distance(hole_center, outline) - diameter / 2.0
            where = f"{name}'s {diameter} hole at ({hole_center[0]:.3f}, {hole_center[1]:.3f})"
            holes.update(margin, where)
            if margin < minimum:
                problems.append(f"{where} is {margin:.3f} inside the outline")
    fail_on(problems, f"keys or holes closer than {minimum} to the outline")
    return (
        f"keys:      {len(layout.KEY_CENTERS_MM)} centers inside the outline, tightest "
        f"{centers}; {hole_count} footprint holes, tightest edge {holes}"
    )


def footprint_extents(key_center, polygon):
    """((low, high) along footprint x, (low, high) along footprint y)
    of a polygon around a key's footprint origin."""
    origin = layout.footprint_point(key_center, (0.0, 0.0))
    extents = []
    for unit in ((1.0, 0.0), (0.0, 1.0)):
        axis = vector_between(origin, layout.footprint_point(key_center, unit))
        values = [dot(vector_between(origin, point), axis) for point in polygon]
        extents.append((min(values), max(values)))
    return extents


def pin_hole_problems():
    """Where a blade (the STEP model's) and its 3.0 hole (the package's)
    are not a pair: not a 3.0 hole, or off along footprint y."""
    problems = []
    holes = dict(layout.CHOC_FOOTPRINT_HOLES_MM)
    pairs = zip(layout.CHOC_PIN_CENTERS_MM, layout.CHOC_FOOTPRINT_PIN_HOLE_CENTERS_MM)
    for pin, hole in pairs:
        if holes.get(hole) != 3.0:
            problems.append(f"the pin hole at {hole} is not one of the footprint's 3.0 holes")
        if abs(pin[1] - hole[1]) > TOLERANCE_MM:
            problems.append(f"the blade at {pin} is off its hole at {hole} along footprint y")
    if len(layout.CHOC_PIN_CENTERS_MM) != len(layout.CHOC_FOOTPRINT_PIN_HOLE_CENTERS_MM):
        problems.append("the blades and the pin holes differ in number")
    return problems


def blade_slit_margins():
    """(slit sizes, blade margins) of every key's blades in their
    default slits, each as (across the blade, along it): the blade's
    thickness along footprint x, its slit's width likewise."""
    width = layout.default_slit_width(DESIGN_PULL_IN_MM)
    length = layout.default_slit_length(DESIGN_PULL_IN_MM)
    sizes = []
    margins = []
    for center in layout.KEY_CENTERS_MM.values():
        slits = layout.pin_slits(center, length, width)
        for pin, slit in zip(layout.CHOC_PIN_CENTERS_MM, slits):
            blade = layout.footprint_rectangle(
                center, pin, layout.CHOC_PIN_BLADE_THICKNESS_MM, layout.CHOC_PIN_BLADE_WIDTH_MM
            )
            slit_extents = footprint_extents(center, slit)
            blade_extents = footprint_extents(center, blade)
            sizes.append(tuple(high - low for low, high in slit_extents))
            margins.append(tuple(
                min(blade_low - slit_low, slit_high - blade_high)
                for (slit_low, slit_high), (blade_low, blade_high)
                in zip(slit_extents, blade_extents)
            ))
    return sizes, margins


def check_switch_pins():
    fail_on(pin_hole_problems(), "the blades against the footprint's pin holes")
    offsets = [
        abs(pin[0] - hole[0])
        for pin, hole in zip(layout.CHOC_PIN_CENTERS_MM, layout.CHOC_FOOTPRINT_PIN_HOLE_CENTERS_MM)
    ]
    sizes, margins = blade_slit_margins()
    figures = [
        require_figure_for_all("blades from their 3.0 holes", offsets, DESIGN_PIN_OFF_HOLE_MM, 2),
        require_figure_for_all(
            "default slits across", [size[0] for size in sizes], DESIGN_DEFAULT_SLIT_MM[0], 1
        ),
        require_figure_for_all(
            "along", [size[1] for size in sizes], DESIGN_DEFAULT_SLIT_MM[1], 1
        ),
        require_figure_for_all(
            "blade clearance per side across",
            [margin[0] for margin in margins],
            DESIGN_SLIT_CLEARANCE_MM[0],
            1,
        ),
        require_figure_for_all(
            "along", [margin[1] for margin in margins], DESIGN_SLIT_CLEARANCE_MM[1], 1
        ),
    ]
    fail_on(failed(figures), "the blades or their slits off DESIGN.md's figures")
    return f"pins:      {len(margins)} blades, " + joined(figures)


def drill_switch_problems(drill, radius):
    """(problems, tightest from the holes, tightest from the sockets) of
    a mounting drill against every key's footprint holes and socket."""
    problems = []
    from_holes = Tightest()
    from_sockets = Tightest()
    for name, center in layout.KEY_CENTERS_MM.items():
        for hole_center, diameter in layout.footprint_holes(center):
            clearance = math.dist(drill, hole_center) - radius - diameter / 2.0
            from_holes.update(clearance, f"drill {drill} and {name}'s {diameter} hole")
            if clearance < -TOLERANCE_MM:
                problems.append(
                    f"drill {drill} overlaps {name}'s {diameter} hole by {-clearance:.3f}"
                )
    for name, polygon in socket_footprints():
        clearance = circle_separation(drill, radius, polygon)
        from_sockets.update(clearance, f"drill {drill} and {name}'s socket")
        if clearance < -TOLERANCE_MM:
            problems.append(f"drill {drill} overlaps {name}'s socket by {-clearance:.3f}")
    return problems, from_holes, from_sockets


def check_mounting_drills():
    outline = layout.OUTLINE_VERTICES_MM
    radius = layout.MOUNTING_DRILL_DIAMETER_MM / 2.0
    problems = []
    inside = Tightest()
    from_holes = Tightest()
    from_sockets = Tightest()
    for drill in layout.MOUNTING_DRILL_CENTERS_MM:
        margin = signed_point_distance(drill, outline) - radius
        inside.update(margin, f"drill {drill}")
        if margin < INSIDE_OUTLINE_MINIMUM_MARGIN_MM:
            problems.append(f"drill {drill} is {margin:.3f} inside the outline")
        switch_problems, holes, sockets = drill_switch_problems(drill, radius)
        problems.extend(switch_problems)
        from_holes.update(holes.value, holes.where)
        from_sockets.update(sockets.value, sockets.where)
    fail_on(problems, "mounting drills off the board or on a switch")
    return (
        f"drills:    {len(layout.MOUNTING_DRILL_CENTERS_MM)} inside the outline, tightest edge "
        f"{inside}; clear of the switch holes by {from_holes}, of the sockets by {from_sockets}"
    )


def check_heights():
    computed = (
        layout.SOCKET_BOTTOM_Z_MM,
        layout.PCB_TOP_Z_MM,
        layout.PLATE_TOP_Z_MM,
        layout.TRAY_RIM_Z_MM,
    )
    figures = [
        require_figure(what, z, stated, 2)
        for (what, stated), z in zip(DESIGN_HEIGHTS_Z_MM, computed)
    ]
    tray_height = layout.TRAY_RIM_Z_MM - layout.FLOOR_UNDERSIDE_Z_MM
    figures.append(require_figure("tray height", tray_height, DESIGN_TRAY_HEIGHT_MM, 1))
    figures.append(
        require_figure(
            "lowest PCB underside",
            layout.MINIMUM_PCB_UNDERSIDE_Z_MM,
            DESIGN_MINIMUM_PCB_UNDERSIDE_Z_MM,
            2,
        )
    )
    problems = failed(figures)
    if layout.PCB_UNDERSIDE_Z_MM < layout.MINIMUM_PCB_UNDERSIDE_Z_MM:
        problems.append(
            f"the PCB underside at {layout.PCB_UNDERSIDE_Z_MM} is below the "
            f"{layout.MINIMUM_PCB_UNDERSIDE_Z_MM:.2f} the battery needs under the sockets"
        )
    fail_on(problems, "the heights differ from DESIGN.md's table")
    return f"heights:   PCB underside {layout.PCB_UNDERSIDE_Z_MM}, " + joined(figures)


def nano_figures():
    west_ledge_face_x = min(x for x, _ in layout.OUTLINE_VERTICES_MM) + layout.ledge_reach()
    nano = layout.NANO_BOARD
    north_outer_face_y = layout.outer_face_y(layout.NORTH_EDGE_Y_OF_COLUMNS_0_AND_1_MM)
    return [
        require_figure(
            "nice!nano width", nano.x_range[1] - nano.x_range[0], DESIGN_NANO_SIZE_MM[0], 1
        ),
        require_figure(
            "nice!nano length", nano.y_range[1] - nano.y_range[0], DESIGN_NANO_SIZE_MM[1], 1
        ),
        require_figure(
            "nice!nano from the west ledge's face",
            nano.x_range[0] - west_ledge_face_x,
            DESIGN_NANO_FROM_WEST_LEDGE_FACE_MM,
            1,
        ),
        require_figure(
            "USB mouth behind the north wall's outer face",
            north_outer_face_y - layout.NANO_USB_SHELL.y_range[1],
            DESIGN_NANO_USB_MOUTH_BEHIND_OUTER_FACE_MM,
            1,
        ),
    ]


def power_switch_figures():
    north_edge_y = layout.NORTH_EDGE_Y_OF_COLUMN_2_MM
    return [
        require_figure(
            "power switch's north face past the cavity wall",
            layout.POWER_SWITCH_BODY.y_range[1] - layout.cavity_wall_y(north_edge_y),
            0.0,
            3,
        ),
        require_figure(
            "lever proud of the outer face",
            layout.POWER_SWITCH_LEVER.y_range[1] - layout.outer_face_y(north_edge_y),
            DESIGN_POWER_SWITCH_LEVER_PROUD_MM[False],
            1,
        ),
        require_figure(
            "as printed", lever_proud_as_printed(), DESIGN_POWER_SWITCH_LEVER_PROUD_MM[True], 1
        ),
    ]


def lever_proud_as_printed():
    """The lever's tip past the outer face as printed: the swollen wall
    pushes the snug body south, and the outer face swells north."""
    north_edge_y = layout.NORTH_EDGE_Y_OF_COLUMN_2_MM
    swelling = layout.PRINT_SWELLING_PER_SIDE_MM
    lever_past_body = layout.POWER_SWITCH_LEVER.y_range[1] - layout.POWER_SWITCH_BODY.y_range[1]
    tip = layout.cavity_wall_y(north_edge_y) - swelling + lever_past_body
    return tip - (layout.outer_face_y(north_edge_y) + swelling)


def battery_figures():
    battery = layout.BATTERY
    return [
        require_figure(
            "battery width", battery.x_range[1] - battery.x_range[0], DESIGN_BATTERY_SIZE_MM[0], 2
        ),
        require_figure(
            "battery length", battery.y_range[1] - battery.y_range[0], DESIGN_BATTERY_SIZE_MM[1], 2
        ),
    ]


def check_part_figures():
    figures = nano_figures() + power_switch_figures() + battery_figures()
    fail_on(failed(figures), "parts placed off DESIGN.md's figures")
    return "figures:   " + joined(figures)


def check_part_containment():
    cavity = layout.tray_cavity_polygon()
    outer = layout.tray_outer_polygon()
    problems = []
    in_cavity = Tightest()
    in_outer = Tightest()
    for envelope in layout.PART_ENVELOPES:
        if envelope.containment == layout.PROUD:
            continue
        inside_cavity = envelope.containment == layout.CAVITY
        region = cavity if inside_cavity else outer
        margin = containment_margin(box_polygon(envelope), region)
        (in_cavity if inside_cavity else in_outer).update(margin, describe_envelope(envelope))
        if margin < -TOLERANCE_MM:
            boundary = "cavity wall" if inside_cavity else "outer face"
            problems.append(
                f"{describe_envelope(envelope)} pokes {-margin:.3f} past the {boundary}"
            )
    fail_on(problems, "parts outside the tray")
    return (
        f"parts:     inside the cavity wall by {in_cavity}; through the wall, inside its outer "
        f"face by {in_outer}"
    )


def part_ledge_problems(pieces):
    """(problems, tightest) of every part against the ledge pieces."""
    problems = []
    tightest = Tightest()
    for envelope in layout.PART_ENVELOPES:
        box = box_polygon(envelope)
        for label, piece, z_range in pieces:
            if not ranges_overlap(envelope.z_range, z_range):
                continue
            clearance = convex_separation(box, piece)
            where = f"{describe_envelope(envelope)} and the {describe_piece(label, z_range)}"
            tightest.update(clearance, where)
            if clearance < -TOLERANCE_MM:
                problems.append(
                    f"{describe_envelope(envelope)} reaches {-clearance:.3f} into the "
                    f"{describe_piece(label, z_range)} ({describe_extent(piece)})"
                )
    return problems, tightest


def ledge_clearance(envelope, pieces):
    return min(
        convex_separation(box_polygon(envelope), piece)
        for _label, piece, z_range in pieces
        if ranges_overlap(envelope.z_range, z_range)
    )


def check_part_ledge():
    pieces = ledge_pieces()
    broken = [
        f"the {describe_piece(label, z_range)} is not convex"
        for label, piece, z_range in pieces
        if not is_convex(piece)
    ]
    fail_on(broken, "the ledge model is broken")
    problems, tightest = part_ledge_problems(pieces)
    cut_away_for = ", ".join(cutaway.part for cutaway in layout.LEDGE_CUTAWAYS)
    fail_on(problems, f"parts in the ledge (DESIGN.md cuts it away only over the {cut_away_for})")
    figures = [
        require_figure(
            "battery from the ledge",
            ledge_clearance(layout.BATTERY, pieces),
            DESIGN_BATTERY_FROM_LEDGE_MM,
            2,
        ),
        require_figure(
            "PCB connector clear zone from the ledge",
            ledge_clearance(layout.PCB_CONNECTOR_CLEAR_ZONE, pieces),
            DESIGN_PCB_CONNECTOR_CLEAR_ZONE_FROM_LEDGE_MM,
            2,
        ),
    ]
    fail_on(failed(figures), "ledge clearances off DESIGN.md's figures")
    return f"ledge:     parts clear of the ledge and the joint block by {tightest}; " + joined(
        figures
    )


def check_part_standoffs():
    radius = layout.STANDOFF_DIAMETER_MM / 2.0
    problems = []
    tightest = Tightest()
    for envelope in layout.PART_ENVELOPES:
        if not ranges_overlap(envelope.z_range, standoff_z_range()):
            continue
        for center in layout.MOUNTING_DRILL_CENTERS_MM:
            clearance = circle_separation(center, radius, box_polygon(envelope))
            where = f"{describe_envelope(envelope)} and the standoff at {center}"
            tightest.update(clearance, where)
            if clearance < -TOLERANCE_MM:
                problems.append(f"{where} overlap by {-clearance:.3f}")
    fail_on(problems, "parts on the standoffs")
    battery = min(
        circle_separation(center, radius, box_polygon(layout.BATTERY))
        for center in layout.MOUNTING_DRILL_CENTERS_MM
    )
    ok, text = require_figure(
        "battery from the standoffs", battery, DESIGN_BATTERY_FROM_STANDOFFS_MM, 2
    )
    fail_on([] if ok else [text], "the battery's standoff clearance is off DESIGN.md's figure")
    return f"standoffs: parts clear by {tightest}; {text}"


def check_parts_apart():
    problems = []
    tightest = Tightest()
    for first, second in itertools.combinations(layout.PART_ENVELOPES, 2):
        if first.part == second.part or not ranges_overlap(first.z_range, second.z_range):
            continue
        clearance = convex_separation(box_polygon(first), box_polygon(second))
        where = f"{describe_envelope(first)} and {describe_envelope(second)}"
        tightest.update(clearance, where)
        if clearance < -TOLERANCE_MM:
            problems.append(f"{where} overlap by {-clearance:.3f}")
    fail_on(problems, "parts on each other (the PCB connector's clear zone counts as a part)")
    return f"apart:     parts and the PCB connector's clear zone clear of each other by {tightest}"


def check_part_sockets(right=False):
    problems = []
    tightest = Tightest()
    for envelope in layout.PART_ENVELOPES:
        if not ranges_overlap(envelope.z_range, socket_z_range()):
            continue
        for name, polygon in socket_footprints(right):
            clearance = convex_separation(box_polygon(envelope), polygon)
            where = f"{describe_envelope(envelope)} and {name}'s socket"
            tightest.update(clearance, where)
            if clearance < -TOLERANCE_MM:
                problems.append(f"{where} overlap by {-clearance:.3f}")
    fail_on(problems, "parts under the sockets at their height")
    highest_other = max(
        envelope.z_range[1]
        for envelope in layout.PART_ENVELOPES
        if not ranges_overlap(envelope.z_range, socket_z_range())
    )
    return (
        f"sockets:   {half_label(right)}parts reaching their height clear in plan by {tightest}; "
        f"every other part stays {layout.SOCKET_BOTTOM_Z_MM - highest_other:.3f} below them"
    )


def check_battery(right=False):
    battery = box_polygon(layout.BATTERY)
    covering_keys = sorted(
        {
            name
            for name, polygon in socket_footprints(right)
            if convex_separation(battery, polygon) < -TOLERANCE_MM
        }
    )
    clearance = layout.SOCKET_BOTTOM_Z_MM - layout.BATTERY.z_range[1]
    ok, clearance_text = require_figure(
        "below them", clearance, DESIGN_BATTERY_BELOW_SOCKETS_MM, 2
    )
    problems = [] if ok else [clearance_text]
    if not covering_keys:
        problems.append("no socket lies over the battery")
    columns = {int(name[2]) for name in covering_keys if name != layout.THUMB_KEY_NAME}
    if columns != DESIGN_BATTERY_COLUMNS:
        problems.append(
            f"it lies under the sockets of columns {sorted(columns)}, DESIGN.md says columns "
            f"{sorted(DESIGN_BATTERY_COLUMNS)}"
        )
    fail_on(problems, "the battery does not sit under the sockets as DESIGN.md states")
    return (
        f"battery:   {half_label(right)}under the sockets of {', '.join(covering_keys)}, "
        f"{clearance_text}"
    )


def design_socket_cut_keys(right):
    """(tab notch keys, ledge relief keys, standoff flats as (key,
    standoff)) of the given half, as DESIGN.md states them."""
    if right:
        flats = {(key, center) for key, center, _, _ in DESIGN_RIGHT_STANDOFF_FLATS}
        return DESIGN_RIGHT_TAB_NOTCH_KEYS, DESIGN_RIGHT_LEDGE_RELIEF_KEYS, flats
    flats = {(key, center) for key, center, _, _ in DESIGN_STANDOFF_FLATS}
    return DESIGN_TAB_NOTCH_KEYS, DESIGN_LEDGE_RELIEF_KEYS, flats


def declared_set_problems(right=False):
    """Where the sockets layout.py gives notches, reliefs and flats on
    the given half differ from DESIGN.md's."""
    design_notches, design_reliefs, design_flats = design_socket_cut_keys(right)
    declared = (
        ("tab notches", set(layout.socket_tab_notch_keys(right)), design_notches),
        ("ledge reliefs", set(layout.socket_ledge_relief_keys(right)), design_reliefs),
        (
            "standoff flats",
            {(key, center) for center, key in layout.socket_standoff_flat_declarations(right)},
            design_flats,
        ),
    )
    return [
        f"{what} for {sorted(in_layout)} in layout.py, for {sorted(in_design)} in DESIGN.md"
        for what, in_layout, in_design in declared
        if in_layout != in_design
    ]


def uncut_declaration_problems(right=False):
    """Sockets named for a cut that kbdkid4's rule does not make on the
    given half."""
    problems = []
    for key in layout.socket_tab_notch_keys(right):
        if not any(not cut.cuts_wall for cut in layout.socket_tab_cuts(key, right)):
            problems.append(f"{key}'s tab tip is not near enough the ledge for the rule's notch")
    for key in layout.socket_ledge_relief_keys(right):
        if not layout.socket_ledge_reliefs(key, right):
            problems.append(f"{key}'s socket is not near enough the ledge for the rule's relief")
    for center, key in layout.socket_standoff_flat_declarations(right):
        if center not in layout.MOUNTING_DRILL_CENTERS_MM:
            problems.append(f"{key}'s flat is on {center}, where there is no mounting drill")
        elif not layout.socket_standoff_flats(center, key, right):
            problems.append(
                f"{key}'s socket is not near enough the standoff at {center} for a flat"
            )
    return problems


def flat_plastic(flat):
    """The plastic a flat leaves between it and the insert bore."""
    return flat.plane_distance - layout.STANDOFF_BORE_DIAMETER_MM / 2.0


def thin_flat_problems(right=False):
    minimum = layout.STANDOFF_RELIEF_MINIMUM_WALL_MM
    return [
        f"the {flat.label} on the standoff at {flat.standoff_center} leaves "
        f"{flat_plastic(flat):.3f} around the bore, less than {minimum}"
        for flat in layout.all_socket_standoff_flats(right)
        if flat_plastic(flat) < minimum - TOLERANCE_MM
    ]


def tab_figures(right=False):
    keys = layout.socket_tab_notch_keys(right)
    tips = [layout.socket_tab_tip_on_edge(key, right) for key in keys]
    past_edge = [past for _index, _along, past in tips]
    pockets = [cut for key in keys for cut in layout.socket_tab_cuts(key, right) if cut.cuts_wall]
    depths = [cut.across_range[1] - layout.TRAY_GAP_MM for cut in pockets]
    if right:
        past_figure = require_figure_for_all(
            "tab tip past the thumb's outer edge",
            past_edge,
            DESIGN_RIGHT_TAB_TIP_PAST_THUMB_EDGE_MM,
            3,
        )
    else:
        past_figure = require_figure_for_all(
            "tab tips past the west edge", past_edge, DESIGN_TAB_TIP_PAST_WEST_EDGE_MM, 3
        )
    return [
        past_figure,
        require_figure_for_all(
            "from the cavity wall",
            [layout.TRAY_GAP_MM - past for past in past_edge],
            DESIGN_TAB_TIP_FROM_CAVITY_WALL_MM,
            3,
        ),
        require_figure_for_all("pockets", depths, DESIGN_TAB_POCKET_DEPTH_MM, 3),
        require_figure_for_all(
            "wall left",
            [layout.TRAY_WALL_MM - depth for depth in depths],
            DESIGN_WALL_LEFT_AT_TAB_POCKETS_MM,
            3,
        ),
    ]


def south_ledge_face_y(x):
    """The south ledge's inner face at x: the south outline edge there
    (running east, the outline being counter-clockwise) moved in by the
    ledge's reach."""
    for start, end in edges(layout.OUTLINE_VERTICES_MM):
        if start[1] == end[1] and start[0] < x < end[0]:
            return start[1] + layout.ledge_reach()
    raise CheckFailure(f"no south outline edge under x {x}")


def relief_figures(right=False):
    reliefs = [
        cut
        for key in layout.socket_ledge_relief_keys(right)
        for cut in layout.socket_ledge_reliefs(key, right)
    ]
    bottom_row = [layout.column_key_name(column, 3) for column in range(6)]
    bottom_row.append(layout.THUMB_KEY_NAME)
    above_face = []
    for key in bottom_row:
        center = layout.KEY_CENTERS_MM[key]
        polygons = layout.socket_polygons_on_half(key, right)
        lowest = min(y for polygon in polygons for _, y in polygon)
        above_face.append(lowest - south_ledge_face_y(center[0]))
    return [
        require_figure_for_all(
            "relief bottoms z",
            [cut.z_range[0] for cut in reliefs],
            DESIGN_LEDGE_RELIEF_BOTTOM_Z_MM,
            2,
        ),
        require_figure_for_all(
            "bottom row's sockets above the south ledge's face",
            above_face,
            DESIGN_BOTTOM_ROW_FROM_SOUTH_LEDGE_FACE_MM,
            2,
        ),
    ]


def closest_socket_to_standoffs(right=False):
    radius = layout.STANDOFF_DIAMETER_MM / 2.0
    return min(
        circle_separation(center, radius, polygon)
        for center in layout.MOUNTING_DRILL_CENTERS_MM
        for _name, polygon in socket_footprints(right)
    )


def flat_figures(right=False):
    if right:
        return [
            require_figure(
                "sockets from the standoffs, without flats",
                closest_socket_to_standoffs(right),
                DESIGN_RIGHT_CLOSEST_SOCKET_TO_STANDOFF_MM,
                3,
            )
        ]
    radius = layout.STANDOFF_DIAMETER_MM / 2.0
    figures = []
    for key, center, stated_clearance, stated_plastic in DESIGN_STANDOFF_FLATS:
        polygons = layout.socket_polygons_on_half(key)
        clearance = min(circle_separation(center, radius, polygon) for polygon in polygons)
        plastic = min(flat_plastic(flat) for flat in layout.socket_standoff_flats(center, key))
        figures.append(
            require_figure(f"{key}'s socket from its standoff", clearance, stated_clearance, 3)
        )
        figures.append(require_figure("plastic left by the flat", plastic, stated_plastic, 3))
    bottoms = [flat.z_range[0] for flat in layout.all_socket_standoff_flats()]
    figures.append(
        require_figure_for_all("flat bottoms z", bottoms, DESIGN_STANDOFF_FLAT_BOTTOM_Z_MM, 2)
    )
    return figures


def check_socket_tray_rules(right=False):
    """The sockets layout.py gives notches, reliefs and flats on the
    given half are DESIGN.md's, kbdkid4's rule cuts each, no flat leaves
    the bore too thin, and the cuts come out at DESIGN.md's figures."""
    fail_on(
        declared_set_problems(right)
        + uncut_declaration_problems(right)
        + thin_flat_problems(right),
        f"{half_label(right)}the sockets' notches, reliefs or flats are off",
    )
    figures = tab_figures(right) + relief_figures(right) + flat_figures(right)
    fail_on(failed(figures), f"{half_label(right)}the sockets' cuts off DESIGN.md's figures")
    return "cuts:      " + half_label(right) + joined(figures)


def check_socket_ledge(right=False):
    minimum = layout.LEDGE_RELIEF_CLEARANCE_MM
    problems, tightest = socket_clearances(ledge_pieces(right), minimum, right)
    fail_on(
        problems,
        f"{half_label(right)}sockets closer than {minimum} to the ledge or the joint block, as cut",
    )
    return (
        f"ledge:     {half_label(right)}sockets clear of the ledge and the joint block, as cut, "
        f"by {tightest}"
    )


def check_socket_wall(right=False):
    minimum = layout.LEDGE_NOTCH_CLEARANCE_MM
    problems, tightest = socket_clearances(wall_pieces(right), minimum, right)
    fail_on(problems, f"{half_label(right)}sockets closer than {minimum} to the wall, as pocketed")
    return f"wall:      {half_label(right)}sockets clear of the wall, as pocketed, by {tightest}"


def check_socket_standoffs(right=False):
    minimum = layout.STANDOFF_RELIEF_CLEARANCE_MM
    problems = []
    tightest = Tightest()
    for center in layout.MOUNTING_DRILL_CENTERS_MM:
        for z_range, flats in standoff_bands(center, right):
            if not ranges_overlap(z_range, socket_z_range()):
                continue
            for name, socket in socket_footprints(right):
                clearance = standoff_clearance(center, flats, socket)
                standoff = describe_piece(f"standoff at {center}", z_range)
                where = f"{name}'s socket and the {standoff}"
                if flats:
                    where += f" with {len(flats)} flat{'s' if len(flats) > 1 else ''}"
                tightest.update(clearance, where)
                if clearance < minimum - TOLERANCE_MM:
                    problems.append(f"{where}: {clearance:.3f}, less than {minimum}")
    fail_on(
        problems, f"{half_label(right)}sockets closer than {minimum} to the standoffs, as flattened"
    )
    return (
        f"posts:     {half_label(right)}sockets clear of the standoffs, as flattened, by "
        f"{tightest}"
    )


def joint_features(right=False):
    """(label, plan polygon, z range) of the magnet slots and the half's
    dowel bosses."""
    return magnet_slots() + dowel_bosses(right)


def magnet_slots():
    return [
        (
            f"magnet slot at {along} along the slant",
            layout.magnet_slot_polygon(along),
            layout.magnet_slot_z_range(),
        )
        for along in layout.MAGNET_ALONGS_MM
    ]


def dowel_bosses(right=False):
    return [
        (
            f"dowel boss at {along} along the slant",
            layout.dowel_boss_polygon(along, right),
            layout.dowel_boss_z_range(),
        )
        for along in layout.DOWEL_PIN_ALONGS_MM
    ]


def boss_fills(right=False):
    """(label, plan polygon, z range) of the plastic filling the
    crevices beside the bosses, up to the PCB's underside."""
    z_range = (0.0, layout.PCB_UNDERSIDE_Z_MM)
    return [
        ("upper dowel boss's fill", layout.upper_boss_fill_polygon(right), z_range),
        ("parking boss's fill", layout.parking_boss_fill_polygon(), z_range),
    ]


def joint_voids(right=False):
    """(label, plan polygon, z range) of the half's holes and slots in
    the joint and the thumb's wall."""
    dowel_holes = [
        (
            f"dowel hole at {along} along the slant",
            layout.dowel_hole_polygon(along, right),
            layout.horizontal_hole_z_range(
                layout.DOWEL_PIN_Z_MM, layout.dowel_hole_diameter(right)
            ),
        )
        for along in layout.DOWEL_PIN_ALONGS_MM
    ]
    parking = (
        "parking hole",
        layout.parking_hole_polygon(),
        layout.horizontal_hole_z_range(layout.PARKING_HOLE_Z_MM, layout.PARKING_HOLE_DIAMETER_MM),
    )
    return magnet_slots() + dowel_holes + [parking]


def dowel_boss_inside_slant_ends():
    """(lower, upper): how far the lower boss's south end and the upper
    boss's north end lie inside the outline slant's ends."""
    half_width = layout.DOWEL_BOSS_DIAMETER_MM / 2.0
    lower = min(layout.DOWEL_PIN_ALONGS_MM) - half_width
    upper = layout.slant_length() - (max(layout.DOWEL_PIN_ALONGS_MM) + half_width)
    return lower, upper


def dowel_pin_figures():
    first_along, second_along = layout.DOWEL_PIN_ALONGS_MM
    slant_ys = [layout.slant_point(along, 0.0)[1] for along in (first_along, second_along)]
    lower_inside, upper_inside = dowel_boss_inside_slant_ends()
    return [
        require_figure(
            "dowel pin spacing along the slant",
            second_along - first_along,
            DESIGN_DOWEL_PIN_SPACING_MM,
            1,
        ),
        require_figure("lower dowel pin's slant y", slant_ys[0], DESIGN_DOWEL_PIN_SLANT_Y_MM[0], 1),
        require_figure("upper dowel pin's slant y", slant_ys[1], DESIGN_DOWEL_PIN_SLANT_Y_MM[1], 1),
        require_figure(
            "lower boss inside the slant's south end",
            lower_inside,
            DESIGN_DOWEL_BOSSES_INSIDE_SLANT_ENDS_MM[0],
            3,
        ),
        require_figure(
            "upper boss inside its north end",
            upper_inside,
            DESIGN_DOWEL_BOSSES_INSIDE_SLANT_ENDS_MM[1],
            3,
        ),
        require_figure("dowel pin height", layout.DOWEL_PIN_Z_MM, DESIGN_DOWEL_PIN_Z_MM, 1),
        require_figure(
            "midway between the bed and the PCB",
            (layout.FLOOR_UNDERSIDE_Z_MM + layout.PCB_UNDERSIDE_Z_MM) / 2.0,
            DESIGN_DOWEL_PIN_Z_MM,
            1,
        ),
        require_figure(
            "parked pin proud of the wall",
            layout.DOWEL_PIN_LENGTH_MM - layout.PARKING_PIN_INSERTION_MM,
            DESIGN_PARKING_PIN_PROUD_MM,
            1,
        ),
        require_figure(
            "print swelling per side",
            layout.PRINT_SWELLING_PER_SIDE_MM,
            DESIGN_PULL_IN_MM,
            1,
        ),
    ]


def features_along_slant():
    """(along, kind, plan polygon) of the dowel bosses and magnet slots,
    in their order along the slant."""
    slots = [
        (along, "slot", layout.magnet_slot_polygon(along)) for along in layout.MAGNET_ALONGS_MM
    ]
    bosses = [
        (along, "boss", layout.dowel_boss_polygon(along)) for along in layout.DOWEL_PIN_ALONGS_MM
    ]
    return sorted(slots + bosses)


def joint_gaps():
    """(boss to slot gaps, slot to slot gaps): the plan clearance
    between each pair of neighbours along the slant among the dowel
    bosses and magnet slots."""
    features = features_along_slant()
    to_bosses = []
    between_slots = []
    for (_, first_kind, first), (_, second_kind, second) in zip(features, features[1:]):
        gap = convex_separation(first, second)
        (between_slots if first_kind == second_kind else to_bosses).append(gap)
    return to_bosses, between_slots


def magnet_figures():
    to_bosses, between_slots = joint_gaps()
    return [
        require_figure_for_all(
            "slots from the bosses along the slant", to_bosses, DESIGN_BOSS_TO_SLOT_GAP_MM, 2
        ),
        require_figure_for_all("slots apart", between_slots, DESIGN_SLOT_TO_SLOT_GAP_MM, 2),
        require_figure(
            "magnet slot bottom above the bed",
            layout.MAGNET_SLOT_BOTTOM_Z_MM - layout.FLOOR_UNDERSIDE_Z_MM,
            DESIGN_MAGNET_SLOT_ABOVE_BED_MM,
            1,
        ),
    ]


def check_joint_figures():
    kinds = [kind for _, kind, _ in features_along_slant()]
    if kinds[0] != "boss" or kinds[-1] != "boss":
        raise CheckFailure(f"the magnets do not sit between the pins: {kinds} along the slant")
    figures = dowel_pin_figures() + magnet_figures()
    fail_on(failed(figures), "the joint off DESIGN.md's figures")
    return "joint:     " + joined(figures)


def printed(modelled):
    """A hole's or slot's size once the print has swollen into it."""
    return modelled - 2.0 * layout.PRINT_SWELLING_PER_SIDE_MM


def magnet_slot_opening_problems(opening_across, wall_left):
    """Where a magnet would not drop into its slot as printed: the slot
    or the opening above it too tight for it with
    MAGNET_DROP_IN_CLEARANCE_MM, the slot not open toward the cavity,
    or the cut-back through the wall."""
    clearance = MAGNET_DROP_IN_CLEARANCE_MM
    thickness = layout.MAGNET_THICKNESS_MM
    diameter = layout.MAGNET_DIAMETER_MM
    needed_across = thickness + clearance
    needed_along = diameter + clearance
    across = printed(layout.MAGNET_SLOT_ACROSS_MM)
    along = printed(layout.MAGNET_SLOT_ALONG_MM)
    problems = []
    if across < needed_across - TOLERANCE_MM:
        problems.append(
            f"the slot prints {across:.3f} across, the {thickness} magnet needs {needed_across:.3f}"
        )
    if along < needed_along - TOLERANCE_MM:
        problems.append(
            f"the slot prints {along:.3f} along the slant, the {diameter} magnet needs "
            f"{needed_along:.3f}"
        )
    if printed(opening_across) < needed_across - TOLERANCE_MM:
        problems.append(
            f"the opening above each slot prints {printed(opening_across):.3f} across, the "
            f"{thickness} magnet needs {needed_across:.3f}"
        )
    inner_side = layout.magnet_slot_outward_range()[0]
    block_inner_face = layout.JOINT_FACE_OUTWARD_MM - layout.JOINT_BLOCK_THICKNESS_MM
    if inner_side > block_inner_face + TOLERANCE_MM:
        problems.append(
            f"the slot's inner side lies {inner_side - block_inner_face:.3f} out of the block's "
            "inner face, which leaves a wall there"
        )
    if wall_left <= TOLERANCE_MM:
        problems.append(f"the cut-back leaves {wall_left:.3f} of wall at the face")
    return problems


def check_magnet_slot_opening():
    """Each slot runs through the block to its inner face, and above the
    block the wall would overhang its outer side, so the wall's inner
    face is cut back to the slot: as printed, the slot and the opening
    above it must take the magnet with MAGNET_DROP_IN_CLEARANCE_MM."""
    cutback = layout.magnet_wall_cutback_outward()
    low, high = layout.magnet_slot_opening_outward_range(cutback)
    low_uncut, high_uncut = layout.magnet_slot_opening_outward_range(layout.TRAY_GAP_MM)
    wall_left = layout.JOINT_FACE_OUTWARD_MM - cutback
    fail_on(
        magnet_slot_opening_problems(high - low, wall_left),
        "the magnets cannot drop into their slots",
    )
    return (
        f"slots:     {layout.MAGNET_SLOT_ACROSS_MM:.1f} x {layout.MAGNET_SLOT_ALONG_MM:.1f} "
        f"modelled, {printed(layout.MAGNET_SLOT_ACROSS_MM):.1f} x "
        f"{printed(layout.MAGNET_SLOT_ALONG_MM):.1f} printed, for the "
        f"{layout.MAGNET_THICKNESS_MM} x {layout.MAGNET_DIAMETER_MM} magnet, open toward the "
        f"cavity and above the block {high - low:.3f} across ({high_uncut - low_uncut:.3f} "
        f"without the cut-back), the cut-back leaving {wall_left:.3f} of wall from z "
        f"{layout.JOINT_BLOCK_TOP_Z_MM} to {layout.MAGNET_WALL_CUTBACK_TOP_Z_MM}"
    )


def check_joint_inside(right=False):
    outer = layout.tray_outer_polygon()
    problems = []
    tightest = Tightest()
    for label, polygon, _z_range in joint_features(right) + boss_fills(right):
        margin = containment_margin(polygon, outer)
        tightest.update(margin, label)
        if margin < -TOLERANCE_MM:
            problems.append(f"the {label} pokes {-margin:.3f} past the tray's outer face")
    fail_on(problems, f"{half_label(right)}joint features outside the tray")
    return (
        f"joint:     {half_label(right)}magnet slots, dowel bosses and their fills inside the "
        f"tray's outer face by {tightest}"
    )


def joint_tray_problems(label, polygon, z_range, right=False, sockets_too=True):
    """(problems, tightest from the sockets, tightest from the
    standoffs) of one joint feature on the given half. Plastic standing
    under the PCB keeps the ledge's clearance from the sockets, as the
    ledge and the parking boss do. Without sockets_too (a slot, empty
    space) only the standoffs count."""
    minimum = layout.LEDGE_RELIEF_CLEARANCE_MM
    standoff_radius = layout.STANDOFF_DIAMETER_MM / 2.0
    problems = []
    from_sockets = Tightest()
    from_standoffs = Tightest()
    if sockets_too and ranges_overlap(z_range, socket_z_range()):
        for name, socket in socket_footprints(right):
            clearance = convex_separation(polygon, socket)
            from_sockets.update(clearance, f"{label} and {name}'s socket")
            if clearance < minimum - TOLERANCE_MM:
                problems.append(
                    f"the {label} comes {clearance:.3f} from {name}'s socket, less than {minimum}"
                )
    if ranges_overlap(z_range, standoff_z_range()):
        for center in layout.MOUNTING_DRILL_CENTERS_MM:
            clearance = circle_separation(center, standoff_radius, polygon)
            from_standoffs.update(clearance, f"{label} and the standoff at {center}")
            if clearance < -TOLERANCE_MM:
                problems.append(
                    f"the {label} overlaps the standoff at {center} by {-clearance:.3f}"
                )
    return problems, from_sockets, from_standoffs


def fill_problems(right):
    """A fill that came out no triangle: the boss's inner corner at or
    past the ledge's face, or the dowel boss's side past the parking
    boss's."""
    return [
        f"the {label} is no triangle (area {layout.polygon_signed_area(polygon):.4f})"
        for label, polygon, _z_range in boss_fills(right)
        if layout.polygon_signed_area(polygon) <= TOLERANCE_MM
    ]


def check_joint_clearances(right=False):
    problems = fill_problems(right)
    from_sockets = Tightest()
    from_standoffs = Tightest()
    plastic = dowel_bosses(right) + boss_fills(right)
    features = [(feature, True) for feature in plastic] + [
        (slot, False) for slot in magnet_slots()
    ]
    for (label, polygon, z_range), sockets_too in features:
        feature_problems, sockets, standoffs = joint_tray_problems(
            label, polygon, z_range, right, sockets_too
        )
        problems.extend(feature_problems)
        from_sockets.update(sockets.value, sockets.where)
        from_standoffs.update(standoffs.value, standoffs.where)
    ok, text = require_figure(
        "bosses from the sockets", from_sockets.value, DESIGN_BOSSES_FROM_SOCKETS_MM[right], 3
    )
    if not ok:
        problems.append(text)
    fail_on(
        problems,
        f"{half_label(right)}joint plastic too close to the sockets, or the joint in the "
        "standoffs' way",
    )
    return (
        f"joint:     {half_label(right)}{text} ({from_sockets.where}), clear of the "
        f"standoffs by {from_standoffs}"
    )


def check_joint_voids(right=False):
    """Every two of the joint's holes and slots keep
    JOINT_LEAST_PLASTIC_BETWEEN_VOIDS_MM of plastic between them in plan
    wherever their heights overlap."""
    minimum = layout.JOINT_LEAST_PLASTIC_BETWEEN_VOIDS_MM
    problems = []
    tightest = Tightest()
    for first, second in itertools.combinations(joint_voids(right), 2):
        first_label, first_polygon, first_z = first
        second_label, second_polygon, second_z = second
        if not ranges_overlap(first_z, second_z):
            continue
        plastic = convex_separation(first_polygon, second_polygon)
        where = f"{first_label} and {second_label}"
        tightest.update(plastic, where)
        if plastic < minimum - TOLERANCE_MM:
            problems.append(f"the {where} leave {plastic:.3f} of plastic, less than {minimum}")
    ok, text = require_figure(
        "least plastic between the voids",
        tightest.value,
        DESIGN_LEAST_PLASTIC_BETWEEN_VOIDS_MM[right],
        2,
    )
    if not ok:
        problems.append(text)
    fail_on(problems, f"{half_label(right)}the joint's holes and slots too close")
    return f"voids:     {half_label(right)}{text} ({tightest.where})"


def parking_boss_problems(right):
    """(problems, figure text) of the parking hole's boss and its fill
    against the sockets: they stand to the PCB's underside like the
    ledge, so they keep the ledge's clearance from them."""
    minimum = layout.LEDGE_RELIEF_CLEARANCE_MM
    bodies = (
        ("parking boss", layout.parking_boss_polygon()),
        ("parking boss's fill", layout.parking_boss_fill_polygon()),
    )
    problems = []
    tightest = Tightest()
    for label, body in bodies:
        for name, polygon in socket_footprints(right):
            clearance = convex_separation(body, polygon)
            tightest.update(clearance, f"the {label} and {name}'s socket")
            if clearance < minimum - TOLERANCE_MM:
                problems.append(f"the {label} comes {clearance:.3f} from {name}'s socket")
    ok, text = require_figure(
        "the boss from the sockets", tightest.value, DESIGN_PARKING_BOSS_FROM_SOCKETS_MM, 3
    )
    return problems + ([] if ok else [text]), f"{text}, {tightest.where}"


def check_parking_hole(right=False):
    """The parking hole runs through the thumb's east wall, its magnet's
    seat no wider than the hole itself (one teardrop serves both). The
    hole is kept clear in plan of the sockets (the thumb's above all)
    and the standoffs (the one at (114.141, 19.765) above all) at any
    height, and of the joint's other voids by check_joint_voids(). Its
    boss may merge with the tray's other plastic, but keeps the ledge's
    clearance from the sockets."""
    hole = layout.parking_hole_polygon()
    east_edge_low_y = 0.0
    east_edge_high_y = layout.SLANT_SOUTH_END_MM[1]
    low_y = min(y for _, y in hole)
    high_y = max(y for _, y in hole)
    wall_margin = min(low_y - east_edge_low_y, east_edge_high_y - high_y)
    problems = []
    if wall_margin < -TOLERANCE_MM:
        problems.append(
            f"the hole spans y {low_y:.3f} to {high_y:.3f}, past the thumb's east edge "
            f"(y {east_edge_low_y} to {east_edge_high_y})"
        )
    if layout.PARKING_MAGNET_SEAT_DIAMETER_MM > layout.PARKING_HOLE_DIAMETER_MM + TOLERANCE_MM:
        problems.append(
            f"the magnet's seat ({layout.PARKING_MAGNET_SEAT_DIAMETER_MM:.2f}) is wider than the "
            f"hole ({layout.PARKING_HOLE_DIAMETER_MM:.2f}), which is cut in one diameter"
        )
    from_sockets = Tightest()
    for name, polygon in socket_footprints(right):
        from_sockets.update(convex_separation(hole, polygon), f"{name}'s socket")
    from_standoffs = Tightest()
    for center in layout.MOUNTING_DRILL_CENTERS_MM:
        from_standoffs.update(
            circle_separation(center, layout.STANDOFF_DIAMETER_MM / 2.0, hole),
            f"the standoff at {center}",
        )
    for tightest in (from_sockets, from_standoffs):
        if tightest.value < -TOLERANCE_MM:
            problems.append(f"the parking hole overlaps {tightest.where} by {-tightest.value:.3f}")
    boss_problems, boss_text = parking_boss_problems(right)
    fail_on(problems + boss_problems, f"{half_label(right)}the parking hole or its boss collides")
    return (
        f"parking:   {half_label(right)}hole {layout.PARKING_HOLE_DIAMETER_MM:.1f} across through "
        f"the thumb's east wall ({wall_margin:.3f} from its ends), clear of the sockets by "
        f"{from_sockets} and the standoffs by {from_standoffs}, {boss_text}"
    )


# The parts' mounts (work item 004): layout.py's mount bodies and voids
# (MountBox) and the wire rooms, against the tray, the parts and the
# sockets. The hook's lip and the round openings are checked as their
# bounding boxes, which hold them.


def describe_mount(box):
    return f"{box.label} ({box.part})"


def mount_pieces(boxes):
    """(label, plan polygon, z range) of mount boxes."""
    return [(describe_mount(box), box_polygon(box), box.z_range) for box in boxes]


def is_floor_void(box):
    """A groove or slot in the floor, not an opening through the wall."""
    return box.z_range[1] <= TOLERANCE_MM


def mount_containment_problems(right, fits=layout.DEFAULT_MOUNT_FITS):
    """(problems, tightest) of the mounts in the tray: the bodies and
    the floor's voids inside the cavity, the floor's voids within the
    floor's thickness, and the wall's voids from the cavity wall to the
    outer face."""
    cavity = layout.tray_cavity_polygon()
    outer = layout.tray_outer_polygon()
    problems = []
    tightest = Tightest()
    floor_voids = [box for box in layout.mount_voids(fits, right) if is_floor_void(box)]
    for box in layout.mount_bodies(fits) + tuple(floor_voids):
        margin = containment_margin(box_polygon(box), cavity)
        tightest.update(margin, describe_mount(box))
        if margin < -TOLERANCE_MM:
            problems.append(f"the {describe_mount(box)} pokes {-margin:.3f} past the cavity wall")
    for box in floor_voids:
        low, high = box.z_range
        if low < layout.FLOOR_UNDERSIDE_Z_MM - TOLERANCE_MM or high > TOLERANCE_MM:
            problems.append(f"the {describe_mount(box)} spans z {low} to {high}, not in the floor")
    for opening in layout.wall_openings(fits):
        problems.extend(wall_opening_problems(opening, cavity, outer))
    return problems, tightest


def wall_opening_problems(opening, cavity, outer):
    """An opening's boxes, from the cavity out, run through the wall:
    the first from the cavity wall, each on from where the one before
    it ends, the last out to the outer face."""
    middle_x = sum(opening[0].x_range) / 2.0
    problems = []
    inner = point_boundary_distance((middle_x, opening[0].y_range[0]), cavity)
    outside = point_boundary_distance((middle_x, opening[-1].y_range[1]), outer)
    if max(inner, outside) > TOLERANCE_MM:
        problems.append(
            f"the {describe_mount(opening[0])} runs {inner:.3f} off the cavity wall and the "
            f"{describe_mount(opening[-1])} {outside:.3f} off the outer face, not through the wall"
        )
    for before, after in zip(opening, opening[1:]):
        if after.y_range[0] > before.y_range[1] + TOLERANCE_MM:
            problems.append(f"the {describe_mount(after)} starts "
                            f"{after.y_range[0] - before.y_range[1]:.3f} past the "
                            f"{describe_mount(before)}")
    return problems


def check_mount_containment(right=False):
    problems, tightest = mount_containment_problems(right)
    fail_on(problems, f"{half_label(right)}mounts outside the tray")
    return (
        f"mounts:    {half_label(right)}bodies and the floor's voids inside the cavity wall by "
        f"{tightest}, the shell's channel and the window, the lever slot and the pin hole "
        "through the wall"
    )


def mount_part_clearances(fits=layout.DEFAULT_MOUNT_FITS):
    """(own, other, zone): the Tightest clearance in plan of the mount
    bodies from their own part's envelopes, from the other parts' and,
    as printed, from the PCB connector's clear zone, wherever their
    heights overlap, and the problems: a body in its own part or the
    zone, or nearer than DESIGN_MOUNT_FROM_OTHER_PARTS_MM to another
    part."""
    own, other, zone = Tightest(), Tightest(), Tightest()
    problems = []
    for box in layout.mount_bodies(fits):
        for envelope in layout.part_envelopes(fits):
            if not ranges_overlap(box.z_range, envelope.z_range):
                continue
            clearance = convex_separation(box_polygon(box), box_polygon(envelope))
            where = f"the {describe_mount(box)} and the {describe_envelope(envelope)}"
            if envelope is layout.PCB_CONNECTOR_CLEAR_ZONE:
                clearance -= layout.PRINT_SWELLING_PER_SIDE_MM
                tightest, minimum = zone, 0.0
            elif envelope.part == box.part:
                tightest, minimum = own, 0.0
            else:
                tightest, minimum = other, DESIGN_MOUNT_FROM_OTHER_PARTS_MM
            tightest.update(clearance, where)
            if clearance < minimum - TOLERANCE_MM:
                problems.append(f"{where}: {clearance:.3f}, less than {minimum}")
    return own, other, zone, problems


def check_mount_parts():
    own, other, zone, problems = mount_part_clearances()
    fail_on(problems, "mounts in the parts' way")
    figures = [
        require_figure(
            "from the other parts", other.value, DESIGN_MOUNTS_LEAST_FROM_OTHER_PARTS_MM, 1
        ),
        require_figure("from the PCB connector's zone as printed", zone.value,
                       DESIGN_MOUNTS_FROM_PCB_ZONE_PRINTED_MM, 1),
    ]
    fail_on(failed(figures), "the mounts' clearance from the other parts is off DESIGN.md")
    return (
        f"mounts:    bodies clear of their own parts by {own}; {figures[0][1]} ({other.where}); "
        f"{figures[1][1]} ({zone.where})"
    )


def mount_socket_problems(right, fits=layout.DEFAULT_MOUNT_FITS):
    """(problems, tightest in plan of the bodies reaching the sockets'
    height, the least height under the sockets of the bodies within
    the ledge's clearance of one in plan)."""
    minimum = layout.LEDGE_RELIEF_CLEARANCE_MM
    bodies = layout.mount_bodies(fits)
    problems, in_plan = socket_clearances(mount_pieces(bodies), minimum, right)
    under = Tightest()
    for box in bodies:
        for name, socket in socket_footprints(right):
            if convex_separation(box_polygon(box), socket) >= minimum - TOLERANCE_MM:
                continue
            height = layout.SOCKET_BOTTOM_Z_MM - box.z_range[1]
            under.update(height, f"the {describe_mount(box)} under {name}'s socket")
            if height < minimum - TOLERANCE_MM:
                problems.append(f"the {describe_mount(box)} stands {height:.3f} under {name}'s")
    return problems, in_plan, under


def check_mount_sockets(right=False):
    """The mounts keep the ledge's clearance from the sockets: in plan
    where they reach the sockets' height, and in height where they come
    under one."""
    problems, in_plan, under = mount_socket_problems(right)
    fail_on(problems, f"{half_label(right)}mounts too close to the sockets")
    reaching = (
        f"bodies at the sockets' height clear in plan by {in_plan}"
        if in_plan.value < math.inf
        else "no body reaches the sockets' height"
    )
    return f"mounts:    {half_label(right)}{reaching}; under a socket by at least {under}"


def mount_standoff_clearances(fits=layout.DEFAULT_MOUNT_FITS):
    """(problems, bodies, voids): the bodies clear of the standoffs (the
    standoffs are the same on both halves in the left half's frame), the
    voids DESIGN_MOUNT_VOIDS_FROM_STANDOFFS_MM from them, so their bases
    stay whole, with the Tightest of each."""
    radius = layout.STANDOFF_DIAMETER_MM / 2.0
    problems = []
    bodies, voids = Tightest(), Tightest()
    for boxes, tightest, minimum in (
        (layout.mount_bodies(fits), bodies, 0.0),
        (layout.mount_voids(fits) + layout.mount_voids(fits, right=True), voids,
         DESIGN_MOUNT_VOIDS_FROM_STANDOFFS_MM),
    ):
        for box in boxes:
            for center in layout.MOUNTING_DRILL_CENTERS_MM:
                clearance = circle_separation(center, radius, box_polygon(box))
                where = f"the {describe_mount(box)} and the standoff at {center}"
                tightest.update(clearance, where)
                if clearance < minimum - TOLERANCE_MM:
                    problems.append(f"{where}: {clearance:.3f}, less than {minimum}")
    return problems, bodies, voids


def check_mount_standoffs():
    problems, bodies, voids = mount_standoff_clearances()
    ok, text = require_figure(
        "voids from the standoffs", voids.value, DESIGN_HOOK_SLOT_FROM_STANDOFF_MM, 3
    )
    fail_on(problems + ([] if ok else [text]), "mounts on the standoffs")
    return f"mounts:    bodies clear of the standoffs by {bodies}; {text} ({voids.where})"


def mount_joint_problems(right, fits=layout.DEFAULT_MOUNT_FITS):
    """(problems, tightest) of the mounts against the joint's plastic
    and its voids, the voids by the joint's least plastic between
    voids."""
    minimum = layout.JOINT_LEAST_PLASTIC_BETWEEN_VOIDS_MM
    problems = []
    tightest = Tightest()
    joint = joint_features(right) + boss_fills(right) + joint_voids(right)
    mounts = [(box, 0.0) for box in layout.mount_bodies(fits)]
    mounts.extend((box, minimum) for box in layout.mount_voids(fits, right))
    for box, needed in mounts:
        for label, polygon, z_range in joint:
            if not ranges_overlap(box.z_range, z_range):
                continue
            clearance = convex_separation(box_polygon(box), polygon)
            where = f"the {describe_mount(box)} and the {label}"
            tightest.update(clearance, where)
            if clearance < needed - TOLERANCE_MM:
                problems.append(f"{where}: {clearance:.3f}, less than {needed}")
    return problems, tightest


def check_mount_joint(right=False):
    """The mounts clear of the joint's plastic and its voids."""
    problems, tightest = mount_joint_problems(right)
    fail_on(problems, f"{half_label(right)}mounts in the joint")
    return f"mounts:    {half_label(right)}clear of the joint's features and voids by {tightest}"


def hook_plan_boxes(fits=layout.DEFAULT_MOUNT_FITS):
    return (layout.nano_hook_blade_box(fits), layout.nano_hook_lip_box(fits))


def hook_under_sockets(fits=layout.DEFAULT_MOUNT_FITS):
    """(least height under them, the keys) of the sockets over the hook
    in plan."""
    keys = set()
    least = math.inf
    for box in hook_plan_boxes(fits):
        for name, socket in socket_footprints():
            if convex_separation(box_polygon(box), socket) < -TOLERANCE_MM:
                keys.add(name)
                least = min(least, layout.SOCKET_BOTTOM_Z_MM - box.z_range[1])
    return least, keys


def hook_deflection_room(fits=layout.DEFAULT_MOUNT_FITS):
    """The deflection slot's width south of the blade as printed."""
    slot = next(
        box for box in layout.nano_hook_slot_boxes(fits) if box.label == "hook's deflection slot"
    )
    return slot.y_range[1] - slot.y_range[0] - 2.0 * layout.PRINT_SWELLING_PER_SIDE_MM


def sole_cutout_figures():
    """The sole's cut-out under the hook on each half, in its frame, and
    its clearance in plan from the nearest standoff."""
    cutout = layout.nano_hook_sole_cutout_box()
    right_x = sorted(layout.mirror_for_right_half((x, 0.0))[0] for x in cutout.x_range)
    radius = layout.STANDOFF_DIAMETER_MM / 2.0
    from_standoffs = min(circle_separation(center, radius, box_polygon(cutout))
                         for center in layout.MOUNTING_DRILL_CENTERS_MM)
    return [
        require_figure(
            "sole cut out from x", cutout.x_range[0], DESIGN_SOLE_CUTOUT_X_MM[False][0], 3
        ),
        require_figure("to", cutout.x_range[1], DESIGN_SOLE_CUTOUT_X_MM[False][1], 3),
        require_figure("y", cutout.y_range[0], DESIGN_SOLE_CUTOUT_Y_MM[0], 3),
        require_figure("to", cutout.y_range[1], DESIGN_SOLE_CUTOUT_Y_MM[1], 3),
        require_figure("on the right from x", right_x[0], DESIGN_SOLE_CUTOUT_X_MM[True][0], 3),
        require_figure("to", right_x[1], DESIGN_SOLE_CUTOUT_X_MM[True][1], 3),
        require_figure("from the standoff", from_standoffs, DESIGN_SOLE_CUTOUT_FROM_STANDOFF_MM, 3),
    ]


def hook_figures():
    lip_low, lip_high = layout.nano_hook_lip_x_range()
    middle_low, middle_high = layout.nano_free_middle_x_range()
    under, keys = hook_under_sockets()
    return [
        require_figure("bending length", layout.NANO_HOOK_BENDING_LENGTH_MM,
                       DESIGN_HOOK_BENDING_LENGTH_MM, 1),
        require_figure("strain as printed %", 100.0 * layout.nano_hook_strain(),
                       DESIGN_HOOK_STRAIN_PERCENT[True], 2),
        require_figure("as modelled %", 100.0 * layout.nano_hook_strain(printed=False),
                       DESIGN_HOOK_STRAIN_PERCENT[False], 2),
        require_figure("free end swings", layout.nano_hook_end_deflection(),
                       DESIGN_HOOK_END_DEFLECTION_MM, 2),
        require_figure("in room as printed", hook_deflection_room(),
                       DESIGN_HOOK_DEFLECTION_ROOM_MM, 1),
        require_figure("lip from x", lip_low, DESIGN_HOOK_LIP_X_MM[0], 1),
        require_figure("to", lip_high, DESIGN_HOOK_LIP_X_MM[1], 1),
        require_figure("in the free middle from x", middle_low, DESIGN_NANO_FREE_MIDDLE_X_MM[0], 3),
        require_figure("to", middle_high, DESIGN_NANO_FREE_MIDDLE_X_MM[1], 3),
        require_figure("top z", layout.nano_hook_top_z(), DESIGN_HOOK_TOP_Z_MM, 2),
        require_figure(f"under {', '.join(sorted(keys))}", under, DESIGN_HOOK_UNDER_SOCKET_MM, 2),
    ] + sole_cutout_figures()


def hook_problems(fits=layout.DEFAULT_MOUNT_FITS):
    """The rules DESIGN.md sets the hook, apart from its figures."""
    problems = []
    strain = 100.0 * layout.nano_hook_strain(fits)
    if strain > DESIGN_HOOK_MAXIMUM_STRAIN_PERCENT:
        problems.append(f"the strain as printed, {strain:.2f} %, is over "
                        f"{DESIGN_HOOK_MAXIMUM_STRAIN_PERCENT} %")
    if layout.NANO_HOOK_BENDING_LENGTH_MM < DESIGN_HOOK_MINIMUM_BENDING_LENGTH_MM:
        problems.append(f"the blade bends over less than {DESIGN_HOOK_MINIMUM_BENDING_LENGTH_MM}")
    swing = layout.nano_hook_end_deflection(fits)
    room = hook_deflection_room(fits)
    if swing > room:
        problems.append(f"the free end swings {swing:.3f}, its slot leaves {room:.3f} as printed")
    lip_low, lip_high = layout.nano_hook_lip_x_range()
    middle_low, middle_high = layout.nano_free_middle_x_range(fits)
    if lip_low < middle_low - TOLERANCE_MM or lip_high > middle_high + TOLERANCE_MM:
        problems.append(f"the lip (x {lip_low:.3f} to {lip_high:.3f}) leaves the board's free "
                        f"middle (x {middle_low:.3f} to {middle_high:.3f})")
    _, keys = hook_under_sockets(fits)
    if keys != DESIGN_HOOK_SOCKET_KEYS:
        problems.append(f"the sockets over the hook are {sorted(keys)}, DESIGN.md says "
                        f"{sorted(DESIGN_HOOK_SOCKET_KEYS)}")
    return problems


def check_nano_hook():
    figures = hook_figures()
    fail_on(hook_problems() + failed(figures), "the nice!nano's snap hook off DESIGN.md")
    return "hook:      " + joined(figures)


def nano_shell_play(fits=layout.DEFAULT_MOUNT_FITS):
    """{direction: how far} the shell can move from its modelled place
    as printed: west and east the board between the west ledge's face
    and the ribs' and the shell between the bar's posts, north the
    board's USB end before the posts."""
    swelling = layout.PRINT_SWELLING_PER_SIDE_MM
    shell = layout.nano_usb_shell_envelope(fits)
    board = layout.nano_board_envelope(fits)
    _bar, west_post, east_post = layout.nano_bar_boxes(fits)
    return {
        "west": min(board.x_range[0] - (layout.west_ledge_face_x() + swelling),
                    shell.x_range[0] - (west_post.x_range[1] + swelling)),
        "east": min((layout.nano_rib_face_x(fits) - swelling) - board.x_range[1],
                    (east_post.x_range[0] - swelling) - shell.x_range[1]),
        "north": (west_post.y_range[0] - swelling) - board.y_range[1],
    }


def shell_in_channel_margins(fits=layout.DEFAULT_MOUNT_FITS):
    """{where: margin} as printed of the shell in its channel wherever
    its play lets it go: across at both sides, over its top, and its
    mouth before the channel's north end, past which the window's
    corner rounds would reach it."""
    swelling = layout.PRINT_SWELLING_PER_SIDE_MM
    shell = layout.nano_usb_shell_envelope(fits)
    channel = layout.usb_shell_channel_box(fits)
    play = nano_shell_play(fits)
    return {
        "sides": min(shell.x_range[0] - play["west"] - (channel.x_range[0] + swelling),
                     (channel.x_range[1] - swelling) - (shell.x_range[1] + play["east"])),
        "top": (channel.z_range[1] - swelling) - shell.z_range[1],
        "end": (channel.y_range[1] - swelling) - (shell.y_range[1] + play["north"]),
    }


def lever_in_slot_margin():
    """The least, as printed, between the lever's swept box and its
    slot."""
    lever = layout.POWER_SWITCH_LEVER
    slot = layout.power_switch_lever_slot_box()
    swelling = layout.PRINT_SWELLING_PER_SIDE_MM
    margins = []
    for lever_range, slot_range in ((lever.x_range, slot.x_range), (lever.z_range, slot.z_range)):
        margins.append(lever_range[0] - (slot_range[0] + swelling))
        margins.append((slot_range[1] - swelling) - lever_range[1])
    return min(margins)


def opening_problems(fits=layout.DEFAULT_MOUNT_FITS):
    """The lever and the shell, wherever its play lets it go, clear of
    their openings as printed."""
    in_channel = shell_in_channel_margins(fits)
    if lever_in_slot_margin() < -TOLERANCE_MM or min(in_channel.values()) < -TOLERANCE_MM:
        return ["the lever or the shell does not clear its opening as printed"]
    return []


def check_mount_openings():
    """The lever passes its slot and the shell its channel as printed,
    the shell wherever its play lets it go, the bar reaches the shell's
    mouth, and the pin hole's axis lies where DESIGN.md puts it."""
    play = nano_shell_play()
    in_channel = shell_in_channel_margins()
    hole_x, hole_z = layout.reset_pin_hole_center()
    figures = [
        require_figure("lever in its slot as printed", lever_in_slot_margin(),
                       DESIGN_LEVER_IN_SLOT_PRINTED_MM, 2),
        require_figure("bar deep to the shell's mouth", layout.nano_bar_depth(),
                       DESIGN_NANO_BAR_DEPTH_MM, 2),
    ] + [
        require_figure(f"shell's play {direction}", play[direction],
                       DESIGN_SHELL_PLAY_MM[direction], 2)
        for direction in DESIGN_SHELL_PLAY_MM
    ] + [
        require_figure(f"in its channel as printed at the {where}", in_channel[where],
                       DESIGN_SHELL_IN_CHANNEL_PRINTED_MM[where], 2)
        for where in DESIGN_SHELL_IN_CHANNEL_PRINTED_MM
    ] + [
        require_figure("pin hole's axis x", hole_x, DESIGN_RESET_PIN_HOLE_AXIS_MM[0], 3),
        require_figure("z", hole_z, DESIGN_RESET_PIN_HOLE_AXIS_MM[1], 2),
    ]
    fail_on(failed(figures) + opening_problems(), "the mounts' openings off DESIGN.md")
    return "openings:  " + joined(figures)


def wire_room_depths():
    """(behind the leads, over the nice!nano's pads): each lead room's
    smaller extent in plan, the room behind the lead, and each pad
    room's height."""
    behind = [
        min(room.x_range[1] - room.x_range[0], room.y_range[1] - room.y_range[0])
        for room in layout.lead_wire_rooms()
    ]
    over = [room.z_range[1] - room.z_range[0] for room in layout.nano_wire_rooms()]
    return behind, over


def wire_room_obstacles(right, fits=layout.DEFAULT_MOUNT_FITS):
    """(label, plan polygon, z range) of everything a wire room must keep
    clear of on the given half, the parts' envelopes as (label, part,
    polygon, z range) apart, since a room may lie against its own
    part."""
    tray = ledge_pieces(right) + wall_pieces(right) + joint_features(right) + boss_fills(right)
    mounts = mount_pieces(layout.mount_bodies(fits))
    sockets = [(f"{name}'s socket", polygon, socket_z_range())
               for name, polygon in socket_footprints(right)]
    parts = [(describe_envelope(envelope), envelope.part, box_polygon(envelope), envelope.z_range)
             for envelope in layout.part_envelopes(fits)]
    return tray + mounts + sockets, parts


def wire_room_problems(right, fits=layout.DEFAULT_MOUNT_FITS):
    obstacles, parts = wire_room_obstacles(right, fits)
    radius = layout.STANDOFF_DIAMETER_MM / 2.0
    problems = []
    tightest = Tightest()
    for room in layout.wire_rooms(fits, right):
        room_polygon = box_polygon(room)
        candidates = [(label, polygon, z_range) for label, polygon, z_range in obstacles]
        candidates.extend((label, polygon, z_range) for label, part, polygon, z_range in parts
                          if part != room.part)
        for label, polygon, z_range in candidates:
            if not ranges_overlap(room.z_range, z_range):
                continue
            clearance = convex_separation(room_polygon, polygon)
            tightest.update(clearance, f"the {describe_envelope(room)} and the {label}")
            if clearance < -TOLERANCE_MM:
                problems.append(f"the {describe_envelope(room)} reaches {-clearance:.3f} into "
                                f"the {describe_piece(label, z_range)}")
        for center in layout.MOUNTING_DRILL_CENTERS_MM:
            clearance = circle_separation(center, radius, room_polygon)
            where = f"the {describe_envelope(room)} and the standoff at {center}"
            tightest.update(clearance, where)
            if clearance < -TOLERANCE_MM:
                problems.append(f"the {describe_envelope(room)} reaches into the standoff at "
                                f"{center}")
    return problems, tightest


def check_wire_rooms(right=False):
    """Every wire room clear of the tray as cut, the mounts, the
    standoffs, the joint, the sockets and the other parts."""
    behind, over = wire_room_depths()
    problems, tightest = wire_room_problems(right)
    figures = [
        require_figure_for_all("behind every lead", behind, DESIGN_WIRE_ROOM_BEHIND_LEADS_MM, 1),
        require_figure_for_all("over the nice!nano's pads", over, DESIGN_WIRE_ROOM_OVER_PADS_MM, 1),
        require_figure("clear by", tightest.value, DESIGN_WIRE_ROOM_LEAST_CLEARANCE_MM, 3),
    ]
    fail_on(problems + failed(figures), f"{half_label(right)}the wires' room taken")
    return f"wires:     {half_label(right)}{joined(figures)} ({tightest.where})"


# The pry recess (work item 006): a void in the floor's top beside and
# under the nice!nano's east edge, checked in plan against the parts
# and the tray's plastic whatever their heights, since a tool comes down
# to it from above and the floor around it holds them. The sockets and
# the PCB connector's zone bind only what stands above the floor, so the
# recess may lie under them. The tool that comes to it is a straight
# flat tip, checked in the section along its path from the east: it
# must reach the recess's reach under the board, lying on the recess's
# bottom as printed, with its top under the board's underside at the
# board's edge, and rise from there over the recess's east edge and
# everything else in its path until it is out over the tray's rim.


def pry_recess_obstacles(right, fits=layout.DEFAULT_MOUNT_FITS):
    """{what: [(label, plan polygon, minimum)]} the pry recess keeps
    clear of in plan: the other parts, the joint, the mount bodies and
    the hook's slots with their bed chamfers (the sole's cut-out). The
    standoffs, circles, are checked on their own."""
    minimums = {what: minimum for what, (_, minimum) in DESIGN_PRY_RECESS_CLEARANCES_MM.items()}
    parts = [
        (describe_envelope(envelope), box_polygon(envelope), minimums["the other parts"])
        for envelope in layout.part_envelopes(fits)
        if envelope.part not in ("nice!nano", layout.PCB_CONNECTOR_CLEAR_ZONE.part)
    ]
    joint = joint_features(right) + boss_fills(right) + joint_voids(right)
    sole = layout.nano_hook_sole_cutout_box(fits)
    return {
        "the other parts": parts,
        "the joint": [(label, polygon, minimums["the joint"]) for label, polygon, _ in joint],
        "the mount bodies": [(describe_mount(box), box_polygon(box), minimums["the mount bodies"])
                             for box in layout.mount_bodies(fits)],
        "the hook's slots and their bed chamfers": [
            (describe_mount(sole), box_polygon(sole),
             minimums["the hook's slots and their bed chamfers"])
        ],
    }


def pry_recess_clearances(right, fits=layout.DEFAULT_MOUNT_FITS):
    """(problems, {what: Tightest}) of the pry recess in plan against its
    obstacles and the standoffs, each kept at its minimum."""
    recess = box_polygon(layout.nano_pry_recess_box(fits))
    obstacles = pry_recess_obstacles(right, fits)
    problems = []
    tightest = {what: Tightest() for what in DESIGN_PRY_RECESS_CLEARANCES_MM}
    for what, items in obstacles.items():
        for label, polygon, minimum in items:
            clearance = convex_separation(recess, polygon)
            tightest[what].update(clearance, label)
            if clearance < minimum - TOLERANCE_MM:
                problems.append(f"the pry recess and the {label}: {clearance:.3f}, less than "
                                f"{minimum}")
    radius = layout.STANDOFF_DIAMETER_MM / 2.0
    minimum = DESIGN_PRY_RECESS_CLEARANCES_MM["the standoffs"][1]
    for center in layout.MOUNTING_DRILL_CENTERS_MM:
        clearance = circle_separation(center, radius, recess)
        tightest["the standoffs"].update(clearance, f"the standoff at {center}")
        if clearance < minimum - TOLERANCE_MM:
            problems.append(f"the pry recess and the standoff at {center}: {clearance:.3f}, less "
                            f"than {minimum}")
    return problems, tightest


def pry_recess_board_problems(fits=layout.DEFAULT_MOUNT_FITS):
    """The recess reaches under the board from beside it, takes no floor
    under the board but within the east pin row's groove and the strip
    between it and the board's edge, so the board lies flat, and leaves
    the floor under it as modelled."""
    recess = layout.nano_pry_recess_box(fits)
    board = layout.nano_board_envelope(fits)
    groove = next(box for box in layout.nano_groove_boxes(fits) if box.label.startswith("east"))
    problems = []
    if not recess.x_range[0] < board.x_range[1] < recess.x_range[1]:
        problems.append("the pry recess does not reach under the board from beside it")
    if (recess.x_range[0] < groove.x_range[0] - TOLERANCE_MM
            or recess.y_range[0] < groove.y_range[0] - TOLERANCE_MM
            or recess.y_range[1] > groove.y_range[1] + TOLERANCE_MM):
        problems.append("the pry recess takes floor under the board beyond the east pin row's "
                        "groove and the board's edge")
    floor_under = recess.z_range[0] - layout.FLOOR_UNDERSIDE_Z_MM
    if floor_under < DESIGN_PRY_RECESS_FLOOR_UNDER_MM - TOLERANCE_MM:
        problems.append(f"the pry recess leaves {floor_under:.3f} of floor under it, less than "
                        f"{DESIGN_PRY_RECESS_FLOOR_UNDER_MM}")
    return problems


def pry_tool_band(fits=layout.DEFAULT_MOUNT_FITS):
    """(low, high) y the tip's width covers, in the middle of the
    recess."""
    middle = sum(layout.nano_pry_recess_box(fits).y_range) / 2.0
    return layout.centered_range(middle, layout.NANO_PRY_TOOL_WIDTH_MM)


def band_x_range(polygon, y_range):
    """(low, high) x of a convex polygon's part between two y, None
    where it has none."""
    clipped = clip_to_half_plane(polygon, (0.0, 1.0), y_range[1])
    if len(clipped) >= 3:
        clipped = clip_to_half_plane(clipped, (0.0, -1.0), -y_range[0])
    if len(clipped) < 3 or polygon_area(clipped) < TOLERANCE_MM:
        return None
    xs = [x for x, _ in clipped]
    return (min(xs), max(xs))


def circle_band_x_range(center, radius, y_range):
    """(low, high) x of a circle's part between two y, None where it has
    none."""
    x, y = center
    nearest = min(max(y, y_range[0]), y_range[1])
    if abs(nearest - y) >= radius:
        return None
    half = math.sqrt(radius**2 - (nearest - y) ** 2)
    return (x - half, x + half)


def pry_tool_obstacles(right, fits=layout.DEFAULT_MOUNT_FITS):
    """(label, x range, top) as printed of everything the tip's path
    from the east crosses: the half's ledge and joint block, walls,
    dowel bosses and fills, the mount bodies and the standoffs, grown by
    the swelling in plan and their tops counted higher by the rise, and
    the parts but the nice!nano as they are."""
    band = pry_tool_band(fits)
    swelling = layout.PRINT_SWELLING_PER_SIDE_MM
    rise = layout.PRINT_RISE_OF_UP_FACING_BOTTOMS_MM
    grown = layout.grown_range(band, swelling)
    tray = (ledge_pieces(right) + wall_pieces(right) + dowel_bosses(right) + boss_fills(right)
            + mount_pieces(layout.mount_bodies(fits)))
    obstacles = []
    for label, polygon, z_range in tray:
        x_range = band_x_range(polygon, grown)
        if x_range is not None:
            obstacles.append((label, layout.grown_range(x_range, swelling), z_range[1] + rise))
    radius = layout.STANDOFF_DIAMETER_MM / 2.0 + swelling
    for center in layout.MOUNTING_DRILL_CENTERS_MM:
        x_range = circle_band_x_range(center, radius, band)
        if x_range is not None:
            obstacles.append((f"standoff at {center}", x_range, layout.STANDOFF_HEIGHT_MM + rise))
    for envelope in layout.part_envelopes(fits):
        if envelope.part in ("nice!nano", layout.PCB_CONNECTOR_CLEAR_ZONE.part):
            continue
        x_range = band_x_range(box_polygon(envelope), band)
        if x_range is not None:
            obstacles.append((describe_envelope(envelope), x_range, envelope.z_range[1]))
    return obstacles


def tool_top_under_board(slope, reach, tip_bottom):
    """The tip's top at the board's edge, the tip lying at the given
    slope with its underside's end at tip_bottom, reach under the
    board."""
    thickness = layout.NANO_PRY_TOOL_THICKNESS_MM
    return tip_bottom + slope * reach + thickness * math.sqrt(1.0 + slope**2)


def steepest_tool_slope(reach, tip_bottom):
    """The steepest slope at which the tip's top stays under the board's
    underside at its edge, by bisection: zero when even a flat tip does
    not."""
    if tool_top_under_board(0.0, reach, tip_bottom) > 0.0:
        return 0.0
    low, high = 0.0, 10.0
    for _ in range(60):
        middle = (low + high) / 2.0
        if tool_top_under_board(middle, reach, tip_bottom) <= 0.0:
            low = middle
        else:
            high = middle
    return low


def pry_tool_slopes(right, fits=layout.DEFAULT_MOUNT_FITS):
    """(shallowest slope, what sets it, steepest slope) of the tip
    reaching the recess's reach under the board as printed, lying on its
    bottom as printed: the shallowest that rises over the recess's east
    edge and every obstacle east of the tip, the steepest that keeps its
    top under the board's underside at the board's edge."""
    swelling = layout.PRINT_SWELLING_PER_SIDE_MM
    recess = layout.nano_pry_recess_box(fits)
    board_east = layout.nano_board_envelope(fits).x_range[1]
    tip_x = recess.x_range[0] + swelling
    reach = board_east - tip_x
    tip_bottom = -layout.nano_pry_tool_room()
    lip_x = recess.x_range[1] - swelling
    shallowest = Tightest()
    shallowest.update(-(0.0 - tip_bottom) / (lip_x - tip_x), "the recess's east edge")
    for label, (low_x, high_x), top in pry_tool_obstacles(right, fits):
        if high_x <= tip_x or top <= tip_bottom:
            continue
        run = low_x - tip_x
        slope = (top - tip_bottom) / run if run > TOLERANCE_MM else math.inf
        shallowest.update(-slope, label)
    return -shallowest.value, shallowest.where, steepest_tool_slope(reach, tip_bottom)


def degrees(slope):
    return math.degrees(math.atan(slope))


def pry_tool_problems(right, fits=layout.DEFAULT_MOUNT_FITS):
    shallowest, where, steepest = pry_tool_slopes(right, fits)
    if shallowest > steepest + TOLERANCE_MM:
        return [f"no slope brings the pry tool under the board: it must rise at least "
                f"{degrees(shallowest):.1f} degrees over the {where}, and at most "
                f"{degrees(steepest):.1f} keeps it under the board"]
    return []


def pry_recess_problems(right, fits=layout.DEFAULT_MOUNT_FITS):
    problems, _ = pry_recess_clearances(right, fits)
    return problems + pry_recess_board_problems(fits) + pry_tool_problems(right, fits)


def pry_recess_figures():
    recess = layout.nano_pry_recess_box()
    board = layout.NANO_BOARD
    swelling = layout.PRINT_SWELLING_PER_SIDE_MM
    rib = layout.battery_northwest_rib_along_x()
    return [
        require_figure("across as printed", recess.y_range[1] - recess.y_range[0] - 2.0 * swelling,
                       DESIGN_PRY_RECESS_ACROSS_PRINTED_MM, 1),
        require_figure("under the board", board.x_range[1] - recess.x_range[0] - swelling,
                       DESIGN_PRY_RECESS_UNDER_BOARD_PRINTED_MM, 1),
        require_figure("beside it", recess.x_range[1] - board.x_range[1] - swelling,
                       DESIGN_PRY_RECESS_BESIDE_BOARD_PRINTED_MM, 1),
        require_figure("deep", -recess.z_range[0], DESIGN_PRY_RECESS_DEPTH_MM, 1),
        require_figure("the tip's room as printed", layout.nano_pry_tool_room(),
                       DESIGN_PRY_TOOL_ROOM_PRINTED_MM, 1),
        require_figure("floor under it", recess.z_range[0] - layout.FLOOR_UNDERSIDE_Z_MM,
                       DESIGN_PRY_RECESS_FLOOR_UNDER_MM, 1),
        require_figure("from the battery's rib", recess.y_range[0] - rib.y_range[1],
                       DESIGN_PRY_RECESS_FROM_BATTERY_RIB_MM, 1),
        require_figure("lever ratio", layout.nano_pry_lever_ratio(), DESIGN_PRY_LEVER_RATIO, 2),
        require_figure("lift at the pry to release the hook",
                       layout.nano_hook_release_lift() / layout.nano_pry_lever_ratio(),
                       DESIGN_PRY_LIFT_TO_RELEASE_MM, 2),
    ]


def pry_recess_groove_overlap():
    """The x range where the recess runs into the east pin row's groove."""
    recess = layout.nano_pry_recess_box()
    groove = next(box for box in layout.nano_groove_boxes() if box.label.startswith("east"))
    return (max(recess.x_range[0], groove.x_range[0]), min(recess.x_range[1], groove.x_range[1]))


def pry_recess_zone_overlap():
    """(x range, y range) of the recess under the PCB connector's zone in
    plan, None where it is not."""
    recess, zone = layout.nano_pry_recess_box(), layout.PCB_CONNECTOR_CLEAR_ZONE
    x_range = (max(recess.x_range[0], zone.x_range[0]), min(recess.x_range[1], zone.x_range[1]))
    y_range = (max(recess.y_range[0], zone.y_range[0]), min(recess.y_range[1], zone.y_range[1]))
    if x_range[1] - x_range[0] <= TOLERANCE_MM or y_range[1] - y_range[0] <= TOLERANCE_MM:
        return None
    return x_range, y_range


def check_pry_recess(right=False):
    """The pry recess's size and place, clear in plan of the parts, the
    standoffs, the joint, the mount bodies and the hook's slots, under
    the board only where the floor is already grooved or at its edge,
    with floor left under it, and a tip that gets under the board."""
    problems, tightest = pry_recess_clearances(right)
    stated_clearances = {
        what: stated[right] if isinstance(stated, dict) else stated
        for what, (stated, _) in DESIGN_PRY_RECESS_CLEARANCES_MM.items()
    }
    shallowest, where, steepest = pry_tool_slopes(right)
    figures = pry_recess_figures() + [
        require_figure(f"from {what}", tightest[what].value, stated, 3 if stated > 1.0 else 1)
        for what, stated in stated_clearances.items()
        if stated is not None
    ] + [
        require_figure("the tip under the board from degrees", degrees(shallowest),
                       DESIGN_PRY_TOOL_DEGREES[right][0], 1),
        require_figure("to", degrees(steepest), DESIGN_PRY_TOOL_DEGREES[right][1], 1),
    ]
    fail_on(problems + pry_recess_board_problems() + pry_tool_problems(right) + failed(figures),
            f"{half_label(right)}the nice!nano's pry recess off DESIGN.md")
    unstated = [f"from {what} {tightest[what]}"
                for what, stated in stated_clearances.items() if stated is None]
    low, high = pry_recess_groove_overlap()
    zone = pry_recess_zone_overlap()
    under_zone = ("under none of the PCB connector's zone" if zone is None else
                  f"under the PCB connector's zone from x {zone[0][0]:.3f} to {zone[0][1]:.3f}, "
                  f"y {zone[1][0]:.3f} to {zone[1][1]:.3f}")
    return (f"recess:    {half_label(right)}{joined(figures)} (the shallowest over the {where}), "
            f"{', '.join(unstated)}, into the east pin row's groove from x {low:.3f} to "
            f"{high:.3f}, {under_zone}")


def on_right_half(check):
    """The check run on the right half, as a check of its own."""

    def check_right_half():
        return check(right=True)

    check_right_half.__name__ = f"{check.__name__}_on_right_half"
    return check_right_half


CHECKS = (
    check_outline,
    check_outline_on_cells,
    check_slant,
    check_keys_and_holes,
    check_switch_pins,
    check_mounting_drills,
    check_heights,
    check_part_figures,
    check_part_containment,
    check_part_ledge,
    check_part_standoffs,
    check_parts_apart,
    check_part_sockets,
    on_right_half(check_part_sockets),
    check_battery,
    on_right_half(check_battery),
    check_socket_tray_rules,
    on_right_half(check_socket_tray_rules),
    check_socket_ledge,
    on_right_half(check_socket_ledge),
    check_socket_wall,
    on_right_half(check_socket_wall),
    check_socket_standoffs,
    on_right_half(check_socket_standoffs),
    check_joint_figures,
    check_joint_inside,
    on_right_half(check_joint_inside),
    check_joint_clearances,
    on_right_half(check_joint_clearances),
    check_joint_voids,
    on_right_half(check_joint_voids),
    check_magnet_slot_opening,
    check_parking_hole,
    on_right_half(check_parking_hole),
    check_mount_containment,
    on_right_half(check_mount_containment),
    check_mount_parts,
    check_mount_sockets,
    on_right_half(check_mount_sockets),
    check_mount_standoffs,
    check_mount_joint,
    on_right_half(check_mount_joint),
    check_nano_hook,
    check_mount_openings,
    check_pry_recess,
    on_right_half(check_pry_recess),
    check_wire_rooms,
    on_right_half(check_wire_rooms),
)


def main():
    for check in CHECKS:
        try:
            print(check())
        except CheckFailure as failure:
            sys.stdout.flush()
            print(f"FAILED: {failure}", file=sys.stderr)
            return 1
    print(f"all {len(CHECKS)} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
