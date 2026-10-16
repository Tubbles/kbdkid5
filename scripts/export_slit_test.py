"""Export the slit test strip (STL): a row of single-key cells, each
the fused mock's PCB layer and plate around one switch, whose pin slits
differ in width only, to find the width that grips a switch's pins.

Each cell is a 19.05 square of the PCB layer with one key's footprint
holes (grown by pull_in) and its two pin slits, under one cell of the
kbdkid3 plate model (plate_shape.py), the cells side by side at the
key pitch. The slits are all fused-mock slits (layout.py) of the
default length, their widths stepping by SLIT_WIDTH_STEP_MM from
SLIT_WIDTH_STEPS_BELOW_DEFAULT step under the default width upward,
so the default width is the second cell's: the range reaches further
above the default than below it, since small FDM holes tend to shrink
more than large ones. Cell k (from 1, west to east) has k notches in
its south edge, so a printed cell names itself.
The strip prints like the fused mock, PCB side down, the PCB layer's
underside on z = 0.

A switch is the same on both halves, so is the strip: the footprint is
the left half's, which the right half's fused mock uses too.

Runs headless under FreeCAD's console interpreter (see
freecad_common.py for the freecadcmd quirks that shape the
invocation):

    freecadcmd scripts/export_slit_test.py --pass <strip.stl> [pull_in=0.2]

It prints each cell's slit width and checks for one valid solid of the
layers' volume less the notches, every plate cutout centered on its
key's center hole, every slit centered on its pin at its size, the
notch count of every cell, and a closed mesh.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import FreeCAD as App
import Part

import layout
import pcb_shape
import plate_shape
from freecad_common import check_closed_mesh, export_stl, run_and_exit, script_arguments

CELL_COUNT = 6
SLIT_WIDTH_STEP_MM = 0.1
SLIT_WIDTH_STEPS_BELOW_DEFAULT = 1

# The notches that number the cells, cut through the whole strip from
# its south edge.
NOTCH_WIDTH_MM = 1.0
NOTCH_DEPTH_MM = 0.8
NOTCH_PITCH_MM = 2.0

# The kbdkid3 plate model's cell the strip's cells are copies of (they
# are all the same cell).
PLATE_CELL_KEY_NAME = "S100"

USAGE = f"""\
usage: freecadcmd scripts/export_slit_test.py --pass <strip.stl>
           [pull_in={pcb_shape.DEFAULT_PULL_IN_MM}]

  pull_in    swelling allowance per side, mm: the footprint holes grow outward
             by this much, and the default slit width and length follow it\
"""


class Arguments:
    def __init__(self):
        self.stl_file = None
        self.pull_in = pcb_shape.DEFAULT_PULL_IN_MM


def parse_arguments(argument_list):
    arguments = Arguments()
    positionals = []
    for argument in argument_list:
        if "=" in argument:
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


def cell_key_center(index):
    """The key center of cell index (from 0) in the strip's frame."""
    half_pitch = layout.KEY_PITCH_MM / 2.0
    return (half_pitch + index * layout.KEY_PITCH_MM, half_pitch)


def cell_slit_width(index, pull_in):
    steps = index - SLIT_WIDTH_STEPS_BELOW_DEFAULT
    return layout.default_slit_width(pull_in) + steps * SLIT_WIDTH_STEP_MM


def strip_holes_and_slits(pull_in):
    """(holes, slits per cell): the footprint holes of every cell and
    each cell's two slits."""
    holes = [
        hole
        for index in range(CELL_COUNT)
        for hole in layout.footprint_holes_without_pin_holes(cell_key_center(index))
    ]
    slit_length = layout.default_slit_length(pull_in)
    slits = [
        layout.pin_slits(cell_key_center(index), slit_length, cell_slit_width(index, pull_in))
        for index in range(CELL_COUNT)
    ]
    return holes, slits


def build_pcb_layer(pull_in, holes, slits):
    """The PCB layer, a box under the cells less the holes and slits,
    checked against its analytic volume."""
    thickness = layout.PCB_THICKNESS_MM
    length = CELL_COUNT * layout.KEY_PITCH_MM
    box = Part.makeBox(length, layout.KEY_PITCH_MM, thickness)
    cutters = [
        pcb_shape.hole_cutter(center, diameter, pull_in, thickness) for center, diameter in holes
    ]
    cutters.extend(pcb_shape.slit_cutter(slit, thickness) for slit in slits)
    layer = box.cut(Part.makeCompound(cutters))
    area = length * layout.KEY_PITCH_MM - sum(
        math.pi * (diameter / 2.0 + pull_in) ** 2 for _center, diameter in holes
    ) - sum(layout.polygon_signed_area(slit) for slit in slits)
    expected = area * thickness
    if not layer.isValid() or len(layer.Solids) != 1:
        raise SystemExit("error: cutting the holes broke the PCB layer")
    if abs(layer.Volume - expected) > pcb_shape.VOLUME_RELATIVE_TOLERANCE * expected:
        raise SystemExit(
            f"error: PCB layer volume {layer.Volume:.4f} mm3, analytic {expected:.4f} mm3"
        )
    return layer.Solids[0], expected


def build_plate_layer():
    """(the cells fused, one cell's volume): copies of the plate model's
    cell, one on each strip key, resting on the PCB layer."""
    plate, _offset, _residual = plate_shape.place_on_layout(plate_shape.load_plate_model())
    layout_center = layout.KEY_CENTERS_MM[PLATE_CELL_KEY_NAME]
    cell = plate.Solids[plate_shape.cell_index_at(plate, layout_center)]
    cell_center = cell.BoundBox.Center
    cells = []
    for index in range(CELL_COUNT):
        x, y = cell_key_center(index)
        copy = cell.copy()
        copy.translate(
            App.Vector(x - cell_center.x, y - cell_center.y, -layout.PCB_UNDERSIDE_Z_MM)
        )
        cells.append(copy)
    return plate_shape.fuse_into_one_solid(Part.makeCompound(cells)), cell.Volume


def notch_x_centers(index):
    """The x centers of cell index's possible notches, west to east."""
    key_x, _ = cell_key_center(index)
    middle = (CELL_COUNT + 1) / 2.0
    return [key_x + (number - middle) * NOTCH_PITCH_MM for number in range(1, CELL_COUNT + 1)]


def notch_cutters(height):
    """Cell k (from 1) gets its first k notches."""
    cutters = []
    for index in range(CELL_COUNT):
        for x in notch_x_centers(index)[: index + 1]:
            cutter = Part.makeBox(
                NOTCH_WIDTH_MM,
                NOTCH_DEPTH_MM + pcb_shape.CUT_EXTRA_MM,
                height + 2.0 * pcb_shape.CUT_EXTRA_MM,
            )
            extra = pcb_shape.CUT_EXTRA_MM
            cutter.translate(App.Vector(x - NOTCH_WIDTH_MM / 2.0, -extra, -extra))
            cutters.append(cutter)
    return cutters


def cut_notches(strip):
    """The strip with the cells' notches, checked by volume and by
    probing every place a notch could be."""
    height = strip.BoundBox.ZLength
    cutters = notch_cutters(height)
    notched = strip.cut(Part.makeCompound(cutters))
    if not notched.isValid() or len(notched.Solids) != 1:
        raise SystemExit("error: cutting the notches broke the strip")
    removed = strip.Volume - notched.Volume
    expected = len(cutters) * NOTCH_WIDTH_MM * NOTCH_DEPTH_MM * height
    if abs(removed - expected) > pcb_shape.VOLUME_RELATIVE_TOLERANCE * strip.Volume:
        raise SystemExit(f"error: the notches took {removed:.4f} mm3, expected {expected:.4f}")
    solid = notched.Solids[0]
    for index in range(CELL_COUNT):
        for number, x in enumerate(notch_x_centers(index), start=1):
            for z in (layout.PCB_THICKNESS_MM / 2.0, height - layout.PLATE_THICKNESS_MM / 2.0):
                point = App.Vector(x, NOTCH_DEPTH_MM / 2.0, z)
                if solid.isInside(point, 1e-6, True) != (number > index + 1):
                    raise SystemExit(f"error: cell {index + 1} has the wrong notches")
    return solid, len(cutters)


def main():
    arguments = parse_arguments(script_arguments(sys.argv))
    holes, slits_per_cell = strip_holes_and_slits(arguments.pull_in)
    slits = [slit for cell_slits in slits_per_cell for slit in cell_slits]
    pcb_layer, pcb_expected = build_pcb_layer(arguments.pull_in, holes, slits)
    plate_layer, cell_volume = build_plate_layer()
    print(f"cells:      {CELL_COUNT} at {layout.KEY_PITCH_MM} pitch, each a PCB layer "
          f"{layout.PCB_THICKNESS_MM} with {len(holes) // CELL_COUNT} footprint holes grown by "
          f"{arguments.pull_in} and 2 slits, under a kbdkid3 plate cell "
          f"{layout.PLATE_THICKNESS_MM}")
    print(f"pcb layer:  volume {pcb_layer.Volume:.3f} mm3 (analytic {pcb_expected:.3f} mm3)")
    print(f"plate:      {CELL_COUNT} cells of {cell_volume:.3f} mm3 fused, volume "
          f"{plate_layer.Volume:.3f} mm3")
    strip = pcb_shape.fuse_layers(pcb_layer, plate_layer)
    print(f"fused:      one solid, volume {strip.Volume:.3f} mm3 (layers "
          f"{pcb_layer.Volume + plate_layer.Volume:.3f} mm3)")
    cutout_count, cutout_worst = pcb_shape.check_cutouts_on_center_holes(
        strip, [cell_key_center(index) for index in range(CELL_COUNT)], arguments.pull_in
    )
    print(f"cutouts:    {cutout_count} plate cutouts, each on its key's center hole, worst "
          f"offset {cutout_worst:.4f} mm")
    measured = pcb_shape.measured_slits(strip, slits)
    for index in range(CELL_COUNT):
        cell_measured = measured[2 * index : 2 * index + 2]
        widths = {round(y_length, 4) for _, _, y_length in cell_measured}
        lengths = {round(x_length, 4) for _, x_length, _ in cell_measured}
        worst = max(offset for offset, _, _ in cell_measured)
        default = " (the default)" if index == SLIT_WIDTH_STEPS_BELOW_DEFAULT else ""
        notches = "1 notch" if index == 0 else f"{index + 1} notches"
        print(f"cell {index + 1}:     {notches}, slits "
              f"{', '.join(f'{width:.3f}' for width in sorted(widths))} wide{default}, "
              f"{', '.join(f'{length:.3f}' for length in sorted(lengths))} long, worst offset "
              f"{worst:.4f} mm")
    strip, notch_count = cut_notches(strip)
    print(f"notches:    {notch_count}, {NOTCH_WIDTH_MM} wide and {NOTCH_DEPTH_MM} deep, volume "
          f"{strip.Volume:.3f} mm3")
    mesh = export_stl(strip, arguments.stl_file)
    check_closed_mesh(arguments.stl_file)
    box = strip.BoundBox
    print(f"print:      PCB side down, its underside on z = 0, {box.XLength:.2f} x "
          f"{box.YLength:.2f} x {box.ZLength:.2f} mm")
    print(f"wrote:      {arguments.stl_file} ({mesh.CountFacets} facets), one closed "
          "manifold shell")


run_and_exit(main)
