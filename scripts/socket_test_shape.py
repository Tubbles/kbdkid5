"""The socket retention test strips' shapes (work item 008): a frame
printed in place of the PCB that holds Kailh Choc hotswap sockets in
pockets on its underside, for a keyboard wired by hand, in three
stackable strips of CELL_COUNT cells at the key pitch.

A frame strip (POCKET, LIP or HOLES) is a plate of the PCB's thickness, each
cell with one key's footprint holes grown by pull_in like the PCB
mock's, so the switch's pins reach the socket's contacts as through a
PCB and the socket's two bosses sit in the 3.0 pin holes, as on a PCB.
On the pocket strip those two holes are POCKET_STRIP_PIN_HOLE_DIAMETER_MM
as modelled instead, so they leave the bosses free and the pocket alone
locates the socket, and on the hole strip they step across the cells.
Under each cell, pocket walls around the socket's plastic body, open
at the bottom, against which the socket's top face rests on the
plate's underside (the ceiling). They follow the body's outline,
curves and all (layout.HOTSWAP_SOCKET_OUTLINE_MM, from the socket's
STEP, not the cover layout.HOTSWAP_SOCKET_LOBES_MM and
HOTSWAP_SOCKET_FILLS_MM give the tray): in plan they are the region
between the outline moved out by the pocket's gap (pocket_gap(), their
inner face) and by the gap plus WALL_THICKNESS_MM (their outer face),
corners extended to their intersections. The walls are
layout.HOTSWAP_SOCKET_BODY_HEIGHT_MM deep, the socket body's height on
Kailh's drawing (1.80, to the bumps on its top that bear on a board),
not layout.HOTSWAP_SOCKET_REACH_MM: kbdkid4's STEP hangs its 1.85 body
0.17 below the PCB, which a socket pressed against a printed ceiling
does not do. The walls are built whole, and every footprint hole runs
on from the plate down through them to their mouth, so the switch's
center post and side pegs, which reach below the plate, pass them: the
west peg's hole bores through lobe B's north wall (the socket's lobe
passes that hole by 0.42), leaving a sliver of the wall's inner side at
the tighter fits and none at the hole strip's. No other hole meets a
wall (cell_wall_bores() finds the ones that do in the walls' plan): the
center post's hole, 1.9 in radius at the default pull_in, keeps 2.38
from its center to the walls' outer face around lobe B's round toward
lobe A at the lip strip's fit. The walls are slotted through their full
depth where the socket's two metal end tabs leave the body's ends. The
slots are wider than the straight part of either end between its
chamfers or its round and step, so they take the walls' inner face
along those parts, but for at most 0.1 of the east end's beside each
slot at the looser fits.

The tabs: the user solders a wire to each tab before pressing the
socket in from below, since an iron on a tab in its pocket would melt
the plastic around it (the tab lies against the ceiling, the wall 0.2
beside it). So each tab's slot is open at the walls' mouth, wide enough
for the tab with TAB_SOLDER_PER_SIDE_MM of solder on both sides at the
slip fit, and runs on into a recess in the ceiling over the tab, which
leaves room for solder on the tab's top face.

The strips print upside down, the plate's top face on the bed, the
walls growing up. In the project's print model (layout.py's printed
fits) every vertical face swells PRINT_SWELLING_PER_SIDE_MM, so the
pockets are printed_fit() of the socket's body and the footprint holes
are grown by pull_in; every up-facing face rises
PRINT_RISE_OF_UP_FACING_BOTTOMS_MM, here the ceiling (the bottom the
socket fits against), the walls' mouths and the bosses' ends, which
all rise together, so relative to the ceiling they stay where they are
modelled; the down-facing faces (the lips' retaining faces) stay where
they are modelled, which brings them that much closer to the ceiling;
and a 45 degree face moves PRINT_SWELLING_AT_45_DEGREES_MM along an
axis. The socket's room is counted from the risen ceiling, so the
lips' retaining faces sit the socket's height plus the rise below the
ceiling as modelled.

POCKET: the pocket's fit steps across the cells (cell_pocket_fit()),
the pin holes at POCKET_STRIP_PIN_HOLE_DIAMETER_MM. Any pocket can be
glued.

HOLES: every pocket at HOLE_STRIP_POCKET_FIT_MM, loose, and the pin
holes stepping down from the pocket strip's across the cells
(cell_pin_hole_diameter()), so only the holes can hold the socket.

LIP: every pocket at the lip strip's fit (LIP_POCKET_FIT_MM, the fit
the pocket strip held a socket best at, unless the export's lip_fit
overrides it), with a lip under three of the socket's lobe faces
(FINGERS) catching the socket's bottom face, a right triangle
LIP_LENGTH_MM long: a flat retaining face under the socket and a 45
degree lead-in below it, so the socket snaps in from below. Their reach
past the walls' inner faces as printed steps across the cells
(cell_lip_reach()), which is their reach under the socket when the
walls sit on it. A fit tighter than snug presses the walls, and so the
fingers, into the socket by the print model, a bend finger_strain()
leaves out (see LIP_POCKET_FIT_MM). The lead-in's swelling moves the
tip LIP_TIP_GROWTH_AS_PRINTED_MM past the wall's own swelling, so each
lip is modelled that much shorter. Printed, the retaining face is an
overhang of the reach. Each lip sits at the free end of a finger
(FINGERS): a blade of the wall's thickness, from the plate's top face
to the walls' mouth, cut free of the plate and the walls by slots
through both. At its other end it runs into the plate and, under the
plate, into a block of solid plastic from the ceiling to the walls'
mouth (finger_root_block_box()), so its root is held over its whole
height, as the snap hook's formula assumes. It bends in plan as the
socket passes the lip, within the hook's 2 % strain as printed by that
formula (finger_strain(), checked by the export), and prints from the
bed up, the slots' and the blade's edges on the bed chamfered like the
tray's snap hook's. The lip strip's walls, fingers and blocks reach
down to the lips' band bottom, where the largest lead-in meets its
finger.

The frame strips carry the same bosses, at every cell boundary and at
both ends of the strip, BOSS_NORTH_OF_KEY_ROW_MM north and
BOSS_SOUTH_OF_KEY_ROW_MM south of the key row, the tray's standoffs'
diameter, bored for the tray's M2 heat-set inserts. They end at the lip
strip's band bottom, so the backing meets the lip strip's walls,
fingers, blocks and bosses in one plane and stands clear of the pocket
strip's walls. The plate reaches BOSS_EDGE_MARGIN_MM past the bosses.

BACKING: a plate BACKING_THICKNESS_MM thick with clearance holes for
M2 screws under the bosses and, under each of the body's lobes, a pad of
the cover's lobe rectangle (PAD_LOBE_RECTANGLES_MM) moved in by
pad_inset() (so it passes inside the largest lip as printed), whose top
relative to the socket's bottom steps across the cells
(cell_pad_offset()). The backing prints bottom down, so its top
and its pads' tops rise together and the pads stand where they are
modelled relative to the bosses' ends and so to the ceiling.

Cell k (from 1, west to east) has k notches in its south edge on every
strip, as on the slit test strip, the frame strips' through the plate
south of the pockets and the backing's in line with them. The lip
strip also has one notch (LIP_STRIP_MARK_*) in the middle of its north
edge, between cells 3 and 4, clear of the bosses and the switches, and
the pocket strip five of that size (POCKET_STRIP_MARK_XS_MM), one at
every cell boundary, which tell it from the first pocket strip, which
had none, the second, which had the two between cells 2 and 3 and
between cells 4 and 5, and the third, which had four, at every
boundary but the middle one. The hole strip has
three (HOLE_STRIP_MARK_XS_MM), between cells 1 and 2, 3 and 4 (where
the lip strip has its one) and 5 and 6. The backing has two
(BACKING_MARK_XS_MM), between cells 2 and 3 and between cells 4 and 5,
which tell it from the second backing, which had the lip strip's one
and pads 0.1 larger each way, and from the first, which had none and
pads 0.3 larger each way.

A switch is the same on both halves, so is the frame: the footprint is
the left half's (layout.footprint_holes() at FOOTPRINT_ROTATION_DEGREES).

Coordinates: the strip's frame, the cells' south west corner at (0, 0),
cell index (from 0) at cell_key_center(index), z 0 on the ceiling, the
plate up to the PCB's thickness, walls and bosses below. The backing is
built with its bottom on z = 0 and stacked by stacked_backing().

Like the other *_shape.py modules this one has no entry point, so
probes and the export script can import it.
"""

import math
from dataclasses import dataclass

import FreeCAD as App
import Part

import layout
import pcb_shape
from freecad_common import offset_outline
from tray_shape import (CUT_EXTRA_MM, UP, layout_polygon_wire, plan_prism, rectangle_wire,
                        require_one_valid_solid)

POCKET = "pocket"
LIP = "lip"
BACKING = "backing"
HOLES = "holes"
STRIP_KINDS = (POCKET, LIP, BACKING, HOLES)
# The frame strips the backing is stacked under and checked against.
FRAME_KINDS = (POCKET, LIP)

CELL_COUNT = 6

# The steps across the cells, cell 1's figure and the step: the pocket's
# fit, the lips' reach past the walls' inner faces as printed, and the
# pads' tops relative to the socket's bottom (negative a gap, positive
# pressing). The pocket's fits are all tighter than snug: on the first
# pocket strip, -0.10 to +0.15, every pocket but cells 3 and 5 printed
# loose (doc/log/2026-10-17.md). The reach's step is the even one that
# takes cell 6 to the largest reach the fingers bend for within the
# hook's 2 % (lobe A's north finger, the shortest).
FIRST_POCKET_FIT_MM = -0.40
POCKET_FIT_STEP_MM = 0.05
FIRST_LIP_REACH_MM = 0.15
LIP_REACH_STEP_MM = 0.04
FIRST_PAD_OFFSET_MM = -0.10
PAD_OFFSET_STEP_MM = 0.05

# The lip strip's pockets, unless the export's lip_fit overrides it: the
# second pocket strip's cell 5, which the user found the best fit, "nice
# satisfying snap and good press fit" (doc/log/2026-10-18.md). By the
# print model its walls press the socket 0.1 a side, which bends the
# fingers before a lip does, 0.1 that finger_strain() leaves out: with
# it the north finger would strain 2.09, 2.32 and 2.55 % in cells 4 to
# 6, over the hook's 2 %. The reaches stay, since both pocket strips
# printed larger than the model says, so the press is less than 0.1.
LIP_POCKET_FIT_MM = -0.20

# The pocket strip's two pin holes (layout.CHOC_FOOTPRINT_PIN_HOLE_CENTERS_MM),
# which the socket's 2.90 bosses sit in, as modelled whatever pull_in.
# On the first pocket strip they were the footprint's 3.0 grown to 3.4,
# and its pockets' result mixed the bosses' fit with the pocket's, so
# these must leave the bosses free and let the pocket alone locate the
# socket. 3.5 is the user's "something like 3.5 mm", within the 3.54 at
# which the tab recess keeps RECESS_HOLE_CLEARANCE_MM (export) from the
# hole. The lip strip keeps the footprint's holes, which the hole strip
# found loose (doc/log/2026-10-18.md), so its lips alone hold the
# socket; its fingers' slots keep FINGER_SLOT_HOLE_WEB_MM from them only
# up to 3.44.
POCKET_STRIP_PIN_HOLE_DIAMETER_MM = 3.5

# The hole strip: every pocket at the first pocket strip's cell 6 fit,
# which the user found loose, so only the pin holes can hold the
# socket, the pin holes stepping down from the pocket strip's across the
# cells (cell_pin_hole_diameter()), as modelled whatever pull_in.
HOLE_STRIP_POCKET_FIT_MM = 0.15
HOLE_STRIP_PIN_HOLE_STEP_MM = 0.10

# The pocket walls, as thick as the tray's (two lines). The switch's
# center post and side pegs, whose holes are
# layout.CHOC_FOOTPRINT_HOLES_MM's first three, reach below the plate.
WALL_THICKNESS_MM = layout.TRAY_WALL_MM
SWITCH_PROTRUDING_HOLE_COUNT = 3

# The tabs' slots and recesses: the tab with this much solder on each
# side passes its slot at the slip fit, and the recess reaches this far
# past the tab's tip and this deep into the plate (its bottom faces up
# as printed, so it leaves 0.3 of room over the tab's top face).
TAB_SOLDER_PER_SIDE_MM = 0.5
TAB_RECESS_PAST_TIP_MM = 0.5
TAB_RECESS_DEPTH_MM = 0.5

# The lips: under the socket's lobe faces whose fingers find room clear
# of the tab slots and the switch's holes: lobe A's north and south faces
# and lobe B's south face, in board coordinates (lobe B's north face is
# bored by the west peg's hole). Each finger runs along its face as the
# outline gives it (layout.HOTSWAP_SOCKET_OUTLINE_MM: y -3.573, -8.223
# and -6.023 from the key center, straight from x -1.18 to 1.32, -1.93
# to 1.32 and -6.73 to -3.43), which the lips lie on, so a blade's inner
# face is the wall's. LIP_LENGTH_MM is short so that lobe A's north
# finger, boxed in by the next cell's wire room, still bends far enough
# from its root.
LIP_LENGTH_MM = 1.0
LIP_TIP_GROWTH_AS_PRINTED_MM = (
    layout.PRINT_SWELLING_AT_45_DEGREES_MM - layout.PRINT_SWELLING_PER_SIDE_MM
)

# The fingers that carry the lips. A finger's blade is the wall's
# thickness and lies on its lip's wall line. Its slots are
# FINGER_FREE_SLOT_MM on the socket's side and past its free end, which
# frees it, and on its other side the room it bends into, which takes
# its free end's swing as printed with FINGER_ROOM_SPARE_MM to spare,
# the snap hook's margin. The free slots are five times the 0.098 under
# which PrusaSlicer's default gap closing fills a gap, and the first
# slit test strip's 0.5 slits printed open wide enough to pass a 0.4
# blade easily (doc/log/2026-10-17.md). The room is counted at the print
# model's 0.2 swelling per side, the narrower reading. The root block
# reaches FINGER_ROOT_BLOCK_LENGTH_MM on past the root and
# FINGER_ROOT_BLOCK_SIDE_MM out from the blade's faces on both sides,
# from the ceiling to the walls' mouth; 0.3, down from 0.4, since at the
# lip strip's fit the blocks' inner sides came 0.18 from their own
# cell's tab wire rooms, under the 0.2 swelling (0.28 and 0.29 now). On
# the bed the slots' outline is chamfered on its two long sides and past
# the free end, the blade on its two faces and its free end, as the snap
# hook's slots and blade are (layout.NANO_HOOK_SLOT_BED_CHAMFER_MM,
# NANO_HOOK_BLADE_BED_CHAMFER_MM), which leaves the blade 0.4 on the bed.
FINGER_THICKNESS_MM = WALL_THICKNESS_MM
FINGER_FREE_SLOT_MM = 0.5
FINGER_ROOM_AS_PRINTED_MM = 0.7
FINGER_ROOM_SPARE_MM = 0.1
FINGER_ROOT_BLOCK_LENGTH_MM = 1.0
FINGER_ROOT_BLOCK_SIDE_MM = 0.3
FINGER_SLOT_BED_CHAMFER_MM = layout.NANO_HOOK_SLOT_BED_CHAMFER_MM
FINGER_BLADE_BED_CHAMFER_MM = layout.NANO_HOOK_BLADE_BED_CHAMFER_MM


@dataclass(frozen=True)
class Finger:
    """A finger along its lip's lobe face, which runs along x in the
    strip's frame: the face's y and the direction toward the socket
    along y, then x of its ends, all relative to the key center: the
    free end (the lip's far end), the root (where the blade meets the
    plate and its block), and the slots' end past the free end."""

    face_y: float
    toward_socket: float
    free_end_x: float
    root_x: float
    slots_end_x: float


FINGERS = (
    # Lobe A's north face: the free end 0.11 east of where the outline's
    # 1.5 fill meets the face's straight part, with the lip on that part
    # (set 0.2 east of the cover's square over the fill,
    # layout.HOTSWAP_SOCKET_FILLS_MM's third). The root block's far end
    # lies 0.2 short of the next cell's west tab's wire room. The room
    # opens into the center post's hole.
    Finger(-3.573, -1.0, -1.07, 5.57, -1.57),
    # Lobe A's south face: the free end as the north finger's, so the two
    # lips face each other on the face's straight part, the root block's
    # far end 0.5 short of the next cell's lobe B finger's slots.
    Finger(-8.223, 1.0, -1.07, 6.57, -1.57),
    # Lobe B's south face: the free end 0.21 west of where the outline's
    # 0.75 fill inside the step meets the face's straight part, with the
    # lip on that part (set 0.2 west of the cover's square over the
    # fill, the second), the root block's far end 0.2 past the previous
    # cell's east tab's wire room. The slots' end lies 0.01 past the
    # walls' inner face along the outline's step (x -2.68 less the gap at
    # the lip strip's fit), so they take the wall between and leave no
    # skin of it.
    Finger(-6.023, 1.0, -3.64, -10.98, -2.77),
)

# The fingers' slots may open into the center post's hole and keep this
# much from every other footprint hole as modelled, below their bed
# chamfers: lobe B's south finger's free slot passes the pin hole at
# footprint (-3.75, 5.0) by 0.17 at the lip strip's fit (0.27 at the
# snug fit, where 0.25 was asked for). The web prints about one line
# wide (0.57 by the print model), and where it does not print the slot
# opens into a hole the hole strip found loose, no harm done.
FINGER_SLOT_HOLE_WEB_MM = 0.15

# The bosses: the tray's standoff diameter and insert bore, on every
# boundary between cells and at both ends of the strip, north and south
# of the key row (the north row 0.5 clear of the walls around the fill
# at the body's north west corner in a +0.15 pocket, the first pocket
# strip's loosest, the south row past the lip strip's fingers' slots,
# which fill the cells' south edge, 0.5 clear of them). The bore's floor
# keeps the plate's top face whole, three layers.
BOSS_DIAMETER_MM = layout.STANDOFF_DIAMETER_MM
INSERT_BORE_DIAMETER_MM = layout.STANDOFF_BORE_DIAMETER_MM
BOSS_NORTH_OF_KEY_ROW_MM = 3.1
BOSS_SOUTH_OF_KEY_ROW_MM = -12.5
INSERT_BORE_FLOOR_MM = 0.6
BOSS_EDGE_MARGIN_MM = 0.5

# The backing: its thickness (the battery clearance in the real tray
# allows backing_thickness_limit(), four layers fit under it), the
# screws' clearance holes (the PCB's mounting drills, printed), and how
# far the pads stay inside the largest lip as printed: 0.3, up from the
# first backing's 0.1 at the user's request after its pads stood off
# under the pocket strip (doc/log/2026-10-18.md), no perfect fit wanted.
BACKING_THICKNESS_MM = 0.8
SCREW_CLEARANCE_HOLE_DIAMETER_MM = layout.printed_fit(
    layout.MOUNTING_DRILL_DIAMETER_MM, layout.SNUG_FIT_MM
)
PAD_CLEARANCE_TO_LIPS_MM = 0.3

# The pads' rectangles before pad_inset(), in footprint-local
# coordinates (x range, y range): the cover's lobes
# (layout.HOTSWAP_SOCKET_LOBES_MM) cut back to the body's ends, which the
# third backing was printed with, their long faces at the outline's
# (0.003 from the cover's rounded ones) so the pads keep their distance
# from the lips, which sit on those faces. Lobe B's reaches down to the
# cover's y 2.25, so on the outline its pad's corner beside the 1.5 fill
# lies 0.534 inside the body, the nearest the pads come to its edge,
# where the pockets' walls follow it.
PAD_LOBE_RECTANGLES_MM = (
    ((-8.223, -3.573), (-2.07, 2.25)),
    ((-6.023, -1.373), (2.25, 7.48)),
)

# The notches that number the cells, as on the slit test strip, through
# each strip from its south edge, and the lip strip's mark in its north
# edge. The pocket strip's five marks are the lip strip's size, at cell
# boundaries like it, so each lies over a boss, 2.0 north of it. The
# third backing has the second pocket strip's two, the second backing
# had the lip strip's one.
NOTCH_WIDTH_MM = 1.0
NOTCH_DEPTH_MM = 0.8
NOTCH_PITCH_MM = 2.0
LIP_STRIP_MARK_WIDTH_MM = 3.0
LIP_STRIP_MARK_DEPTH_MM = 1.5
LIP_STRIP_MARK_X_MM = 3 * layout.KEY_PITCH_MM
POCKET_STRIP_MARK_XS_MM = tuple(boundary * layout.KEY_PITCH_MM for boundary in range(1, CELL_COUNT))
HOLE_STRIP_MARK_XS_MM = (1 * layout.KEY_PITCH_MM, 3 * layout.KEY_PITCH_MM,
                         5 * layout.KEY_PITCH_MM)
BACKING_MARK_XS_MM = tuple(boundary * layout.KEY_PITCH_MM for boundary in (2, 4))

VOLUME_RELATIVE_TOLERANCE = pcb_shape.VOLUME_RELATIVE_TOLERANCE
AREA_TOLERANCE_MM2 = 1e-9
LENGTH_TOLERANCE_MM = 1e-9

# The bed chamfers' share of the footprint holes is integrated over the
# chamfer's height in this many steps (Simpson's rule, an even number).
CHAMFER_INTEGRATION_STEPS = 400


# Plane geometry, plain Python.


def cross(origin, point_a, point_b):
    return (point_a[0] - origin[0]) * (point_b[1] - origin[1]) - (
        point_a[1] - origin[1]
    ) * (point_b[0] - origin[0])


def clip_convex(subject, clip):
    """The part of a convex counter-clockwise polygon inside another
    (Sutherland-Hodgman), possibly empty. A point on a clip edge's line
    (within rounding, as where two cutters meet) counts as inside, so an
    edge along that line is kept whole rather than crossed."""
    output = list(subject)
    for index in range(len(clip)):
        edge_start, edge_end = clip[index], clip[(index + 1) % len(clip)]
        points, output = output, []
        for point_index, point in enumerate(points):
            before = points[point_index - 1]
            point_inside = cross(edge_start, edge_end, point) >= -AREA_TOLERANCE_MM2
            before_inside = cross(edge_start, edge_end, before) >= -AREA_TOLERANCE_MM2
            if point_inside != before_inside:
                output.append(segment_line_crossing(before, point, edge_start, edge_end))
            if point_inside:
                output.append(point)
        if not output:
            return ()
    return tuple(output)


def segment_line_crossing(start, end, line_start, line_end):
    direction = (end[0] - start[0], end[1] - start[1])
    line_direction = (line_end[0] - line_start[0], line_end[1] - line_start[1])
    return layout.line_intersection(start, direction, line_start, line_direction)


def convex_area(polygons):
    """The area common to convex counter-clockwise polygons."""
    common = polygons[0]
    for polygon in polygons[1:]:
        common = clip_convex(common, polygon)
        if len(common) < 3:
            return 0.0
    return layout.polygon_signed_area(common)


def covered_area(cutters, measure):
    """measure() of the convex cutters' union, by inclusion and
    exclusion over their intersections, which are convex too."""
    total = 0.0

    def visit(start, common, sign):
        nonlocal total
        for index in range(start, len(cutters)):
            clipped = cutters[index] if common is None else clip_convex(common, cutters[index])
            if len(clipped) < 3 or layout.polygon_signed_area(clipped) <= AREA_TOLERANCE_MM2:
                continue
            total += sign * measure(clipped)
            visit(index + 1, clipped, -sign)

    visit(0, None, 1.0)
    return total


def rectangle(x_range, y_range):
    return (
        (x_range[0], y_range[0]),
        (x_range[1], y_range[0]),
        (x_range[1], y_range[1]),
        (x_range[0], y_range[1]),
    )


def polygon_box(polygon):
    """(x range, y range) of a polygon that is an axis-aligned rectangle."""
    xs = [x for x, _ in polygon]
    ys = [y for _, y in polygon]
    box = ((min(xs), max(xs)), (min(ys), max(ys)))
    if abs(layout.polygon_signed_area(rectangle(*box)) - layout.polygon_signed_area(polygon)) > (
        AREA_TOLERANCE_MM2
    ):
        raise SystemExit("error: a cutter that meets a hole is not an axis-aligned rectangle")
    return box


def circle_arc_integral(x, radius):
    """The integral of sqrt(radius^2 - t^2) dt from 0 to x, x clamped to
    the circle."""
    x = max(-radius, min(radius, x))
    return (x * math.sqrt(radius**2 - x**2) + radius**2 * math.asin(x / radius)) / 2.0


def circle_arc_area(low, high, radius):
    if low >= high:
        return 0.0
    return circle_arc_integral(high, radius) - circle_arc_integral(low, radius)


def circle_area_below(y, x_range, radius):
    """The area of the circle around the origin below the line at y,
    between two x."""
    low, high = max(x_range[0], -radius), min(x_range[1], radius)
    if low >= high or y <= -radius:
        return 0.0
    if y >= radius:
        return 2.0 * circle_arc_area(low, high, radius)
    half_chord = math.sqrt(radius**2 - y**2)
    inner = (max(low, -half_chord), min(high, half_chord))
    area = y * max(0.0, inner[1] - inner[0]) + circle_arc_area(*inner, radius)
    if y > 0.0:
        area += 2.0 * (circle_arc_area(low, min(high, -half_chord), radius)
                       + circle_arc_area(max(low, half_chord), high, radius))
    return area


def circle_box_area(center, radius, box):
    """The area a circle and an axis-aligned rectangle share."""
    (x_low, x_high), (y_low, y_high) = box
    x_range = (x_low - center[0], x_high - center[0])
    return circle_area_below(y_high - center[1], x_range, radius) - circle_area_below(
        y_low - center[1], x_range, radius
    )


def simpson_integral(function, low, high, steps=CHAMFER_INTEGRATION_STEPS):
    width = (high - low) / steps
    weights = [1.0 if index in (0, steps) else (4.0 if index % 2 else 2.0)
               for index in range(steps + 1)]
    return width / 3.0 * sum(
        weight * function(low + index * width) for index, weight in enumerate(weights)
    )


# The cells and their steps.


def cell_key_center(index):
    """Cell index's (from 0) key center in the strip's frame."""
    half_pitch = layout.KEY_PITCH_MM / 2.0
    return (half_pitch + index * layout.KEY_PITCH_MM, half_pitch)


def cell_pocket_fit(kind, index, lip_fit=LIP_POCKET_FIT_MM):
    if kind == LIP:
        return lip_fit
    if kind == HOLES:
        return HOLE_STRIP_POCKET_FIT_MM
    return FIRST_POCKET_FIT_MM + index * POCKET_FIT_STEP_MM


def cell_lip_reach(index):
    """Cell index's lip reach past the walls' inner faces as printed."""
    return FIRST_LIP_REACH_MM + index * LIP_REACH_STEP_MM


def lip_protrusion(reach):
    """A lip's protrusion from its wall's inner face as modelled, for
    its reach past that face as printed."""
    return reach - LIP_TIP_GROWTH_AS_PRINTED_MM


def cell_pad_offset(index):
    return FIRST_PAD_OFFSET_MM + index * PAD_OFFSET_STEP_MM


def pocket_gap(fit):
    """How far a pocket wall's inner face lies outside the socket, as
    modelled."""
    return layout.half_fit_gap(0.0, fit)


# Heights, below the ceiling (positive numbers, the strip's z is their
# negative).


def socket_height():
    return layout.HOTSWAP_SOCKET_BODY_HEIGHT_MM


def lip_retaining_depth():
    """The lips' retaining faces as modelled: the socket's height below
    the ceiling as printed, which rises."""
    return socket_height() + layout.PRINT_RISE_OF_UP_FACING_BOTTOMS_MM


def lip_band_bottom_depth():
    """Where the largest lip's lead-in meets its wall: the lip strip's
    walls' mouth, the bosses' ends and the backing's top."""
    largest = lip_protrusion(cell_lip_reach(CELL_COUNT - 1))
    return lip_retaining_depth() + largest


def wall_depth(kind):
    return lip_band_bottom_depth() if kind == LIP else socket_height()


def boss_height():
    """From the plate's top face to the boss's end."""
    return layout.PCB_THICKNESS_MM + lip_band_bottom_depth()


def longest_insert_length():
    """The longest insert the boss holds: its height less the bore's
    floor and the rise of the bore's bottom, which faces up as printed."""
    return boss_height() - INSERT_BORE_FLOOR_MM - layout.PRINT_RISE_OF_UP_FACING_BOTTOMS_MM


def insert_bore_depth(insert_length):
    return insert_length + layout.PRINT_RISE_OF_UP_FACING_BOTTOMS_MM


def pad_top_depth(index):
    return socket_height() - cell_pad_offset(index)


def pad_height(index):
    """Cell index's pads above the backing's top."""
    return lip_band_bottom_depth() - pad_top_depth(index)


def pad_inset():
    """How far a pad lies inside its socket lobe as modelled: the
    largest lip's reach past the walls' inner faces as printed, how far
    those faces lie inside the lobe as printed at the lip strip's fit,
    the pad's swelling and the clearance, so it passes inside every lip
    as printed."""
    walls_inside_lobe = layout.PRINT_SWELLING_PER_SIDE_MM - pocket_gap(LIP_POCKET_FIT_MM)
    return (
        cell_lip_reach(CELL_COUNT - 1)
        + walls_inside_lobe
        + layout.PRINT_SWELLING_PER_SIDE_MM
        + PAD_CLEARANCE_TO_LIPS_MM
    )


def backing_thickness_limit(socket_bottom_z=None):
    """The thickest backing the battery allows in the real tray: from
    the socket's bottom with the frame in the PCB's place, less the
    lips' band, the backing's own rise as printed (its top rises, so
    its bottom lies that much lower) and the clearance to the battery."""
    if socket_bottom_z is None:
        socket_bottom_z = layout.PCB_UNDERSIDE_Z_MM - socket_height()
    lips = lip_band_bottom_depth() - socket_height()
    return (
        socket_bottom_z
        - lips
        - layout.PRINT_RISE_OF_UP_FACING_BOTTOMS_MM
        - layout.MINIMUM_BATTERY_TO_SOCKET_CLEARANCE_MM
        - layout.BATTERY_TOP_Z_MM
    )


# The socket and its pocket in plan.


def outline_local_points():
    """The outline's points in footprint-local coordinates: its start
    and every line's and arc's points."""
    start, segments = layout.HOTSWAP_SOCKET_OUTLINE_MM
    return [start] + [point for _, *points in segments for point in points]


def board_vector(key_center, local_point):
    return App.Vector(*layout.footprint_point(key_center, local_point), 0.0)


def outline_wire(key_center):
    """The socket's plastic body's outline (layout.HOTSWAP_SOCKET_OUTLINE_MM)
    in board coordinates, a closed wire on z = 0."""
    start, segments = layout.HOTSWAP_SOCKET_OUTLINE_MM
    current = board_vector(key_center, start)
    edges = []
    for kind, *points in segments:
        through = [board_vector(key_center, point) for point in points]
        curve = (Part.LineSegment(current, *through) if kind == "line"
                 else Part.Arc(current, *through))
        edges.append(curve.toShape())
        current = through[-1]
    wire = Part.Wire(edges)
    if not wire.isClosed():
        raise SystemExit("error: the socket's outline does not close")
    return wire


def outline_face(key_center):
    return Part.Face(outline_wire(key_center))


def pocket_face(key_center, distance):
    """The outline moved out by distance, its corners extended to their
    intersections, as a plan face."""
    wire = outline_wire(key_center)
    if distance < LENGTH_TOLERANCE_MM:
        return Part.Face(wire)
    return Part.Face(offset_outline(wire, distance))


def plan_face(polygon):
    return Part.Face(layout_polygon_wire(polygon, 0.0))


def circle_face(center, radius):
    return Part.Face(Part.Wire(Part.makeCircle(radius, App.Vector(center[0], center[1], 0.0))))


def socket_tab_specs():
    """Each end tab as (footprint-local x center, its width, the y of
    the body's end it leaves, the y of its tip)."""
    low, high = layout.HOTSWAP_SOCKET_BODY_ENDS_MM
    specs = []
    for polygon in layout.HOTSWAP_SOCKET_TABS_MM:
        xs = [x for x, _ in polygon]
        ys = [y for _, y in polygon]
        if min(ys) >= high:
            face, tip = high, max(ys)
        elif max(ys) <= low:
            face, tip = low, min(ys)
        else:
            raise SystemExit("error: a socket tab does not leave the body's end")
        specs.append(((min(xs) + max(xs)) / 2.0, max(xs) - min(xs), face, tip))
    return specs


def tab_slot_width(tab_width):
    return layout.printed_fit(tab_width + 2.0 * TAB_SOLDER_PER_SIDE_MM, layout.SLIP_FIT_MM)


def footprint_span_rectangle(key_center, x_center, width, y_from, y_to):
    """A rectangle in board coordinates, footprint-local x center and
    width, between two footprint-local y."""
    return layout.footprint_rectangle(
        key_center, (x_center, (y_from + y_to) / 2.0), width, abs(y_to - y_from)
    )


def tab_slot(key_center, tab):
    """The tab's slot through the walls and recess into the plate in
    plan: from the body's end past the tip."""
    x_center, width, face, tip = tab
    end = tip + math.copysign(TAB_RECESS_PAST_TIP_MM, tip - face)
    return footprint_span_rectangle(key_center, x_center, tab_slot_width(width), face, end)


def tab_wire_room(key_center, tab):
    """Room for the wire soldered to the tab, by layout.py's wire room
    rule: WIRE_ROOM_BEHIND_LEADS_MM past the tip, the tab and
    WIRE_ROOM_BESIDE_LEADS_MM beside it."""
    x_center, width, face, tip = tab
    end = tip + math.copysign(layout.WIRE_ROOM_BEHIND_LEADS_MM, tip - face)
    room_width = width + 2.0 * layout.WIRE_ROOM_BESIDE_LEADS_MM
    return footprint_span_rectangle(key_center, x_center, room_width, tip, end)


def wall_cutters(key_center):
    """The tab slots, cut out of every cell's pocket walls, which do not
    overlap."""
    cutters = [tab_slot(key_center, tab) for tab in socket_tab_specs()]
    for first in range(len(cutters)):
        for second in range(first + 1, len(cutters)):
            if convex_area((cutters[first], cutters[second])) > AREA_TOLERANCE_MM2:
                raise SystemExit("error: two of a pocket's wall cutters overlap")
    return cutters


def wall_ring(key_center, fit):
    """A cell's pocket walls in plan before their cuts: between the
    outline moved out by the pocket's gap (the walls' inner face) and by
    the gap plus WALL_THICKNESS_MM (their outer face)."""
    gap = pocket_gap(fit)
    return pocket_face(key_center, gap + WALL_THICKNESS_MM).cut(pocket_face(key_center, gap))


def cell_wall_cutters(kind, key_center, lip_fit=LIP_POCKET_FIT_MM):
    """Everything cut out of a cell's walls but the footprint holes: the
    tab slots and, on the lip strip, the fingers' slots."""
    return wall_cutters(key_center) + finger_slots(kind, key_center, lip_fit)


def cell_walls_plan(kind, index, lip_fit=LIP_POCKET_FIT_MM):
    """Cell index's walls in plan less their cutters, before the
    footprint holes bore them."""
    key_center = cell_key_center(index)
    cutters = [plan_face(cutter) for cutter in cell_wall_cutters(kind, key_center, lip_fit)]
    ring = wall_ring(key_center, cell_pocket_fit(kind, index, lip_fit))
    return ring.cut(Part.makeCompound(cutters))


def cell_wall_bores(kind, index, pull_in, lip_fit=LIP_POCKET_FIT_MM):
    """{footprint-local center: the area its hole bores out of cell
    index's walls} for every footprint hole that meets their plan. The
    holes do not overlap, so their shares add up."""
    walls = cell_walls_plan(kind, index, lip_fit)
    bores = {}
    for (local_center, _), (center, radius) in zip(layout.CHOC_FOOTPRINT_HOLES_MM,
                                                   cell_holes(kind, index, pull_in)):
        area = walls.common(circle_face(center, radius)).Area
        if area > AREA_TOLERANCE_MM2:
            bores[local_center] = area
    return bores


def wall_area(kind, index, pull_in, lip_fit=LIP_POCKET_FIT_MM):
    """Cell index's walls in plan as built: less their cutters and the
    footprint holes."""
    bores = cell_wall_bores(kind, index, pull_in, lip_fit)
    return cell_walls_plan(kind, index, lip_fit).Area - sum(bores.values())


# The lip strip's fingers.


def finger_faces(key_center, finger, fit):
    """(its inner face's y, its outer face's y, the inward direction
    along y) of a finger on its lip's wall line."""
    inward = finger.toward_socket
    inner = key_center[1] + finger.face_y - inward * pocket_gap(fit)
    return inner, inner - inward * FINGER_THICKNESS_MM, inward


def finger_toward_root(finger):
    return math.copysign(1.0, finger.root_x - finger.free_end_x)


def ordered(first, second):
    return (min(first, second), max(first, second))


def finger_box(key_center, finger, fit):
    """The finger's blade in plan, (x range, y range)."""
    inner, outer, _ = finger_faces(key_center, finger, fit)
    key_x, _ = key_center
    return ordered(key_x + finger.free_end_x, key_x + finger.root_x), ordered(inner, outer)


def finger_root_block_box(key_center, finger, fit):
    """The block the blade's root runs into below the ceiling, in plan."""
    inner, outer, inward = finger_faces(key_center, finger, fit)
    root = key_center[0] + finger.root_x
    far = root + finger_toward_root(finger) * FINGER_ROOT_BLOCK_LENGTH_MM
    side = FINGER_ROOT_BLOCK_SIDE_MM
    return ordered(root, far), ordered(inner + inward * side, outer - inward * side)


def finger_room_modelled():
    return layout.printed_fit(FINGER_ROOM_AS_PRINTED_MM, layout.SNUG_FIT_MM)


def finger_slots_box(key_center, finger, fit):
    """The blade and its slots in plan, (x range, y range): from the
    slots' end to the root, the free slot on the socket's side, the
    room on the other."""
    inner, outer, inward = finger_faces(key_center, finger, fit)
    key_x, _ = key_center
    sides = (inner + inward * FINGER_FREE_SLOT_MM, outer - inward * finger_room_modelled())
    return ordered(key_x + finger.slots_end_x, key_x + finger.root_x), ordered(*sides)


def finger_slots(kind, key_center, lip_fit=LIP_POCKET_FIT_MM):
    """A cell's fingers' slots, blades included, as plan polygons."""
    if kind != LIP:
        return []
    return [rectangle(*finger_slots_box(key_center, finger, lip_fit)) for finger in FINGERS]


def lip_snap_deflection(reach):
    """How far a finger bends for the socket to pass its lip, as the
    tray's snap hook counted it before work item 009 removed it: the lip's
    overlap with the socket as modelled with the walls on it (the snug
    fit) plus the swelling of its 45 degree face, which is the lip's
    reach as printed."""
    overlap = lip_protrusion(reach) - pocket_gap(layout.SNUG_FIT_MM)
    return overlap + layout.PRINT_SWELLING_AT_45_DEGREES_MM


def finger_printed_thickness():
    return FINGER_THICKNESS_MM + 2.0 * layout.PRINT_SWELLING_PER_SIDE_MM


def finger_bending_length(finger):
    """From the root to the lip's near end, where the snap hook's
    formula puts the load."""
    lip_near_end = finger.free_end_x + finger_toward_root(finger) * LIP_LENGTH_MM
    return abs(finger.root_x - lip_near_end)


def finger_strain(finger, reach):
    """The root's bending strain as printed while the lip passes the
    socket's edge."""
    return layout.cantilever_strain(
        lip_snap_deflection(reach), finger_printed_thickness(), finger_bending_length(finger)
    )


def finger_swing(finger, reach):
    """How far the free end swings as printed while the lip's near end
    bends the snap deflection: past the load the finger turns straight,
    by 3/2 the deflection over the bending length per mm, as the removed
    snap hook's blade did."""
    deflection = lip_snap_deflection(reach)
    slope = 1.5 * deflection / finger_bending_length(finger)
    return deflection + slope * LIP_LENGTH_MM


def lip_placements(key_center, fit, reach):
    """Each lip as (start of its retaining face's wall edge, direction
    along the wall, inward normal, protrusion): at its finger's free
    end, toward the root."""
    placements = []
    for finger in FINGERS:
        inner, _, inward = finger_faces(key_center, finger, fit)
        start = (key_center[0] + finger.free_end_x, inner)
        placements.append(
            (start, (finger_toward_root(finger), 0.0), (0.0, inward), lip_protrusion(reach))
        )
    return placements


def lip_volume(reach):
    return lip_protrusion(reach) ** 2 / 2.0 * LIP_LENGTH_MM


def chamfered_slots_box(box, toward_root, height):
    """A finger's slots' outline `height` into its bed chamfer: grown by
    it on both long sides and past the free end, not at the root."""
    (x_low, x_high), (y_low, y_high) = box
    if toward_root > 0.0:
        x_low -= height
    else:
        x_high += height
    return (x_low, x_high), (y_low - height, y_high + height)


def strip_finger_slot_boxes(kind, lip_fit=LIP_POCKET_FIT_MM):
    """Every cell's fingers' slots as (box, the direction toward the
    root along x)."""
    if kind != LIP:
        return []
    return [(finger_slots_box(cell_key_center(index), finger, lip_fit), finger_toward_root(finger))
            for index in range(CELL_COUNT) for finger in FINGERS]


def slots_on_bed(kind, lip_fit=LIP_POCKET_FIT_MM):
    """The fingers' slots' outlines on the bed, their chamfers included."""
    return [rectangle(*chamfered_slots_box(box, toward, FINGER_SLOT_BED_CHAMFER_MM))
            for box, toward in strip_finger_slot_boxes(kind, lip_fit)]


# The strip's plate, bosses and notches in plan.


def boss_centers():
    _, key_row_y = cell_key_center(0)
    return [
        (boundary * layout.KEY_PITCH_MM, key_row_y + offset)
        for boundary in range(CELL_COUNT + 1)
        for offset in (BOSS_NORTH_OF_KEY_ROW_MM, BOSS_SOUTH_OF_KEY_ROW_MM)
    ]


def plate_rectangle():
    """The strip's outline: the cells, reaching BOSS_EDGE_MARGIN_MM past
    the bosses at the ends and the south."""
    reach = BOSS_DIAMETER_MM / 2.0 + BOSS_EDGE_MARGIN_MM
    _, key_row_y = cell_key_center(0)
    return (
        (-reach, CELL_COUNT * layout.KEY_PITCH_MM + reach),
        (key_row_y + BOSS_SOUTH_OF_KEY_ROW_MM - reach, layout.KEY_PITCH_MM),
    )


def plate_area():
    (x_low, x_high), (y_low, y_high) = plate_rectangle()
    return (x_high - x_low) * (y_high - y_low)


def notch_x_centers(index):
    """The x centers of cell index's possible notches, west to east."""
    key_x, _ = cell_key_center(index)
    middle = (CELL_COUNT + 1) / 2.0
    return [key_x + (number - middle) * NOTCH_PITCH_MM for number in range(1, CELL_COUNT + 1)]


def notch_rectangles():
    """Cell k (from 1) gets its first k notches, in the south edge."""
    _, (y_low, _) = plate_rectangle()
    return [
        rectangle((x - NOTCH_WIDTH_MM / 2.0, x + NOTCH_WIDTH_MM / 2.0),
                  (y_low, y_low + NOTCH_DEPTH_MM))
        for index in range(CELL_COUNT)
        for x in notch_x_centers(index)[: index + 1]
    ]


def strip_mark_xs(kind):
    """The x centers of a strip's marks in its north edge."""
    marks = {LIP: (LIP_STRIP_MARK_X_MM,), POCKET: POCKET_STRIP_MARK_XS_MM,
             HOLES: HOLE_STRIP_MARK_XS_MM, BACKING: BACKING_MARK_XS_MM}
    return marks.get(kind, ())


def mark_rectangle(x):
    _, (_, y_high) = plate_rectangle()
    half = LIP_STRIP_MARK_WIDTH_MM / 2.0
    return rectangle(
        (x - half, x + half),
        (y_high - LIP_STRIP_MARK_DEPTH_MM, y_high),
    )


def edge_cut_rectangles(kind):
    """The notches, and the strip's marks."""
    return notch_rectangles() + [mark_rectangle(x) for x in strip_mark_xs(kind)]


# Analytic volumes, from the plan geometry above alone: the walls' areas
# from 2D booleans of their plan faces (wall_area()), the rest from
# plain Python, so the solids' 3D fuses and cuts are checked against
# them.


def strip_finger_slots(kind, lip_fit=LIP_POCKET_FIT_MM):
    return [rectangle(*box) for box, _ in strip_finger_slot_boxes(kind, lip_fit)]


def is_pin_hole(local_center):
    return local_center in layout.CHOC_FOOTPRINT_PIN_HOLE_CENTERS_MM


def cell_pin_hole_diameter(index):
    """The hole strip's cell index's pin holes as modelled."""
    return POCKET_STRIP_PIN_HOLE_DIAMETER_MM - index * HOLE_STRIP_PIN_HOLE_STEP_MM


def hole_radius(kind, index, local_center, diameter, pull_in):
    """Cell index's footprint hole's radius as modelled: grown by
    pull_in, but the pocket strip's pin holes
    POCKET_STRIP_PIN_HOLE_DIAMETER_MM across and the hole strip's
    cell_pin_hole_diameter()."""
    if kind == POCKET and is_pin_hole(local_center):
        return POCKET_STRIP_PIN_HOLE_DIAMETER_MM / 2.0
    if kind == HOLES and is_pin_hole(local_center):
        return cell_pin_hole_diameter(index) / 2.0
    return diameter / 2.0 + pull_in


def cell_holes(kind, index, pull_in):
    """Cell index's footprint holes as (center, radius as modelled), in
    layout.CHOC_FOOTPRINT_HOLES_MM's order."""
    return [(center, hole_radius(kind, index, local_center, diameter, pull_in))
            for (center, diameter), (local_center, _) in zip(
                layout.footprint_holes(cell_key_center(index)), layout.CHOC_FOOTPRINT_HOLES_MM)]


def hole_cutter(center, radius, thickness):
    return pcb_shape.hole_cutter(center, 2.0 * radius, 0.0, thickness)


def strip_holes(kind, pull_in):
    """Every cell's footprint holes as (center, radius) in the plate."""
    return [hole for index in range(CELL_COUNT)
            for hole in cell_holes(kind, index, pull_in)]


def strip_tab_slots():
    return [tab_slot(cell_key_center(index), tab)
            for index in range(CELL_COUNT) for tab in socket_tab_specs()]


def require_apart(first, second, what):
    """No area shared between two lists of convex polygons."""
    for polygon in first:
        if covered_area(second, lambda cutter: convex_area((polygon, cutter))) > AREA_TOLERANCE_MM2:
            raise SystemExit(f"error: {what} overlap")


def require_each_apart(polygons, what):
    for index, polygon in enumerate(polygons):
        require_apart([polygon], polygons[index + 1:], what)


def plate_slots_area(kind, pull_in, lip_fit=LIP_POCKET_FIT_MM):
    """The plate's area the fingers' slots take, less what they share
    with the footprint holes (the center post's)."""
    slots = strip_finger_slots(kind, lip_fit)
    require_apart(slots, strip_tab_slots() + edge_cut_rectangles(kind),
                  "the fingers' slots and the tab recesses or edge cuts")
    on_bed = slots_on_bed(kind, lip_fit)
    require_each_apart(on_bed, "the fingers' slots on the bed")
    require_apart(on_bed, edge_cut_rectangles(kind),
                  "the fingers' slots on the bed and the edge cuts")
    shared = sum(
        covered_area(slots, lambda cutter: circle_box_area(center, radius, polygon_box(cutter)))
        for center, radius in strip_holes(kind, pull_in)
    )
    return covered_area(slots, layout.polygon_signed_area) - shared


def slot_chamfer_volume(box, toward_root, holes):
    """The plate a slots box's bed chamfer removes: the chamfer's
    triangle along each of its three sides and where two meet, less what
    the footprint holes it meets had already taken."""
    size = FINGER_SLOT_BED_CHAMFER_MM
    (x_low, x_high), (y_low, y_high) = box
    along_x, along_y = x_high - x_low, y_high - y_low
    triangles = along_x * size**2 + along_y * size**2 / 2.0 + 2.0 * size**3 / 3.0
    met = [(center, radius) for center, radius in holes
           if circle_box_area(center, radius, chamfered_slots_box(box, toward_root, size)) > 0.0]

    def taken(height):
        grown = chamfered_slots_box(box, toward_root, height)
        return sum(circle_box_area(center, radius, grown) - circle_box_area(center, radius, box)
                   for center, radius in met)

    return triangles - (simpson_integral(taken, 0.0, size) if met else 0.0)


def blade_chamfer_volume(box):
    """What a blade's bed chamfer removes on its two faces and its free
    end."""
    size = FINGER_BLADE_BED_CHAMFER_MM
    (x_low, x_high), (y_low, y_high) = box
    return (x_high - x_low) * size**2 + (y_high - y_low) * size**2 / 2.0 - 2.0 * size**3 / 3.0


def strip_fingers(kind, lip_fit=LIP_POCKET_FIT_MM):
    """Every cell's fingers' blades in plan, (x range, y range)."""
    if kind != LIP:
        return []
    return [finger_box(cell_key_center(index), finger, lip_fit)
            for index in range(CELL_COUNT) for finger in FINGERS]


def strip_root_blocks(kind, lip_fit=LIP_POCKET_FIT_MM):
    """Every cell's fingers' root blocks in plan, (x range, y range)."""
    if kind != LIP:
        return []
    return [finger_root_block_box(cell_key_center(index), finger, lip_fit)
            for index in range(CELL_COUNT) for finger in FINGERS]


def finger_height():
    """From the plate's top face to the walls' mouth."""
    return layout.PCB_THICKNESS_MM + lip_band_bottom_depth()


def box_area(box):
    (x_low, x_high), (y_low, y_high) = box
    return (x_high - x_low) * (y_high - y_low)


def frame_mouth_area(kind, pull_in, lip_fit=LIP_POCKET_FIT_MM):
    """The walls', fingers' and root blocks' ends at the walls' mouth in
    plan."""
    walls = sum(wall_area(kind, index, pull_in, lip_fit) for index in range(CELL_COUNT))
    fingers = strip_fingers(kind, lip_fit) + strip_root_blocks(kind, lip_fit)
    return walls + sum(box_area(box) for box in fingers)


def frame_analytic_volume(kind, pull_in, insert_length, lip_fit=LIP_POCKET_FIT_MM):
    plate = layout.PCB_THICKNESS_MM
    holes = sum(math.pi * radius**2 for _center, radius in strip_holes(kind, pull_in))
    recesses = sum(layout.polygon_signed_area(slot) for slot in strip_tab_slots())
    walls = 0.0
    lips = 0.0
    for index in range(CELL_COUNT):
        walls += wall_area(kind, index, pull_in, lip_fit)
        if kind == LIP:
            lips += len(FINGERS) * lip_volume(cell_lip_reach(index))
    blades = strip_fingers(kind, lip_fit)
    fingers = sum(box_area(box) * finger_height() - blade_chamfer_volume(box) for box in blades)
    blocks = sum(box_area(box) for box in strip_root_blocks(kind, lip_fit)) * (
        lip_band_bottom_depth()
    )
    chamfers = sum(slot_chamfer_volume(box, toward, strip_holes(kind, pull_in))
                   for box, toward in strip_finger_slot_boxes(kind, lip_fit))
    edge_cuts = sum(layout.polygon_signed_area(cut) for cut in edge_cut_rectangles(kind))
    boss_count = len(boss_centers())
    bosses = boss_count * math.pi * (BOSS_DIAMETER_MM / 2.0) ** 2 * lip_band_bottom_depth()
    bores = (
        boss_count * math.pi * (INSERT_BORE_DIAMETER_MM / 2.0) ** 2
        * insert_bore_depth(insert_length)
    )
    return (
        (plate_area() - holes - edge_cuts - plate_slots_area(kind, pull_in, lip_fit)) * plate
        - recesses * TAB_RECESS_DEPTH_MM
        - chamfers
        + walls * wall_depth(kind)
        + fingers
        + blocks
        + lips
        + bosses
        - bores
    )


def pad_polygons(key_center):
    """The pads: each of PAD_LOBE_RECTANGLES_MM moved in by pad_inset().
    The rectangle rather than the cover's chamfered lobe B, whose 0.608
    chamfer edge collapses under an inset past 0.73 and turned the pad
    inside out at 0.85."""
    inset = pad_inset()
    pads = []
    for local_range in PAD_LOBE_RECTANGLES_MM:
        corners = layout.footprint_polygon(key_center, rectangle(*local_range))
        xs = [x for x, _ in corners]
        ys = [y for _, y in corners]
        pads.append(rectangle((min(xs) + inset, max(xs) - inset),
                              (min(ys) + inset, max(ys) - inset)))
    return pads


def backing_analytic_volume():
    hole_area = math.pi * (SCREW_CLEARANCE_HOLE_DIAMETER_MM / 2.0) ** 2
    edge_cuts = sum(layout.polygon_signed_area(cut) for cut in edge_cut_rectangles(BACKING))
    plate = (plate_area() - len(boss_centers()) * hole_area - edge_cuts) * BACKING_THICKNESS_MM
    pads = sum(
        layout.polygon_signed_area(polygon) * pad_height(index)
        for index in range(CELL_COUNT)
        for polygon in pad_polygons(cell_key_center(index))
    )
    return plate + pads


# FreeCAD solids.


def vertical_cutter(polygon, bottom, top):
    """A plan polygon as a prism overshooting bottom and top."""
    return plan_prism(polygon, bottom - CUT_EXTRA_MM, top + CUT_EXTRA_MM)


def slot_bed_chamfer_cutter(box, toward_root):
    """A ruled loft from the slots' outline grown by the chamfer and a
    little more just over the bed (the plate's top face) to the outline
    itself at the chamfer's depth."""
    size = FINGER_SLOT_BED_CHAMFER_MM
    bed = layout.PCB_THICKNESS_MM
    overshoot = 0.05
    grown = chamfered_slots_box(box, toward_root, size + overshoot)
    return Part.makeLoft(
        [rectangle_wire(*grown, bed + overshoot), rectangle_wire(*box, bed - size)], True, True
    )


def build_plate(kind, pull_in, lip_fit=LIP_POCKET_FIT_MM):
    """The plate with every cell's footprint holes, the tabs' recesses,
    the edge cuts and the fingers' slots with their bed chamfers."""
    (x_low, x_high), (y_low, y_high) = plate_rectangle()
    thickness = layout.PCB_THICKNESS_MM
    plate = Part.makeBox(x_high - x_low, y_high - y_low, thickness, App.Vector(x_low, y_low, 0))
    cutters = []
    for index in range(CELL_COUNT):
        key_center = cell_key_center(index)
        cutters.extend(
            hole_cutter(center, radius, thickness)
            for center, radius in cell_holes(kind, index, pull_in)
        )
        cutters.extend(
            plan_prism(tab_slot(key_center, tab), -CUT_EXTRA_MM, TAB_RECESS_DEPTH_MM)
            for tab in socket_tab_specs()
        )
    cutters.extend(vertical_cutter(cut, 0.0, thickness) for cut in edge_cut_rectangles(kind))
    for box, toward in strip_finger_slot_boxes(kind, lip_fit):
        cutters.append(vertical_cutter(rectangle(*box), 0.0, thickness))
        cutters.append(slot_bed_chamfer_cutter(box, toward))
    plate = plate.cut(Part.makeCompound(cutters))
    require_one_valid_solid(plate, "cutting the plate")
    return plate.Solids[0]


def face_prism(face, depth):
    """A plan face extruded from the ceiling down to depth."""
    prism = face.extrude(UP * depth)
    prism.translate(UP * -depth)
    return prism


def build_cell_walls(kind, key_center, fit, depth, lip_fit=LIP_POCKET_FIT_MM):
    """A cell's pocket walls below the ceiling, in pieces: the prism of
    the walls' outer face less that of their inner face, then their
    cutters."""
    gap = pocket_gap(fit)
    outer, inner = (face_prism(pocket_face(key_center, distance), depth)
                    for distance in (gap + WALL_THICKNESS_MM, gap))
    ring = outer.cut(inner)
    cutters = [vertical_cutter(cutter, -depth, 0.0)
               for cutter in cell_wall_cutters(kind, key_center, lip_fit)]
    return ring.cut(Part.makeCompound(cutters)).removeSplitter()


def build_blade(box, toward_root):
    """A finger's blade from the walls' mouth to the plate's top face,
    its bed edges chamfered on its two faces and its free end."""
    size = FINGER_BLADE_BED_CHAMFER_MM
    bed = layout.PCB_THICKNESS_MM
    body = plan_prism(rectangle(*box), -lip_band_bottom_depth(), bed - size)
    shrunk = chamfered_slots_box(box, toward_root, -size)
    top = Part.makeLoft(
        [rectangle_wire(*box, bed - size), rectangle_wire(*shrunk, bed)], True, True
    )
    return body.fuse(top).removeSplitter()


def build_fingers(kind, lip_fit=LIP_POCKET_FIT_MM):
    """(the fingers' blades, their root blocks from the walls' mouth to
    the ceiling)."""
    towards = [finger_toward_root(finger) for _ in range(CELL_COUNT) for finger in FINGERS]
    blades = [build_blade(box, toward)
              for box, toward in zip(strip_fingers(kind, lip_fit), towards)]
    blocks = [plan_prism(rectangle(*box), -lip_band_bottom_depth(), 0.0)
              for box in strip_root_blocks(kind, lip_fit)]
    return blades, blocks


def build_lip(placement, retaining_depth):
    """A lip: its retaining face on top at the retaining depth, its 45
    degree lead-in below, its back on the wall's inner face."""
    (start_x, start_y), along, inward, protrusion = placement
    top = -retaining_depth
    corner = App.Vector(start_x, start_y, top)
    tip = corner + App.Vector(inward[0], inward[1], 0.0) * protrusion
    foot = corner + App.Vector(0.0, 0.0, -protrusion)
    triangle = Part.Face(Part.makePolygon([corner, tip, foot, corner]))
    return triangle.extrude(App.Vector(along[0], along[1], 0.0) * LIP_LENGTH_MM)


def build_bosses(depth):
    radius = BOSS_DIAMETER_MM / 2.0
    return [
        Part.makeCylinder(radius, depth, App.Vector(x, y, -depth), UP) for x, y in boss_centers()
    ]


def build_bores(depth, insert_length):
    radius = INSERT_BORE_DIAMETER_MM / 2.0
    bore = insert_bore_depth(insert_length)
    return [
        Part.makeCylinder(
            radius, bore + CUT_EXTRA_MM, App.Vector(x, y, -depth - CUT_EXTRA_MM), UP
        )
        for x, y in boss_centers()
    ]


def frame_bodies(kind, lip_fit=LIP_POCKET_FIT_MM):
    """(walls of every cell, fingers' blades, their root blocks, lips of
    every cell, bosses) before fusing and before the footprint holes run
    on through the walls, for the build and for clearance probes."""
    depth = wall_depth(kind)
    walls = []
    lips = []
    for index in range(CELL_COUNT):
        key_center = cell_key_center(index)
        fit = cell_pocket_fit(kind, index, lip_fit)
        walls.append(build_cell_walls(kind, key_center, fit, depth, lip_fit))
        if kind == LIP:
            lips.extend(
                build_lip(placement, lip_retaining_depth())
                for placement in lip_placements(key_center, fit, cell_lip_reach(index))
            )
    blades, blocks = build_fingers(kind, lip_fit)
    return walls, blades, blocks, lips, build_bosses(lip_band_bottom_depth())


def footprint_hole_bores(kind, pull_in):
    """Every cell's footprint holes from the plate's top face down to the
    walls' mouth, overshooting both."""
    depth = wall_depth(kind)
    bores = []
    for center, radius in strip_holes(kind, pull_in):
        bore = hole_cutter(center, radius, layout.PCB_THICKNESS_MM + depth)
        bore.translate(App.Vector(0.0, 0.0, -depth))
        bores.append(bore)
    return bores


def walls_bored_volume(kind, pull_in, lip_fit=LIP_POCKET_FIT_MM):
    """What the footprint holes bore out of every cell's walls."""
    return wall_depth(kind) * sum(
        sum(cell_wall_bores(kind, index, pull_in, lip_fit).values())
        for index in range(CELL_COUNT)
    )


def bore_footprint_holes(frame, kind, pull_in, lip_fit=LIP_POCKET_FIT_MM):
    """The frame with its footprint holes run on through the walls, the
    plate's already cut, checked to take the walls' share from their
    plan (cell_wall_bores()) within VOLUME_RELATIVE_TOLERANCE of it (1e-5
    to 1.5e-5 mm3 at the defaults), so the holes take no boss, finger,
    block or lip (the smallest lip is 0.002 mm3) nor more than a graze of
    one; the export checks the switch's post and pegs clear of the
    frame."""
    bored = frame.cut(Part.makeCompound(footprint_hole_bores(kind, pull_in)))
    require_one_valid_solid(bored, "boring the footprint holes through the walls")
    removed = frame.Volume - bored.Volume
    expected = walls_bored_volume(kind, pull_in, lip_fit)
    if abs(removed - expected) > VOLUME_RELATIVE_TOLERANCE * expected:
        raise SystemExit(
            f"error: the footprint holes take {removed:.6f} mm3 below the plate, the walls' "
            f"share is {expected:.6f} mm3"
        )
    return bored


def build_frame(kind, pull_in, insert_length, lip_fit=LIP_POCKET_FIT_MM):
    """(frame strip, its analytic volume), checked to be one valid solid
    of that volume."""
    if not 0.0 < insert_length <= longest_insert_length() + 1e-9:
        raise SystemExit(
            f"error: an insert {insert_length} long does not fit the boss, which holds up to "
            f"{longest_insert_length():.3f}"
        )
    plate = build_plate(kind, pull_in, lip_fit)
    walls, blades, blocks, lips, bosses = frame_bodies(kind, lip_fit)
    frame = plate.fuse(walls + blades + blocks + lips + bosses).removeSplitter()
    require_one_valid_solid(frame, "fusing the walls, fingers, lips and bosses to the plate")
    frame = bore_footprint_holes(frame, kind, pull_in, lip_fit)
    frame = frame.cut(Part.makeCompound(build_bores(lip_band_bottom_depth(), insert_length)))
    require_one_valid_solid(frame, "boring the bosses")
    expected = frame_analytic_volume(kind, pull_in, insert_length, lip_fit)
    if abs(frame.Volume - expected) > VOLUME_RELATIVE_TOLERANCE * expected:
        raise SystemExit(
            f"error: the {kind} strip's volume is {frame.Volume:.4f} mm3, analytic "
            f"{expected:.4f} mm3"
        )
    return frame.Solids[0], expected


def build_backing():
    """(backing strip with its bottom on z = 0, its analytic volume)."""
    (x_low, x_high), (y_low, y_high) = plate_rectangle()
    thickness = BACKING_THICKNESS_MM
    plate = Part.makeBox(x_high - x_low, y_high - y_low, thickness, App.Vector(x_low, y_low, 0))
    radius = SCREW_CLEARANCE_HOLE_DIAMETER_MM / 2.0
    cutters = [
        Part.makeCylinder(radius, thickness + 2.0 * CUT_EXTRA_MM,
                          App.Vector(x, y, -CUT_EXTRA_MM), UP)
        for x, y in boss_centers()
    ]
    cutters.extend(vertical_cutter(cut, 0.0, thickness) for cut in edge_cut_rectangles(BACKING))
    plate = plate.cut(Part.makeCompound(cutters))
    pads = [
        plan_prism(polygon, thickness, thickness + pad_height(index))
        for index in range(CELL_COUNT)
        for polygon in pad_polygons(cell_key_center(index))
    ]
    backing = plate.fuse(pads).removeSplitter()
    require_one_valid_solid(backing, "fusing the pads to the backing")
    expected = backing_analytic_volume()
    if abs(backing.Volume - expected) > VOLUME_RELATIVE_TOLERANCE * expected:
        raise SystemExit(
            f"error: the backing's volume is {backing.Volume:.4f} mm3, analytic "
            f"{expected:.4f} mm3"
        )
    return backing.Solids[0], expected


def stacked_backing(backing):
    """The backing under a frame strip, its top on the bosses' ends."""
    moved = backing.copy()
    moved.translate(App.Vector(0.0, 0.0, -lip_band_bottom_depth() - BACKING_THICKNESS_MM))
    return moved


def turned_for_printing(frame):
    """A frame strip upside down, its plate's top face on z = 0, placed
    by the plate's own faces: the lip strip's BoundBox reaches 0.05 past
    its plate's top face, which lifted the strip off the bed."""
    turned = frame.copy()
    turned.rotate(App.Vector(0, 0, 0), App.Vector(1, 0, 0), 180.0)
    _, (_, y_high) = plate_rectangle()
    turned.translate(App.Vector(0.0, y_high, layout.PCB_THICKNESS_MM))
    return turned
