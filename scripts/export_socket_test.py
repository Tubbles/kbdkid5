"""Export one of the socket retention test strips (STL), work item 008:
a frame printed in place of the PCB, holding Kailh Choc hotswap sockets
in pockets on its underside, to try a keyboard wired by hand.

The word chooses the strip (socket_test_shape.py builds them and its
docstring has the design):

  pocket   the pocket's fit steps across the cells, -0.40 to -0.15 in
           0.05 steps, the two pin holes 3.5 across as modelled so the
           pocket alone locates the socket; any pocket can be glued
  lip      every pocket snug (or at lip_fit), with lips at its mouth on
           fingers that the socket bends aside as it snaps past, their
           reach past the walls' inner faces as printed 0.15 to 0.35 in
           0.04 steps
  backing  a plate screwed under either frame strip with M2 screws into
           heat-set inserts in the frame's bosses, a pad under each
           socket lobe whose top relative to the socket's bottom steps
           from -0.10 (a gap) to +0.15 (pressing) in 0.05 steps
  holes    every pocket loose (+0.15), the two pin holes stepping 3.5 to
           3.0 across as modelled in 0.1 steps, so only they hold the
           socket

Cell k (from 1, west to east) has k notches in its south edge on every
strip; the lip strip also has a notch in the middle of its north edge,
the pocket strip four, between cells 1 and 2, 2 and 3, 4 and 5, and 5
and 6, the hole strip three, between cells 1 and 2, 3 and 4, and 5 and
6. The frame strips print upside down, the plate's top face on z = 0;
the backing prints bottom down.

Runs headless under FreeCAD's console interpreter (see
freecad_common.py for the freecadcmd quirks that shape the
invocation):

    freecadcmd scripts/export_socket_test.py --pass <strip.stl> pocket|lip|backing|holes
        [pull_in=0.2] [insert_length=<mm>] [lip_fit=<mm>]

lip_fit sets the lip strip's pocket fit (snug, 0, by default), for the
fit the pocket strip shows best; the walls, fingers and lips move
together, so the lips keep their reach past the walls' inner faces and
the fingers their strain. The figures that follow from it are then
printed rather than checked against DESIGN.md.

A frame strip is checked for one valid solid of its analytic volume,
each pocket centered on its key's socket at its fit as printed, the
walls' depth, each lip's reach as printed, length and place, each
finger's bending length and thickness from its faces, its strain as
printed (failing above 2 %), its slots open and its room against its
swing, its root plastic over the finger's whole height, the slots' and
blades' bed chamfers, the tab slots' width, the pin holes' size, the
footprint holes through the walls (the switch's post and pegs clear of
the frame, lobe B's north wall open on the west peg's hole and whole
beside it, the sliver of the wall the hole leaves), every bore on its
boss at the insert's depth, the bosses', walls', fingers', blocks' and
slots' clearances, the notches and the marks, and a closed mesh. The
backing is checked for one valid solid of its analytic volume, each
pad's height against the socket's bottom, the screw holes, and stacked
under both frame strips: nothing overlapping, the backing touching only
the bosses' ends (and the lip strip's walls', fingers' and blocks'
ends), the pads inside the lips as printed, every bore over its screw
hole, the tabs' wire rooms clear, and the battery clearance in the real
tray.
Every strip's mesh must have its lowest point on z = 0, the bed.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import FreeCAD as App
import Part

import layout
import pcb_shape
import socket_test_shape as shape
from freecad_common import check_closed_mesh, export_stl, run_and_exit, script_arguments
from tray_shape import UP, plan_prism

# DESIGN.md's figures ("Hand-wired frame test"), transcribed
# independently of the constants the strips are built from, each
# compared within half its last digit.
DESIGN_POCKET_FITS_MM = (-0.40, -0.35, -0.30, -0.25, -0.20, -0.15)
DESIGN_POCKET_PRINTED_X_MM = (9.15, 9.20, 9.25, 9.30, 9.35, 9.40)
DESIGN_POCKET_PRINTED_Y_MM = (6.45, 6.50, 6.55, 6.60, 6.65, 6.70)
DESIGN_POCKET_PIN_HOLE_DIAMETER_MM = 3.50
DESIGN_HOLE_STRIP_HOLES_MM = (3.50, 3.40, 3.30, 3.20, 3.10, 3.00)
DESIGN_HOLE_STRIP_POCKET_FIT_MM = 0.15
DESIGN_HOLE_STRIP_POCKET_PRINTED_MM = (9.70, 7.00)
DESIGN_LIP_POCKET_PRINTED_MM = (9.55, 6.85)
DESIGN_LIP_REACHES_MM = (0.15, 0.19, 0.23, 0.27, 0.31, 0.35)
DESIGN_LIP_LENGTH_MM = 1.00
DESIGN_PAD_OFFSETS_MM = (-0.10, -0.05, 0.00, 0.05, 0.10, 0.15)
DESIGN_WALL_DEPTHS_MM = {shape.POCKET: 1.80, shape.LIP: 2.27, shape.HOLES: 1.80}
DESIGN_LIP_RETAINING_DEPTH_MM = 2.00
DESIGN_TAB_SLOT_WIDTH_MM = 3.18
DESIGN_BOSS_HEIGHT_MM = 3.87
DESIGN_LONGEST_INSERT_MM = 3.067
DESIGN_BACKING_THICKNESS_MM = 0.80
DESIGN_BATTERY_CLEARANCE_AS_PRINTED_MM = 0.62
DESIGN_FINGER_BENDING_LENGTHS_MM = (5.64, 6.64, 6.34)  # in shape.FINGERS' order
DESIGN_FINGER_PRINTED_THICKNESS_MM = 1.20
DESIGN_FINGER_ROOM_PRINTED_MM = 0.70
DESIGN_FINGER_ROOT_BLOCK_MM = (1.00, 0.40)  # past the root, out from the blade's faces
DESIGN_FINGER_BED_CHAMFERS_MM = {"slots": 0.40, "blade": 0.20}
DESIGN_LIP_STRAIN_PERCENT = (0.85, 1.08, 1.30, 1.53, 1.75, 1.98)  # the largest of a cell's
DESIGN_LIP_MAXIMUM_STRAIN_PERCENT = 2.0
DESIGN_STRIP_MARK_XS_MM = {shape.POCKET: (19.05, 38.10, 76.20, 95.25), shape.LIP: (57.15,),
                           shape.HOLES: (19.05, 57.15, 95.25)}
DESIGN_FIGURE_DECIMALS = 2

# Clearances the checks ask for, as modelled: the bosses from the walls,
# the tabs' wire rooms, the switch's protruding parts and the footprint
# holes, the fingers and their root blocks from the tab slots, the
# switch's protruding parts and the footprint holes, the fingers from
# the wire rooms, the blocks from the bosses and the other fingers'
# slots, the fingers' slots from the bosses and the lips from the tab
# slots. The tabs' recesses in the ceiling start at the body's ends,
# where the tabs, 0.05 taller than the body's bumps, leave it, which
# brings the south tab's within 0.5 of its pin hole: they keep
# RECESS_HOLE_CLEARANCE_MM, more as printed, where the hole and the
# recess each print 0.2 smaller. The walls, blocks and bosses beside the
# wire rooms must stay out of them as printed.
FEATURE_CLEARANCE_MM = 0.5
RECESS_HOLE_CLEARANCE_MM = 0.3
WIRE_ROOM_PRINTED_CLEARANCE_MM = layout.PRINT_SWELLING_PER_SIDE_MM

# How many heights the root's probe takes over the finger's height.
ROOT_PROBE_HEIGHTS = 12

# How the switch's center post and side pegs reach below the plate
# (DESIGN.md, "Fused mock").
SWITCH_PARTS_BELOW_PLATE_MM = 1.4

# Lobe B's north wall, which the west peg's hole bores through, is
# probed solid at these footprint-local y at its mid depth: beside the
# hole, where the wall was cut back before the holes ran through it
# (4.0, 7.0), and farther along (3.0, 7.3).
WALL_PROBE_LOCAL_YS_MM = (3.0, 4.0, 7.0, 7.3)

# The stack's contact check sinks the frame this far into the backing.
CONTACT_PROBE_DEPTH_MM = 0.01
CONTACT_VOLUME_RELATIVE_TOLERANCE = 1e-4
MEASURE_TOLERANCE_MM = 1e-6
# A thickness measured between two edges, each found by bisection
# within isInside()'s tolerance.
THICKNESS_TOLERANCE_MM = 3.0 * MEASURE_TOLERANCE_MM
WINDOW_MM = 0.5

USAGE = f"""\
usage: freecadcmd scripts/export_socket_test.py --pass <strip.stl> pocket|lip|backing|holes
           [pull_in={pcb_shape.DEFAULT_PULL_IN_MM}] [insert_length=<mm>] [lip_fit=<mm>]

  pocket         the pocket strip, its pocket's fit stepping across the cells
  lip            the lip strip, its lips' reach stepping across the cells
  backing        the backing strip, its pads' height stepping across the cells
  holes          the hole strip, its pin holes stepping across the cells
  pull_in        swelling allowance per side, mm: the footprint holes grow by it
                 (all but the pocket strip's pin holes, 3.5 as modelled)
  insert_length  the heat-set inserts' length, mm, which sets the bores' depth:
                 at most (and by default) the longest the bosses hold,
                 {shape.longest_insert_length():.3f}
  lip_fit        the lip strip's pocket fit, mm, as the pocket strip's cells
                 step it (default {shape.LIP_POCKET_FIT_MM:.2f}, snug); the backing
                 is stacked under the lip strip at it\
"""


class Arguments:
    def __init__(self):
        self.stl_file = None
        self.kind = None
        self.pull_in = pcb_shape.DEFAULT_PULL_IN_MM
        self.insert_length = shape.longest_insert_length()
        self.lip_fit = shape.LIP_POCKET_FIT_MM


def parse_number(key, value):
    try:
        return float(value)
    except ValueError:
        raise SystemExit(f"error: '{key}' needs a number, got '{value}'")


def parse_arguments(argument_list):
    arguments = Arguments()
    positionals = []
    for argument in argument_list:
        if "=" in argument:
            key, _, value = argument.partition("=")
            if key not in ("pull_in", "insert_length", "lip_fit"):
                raise SystemExit(f"error: unknown option '{key}'\n{USAGE}")
            setattr(arguments, key, parse_number(key, value))
        elif argument in shape.STRIP_KINDS:
            if arguments.kind is not None:
                raise SystemExit(f"error: choose one strip\n{USAGE}")
            arguments.kind = argument
        else:
            positionals.append(argument)
    if len(positionals) != 1 or arguments.kind is None:
        raise SystemExit(USAGE)
    arguments.stl_file = positionals[0]
    return arguments


def design_tolerance():
    return 0.5 * 10.0**-DESIGN_FIGURE_DECIMALS + MEASURE_TOLERANCE_MM


def require_design(what, measured, design):
    if abs(measured - design) > design_tolerance():
        raise SystemExit(f"error: {what} is {measured:.4f}, DESIGN.md says {design:.2f}")


# Faces.


def planar_faces_along(solid, axis_index):
    """The solid's planar faces whose normal lies along an axis (0 x, 1
    y, 2 z)."""
    faces = []
    for face in solid.Faces:
        if isinstance(face.Surface, Part.Plane):
            normal = face.Surface.Axis
            if abs((normal.x, normal.y, normal.z)[axis_index]) > 0.999:
                faces.append(face)
    return faces


def face_coordinate(face, axis_index):
    center = face.CenterOfMass
    return (center.x, center.y, center.z)[axis_index]


def upward(face):
    u_low, u_high, v_low, v_high = face.ParameterRange
    return face.normalAt((u_low + u_high) / 2.0, (v_low + v_high) / 2.0).z > 0.0


def socket_extents(key_center):
    """(x range, y range) of the socket's plastic body's lobes."""
    points = [point for lobe in shape.body_lobes(key_center) for point in lobe]
    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    return (min(xs), max(xs)), (min(ys), max(ys))


def wall_face_plane(frame_faces, key_center, axis_index, socket_face, outward):
    """The plane of the pocket walls' inner faces nearest outside or on
    a socket face (a pocket at the -0.40 fit is modelled on the body),
    from the faces below the ceiling within the cell (past the body's
    west end a fill's walls lie farther out)."""
    planes = set()
    for face in frame_faces[axis_index]:
        center = face.CenterOfMass
        if center.z >= 0.0 or abs(center.x - key_center[0]) > layout.KEY_PITCH_MM / 2.0:
            continue
        offset = (face_coordinate(face, axis_index) - socket_face) * outward
        if -MEASURE_TOLERANCE_MM <= offset <= WINDOW_MM:
            planes.add(round(face_coordinate(face, axis_index), 6))
    if not planes:
        raise SystemExit(f"error: found no wall plane outside the socket face at "
                         f"{socket_face:.3f} near {key_center}")
    return min(planes, key=lambda plane: (plane - socket_face) * outward)


def measured_pocket(frame_faces, key_center):
    """(center offset from the socket's, x size, y size) of a cell's
    pocket as modelled."""
    (x_low, x_high), (y_low, y_high) = socket_extents(key_center)
    west = wall_face_plane(frame_faces, key_center, 0, x_low, -1.0)
    east = wall_face_plane(frame_faces, key_center, 0, x_high, 1.0)
    south = wall_face_plane(frame_faces, key_center, 1, y_low, -1.0)
    north = wall_face_plane(frame_faces, key_center, 1, y_high, 1.0)
    offset = math.dist(((west + east) / 2.0, (south + north) / 2.0),
                       ((x_low + x_high) / 2.0, (y_low + y_high) / 2.0))
    return offset, east - west, north - south


def design_pocket_size(kind, index, lip_fit):
    """DESIGN.md's pocket as printed, or None where it follows from a
    lip_fit override."""
    if kind == shape.LIP:
        return DESIGN_LIP_POCKET_PRINTED_MM if lip_fit == shape.LIP_POCKET_FIT_MM else None
    if kind == shape.HOLES:
        return DESIGN_HOLE_STRIP_POCKET_PRINTED_MM
    return DESIGN_POCKET_PRINTED_X_MM[index], DESIGN_POCKET_PRINTED_Y_MM[index]


def check_pockets(kind, frame, frame_faces, lip_fit):
    swelling = 2.0 * layout.PRINT_SWELLING_PER_SIDE_MM
    for index in range(shape.CELL_COUNT):
        key_center = shape.cell_key_center(index)
        offset, x_size, y_size = measured_pocket(frame_faces, key_center)
        if offset > MEASURE_TOLERANCE_MM:
            raise SystemExit(f"error: cell {index + 1}'s pocket lies {offset:.6f} off its socket")
        fit = shape.cell_pocket_fit(kind, index, lip_fit)
        expected = layout.printed_fit(0.0, fit)
        (x_low, x_high), (y_low, y_high) = socket_extents(key_center)
        for what, size, body in (("x", x_size, x_high - x_low), ("y", y_size, y_high - y_low)):
            if abs(size - body - expected) > MEASURE_TOLERANCE_MM:
                raise SystemExit(f"error: cell {index + 1}'s pocket along {what} is {size:.4f} "
                                 f"around the body's {body:.4f} at the fit {fit:+.2f}")
        design = design_pocket_size(kind, index, lip_fit)
        if design is not None:
            require_design(f"cell {index + 1}'s pocket along x as printed", x_size - swelling,
                           design[0])
            require_design(f"cell {index + 1}'s pocket along y as printed", y_size - swelling,
                           design[1])
        if kind == shape.POCKET:
            require_design(f"cell {index + 1}'s fit", fit, DESIGN_POCKET_FITS_MM[index])
        if kind == shape.HOLES:
            require_design(f"cell {index + 1}'s fit", fit, DESIGN_HOLE_STRIP_POCKET_FIT_MM)
        print(f"cell {index + 1}:     pocket fit {fit:+.2f}, {x_size:.3f} x {y_size:.3f} modelled, "
              f"{x_size - swelling:.3f} x {y_size - swelling:.3f} printed, centered within "
              f"{offset:.1e}")


def check_wall_depth(kind, frame):
    mouths = [face for face in planar_faces_along(frame, 2)
              if not upward(face) and face_coordinate(face, 2) < -MEASURE_TOLERANCE_MM]
    depths = sorted({round(-face_coordinate(face, 2), 6) for face in mouths})
    walls = shape.wall_depth(kind)
    expected = sorted({walls, shape.lip_band_bottom_depth()})
    if len(depths) != len(expected) or any(
            abs(found - wanted) > MEASURE_TOLERANCE_MM for found, wanted in zip(depths, expected)):
        raise SystemExit(f"error: the walls' and bosses' mouths lie at {depths} below the "
                         f"ceiling, expected {expected}")
    require_design("the walls' depth", walls, DESIGN_WALL_DEPTHS_MM[kind])
    print(f"walls:      {shape.WALL_THICKNESS_MM} thick, {walls:.3f} deep below the ceiling "
          f"(the socket's body {shape.socket_height()}), mouths at {sorted(depths)}")


def lip_faces_by_cell(frame):
    """Each cell's lips' retaining faces, which face the socket."""
    depth = shape.lip_retaining_depth()
    faces = [face for face in planar_faces_along(frame, 2)
             if upward(face) and abs(face_coordinate(face, 2) + depth) < MEASURE_TOLERANCE_MM]
    cells = [[] for _ in range(shape.CELL_COUNT)]
    for face in faces:
        index = int(face.CenterOfMass.x // layout.KEY_PITCH_MM)
        cells[index].append(face)
    return cells


def lip_wall_middle(placement):
    start, along, _, _ = placement
    return (start[0] + along[0] * shape.LIP_LENGTH_MM / 2.0,
            start[1] + along[1] * shape.LIP_LENGTH_MM / 2.0)


def lip_face_at(index, placement, faces):
    """The one retaining face of a cell's lips at its placement."""
    wall_middle = lip_wall_middle(placement)
    near = [face for face in faces
            if math.dist((face.CenterOfMass.x, face.CenterOfMass.y), wall_middle) < 1.0]
    if len(near) != 1:
        raise SystemExit(f"error: cell {index + 1} has {len(near)} lips at {wall_middle}")
    return near[0]


def measured_lip_reach(index, placement, faces):
    """The reach as printed of the lip whose retaining face lies at its
    placement on the wall's inner face, LIP_LENGTH_MM long."""
    _, _, inward, _ = placement
    wall_middle = lip_wall_middle(placement)
    face = lip_face_at(index, placement, faces)
    protrusion = face.Area / shape.LIP_LENGTH_MM
    middle = (wall_middle[0] + inward[0] * protrusion / 2.0,
              wall_middle[1] + inward[1] * protrusion / 2.0)
    box = face.BoundBox
    if (math.dist((face.CenterOfMass.x, face.CenterOfMass.y), middle) > MEASURE_TOLERANCE_MM
            or abs(max(box.XLength, box.YLength) - shape.LIP_LENGTH_MM) > MEASURE_TOLERANCE_MM):
        raise SystemExit(f"error: a lip of cell {index + 1} is not where it belongs")
    return protrusion + shape.LIP_TIP_GROWTH_AS_PRINTED_MM


def check_lips(frame, lip_fit):
    require_design("the lips' retaining faces' depth", shape.lip_retaining_depth(),
                   DESIGN_LIP_RETAINING_DEPTH_MM)
    require_design("the lips' length", shape.LIP_LENGTH_MM, DESIGN_LIP_LENGTH_MM)
    for index, faces in enumerate(lip_faces_by_cell(frame)):
        key_center = shape.cell_key_center(index)
        placements = shape.lip_placements(key_center, lip_fit, shape.cell_lip_reach(index))
        if len(faces) != len(placements):
            raise SystemExit(f"error: cell {index + 1} has {len(faces)} lips, expected "
                             f"{len(placements)}")
        reaches = [measured_lip_reach(index, placement, faces) for placement in placements]
        for reach in reaches:
            require_design(f"cell {index + 1}'s lip reach as printed", reach,
                           DESIGN_LIP_REACHES_MM[index])
        print(f"cell {index + 1}:     {len(reaches)} lips {shape.LIP_LENGTH_MM} long, "
              f"{reaches[0] - shape.LIP_TIP_GROWTH_AS_PRINTED_MM:.3f} modelled, reach "
              f"{reaches[0]:.3f} past the walls' inner faces as printed, overhang "
              f"{reaches[0]:.3f} printed")


def finger_face(frame_faces, key_center, finger, face_y, lip_fit):
    """The one face on a plane along a finger, within its blade's ends,
    from the walls' mouth to its bed chamfer."""
    (x_low, x_high), _ = shape.finger_box(key_center, finger, lip_fit)
    found = [face for face in frame_faces[1]
             if abs(face_coordinate(face, 1) - face_y) < MEASURE_TOLERANCE_MM
             and face.BoundBox.XMin > x_low - WINDOW_MM and face.BoundBox.XMax < x_high + WINDOW_MM]
    if len(found) != 1:
        raise SystemExit(f"error: found {len(found)} finger faces at y {face_y:.3f}, expected one")
    box = found[0].BoundBox
    top = layout.PCB_THICKNESS_MM - shape.FINGER_BLADE_BED_CHAMFER_MM
    if (abs(box.ZMin + shape.lip_band_bottom_depth()) > MEASURE_TOLERANCE_MM
            or abs(box.ZMax - top) > MEASURE_TOLERANCE_MM):
        raise SystemExit(f"error: the finger face at y {face_y:.3f} does not run from the walls' "
                         "mouth to its bed chamfer")
    return found[0]


def measured_finger(frame_faces, key_center, finger, lip_face, lip_fit):
    """(bending length, thickness as modelled) of a finger from its
    faces: from its outer face's end at the root to its lip's near end,
    and between its outer and inner faces."""
    inner, outer, _ = shape.finger_faces(key_center, finger, lip_fit)
    outer_box = finger_face(frame_faces, key_center, finger, outer, lip_fit).BoundBox
    inner_face = finger_face(frame_faces, key_center, finger, inner, lip_fit)
    if shape.finger_toward_root(finger) > 0.0:
        length = outer_box.XMax - lip_face.BoundBox.XMax
    else:
        length = lip_face.BoundBox.XMin - outer_box.XMin
    return length, abs(face_coordinate(inner_face, 1) - outer_box.YMin)


def finger_probe_points(key_center, finger, lip_fit):
    """(points that must be open, points that must be solid) around a
    finger: its slots at the free end and near the root, through the
    plate and below it, the plate just past the room, and the finger at
    both ends."""
    inner, outer, inward = shape.finger_faces(key_center, finger, lip_fit)
    toward = shape.finger_toward_root(finger)
    free = key_center[0] + finger.free_end_x
    root = key_center[0] + finger.root_x
    near_root = root - toward * WINDOW_MM
    room = shape.finger_room_modelled()
    middle = (inner + outer) / 2.0
    slot_end = (key_center[0] + finger.slots_end_x + free) / 2.0
    plate_z = layout.PCB_THICKNESS_MM / 2.0
    wall_z = -shape.lip_band_bottom_depth() / 2.0
    open_points = [
        App.Vector(x, y, z)
        for x, y in ((free, inner + inward * shape.FINGER_FREE_SLOT_MM / 2.0),
                     (near_root, inner + inward * shape.FINGER_FREE_SLOT_MM / 2.0),
                     (free, outer - inward * room / 2.0),
                     (near_root, outer - inward * (room - 0.01)),
                     (slot_end, middle))
        for z in (plate_z, wall_z)
    ]
    solid_points = [
        App.Vector(near_root, outer - inward * (room + 0.01), plate_z),
        App.Vector(root + toward * 0.01, middle, plate_z),
        App.Vector(root - toward * 0.01, middle, wall_z),
        App.Vector(free + toward * 0.01, middle, wall_z),
    ]
    return open_points, solid_points


def check_finger_root(frame, index, key_center, finger, lip_fit):
    """Just past the root, plastic over the finger's whole height and
    across its whole thickness (the plate above the ceiling, the block
    below), and the block where it belongs: solid to its far end and its
    sides, open just past them under the ceiling."""
    inner, outer, inward = shape.finger_faces(key_center, finger, lip_fit)
    toward = shape.finger_toward_root(finger)
    root = key_center[0] + finger.root_x
    bottom = -shape.lip_band_bottom_depth()
    top = layout.PCB_THICKNESS_MM
    heights = [bottom + 0.01 + (top - bottom - 0.02) * step / (ROOT_PROBE_HEIGHTS - 1)
               for step in range(ROOT_PROBE_HEIGHTS)]
    across = (inner - inward * 0.01, (inner + outer) / 2.0, outer + inward * 0.01)
    for z in heights:
        for y in across:
            require_solid(frame, App.Vector(root + toward * 0.01, y, z),
                          f"cell {index + 1}'s finger root")
    length, side = shape.FINGER_ROOT_BLOCK_LENGTH_MM, shape.FINGER_ROOT_BLOCK_SIDE_MM
    wall_z = bottom / 2.0
    middle_x = root + toward * length / 2.0
    for point, want_solid in (
            ((root + toward * (length - 0.01), (inner + outer) / 2.0), True),
            ((root + toward * (length + 0.01), (inner + outer) / 2.0), False),
            ((middle_x, inner + inward * (side - 0.01)), True),
            ((middle_x, inner + inward * (side + 0.01)), False),
            ((middle_x, outer - inward * (side - 0.01)), True),
            ((middle_x, outer - inward * (side + 0.01)), False)):
        (require_solid if want_solid else require_open)(
            frame, App.Vector(*point, wall_z), f"cell {index + 1}'s finger root block")


def check_finger_slots(frame, index, key_center, finger, lip_fit):
    """The slots open and the finger whole, the room as printed taking
    the free end's swing with the spare."""
    open_points, solid_points = finger_probe_points(key_center, finger, lip_fit)
    for point in open_points:
        require_open(frame, point, f"cell {index + 1}'s finger slots")
    for point in solid_points:
        require_solid(frame, point, f"cell {index + 1}'s finger or the plate around it")
    check_finger_root(frame, index, key_center, finger, lip_fit)
    swing = shape.finger_swing(finger, shape.cell_lip_reach(index))
    room = shape.finger_room_modelled() - 2.0 * layout.PRINT_SWELLING_PER_SIDE_MM
    if room < swing + shape.FINGER_ROOM_SPARE_MM - MEASURE_TOLERANCE_MM:
        raise SystemExit(f"error: cell {index + 1}'s finger swings {swing:.3f} in a room of "
                         f"{room:.3f} as printed")
    return swing


def check_fingers(frame, frame_faces, lip_fit):
    """Each finger's bending length and thickness from its faces, its
    root's strain as printed by the removed snap hook's formula
    (layout.cantilever_strain()) with its lip's
    measured reach, failing above DESIGN_LIP_MAXIMUM_STRAIN_PERCENT, its
    slots and its root."""
    room = shape.finger_room_modelled() - 2.0 * layout.PRINT_SWELLING_PER_SIDE_MM
    require_design("the fingers' room as printed", room, DESIGN_FINGER_ROOM_PRINTED_MM)
    require_design("the root blocks' length past the root", shape.FINGER_ROOT_BLOCK_LENGTH_MM,
                   DESIGN_FINGER_ROOT_BLOCK_MM[0])
    require_design("the root blocks' reach past the blade's faces", shape.FINGER_ROOT_BLOCK_SIDE_MM,
                   DESIGN_FINGER_ROOT_BLOCK_MM[1])
    for index, lip_faces in enumerate(lip_faces_by_cell(frame)):
        key_center = shape.cell_key_center(index)
        placements = shape.lip_placements(key_center, lip_fit, shape.cell_lip_reach(index))
        figures = []
        for number, (finger, placement) in enumerate(zip(shape.FINGERS, placements)):
            length, thickness = measured_finger(
                frame_faces, key_center, finger, lip_face_at(index, placement, lip_faces), lip_fit)
            printed = thickness + 2.0 * layout.PRINT_SWELLING_PER_SIDE_MM
            require_design(f"finger {number + 1}'s bending length", length,
                           DESIGN_FINGER_BENDING_LENGTHS_MM[number])
            require_design("the fingers' thickness as printed", printed,
                           DESIGN_FINGER_PRINTED_THICKNESS_MM)
            reach = measured_lip_reach(index, placement, lip_faces)
            strain = 100.0 * layout.cantilever_strain(reach, printed, length)
            designed = 100.0 * shape.finger_strain(finger, shape.cell_lip_reach(index))
            if abs(strain - designed) > MEASURE_TOLERANCE_MM:
                raise SystemExit(f"error: cell {index + 1}'s finger {number + 1} strains "
                                 f"{strain:.4f} % as measured, {designed:.4f} % as designed")
            if strain > DESIGN_LIP_MAXIMUM_STRAIN_PERCENT:
                raise SystemExit(f"error: cell {index + 1}'s finger {number + 1} strains "
                                 f"{strain:.2f} % as printed, over "
                                 f"{DESIGN_LIP_MAXIMUM_STRAIN_PERCENT} %")
            swing = check_finger_slots(frame, index, key_center, finger, lip_fit)
            figures.append((length, strain, swing))
        require_design(f"cell {index + 1}'s largest finger strain as printed (%)",
                       max(strain for _, strain, _ in figures), DESIGN_LIP_STRAIN_PERCENT[index])
        print(f"cell {index + 1}:     fingers " + ", ".join(
            f"{length:.2f} long {strain:.2f} %" for length, strain, _ in figures)
            + f" as printed ({printed:.1f} thick), free ends swing up to "
            f"{max(swing for _, _, swing in figures):.3f} in {room:.2f} of room, roots plastic "
            "over the fingers' height")


def first_solid(solid, start, direction, length):
    """How far from start along a unit direction the solid begins, open
    at start and solid at length, by bisection."""
    def at(distance):
        return solid.isInside(start + direction * distance, MEASURE_TOLERANCE_MM, True)

    if at(0.0) or not at(length):
        raise SystemExit(f"error: no edge to measure from {start} along {direction}")
    low, high = 0.0, length
    for _ in range(24):
        middle = (low + high) / 2.0
        low, high = (low, middle) if at(middle) else (middle, high)
    return high


def bed_chamfer(solid, edge, into, inside):
    """(along the bed, up the face) of a 45 degree chamfer at the bed's
    edge of a vertical face through `edge` (x, y), the material on the
    `into` side (a unit plan vector), solid `inside` from the face."""
    bed = layout.PCB_THICKNESS_MM
    step = 0.001
    inward = App.Vector(into[0], into[1], 0.0)
    along = first_solid(solid, App.Vector(edge[0], edge[1], bed - step), inward, inside)
    up = first_solid(solid, App.Vector(edge[0], edge[1], bed) + inward * step,
                     App.Vector(0.0, 0.0, -1.0), inside)
    return along + step, up + step


def slot_chamfer_edges(box, toward_root, lip_fit, key_center, finger):
    """(slots' edges, blade's edges) at the bed as (point, into): the
    slots' long sides at the blade's middle and their free end at the
    blade's middle line, the blade's faces and free end the same way."""
    (x_low, x_high), (y_low, y_high) = box
    blade_x, blade_y = shape.finger_box(key_center, finger, lip_fit)
    middle_x = (blade_x[0] + blade_x[1]) / 2.0
    middle_y = (blade_y[0] + blade_y[1]) / 2.0
    slot_end, blade_end = (x_low, blade_x[0]) if toward_root > 0.0 else (x_high, blade_x[1])
    slots = [((middle_x, y_low), (0.0, -1.0)), ((middle_x, y_high), (0.0, 1.0)),
             ((slot_end, middle_y), (-toward_root, 0.0))]
    blade = [((middle_x, blade_y[0]), (0.0, 1.0)), ((middle_x, blade_y[1]), (0.0, -1.0)),
             ((blade_end, middle_y), (toward_root, 0.0))]
    return slots, blade


def near_bed(frame, box):
    """The frame within 1.0 of a slots box in plan and 0.7 of the bed,
    a small solid to probe."""
    (x_low, x_high), (y_low, y_high) = box
    margin, depth = 1.0, 0.7
    bed = layout.PCB_THICKNESS_MM
    crop = Part.makeBox(x_high - x_low + 2.0 * margin, y_high - y_low + 2.0 * margin, depth + 0.1,
                        App.Vector(x_low - margin, y_low - margin, bed - depth))
    return frame.common(crop)


def check_bed_chamfers(frame, lip_fit):
    """Every finger's slots' and blade's bed chamfers, along the bed and
    up the face; returns the text."""
    sizes = {"slots": [], "blade": []}
    inside = {"slots": 0.6, "blade": shape.FINGER_THICKNESS_MM / 2.0}
    for index in range(shape.CELL_COUNT):
        key_center = shape.cell_key_center(index)
        for finger in shape.FINGERS:
            box = shape.finger_slots_box(key_center, finger, lip_fit)
            edges = slot_chamfer_edges(box, shape.finger_toward_root(finger), lip_fit,
                                       key_center, finger)
            local = near_bed(frame, box)
            for what, what_edges in zip(("slots", "blade"), edges):
                for edge, into in what_edges:
                    sizes[what].extend(bed_chamfer(local, edge, into, inside[what]))
    texts = []
    for what, stated in DESIGN_FINGER_BED_CHAMFERS_MM.items():
        worst = max(sizes[what], key=lambda size: abs(size - stated))
        require_design(f"the fingers' {what} bed chamfer", worst, stated)
        texts.append(f"{what} {worst:.3f}")
    return ", ".join(texts)


def require_open(solid, point, what):
    if solid.isInside(point, MEASURE_TOLERANCE_MM, True):
        raise SystemExit(f"error: {what} is not open at {point}")


def require_solid(solid, point, what):
    if not solid.isInside(point, MEASURE_TOLERANCE_MM, True):
        raise SystemExit(f"error: {what} is missing at {point}")


def check_tab_slots(kind, frame, lip_fit):
    """Probe each slot at the walls' middle: open across its width, the
    wall present just past both sides."""
    depth = shape.wall_depth(kind)
    for index in range(shape.CELL_COUNT):
        key_center = shape.cell_key_center(index)
        gap = shape.pocket_gap(shape.cell_pocket_fit(kind, index, lip_fit))
        for x_center, width, face, tip in shape.socket_tab_specs():
            half = shape.tab_slot_width(width) / 2.0
            in_wall = face + math.copysign(gap + shape.WALL_THICKNESS_MM / 2.0, tip - face)
            for across, open_expected in ((0.0, True), (half - 0.01, True), (-half + 0.01, True),
                                          (half + 0.01, False), (-half - 0.01, False)):
                x, y = layout.footprint_point(key_center, (x_center + across, in_wall))
                point = App.Vector(x, y, -depth / 2.0)
                (require_open if open_expected else require_solid)(
                    frame, point, f"cell {index + 1}'s tab slot")
    width = shape.tab_slot_width(shape.socket_tab_specs()[0][1])
    require_design("the tab slots' width", width, DESIGN_TAB_SLOT_WIDTH_MM)
    printed = width - 2.0 * layout.PRINT_SWELLING_PER_SIDE_MM
    print(f"tab slots:  {width:.3f} wide modelled, {printed:.3f} printed, for the "
          f"{shape.socket_tab_specs()[0][1]:.2f} tab with {shape.TAB_SOLDER_PER_SIDE_MM} of "
          f"solder each side, from the body's ends; recess {shape.TAB_RECESS_DEPTH_MM} deep "
          f"({shape.TAB_RECESS_DEPTH_MM - layout.PRINT_RISE_OF_UP_FACING_BOTTOMS_MM:.1f} printed) "
          f"to {shape.TAB_RECESS_PAST_TIP_MM} past the tip")


def bore_faces(solid, radius):
    """{(x, y): (bottom z, top z)} of the solid's vertical cylinders of
    a radius that reach below the ceiling."""
    bores = {}
    for face in solid.Faces:
        surface = face.Surface
        if (isinstance(surface, Part.Cylinder)
                and abs(surface.Radius - radius) < MEASURE_TOLERANCE_MM
                and abs(surface.Axis.z) > 0.999):
            key = (round(surface.Center.x, 6), round(surface.Center.y, 6))
            box = face.BoundBox
            low, high = bores.get(key, (box.ZMin, box.ZMax))
            bores[key] = (min(low, box.ZMin), max(high, box.ZMax))
    return bores


def require_on_boss_centers(centers, what):
    expected = {(round(x, 6), round(y, 6)) for x, y in shape.boss_centers()}
    if set(centers) != expected:
        raise SystemExit(f"error: {len(centers)} {what}, not one on each of the "
                         f"{len(expected)} bosses")


def check_bores(frame, insert_length):
    bores = bore_faces(frame, shape.INSERT_BORE_DIAMETER_MM / 2.0)
    bores = {center: span for center, span in bores.items() if span[0] < -MEASURE_TOLERANCE_MM}
    require_on_boss_centers(bores, "insert bores")
    band = shape.lip_band_bottom_depth()
    for low, high in bores.values():
        if (abs(low + band) > MEASURE_TOLERANCE_MM
                or abs(high - low - shape.insert_bore_depth(insert_length)) > MEASURE_TOLERANCE_MM):
            raise SystemExit(f"error: a bore runs from z {low:.4f} to {high:.4f}")
    require_design("the bosses' height", shape.boss_height(), DESIGN_BOSS_HEIGHT_MM)
    require_design("the longest insert", shape.longest_insert_length(), DESIGN_LONGEST_INSERT_MM)
    floor = layout.PCB_THICKNESS_MM - (insert_length - band
                                       + layout.PRINT_RISE_OF_UP_FACING_BOTTOMS_MM)
    print(f"bosses:     {len(bores)}, {shape.BOSS_DIAMETER_MM} across, {shape.boss_height():.3f} "
          f"tall from the plate's top, bored {shape.INSERT_BORE_DIAMETER_MM} for an insert "
          f"{insert_length:.3f} long ({shape.insert_bore_depth(insert_length):.3f} deep, its "
          f"bottom rising {layout.PRINT_RISE_OF_UP_FACING_BOTTOMS_MM} as printed), floor "
          f"{floor:.3f}; the longest insert they hold {shape.longest_insert_length():.3f}")


def measured_pin_holes(frame, index, radius):
    """The centers of cell index's vertical cylinders of a radius that
    run through the plate, the plate's top face to the ceiling."""
    key_x, _ = shape.cell_key_center(index)
    return {center for center, (low, high) in bore_faces(frame, radius).items()
            if abs(low) < MEASURE_TOLERANCE_MM
            and abs(high - layout.PCB_THICKNESS_MM) < MEASURE_TOLERANCE_MM
            and abs(center[0] - key_x) < layout.KEY_PITCH_MM / 2.0}


def design_pin_hole(kind, index):
    """DESIGN.md's pin holes as modelled, or None where they follow
    from pull_in."""
    if kind == shape.POCKET:
        return DESIGN_POCKET_PIN_HOLE_DIAMETER_MM
    if kind == shape.HOLES:
        return DESIGN_HOLE_STRIP_HOLES_MM[index]
    return None


def check_pin_holes(kind, frame, pull_in):
    """The two holes the socket's bosses sit in, in every cell, through
    the plate at the cell's size."""
    local = layout.CHOC_FOOTPRINT_PIN_HOLE_CENTERS_MM[0]
    diameters = []
    for index in range(shape.CELL_COUNT):
        radius = shape.hole_radius(kind, index, local, dict(layout.CHOC_FOOTPRINT_HOLES_MM)[local],
                                   pull_in)
        expected = {(round(x, 6), round(y, 6))
                    for x, y in (layout.footprint_point(shape.cell_key_center(index), center)
                                 for center in layout.CHOC_FOOTPRINT_PIN_HOLE_CENTERS_MM)}
        found = measured_pin_holes(frame, index, radius)
        if found != expected:
            raise SystemExit(f"error: cell {index + 1} has {len(found)} pin holes "
                             f"{2.0 * radius:.3f} across through the plate, expected "
                             f"{len(expected)}")
        design = design_pin_hole(kind, index)
        if design is not None:
            require_design(f"cell {index + 1}'s pin holes", 2.0 * radius, design)
        diameters.append(2.0 * radius)
    swelling = 2.0 * layout.PRINT_SWELLING_PER_SIDE_MM
    print(f"pin holes:  {2 * shape.CELL_COUNT}, cells 1 to {shape.CELL_COUNT} "
          + ", ".join(f"{diameter:.3f}" for diameter in diameters) + " across modelled, "
          + ", ".join(f"{diameter - swelling:.3f}" for diameter in diameters) + " printed")


def switch_part_columns(key_center):
    """The switch's center post and side pegs below the plate, their
    holes' nominal size plus the walls' swelling."""
    columns = []
    holes = layout.footprint_holes(key_center)[: shape.SWITCH_PROTRUDING_HOLE_COUNT]
    for (x, y), diameter in holes:
        radius = diameter / 2.0 + layout.PRINT_SWELLING_PER_SIDE_MM
        columns.append(Part.makeCylinder(radius, SWITCH_PARTS_BELOW_PLATE_MM,
                                         App.Vector(x, y, -SWITCH_PARTS_BELOW_PLATE_MM), UP))
    return columns


def switch_hole_columns(kind, pull_in):
    """The switch's center post and side pegs at their holes' size as
    modelled, from SWITCH_PARTS_BELOW_PLATE_MM below the plate up
    through it."""
    height = SWITCH_PARTS_BELOW_PLATE_MM + layout.PCB_THICKNESS_MM
    return [
        Part.makeCylinder(radius, height, App.Vector(x, y, -SWITCH_PARTS_BELOW_PLATE_MM), UP)
        for index in range(shape.CELL_COUNT)
        for (x, y), radius in shape.cell_holes(kind, index, pull_in)[
            : shape.SWITCH_PROTRUDING_HOLE_COUNT]
    ]


def measured_sliver(frame, at, inner, hole_center, radius, expected):
    """The sliver of a wall's inner side between its inner face, at
    footprint-local x `inner`, and a hole's edge, along the footprint's
    x through the hole's center, where it is thinnest: from the pocket
    to the face and from the hole's center to its edge. at(local x,
    local y) gives the probe point."""
    local_x, local_y = hole_center
    start = at(inner - WINDOW_MM, local_y)
    outward = at(inner, local_y) - start
    outward.normalize()
    face = first_solid(frame, start, outward, WINDOW_MM + expected / 2.0)
    edge = first_solid(frame, at(local_x, local_y), outward * -1.0, radius + expected / 2.0)
    return (local_x - edge) - (inner - WINDOW_MM + face)


def check_holes_through_walls(kind, frame, pull_in, lip_fit):
    """The footprint holes through the walls: the switch's post and pegs
    at their holes' size clear of the frame, the west peg's hole open
    through lobe B's north wall at its mid depth, on the hole's axis and
    in the wall's middle, the wall whole along it, and the sliver of its
    inner side the hole leaves, measured where it is thinnest, or the
    hole open past the inner face where none is left."""
    overlap = frame.common(Part.makeCompound(switch_hole_columns(kind, pull_in))).Volume
    if overlap > MEASURE_TOLERANCE_MM:
        raise SystemExit(f"error: the switch's post and pegs overlap the {kind} strip by "
                         f"{overlap:.6f} mm3")
    post, peg = shape.WALL_BORING_HOLE_CENTERS_MM
    lobe_x = max(x for x, _ in shape.body_lobes_local()[1])
    middle_z = -shape.wall_depth(kind) / 2.0
    slivers = []
    bores = []
    for index in range(shape.CELL_COUNT):
        key_center = shape.cell_key_center(index)

        def at(local_x, local_y):
            return App.Vector(*layout.footprint_point(key_center, (local_x, local_y)), middle_z)

        holes = {local_center: hole for (local_center, _), hole in zip(
            layout.CHOC_FOOTPRINT_HOLES_MM, shape.cell_holes(kind, index, pull_in))}
        radius = holes[peg][1]
        inner = lobe_x + shape.pocket_gap(shape.cell_pocket_fit(kind, index, lip_fit))
        wall_middle = inner + shape.WALL_THICKNESS_MM / 2.0
        what = f"cell {index + 1}'s lobe B north wall"
        for point in (at(*peg), at(wall_middle, peg[1])):
            require_open(frame, point, f"{what} on the west peg's hole")
        for local_y in WALL_PROBE_LOCAL_YS_MM:
            require_solid(frame, at(wall_middle, local_y), what)
        expected = peg[0] - radius - inner
        if expected > MEASURE_TOLERANCE_MM:
            sliver = measured_sliver(frame, at, inner, peg, radius, expected)
            if abs(sliver - expected) > THICKNESS_TOLERANCE_MM:
                raise SystemExit(f"error: {what}'s sliver is {sliver:.6f}, expected "
                                 f"{expected:.6f}")
        else:
            require_open(frame, at(inner, peg[1]), f"{what}'s inner face on the west peg's hole")
            sliver = expected
        slivers.append(sliver)
        area = shape.cell_wall_bores(kind, index, pull_in, lip_fit)
        bores.append((area.get(peg, 0.0), area.get(post, 0.0)))
    probes = ", ".join(f"{local_y:.1f}" for local_y in WALL_PROBE_LOCAL_YS_MM)
    print(f"holes:      every footprint hole through the plate and the walls to their mouth; the "
          f"switch's post and pegs at their holes' size, {SWITCH_PARTS_BELOW_PLATE_MM} below the "
          f"plate, overlap the frame by {overlap:.1e} mm3; cells 1 to {shape.CELL_COUNT}'s walls "
          "bored " + ", ".join(f"{peg_area:.3f}" for peg_area, _ in bores) + " mm2 by the west "
          "peg's hole, " + ", ".join(f"{post_area:.3f}" for _, post_area in bores) + " mm2 by "
          f"the center post's; lobe B's north wall open on the peg's axis and through its "
          f"middle there, solid at footprint-local y {probes}, all at its mid depth")
    print(f"sliver:     lobe B's north wall's inner face to the west peg's hole, cells 1 to "
          f"{shape.CELL_COUNT} " + ", ".join(f"{sliver:.3f}" for sliver in slivers)
          + " (measured where positive; negative, the hole reaches past the face into the "
          "pocket)")


def wire_room_boxes(bottom, top):
    return [
        plan_prism(shape.tab_wire_room(shape.cell_key_center(index), tab), bottom, top)
        for index in range(shape.CELL_COUNT)
        for tab in shape.socket_tab_specs()
    ]


def least_distance(first, second):
    return Part.makeCompound(first).distToShape(Part.makeCompound(second))[0]


def require_clearance(what, distance, least):
    if distance < least - MEASURE_TOLERANCE_MM:
        raise SystemExit(f"error: {what} keep {distance:.4f}, less than {least}")
    return distance


def finger_slot_prisms(kind, lip_fit):
    return [plan_prism(slot, -shape.lip_band_bottom_depth(), layout.PCB_THICKNESS_MM)
            for slot in shape.strip_finger_slots(kind, lip_fit)]


def center_post_opening(kind, pull_in, lip_fit):
    """(at their faces, on the bed with their chamfers): the widest chord
    along which the fingers' slots open into a center post's hole as
    modelled, which must stay narrower than the hole's nominal size, so
    the post stays held. A slot that opens into the hole must cut a
    segment of it off with one of its long sides, the chord within the
    slot's ends."""
    widest = [0.0, 0.0]
    for index in range(shape.CELL_COUNT):
        key_center = shape.cell_key_center(index)
        center, diameter = layout.footprint_holes(key_center)[0]
        radius = diameter / 2.0 + pull_in
        for finger in shape.FINGERS:
            box = shape.finger_slots_box(key_center, finger, lip_fit)
            on_bed = shape.chamfered_slots_box(box, shape.finger_toward_root(finger),
                                               shape.FINGER_SLOT_BED_CHAMFER_MM)
            for which, outline in enumerate((box, on_bed)):
                if shape.circle_box_area(center, radius, outline) <= MEASURE_TOLERANCE_MM:
                    continue
                (x_low, x_high), (y_low, y_high) = outline
                edges = [edge for edge in (y_low, y_high) if abs(edge - center[1]) < radius]
                half = (math.sqrt(radius**2 - (edges[0] - center[1]) ** 2)
                        if len(edges) == 1 else 0.0)
                if (len(edges) != 1 or y_low <= center[1] <= y_high
                        or center[0] - half < x_low or center[0] + half > x_high):
                    raise SystemExit("error: a finger's slot does not cut a segment off the "
                                     "center post's hole")
                widest[which] = max(widest[which], 2.0 * half)
    if max(widest) >= layout.CHOC_FOOTPRINT_HOLES_MM[0][1]:
        raise SystemExit(f"error: the fingers' slots open {max(widest):.3f} of a center post's "
                         "hole")
    return widest


def box_distance(point, box):
    (x_low, x_high), (y_low, y_high) = box
    dx = max(x_low - point[0], 0.0, point[0] - x_high)
    dy = max(y_low - point[1], 0.0, point[1] - y_high)
    return math.hypot(dx, dy)


def bed_openings(kind, pull_in, lip_fit):
    """How deep the slots' outlines on the bed reach into the other
    footprint holes' rims, the deepest: below the chamfers the slots keep
    their web from those holes."""
    deepest = 0.0
    for index in range(shape.CELL_COUNT):
        key_center = shape.cell_key_center(index)
        for finger in shape.FINGERS:
            box = shape.finger_slots_box(key_center, finger, lip_fit)
            on_bed = shape.chamfered_slots_box(box, shape.finger_toward_root(finger),
                                               shape.FINGER_SLOT_BED_CHAMFER_MM)
            for center, diameter in layout.footprint_holes(key_center)[1:]:
                deepest = max(deepest, diameter / 2.0 + pull_in - box_distance(center, on_bed))
    return deepest


def blocks_from_other_slots(kind, lip_fit, blocks, slot_prisms):
    """The least distance from each root block to every finger's slots
    but its own finger's."""
    least = math.inf
    for number, block in enumerate(blocks):
        others = slot_prisms[:number] + slot_prisms[number + 1:]
        least = min(least, least_distance([block], others))
    return least


def socket_prisms(kind, lip_fit):
    """Every cell's socket body from the ceiling down to its bottom."""
    return [plan_prism(piece, -shape.socket_height(), 0.0)
            for index in range(shape.CELL_COUNT)
            for piece in shape.pocket_pieces(shape.cell_key_center(index))]


def check_finger_clearances(kind, pull_in, lip_fit, frame, bodies, columns, slots, rooms,
                            holes):
    """The fingers', blocks' and their slots' figures, empty for the
    pocket strip."""
    walls, blades, blocks, lips, bosses = bodies
    if not blades:
        return []
    other_holes = [shape.hole_cutter(center, radius, layout.PCB_THICKNESS_MM)
                   for index in range(shape.CELL_COUNT)
                   for center, radius in shape.cell_holes(kind, index, pull_in)[1:]]
    slot_prisms = finger_slot_prisms(kind, lip_fit)
    web = least_distance(slot_prisms, other_holes)
    require_clearance("the fingers' slots from the footprint holes but the center post's", web,
                      shape.FINGER_SLOT_HOLE_WEB_MM)
    at_faces, on_bed = center_post_opening(kind, pull_in, lip_fit)
    print(f"slots:      fingers' slots {shape.FINGER_FREE_SLOT_MM} free, "
          f"{shape.finger_room_modelled():.1f} room modelled, {web:.3f} from the footprint holes "
          f"but the center post's, whose hole they open {at_faces:.3f} wide ({on_bed:.3f} on the "
          f"bed); bed chamfers {check_bed_chamfers(frame, lip_fit)} as measured, "
          f"reaching {bed_openings(kind, pull_in, lip_fit):.3f} into the other holes' rims on "
          "the bed")
    socket_gap = min(shape.pocket_gap(lip_fit), layout.PRINT_SWELLING_PER_SIDE_MM)
    socket = require_clearance("the fingers from the socket's body",
                               least_distance(blades, socket_prisms(kind, lip_fit)), socket_gap)
    in_rooms = require_clearance("the fingers' blocks from the wire rooms",
                                 least_distance(blocks, rooms), WIRE_ROOM_PRINTED_CLEARANCE_MM)
    print(f"fingers:    {socket:.3f} from the socket's body (each blade's free end and inner "
          f"face), blocks {in_rooms:.3f} from the wire rooms")
    return [
        ("fingers from the tab slots", least_distance(blades, slots)),
        ("fingers from the wire rooms", least_distance(blades, rooms)),
        ("fingers from the switch's post and pegs", least_distance(blades, columns)),
        ("fingers from the footprint holes", least_distance(blades, holes)),
        ("blocks from the tab slots", least_distance(blocks, slots)),
        ("blocks from the switch's post and pegs", least_distance(blocks, columns)),
        ("blocks from the footprint holes", least_distance(blocks, holes)),
        ("blocks from the bosses", least_distance(blocks, bosses)),
        ("blocks from the other fingers' slots",
         blocks_from_other_slots(kind, lip_fit, blocks, slot_prisms)),
        ("fingers' slots from the bosses", least_distance(slot_prisms, bosses)),
    ]


def check_frame_clearances(kind, pull_in, lip_fit, frame):
    bodies = shape.frame_bodies(kind, lip_fit)
    walls, blades, blocks, lips, bosses = bodies
    columns = [column for index in range(shape.CELL_COUNT)
               for column in switch_part_columns(shape.cell_key_center(index))]
    rooms = wire_room_boxes(-shape.lip_band_bottom_depth(), 0.0)
    depth = shape.wall_depth(kind)
    slots = []
    recesses = []
    holes = []
    for index in range(shape.CELL_COUNT):
        key_center = shape.cell_key_center(index)
        slots.extend(plan_prism(shape.tab_slot(key_center, tab), -depth, 0.0)
                     for tab in shape.socket_tab_specs())
        recesses.extend(plan_prism(shape.tab_slot(key_center, tab), 0.0, shape.TAB_RECESS_DEPTH_MM)
                        for tab in shape.socket_tab_specs())
        holes.extend(shape.hole_cutter(center, radius, layout.PCB_THICKNESS_MM)
                     for center, radius in shape.cell_holes(kind, index, pull_in))
    recess_web = require_clearance("the tabs' recesses from the footprint holes",
                                   least_distance(recesses, holes), RECESS_HOLE_CLEARANCE_MM)
    tab_count, hole_count = len(shape.socket_tab_specs()), len(layout.CHOC_FOOTPRINT_HOLES_MM)
    cell_webs = [least_distance(recesses[index * tab_count:(index + 1) * tab_count],
                                holes[index * hole_count:(index + 1) * hole_count])
                 for index in range(shape.CELL_COUNT)]
    print(f"recesses:   {recess_web:.3f} from the footprint holes as modelled, "
          f"{recess_web + 2.0 * layout.PRINT_SWELLING_PER_SIDE_MM:.3f} as printed; cells 1 to "
          f"{shape.CELL_COUNT} " + ", ".join(f"{web:.3f}" for web in cell_webs) + " as modelled")
    figures = [
        ("bosses from the walls", least_distance(bosses, walls)),
        ("bosses from the wire rooms", least_distance(bosses, rooms)),
        ("bosses from the switch's post and pegs", least_distance(bosses, columns)),
        ("bosses from the footprint holes", least_distance(bosses, holes)),
    ]
    figures += check_finger_clearances(kind, pull_in, lip_fit, frame, bodies, columns, slots,
                                       rooms, holes)
    if lips:
        figures.append(("lips from the tab slots", least_distance(lips, slots)))
    for what, distance in figures:
        require_clearance(what, distance, FEATURE_CLEARANCE_MM)
    print("clearances: " + ", ".join(f"{what} {distance:.3f}" for what, distance in figures))


def check_notches(strip, z):
    _, (y_low, _) = shape.plate_rectangle()
    for index in range(shape.CELL_COUNT):
        for number, x in enumerate(shape.notch_x_centers(index), start=1):
            point = App.Vector(x, y_low + shape.NOTCH_DEPTH_MM / 2.0, z)
            if strip.isInside(point, MEASURE_TOLERANCE_MM, True) != (number > index + 1):
                raise SystemExit(f"error: cell {index + 1} has the wrong notches")


def check_marks(kind, frame):
    """The strip's marks at DESIGN.md's places, its north edge open at
    them and solid at every other strip's that is not also its own (the
    hole strip shares the lip strip's middle one and two of the pocket
    strip's)."""
    _, (_, y_high) = shape.plate_rectangle()
    own = shape.strip_mark_xs(kind)
    design = DESIGN_STRIP_MARK_XS_MM[kind]
    if len(own) != len(design):
        raise SystemExit(f"error: the {kind} strip has {len(own)} marks, DESIGN.md says "
                         f"{len(design)}")
    for x, design_x in zip(own, design):
        require_design(f"the {kind} strip's mark", x, design_x)
    for x in sorted({x for mark_kind in shape.STRIP_KINDS for x in shape.strip_mark_xs(mark_kind)}):
        point = App.Vector(x, y_high - shape.LIP_STRIP_MARK_DEPTH_MM / 2.0,
                           layout.PCB_THICKNESS_MM / 2.0)
        if frame.isInside(point, MEASURE_TOLERANCE_MM, True) == (x in own):
            raise SystemExit(f"error: the {kind} strip's north edge is wrong at x {x:.2f}")


def export_frame(arguments):
    kind = arguments.kind
    lip_fit = arguments.lip_fit
    frame, expected = shape.build_frame(kind, arguments.pull_in, arguments.insert_length, lip_fit)
    (x_low, x_high), (y_low, y_high) = shape.plate_rectangle()
    fit_text = f", pockets at the fit {lip_fit:+.2f}" if kind == shape.LIP else ""
    print(f"strip:      {kind}, {shape.CELL_COUNT} cells at {layout.KEY_PITCH_MM} pitch, plate "
          f"{x_high - x_low:.3f} x {y_high - y_low:.3f} x {layout.PCB_THICKNESS_MM}, footprint "
          f"holes grown by {arguments.pull_in}{fit_text}")
    print(f"volume:     {frame.Volume:.3f} mm3 (analytic {expected:.3f} mm3)")
    frame_faces = [planar_faces_along(frame, axis) for axis in range(3)]
    check_pockets(kind, frame, frame_faces, lip_fit)
    check_wall_depth(kind, frame)
    if kind == shape.LIP:
        check_lips(frame, lip_fit)
        check_fingers(frame, frame_faces, lip_fit)
    check_tab_slots(kind, frame, lip_fit)
    check_pin_holes(kind, frame, arguments.pull_in)
    check_holes_through_walls(kind, frame, arguments.pull_in, lip_fit)
    check_bores(frame, arguments.insert_length)
    check_frame_clearances(kind, arguments.pull_in, lip_fit, frame)
    check_notches(frame, layout.PCB_THICKNESS_MM / 2.0)
    check_marks(kind, frame)
    marks = ", ".join(f"{x:.2f}" for x in shape.strip_mark_xs(kind))
    print(f"notches:    cell k has k in the south edge; marks in the north edge at x {marks}")
    return shape.turned_for_printing(frame)


# The backing.


def check_pads(backing):
    thickness = shape.BACKING_THICKNESS_MM
    tops = [face for face in planar_faces_along(backing, 2)
            if upward(face) and face_coordinate(face, 2) > thickness + MEASURE_TOLERANCE_MM]
    for index in range(shape.CELL_COUNT):
        key_center = shape.cell_key_center(index)
        cell_tops = [face for face in tops
                     if abs(face.CenterOfMass.x - key_center[0]) < layout.KEY_PITCH_MM / 2.0]
        lobes = shape.body_lobes(key_center)
        if len(cell_tops) != len(lobes):
            raise SystemExit(f"error: cell {index + 1} has {len(cell_tops)} pads")
        heights = {round(face_coordinate(face, 2) - thickness, 6) for face in cell_tops}
        if len(heights) != 1:
            raise SystemExit(f"error: cell {index + 1}'s pads differ in height")
        height = heights.pop()
        offset = round(height - (shape.lip_band_bottom_depth() - shape.socket_height()), 6) + 0.0
        require_design(f"cell {index + 1}'s pads against the socket's bottom", offset,
                       DESIGN_PAD_OFFSETS_MM[index])
        for face in cell_tops:
            point = face.CenterOfMass
            lobe_boxes = [((min(x for x, _ in lobe), max(x for x, _ in lobe)),
                           (min(y for _, y in lobe), max(y for _, y in lobe))) for lobe in lobes]
            if not any(face.BoundBox.XMin > x_range[0] and face.BoundBox.XMax < x_range[1]
                       and face.BoundBox.YMin > y_range[0] and face.BoundBox.YMax < y_range[1]
                       for x_range, y_range in lobe_boxes):
                raise SystemExit(f"error: a pad of cell {index + 1} at ({point.x:.3f}, "
                                 f"{point.y:.3f}) is not under a socket lobe")
        print(f"cell {index + 1}:     pads {height:.3f} tall, top {offset:+.3f} against the "
              "socket's bottom")


def check_screw_holes(backing):
    holes = bore_faces(backing, shape.SCREW_CLEARANCE_HOLE_DIAMETER_MM / 2.0)
    require_on_boss_centers(holes, "screw holes")
    return holes


def check_stack(kind, stacked, frame, pull_in, lip_fit):
    if frame.common(stacked).Volume > MEASURE_TOLERANCE_MM:
        raise SystemExit(f"error: the backing overlaps the {kind} strip")
    sunk = frame.copy()
    sunk.translate(App.Vector(0.0, 0.0, -CONTACT_PROBE_DEPTH_MM))
    contact = sunk.common(stacked).Volume / CONTACT_PROBE_DEPTH_MM
    boss_ends = len(shape.boss_centers()) * math.pi * (
        (shape.BOSS_DIAMETER_MM / 2.0) ** 2 - (shape.INSERT_BORE_DIAMETER_MM / 2.0) ** 2)
    mouths = shape.frame_mouth_area(kind, pull_in, lip_fit) if kind == shape.LIP else 0.0
    expected = boss_ends + mouths
    if abs(contact - expected) > CONTACT_VOLUME_RELATIVE_TOLERANCE * expected:
        raise SystemExit(f"error: the backing touches the {kind} strip over {contact:.4f} mm2, "
                         f"the bosses', walls', fingers' and blocks' ends are {expected:.4f} mm2")
    return contact


def stacked_pads():
    top = -shape.lip_band_bottom_depth()
    return [
        plan_prism(polygon, top, top + shape.pad_height(index))
        for index in range(shape.CELL_COUNT)
        for polygon in shape.pad_polygons(shape.cell_key_center(index))
    ]


def expected_pad_distance(kind, lip_fit):
    """(distance, its horizontal part) from the pads to the nearest of
    the frame: the lips' tips, which span the pads' height, or the
    pocket walls, which the lowest pads pass under."""
    nearest = None
    for index in range(shape.CELL_COUNT):
        gap = shape.pocket_gap(shape.cell_pocket_fit(kind, index, lip_fit))
        if kind == shape.LIP:
            horizontal = shape.pad_inset() + gap - shape.lip_protrusion(shape.cell_lip_reach(index))
            vertical = 0.0
        else:
            horizontal = shape.pad_inset() + gap
            vertical = max(0.0, shape.pad_top_depth(index) - shape.wall_depth(kind))
        candidate = (math.hypot(horizontal, vertical), horizontal)
        nearest = candidate if nearest is None else min(nearest, candidate)
    return nearest


def check_pads_clear(kind, frame, lip_fit):
    distance = frame.distToShape(Part.makeCompound(stacked_pads()))[0]
    expected, horizontal = expected_pad_distance(kind, lip_fit)
    if abs(distance - expected) > MEASURE_TOLERANCE_MM:
        raise SystemExit(f"error: the pads come {distance:.4f} from the {kind} strip, "
                         f"expected {expected:.4f}")
    # The pad's face and the wall's swell toward each other; a lip's tip
    # grows the lead-in's swelling along the axis.
    nearest_growth = layout.PRINT_SWELLING_PER_SIDE_MM
    if kind == shape.LIP:
        nearest_growth += shape.LIP_TIP_GROWTH_AS_PRINTED_MM
    printed = horizontal - layout.PRINT_SWELLING_PER_SIDE_MM - nearest_growth
    if printed < shape.PAD_CLEARANCE_TO_LIPS_MM - MEASURE_TOLERANCE_MM:
        raise SystemExit(f"error: the pads come {printed:.4f} from the {kind} strip as printed")
    return distance, printed


def check_bores_over_holes(frame, holes):
    bores = bore_faces(frame, shape.INSERT_BORE_DIAMETER_MM / 2.0)
    bores = {center for center, span in bores.items() if span[0] < -MEASURE_TOLERANCE_MM}
    stacked_holes = set(holes)
    if bores != stacked_holes:
        raise SystemExit("error: the bores and the screw holes do not line up")
    return len(bores)


def check_wire_rooms(kind, frame, stacked, lip_fit):
    """The tabs' wire rooms, from the ceiling to the backing's top: no
    plastic inside, and the walls, fingers, blocks, lips and bosses far
    enough beside them to stay out as printed. Returns that clearance."""
    rooms = wire_room_boxes(-shape.lip_band_bottom_depth(), 0.0)
    for solid in (frame, stacked):
        inside = solid.common(Part.makeCompound(rooms)).Volume
        if inside > MEASURE_TOLERANCE_MM:
            raise SystemExit(f"error: {inside:.4f} mm3 of plastic in the wire rooms under the "
                             f"{kind} strip")
    walls, blades, blocks, lips, bosses = shape.frame_bodies(kind, lip_fit)
    distance = least_distance(rooms, walls + blades + blocks + lips + bosses)
    return require_clearance(f"the walls, fingers, blocks and bosses beside the wire rooms of the "
                             f"{kind} strip", distance, WIRE_ROOM_PRINTED_CLEARANCE_MM)


def battery_figures():
    socket_bottom = layout.PCB_UNDERSIDE_Z_MM - shape.socket_height()
    lips = shape.lip_band_bottom_depth() - shape.socket_height()
    rise = layout.PRINT_RISE_OF_UP_FACING_BOTTOMS_MM
    bottom = socket_bottom - lips - shape.BACKING_THICKNESS_MM
    clearance = bottom - rise - layout.BATTERY_TOP_Z_MM
    return socket_bottom, lips, bottom, clearance


def check_battery():
    socket_bottom, lips, bottom, clearance = battery_figures()
    limit = shape.backing_thickness_limit()
    require_clearance("the backing from the battery as printed", clearance,
                      layout.MINIMUM_BATTERY_TO_SOCKET_CLEARANCE_MM)
    require_design("the backing's thickness", shape.BACKING_THICKNESS_MM,
                   DESIGN_BACKING_THICKNESS_MM)
    require_design("the battery clearance as printed", clearance,
                   DESIGN_BATTERY_CLEARANCE_AS_PRINTED_MM)
    rise = layout.PRINT_RISE_OF_UP_FACING_BOTTOMS_MM
    print(f"battery:    in the tray the frame in the PCB's place puts the socket's bottom at "
          f"z {socket_bottom:.3f} (under a PCB {layout.SOCKET_BOTTOM_Z_MM:.2f}); below it the "
          f"lips' band takes {lips:.3f} and the backing {shape.BACKING_THICKNESS_MM} (of "
          f"{limit:.3f} the battery allows), its bottom at z {bottom:.3f}, {bottom - rise:.3f} "
          f"as printed (its top rises {rise}), "
          f"{clearance:.3f} over the battery's top {layout.BATTERY_TOP_Z_MM} as printed "
          f"(at least {layout.MINIMUM_BATTERY_TO_SOCKET_CLEARANCE_MM})")


def export_backing(arguments):
    backing, expected = shape.build_backing()
    (x_low, x_high), (y_low, y_high) = shape.plate_rectangle()
    print(f"strip:      backing, {x_high - x_low:.3f} x {y_high - y_low:.3f} x "
          f"{shape.BACKING_THICKNESS_MM}, pads {shape.pad_inset():.2f} inside each socket lobe")
    print(f"volume:     {backing.Volume:.3f} mm3 (analytic {expected:.3f} mm3)")
    check_pads(backing)
    holes = check_screw_holes(backing)
    print(f"holes:      {len(holes)}, {shape.SCREW_CLEARANCE_HOLE_DIAMETER_MM:.2f} modelled "
          f"({layout.MOUNTING_DRILL_DIAMETER_MM} printed) for M2 screws")
    stacked = shape.stacked_backing(backing)
    for kind in shape.FRAME_KINDS:
        frame, _ = shape.build_frame(kind, arguments.pull_in, arguments.insert_length,
                                     arguments.lip_fit)
        contact = check_stack(kind, stacked, frame, arguments.pull_in, arguments.lip_fit)
        distance, printed = check_pads_clear(kind, frame, arguments.lip_fit)
        bores = check_bores_over_holes(frame, holes)
        rooms = check_wire_rooms(kind, frame, stacked, arguments.lip_fit)
        touching = ("the bosses', walls', fingers' and blocks' ends" if kind == shape.LIP
                    else "the bosses' ends")
        print(f"stack:      under the {kind} strip nothing overlaps, contact {contact:.3f} mm2 "
              f"({touching}), "
              f"pads {distance:.3f} from it ({printed:.3f} across as printed), {bores} bores over "
              f"their screw holes, wire rooms {rooms:.3f} clear")
    check_battery()
    check_notches(backing, shape.BACKING_THICKNESS_MM / 2.0)
    print("notches:    cell k has k in the south edge")
    return backing


def main():
    arguments = parse_arguments(script_arguments(sys.argv))
    if arguments.kind == shape.BACKING:
        strip = export_backing(arguments)
    else:
        strip = export_frame(arguments)
    mesh = export_stl(strip, arguments.stl_file)
    check_closed_mesh(arguments.stl_file)
    if abs(mesh.BoundBox.ZMin) > MEASURE_TOLERANCE_MM:
        raise SystemExit(f"error: the mesh's lowest point lies at z {mesh.BoundBox.ZMin:.4f}, "
                         "not on the bed")
    box = strip.BoundBox
    print(f"print:      {'bottom' if arguments.kind == shape.BACKING else 'plate top'} on z = 0, "
          f"{box.XLength:.2f} x {box.YLength:.2f} x {box.ZLength:.2f} mm")
    print(f"wrote:      {arguments.stl_file} ({mesh.CountFacets} facets), one closed "
          "manifold shell")


run_and_exit(main)
