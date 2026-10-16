# kbdkid5

A wireless split keyboard with Kailh Choc v1 switches on hotswap sockets and a nice!nano v2 per half, the successor of [kbdkid4](https://github.com/Tubbles/kbdkid4). The PCB carries only the switch matrix. The nice!nano, power switch, reset button and battery connector are wired by hand and mounted in the 3D-printed tray, which makes the half smaller than kbdkid4's. A slanted inner edge lets the two halves join with magnets and steel dowel pins into one Alice-like board.

The design, with every dimension, is in [DESIGN.md](DESIGN.md). The part choices and their sources are in [doc/components.md](doc/components.md), and the plan is in [PLAN.md](PLAN.md). The PCB itself is not designed yet. For now a printed mock stands in for it.

## 3D printed PCB mock

`scripts/export_pcb.py` exports a printable stand-in for the PCB until the real one is designed: the outline from `scripts/layout.py` (the geometry of DESIGN.md as data) extruded to 1.6 mm, with every key's Choc hotswap footprint holes and the mounting drills, and no sockets. Switches clip into it for a feel of the layout, and it test-fits the printed tray and plate. Printed parts come out slightly larger than modelled, so the mock is pulled in by `pull_in` (default 0.2 mm) per side: the outline moves inward and every hole grows outward by that much.

    docker build -t freecad-headless -f scripts/freecad.Dockerfile scripts
    docker run --rm -v "$PWD":/work -w /work freecad-headless \
        freecadcmd scripts/export_pcb.py --pass pcb.stl [right] [pull_in=0.2]

CI first checks the layout with `python3 scripts/check_layout.py` (outline, keys, drills, the parts in the tray, the sockets against the tray, the joint), then uploads both halves as the `pcb-stl` artifact: `kbdkid5_Pcb_Left.stl`, and `kbdkid5_Pcb_Right.stl` mirrored across the outline's center line (the word `right`). A bare board turned over would be its own mirror image, but a print is not: its bed side and its top side come out with different surfaces.

## 3D printed switch plate

`scripts/export_plate.py` exports the switch plate: kbdkid3's plate (one Choc cell per key) aligned onto the layout's keys, trimmed 0.4 mm at its outer edges to fit the tray, the switch-free corner by the slant covered up to 0.35 mm past the outline's slant, and 4.17 mm holes over the screw heads at the mounting drills. kbdkid4's print corrections apply: the hole pattern moves `pattern_shift` (default 0.25 mm) along x while the outline stays put, and `side_shave` (default 0.1 mm) comes off the west and east edges and the slanted edge. The word `covered` makes the plate for a half without the hard-to-reach key S123: its cutout is filled in and a pit in the underside clears its diode. The plate is written upside down, its top face on the bed.

    docker run --rm -v "$PWD":/work -w /work freecad-headless \
        freecadcmd scripts/export_plate.py --pass plate.stl [right] [covered] \
        [pattern_shift=0.25] [side_shave=0.1] [hole_diameter=4.17]

CI uploads both halves, plain and covered, as the `plate-stl` artifact: `kbdkid5_Plate_Left.stl`, `kbdkid5_Plate_Right.stl`, `kbdkid5_Plate_Left_Covered.stl` and `kbdkid5_Plate_Right_Covered.stl`. The right ones are mirrored across the outline's center line, like the PCB mock's.
