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
# clearance DESIGN.md gives a slot (3.1 across for the 3.0 magnet).
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
DESIGN_POWER_SWITCH_LEVER_PROUD_MM = 2.2
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
DESIGN_MAGNET_SLOT_FROM_DOWEL_BOSSES_MM = 1.0
DESIGN_MAGNET_SLOTS_APART_MM = 2.2
DESIGN_DOWEL_PIN_SPACING_MM = 48.5
DESIGN_DOWEL_PIN_SLANT_Y_MM = (25.0, 71.2)
DESIGN_PARKING_PIN_PROUD_MM = 1.5
DESIGN_MAGNET_SLOT_ABOVE_BED_MM = 0.5
DESIGN_PIN_OFF_HOLE_MM = 0.05  # each blade from its 3.0 hole, along footprint x
DESIGN_PULL_IN_MM = 0.2
DESIGN_DEFAULT_SLIT_MM = (0.6, 1.6)  # across the blade, along it
DESIGN_SLIT_CLEARANCE_MM = (0.2, 0.4)  # per side as modelled: across the blade, along it


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


def socket_footprints():
    """(key name, convex polygon) for every socket polygon."""
    return [
        (name, polygon)
        for name, center in layout.KEY_CENTERS_MM.items()
        for polygon in layout.socket_polygons(center)
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


def north_edge_index(cutaway):
    """The north outline edge a ledge cut-away lies on: horizontal at
    the cut-away's y, covering its x range, running west (the outline
    runs counter-clockwise)."""
    low_x, high_x = cutaway.x_range
    for index, (start, end) in enumerate(edges(layout.OUTLINE_VERTICES_MM)):
        if (
            abs(start[1] - cutaway.north_edge_y) < TOLERANCE_MM
            and abs(end[1] - cutaway.north_edge_y) < TOLERANCE_MM
            and end[0] <= low_x
            and high_x <= start[0]
        ):
            return index
    raise CheckFailure(
        f"no north outline edge at y {cutaway.north_edge_y} covers the "
        f"{cutaway.part}'s ledge cut-away over x {cutaway.x_range}"
    )


def cutaway_cut(cutaway):
    """A ledge cut-away as a cut through the ledge's full width and
    height. Its north edge runs west, so along it is the start's x less
    x."""
    index = north_edge_index(cutaway)
    start_x = layout.OUTLINE_VERTICES_MM[index][0]
    low_x, high_x = cutaway.x_range
    return layout.TrayCut(
        f"{cutaway.part} cut-away",
        index,
        (start_x - high_x, start_x - low_x),
        layout.ledge_cut_across_range(),
        ledge_z_range(),
    )


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


def ledge_pieces():
    """(label, convex polygon, z range) of the ledge and the joint block
    as cut: DESIGN.md's cut-aways and the sockets' notches, pockets and
    reliefs taken out."""
    cuts = [cutaway_cut(cutaway) for cutaway in layout.LEDGE_CUTAWAYS]
    cuts.extend(layout.all_socket_tray_cuts())
    rings = ring_pieces(layout.tray_cavity_polygon(), layout.ledge_inner_polygon())
    pieces = []
    for index, ring_piece in enumerate(rings):
        if index == layout.SLANT_EDGE_INDEX:
            label = "joint block"
        else:
            label = f"ledge along outline edge {index}"
        pieces.extend(cut_piece(label, ring_piece, ledge_z_range(), cuts))
    return pieces


def wall_pieces():
    """(label, convex polygon, z range) of the wall between the cavity
    and the outer face, the sockets' tab pockets taken out of it."""
    pockets = [cut for cut in layout.all_socket_tray_cuts() if cut.cuts_wall]
    rings = ring_pieces(layout.tray_outer_polygon(), layout.tray_cavity_polygon())
    pieces = []
    for index, ring_piece in enumerate(rings):
        label = f"wall along outline edge {index}"
        pieces.extend(cut_piece(label, ring_piece, wall_z_range(), pockets))
    return pieces


def standoff_bands(center):
    """(z range, flats) of a standoff's height bands, with the sockets'
    flats cut into each band."""
    flats = [flat for flat in layout.all_socket_standoff_flats() if flat.standoff_center == center]
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


def socket_clearances(obstacles, minimum):
    """(problems, tightest) of every socket polygon against (label,
    convex polygon, z range) obstacles wherever their z ranges
    overlap."""
    problems = []
    tightest = Tightest()
    for name, socket in socket_footprints():
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
            DESIGN_POWER_SWITCH_LEVER_PROUD_MM,
            1,
        ),
    ]


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


def check_part_sockets():
    problems = []
    tightest = Tightest()
    for envelope in layout.PART_ENVELOPES:
        if not ranges_overlap(envelope.z_range, socket_z_range()):
            continue
        for name, polygon in socket_footprints():
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
        f"sockets:   parts reaching their height clear in plan by {tightest}; every other part "
        f"stays {layout.SOCKET_BOTTOM_Z_MM - highest_other:.3f} below them"
    )


def check_battery():
    battery = box_polygon(layout.BATTERY)
    covering_keys = sorted(
        {
            name
            for name, polygon in socket_footprints()
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
    return f"battery:   under the sockets of {', '.join(covering_keys)}, {clearance_text}"


def declared_set_problems():
    """Where the sockets layout.py gives notches, reliefs and flats
    differ from DESIGN.md's."""
    declared = (
        ("tab notches", set(layout.SOCKET_TAB_NOTCH_KEYS), DESIGN_TAB_NOTCH_KEYS),
        ("ledge reliefs", set(layout.SOCKET_LEDGE_RELIEF_KEYS), DESIGN_LEDGE_RELIEF_KEYS),
        (
            "standoff flats",
            {(key, center) for center, key in layout.SOCKET_STANDOFF_FLATS},
            {(key, center) for key, center, _, _ in DESIGN_STANDOFF_FLATS},
        ),
    )
    return [
        f"{what} for {sorted(in_layout)} in layout.py, for {sorted(in_design)} in DESIGN.md"
        for what, in_layout, in_design in declared
        if in_layout != in_design
    ]


def uncut_declaration_problems():
    """Sockets named for a cut that kbdkid4's rule does not make."""
    problems = []
    for key in layout.SOCKET_TAB_NOTCH_KEYS:
        if not any(not cut.cuts_wall for cut in layout.socket_tab_cuts(key)):
            problems.append(f"{key}'s tab tip is not near enough the ledge for the rule's notch")
    for key in layout.SOCKET_LEDGE_RELIEF_KEYS:
        if not layout.socket_ledge_reliefs(key):
            problems.append(f"{key}'s socket is not near enough the ledge for the rule's relief")
    for center, key in layout.SOCKET_STANDOFF_FLATS:
        if center not in layout.MOUNTING_DRILL_CENTERS_MM:
            problems.append(f"{key}'s flat is on {center}, where there is no mounting drill")
        elif not layout.socket_standoff_flats(center, key):
            problems.append(
                f"{key}'s socket is not near enough the standoff at {center} for a flat"
            )
    return problems


def flat_plastic(flat):
    """The plastic a flat leaves between it and the insert bore."""
    return flat.plane_distance - layout.STANDOFF_BORE_DIAMETER_MM / 2.0


def thin_flat_problems():
    minimum = layout.STANDOFF_RELIEF_MINIMUM_WALL_MM
    return [
        f"the {flat.label} on the standoff at {flat.standoff_center} leaves "
        f"{flat_plastic(flat):.3f} around the bore, less than {minimum}"
        for flat in layout.all_socket_standoff_flats()
        if flat_plastic(flat) < minimum - TOLERANCE_MM
    ]


def tab_figures():
    tips = [layout.socket_tab_tip_on_edge(key) for key in layout.SOCKET_TAB_NOTCH_KEYS]
    past_edge = [past for _index, _along, past in tips]
    pockets = [
        cut
        for key in layout.SOCKET_TAB_NOTCH_KEYS
        for cut in layout.socket_tab_cuts(key)
        if cut.cuts_wall
    ]
    depths = [cut.across_range[1] - layout.TRAY_GAP_MM for cut in pockets]
    return [
        require_figure_for_all(
            "tab tips past the west edge", past_edge, DESIGN_TAB_TIP_PAST_WEST_EDGE_MM, 3
        ),
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


def relief_figures():
    reliefs = [
        cut for key in layout.SOCKET_LEDGE_RELIEF_KEYS for cut in layout.socket_ledge_reliefs(key)
    ]
    bottom_row = [layout.column_key_name(column, 3) for column in range(6)]
    bottom_row.append(layout.THUMB_KEY_NAME)
    above_face = []
    for key in bottom_row:
        center = layout.KEY_CENTERS_MM[key]
        lowest = min(y for polygon in layout.socket_polygons(center) for _, y in polygon)
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


def flat_figures():
    radius = layout.STANDOFF_DIAMETER_MM / 2.0
    figures = []
    for key, center, stated_clearance, stated_plastic in DESIGN_STANDOFF_FLATS:
        polygons = layout.socket_polygons(layout.KEY_CENTERS_MM[key])
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


def check_socket_tray_rules():
    """The sockets layout.py gives notches, reliefs and flats are
    DESIGN.md's, kbdkid4's rule cuts each, no flat leaves the bore too
    thin, and the cuts come out at DESIGN.md's figures."""
    fail_on(
        declared_set_problems() + uncut_declaration_problems() + thin_flat_problems(),
        "the sockets' notches, reliefs or flats are off",
    )
    figures = tab_figures() + relief_figures() + flat_figures()
    fail_on(failed(figures), "the sockets' cuts off DESIGN.md's figures")
    return "cuts:      " + joined(figures)


def check_socket_ledge():
    minimum = layout.LEDGE_RELIEF_CLEARANCE_MM
    problems, tightest = socket_clearances(ledge_pieces(), minimum)
    fail_on(problems, f"sockets closer than {minimum} to the ledge or the joint block, as cut")
    return f"ledge:     sockets clear of the ledge and the joint block, as cut, by {tightest}"


def check_socket_wall():
    minimum = layout.LEDGE_NOTCH_CLEARANCE_MM
    problems, tightest = socket_clearances(wall_pieces(), minimum)
    fail_on(problems, f"sockets closer than {minimum} to the wall, as pocketed")
    return f"wall:      sockets clear of the wall, as pocketed, by {tightest}"


def check_socket_standoffs():
    minimum = layout.STANDOFF_RELIEF_CLEARANCE_MM
    problems = []
    tightest = Tightest()
    for center in layout.MOUNTING_DRILL_CENTERS_MM:
        for z_range, flats in standoff_bands(center):
            if not ranges_overlap(z_range, socket_z_range()):
                continue
            for name, socket in socket_footprints():
                clearance = standoff_clearance(center, flats, socket)
                standoff = describe_piece(f"standoff at {center}", z_range)
                where = f"{name}'s socket and the {standoff}"
                if flats:
                    where += f" with {len(flats)} flat{'s' if len(flats) > 1 else ''}"
                tightest.update(clearance, where)
                if clearance < minimum - TOLERANCE_MM:
                    problems.append(f"{where}: {clearance:.3f}, less than {minimum}")
    fail_on(problems, f"sockets closer than {minimum} to the standoffs, as flattened")
    return f"posts:     sockets clear of the standoffs, as flattened, by {tightest}"


def joint_features():
    """(label, plan polygon, z range) of the magnet slots and the dowel
    bosses."""
    return magnet_slots() + dowel_bosses()


def magnet_slots():
    return [
        (
            f"magnet slot at {along} along the slant",
            layout.magnet_slot_polygon(along),
            layout.magnet_slot_z_range(),
        )
        for along in layout.MAGNET_ALONGS_MM
    ]


def dowel_bosses():
    return [
        (
            f"dowel boss at {along} along the slant",
            layout.dowel_boss_polygon(along),
            layout.dowel_boss_z_range(),
        )
        for along in layout.DOWEL_PIN_ALONGS_MM
    ]


def tightest_of_pairs(pairs):
    """The smallest plan clearance over pairs of joint features."""
    tightest = Tightest()
    for (first_label, first_polygon, _), (second_label, second_polygon, _) in pairs:
        tightest.update(
            convex_separation(first_polygon, second_polygon), f"{first_label} and {second_label}"
        )
    return tightest


def tightest_between(first_features, second_features):
    return tightest_of_pairs(itertools.product(first_features, second_features))


def tightest_within(features):
    return tightest_of_pairs(itertools.combinations(features, 2))


def dowel_pin_figures():
    first_along, second_along = layout.DOWEL_PIN_ALONGS_MM
    slant_ys = [layout.slant_point(along, 0.0)[1] for along in (first_along, second_along)]
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
            "dowel pin height, midway between the bed and the PCB",
            layout.DOWEL_PIN_Z_MM,
            (layout.FLOOR_UNDERSIDE_Z_MM + layout.PCB_UNDERSIDE_Z_MM) / 2.0,
            1,
        ),
        require_figure(
            "parked pin proud of the wall",
            layout.DOWEL_PIN_LENGTH_MM - layout.PARKING_PIN_INSERTION_MM,
            DESIGN_PARKING_PIN_PROUD_MM,
            1,
        ),
    ]


def magnet_figures():
    return [
        require_figure(
            "magnet slots from the dowel bosses",
            tightest_between(magnet_slots(), dowel_bosses()).value,
            DESIGN_MAGNET_SLOT_FROM_DOWEL_BOSSES_MM,
            1,
        ),
        require_figure(
            "magnet slots apart",
            tightest_within(magnet_slots()).value,
            DESIGN_MAGNET_SLOTS_APART_MM,
            1,
        ),
        require_figure(
            "magnet slot bottom above the bed",
            layout.MAGNET_SLOT_BOTTOM_Z_MM - layout.FLOOR_UNDERSIDE_Z_MM,
            DESIGN_MAGNET_SLOT_ABOVE_BED_MM,
            1,
        ),
    ]


def check_joint_figures():
    figures = dowel_pin_figures() + magnet_figures()
    fail_on(failed(figures), "the joint off DESIGN.md's figures")
    return "joint:     " + joined(figures)


def magnet_slot_opening_problems(opening_across, wall_left):
    """Where a magnet would not drop into its slot: the slot or the
    opening above it too tight for it with MAGNET_DROP_IN_CLEARANCE_MM,
    or the cut-back through the wall."""
    clearance = MAGNET_DROP_IN_CLEARANCE_MM
    thickness = layout.MAGNET_THICKNESS_MM
    diameter = layout.MAGNET_DIAMETER_MM
    needed_across = thickness + clearance
    needed_along = diameter + clearance
    problems = []
    if layout.MAGNET_SLOT_ACROSS_MM < needed_across - TOLERANCE_MM:
        problems.append(
            f"the slot is {layout.MAGNET_SLOT_ACROSS_MM} across, the {thickness} magnet needs "
            f"{needed_across:.3f}"
        )
    if layout.MAGNET_SLOT_ALONG_MM < needed_along - TOLERANCE_MM:
        problems.append(
            f"the slot is {layout.MAGNET_SLOT_ALONG_MM} along the slant, the {diameter} magnet "
            f"needs {needed_along:.3f}"
        )
    if opening_across < needed_across - TOLERANCE_MM:
        problems.append(
            f"the opening above each slot is {opening_across:.3f} across, the {thickness} magnet "
            f"needs {needed_across:.3f}"
        )
    if wall_left <= TOLERANCE_MM:
        problems.append(f"the cut-back leaves {wall_left:.3f} of wall at the face")
    return problems


def check_magnet_slot_opening():
    """Above the block the wall would cover the slot's outer side, so
    its inner face is cut back to the slot: the slot and the opening
    must take the magnet with MAGNET_DROP_IN_CLEARANCE_MM."""
    cutback = layout.magnet_wall_cutback_outward()
    low, high = layout.magnet_slot_opening_outward_range(cutback)
    low_uncut, high_uncut = layout.magnet_slot_opening_outward_range(layout.TRAY_GAP_MM)
    wall_left = layout.JOINT_FACE_OUTWARD_MM - cutback
    fail_on(
        magnet_slot_opening_problems(high - low, wall_left),
        "the magnets cannot drop into their slots",
    )
    return (
        f"slots:     {layout.MAGNET_SLOT_ACROSS_MM} x {layout.MAGNET_SLOT_ALONG_MM} for the "
        f"{layout.MAGNET_THICKNESS_MM} x {layout.MAGNET_DIAMETER_MM} magnet, open above the "
        f"block {high - low:.3f} across ({high_uncut - low_uncut:.3f} without the cut-back), "
        f"the cut-back leaving {wall_left:.3f} of wall from z {layout.JOINT_BLOCK_TOP_Z_MM} to "
        f"{layout.MAGNET_WALL_CUTBACK_TOP_Z_MM}"
    )


def check_joint_inside():
    outer = layout.tray_outer_polygon()
    problems = []
    tightest = Tightest()
    for label, polygon, _z_range in joint_features():
        margin = containment_margin(polygon, outer)
        tightest.update(margin, label)
        if margin < -TOLERANCE_MM:
            problems.append(f"the {label} pokes {-margin:.3f} past the tray's outer face")
    fail_on(problems, "joint features outside the tray")
    return f"joint:     magnet slots and dowel bosses inside the tray's outer face by {tightest}"


def joint_tray_problems(label, polygon, z_range):
    """(problems, tightest from the sockets, tightest from the
    standoffs) of one joint feature."""
    standoff_radius = layout.STANDOFF_DIAMETER_MM / 2.0
    problems = []
    from_sockets = Tightest()
    from_standoffs = Tightest()
    if ranges_overlap(z_range, socket_z_range()):
        for name, socket in socket_footprints():
            clearance = convex_separation(polygon, socket)
            from_sockets.update(clearance, f"{label} and {name}'s socket")
            if clearance < -TOLERANCE_MM:
                problems.append(f"the {label} overlaps {name}'s socket by {-clearance:.3f}")
    if ranges_overlap(z_range, standoff_z_range()):
        for center in layout.MOUNTING_DRILL_CENTERS_MM:
            clearance = circle_separation(center, standoff_radius, polygon)
            from_standoffs.update(clearance, f"{label} and the standoff at {center}")
            if clearance < -TOLERANCE_MM:
                problems.append(
                    f"the {label} overlaps the standoff at {center} by {-clearance:.3f}"
                )
    return problems, from_sockets, from_standoffs


def check_joint_clearances():
    features = joint_features()
    problems = []
    from_sockets = Tightest()
    from_standoffs = Tightest()
    from_each_other = Tightest()
    for label, polygon, z_range in features:
        feature_problems, sockets, standoffs = joint_tray_problems(label, polygon, z_range)
        problems.extend(feature_problems)
        from_sockets.update(sockets.value, sockets.where)
        from_standoffs.update(standoffs.value, standoffs.where)
    for first, second in itertools.combinations(features, 2):
        first_label, first_polygon, first_z = first
        second_label, second_polygon, second_z = second
        if not ranges_overlap(first_z, second_z):
            continue
        clearance = convex_separation(first_polygon, second_polygon)
        where = f"{first_label} and {second_label}"
        from_each_other.update(clearance, where)
        if clearance < -TOLERANCE_MM:
            problems.append(f"the {where} overlap by {-clearance:.3f}")
    fail_on(problems, "joint features in each other's way, or the sockets' or standoffs'")
    return (
        f"joint:     clear of the sockets by {from_sockets}, of the standoffs by "
        f"{from_standoffs}, of each other by {from_each_other}"
    )


def check_parking_hole():
    """The parking hole runs through the thumb's east wall, and since
    DESIGN.md gives its boss no size, it is kept clear in plan of the
    sockets (the thumb's above all), the standoffs (the one at (114.141,
    19.765) above all) and the joint features (the lower dowel boss above
    all) at any height."""
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
    from_sockets = Tightest()
    for name, polygon in socket_footprints():
        from_sockets.update(convex_separation(hole, polygon), f"{name}'s socket")
    from_standoffs = Tightest()
    for center in layout.MOUNTING_DRILL_CENTERS_MM:
        from_standoffs.update(
            circle_separation(center, layout.STANDOFF_DIAMETER_MM / 2.0, hole),
            f"the standoff at {center}",
        )
    from_joint = Tightest()
    for label, polygon, _z_range in joint_features():
        from_joint.update(convex_separation(hole, polygon), f"the {label}")
    for tightest in (from_sockets, from_standoffs, from_joint):
        if tightest.value < -TOLERANCE_MM:
            problems.append(f"the parking hole overlaps {tightest.where} by {-tightest.value:.3f}")
    fail_on(problems, "the parking hole collides")
    return (
        f"parking:   hole through the thumb's east wall ({wall_margin:.3f} from its ends), clear "
        f"of the sockets by {from_sockets}, the standoffs by {from_standoffs}, the joint by "
        f"{from_joint}"
    )


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
    check_battery,
    check_socket_tray_rules,
    check_socket_ledge,
    check_socket_wall,
    check_socket_standoffs,
    check_joint_figures,
    check_joint_inside,
    check_joint_clearances,
    check_magnet_slot_opening,
    check_parking_hole,
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
