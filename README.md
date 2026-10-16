# kbdkid5

A wireless split keyboard with Kailh Choc v1 switches on hotswap sockets and a nice!nano v2 per half, the successor of [kbdkid4](https://github.com/Tubbles/kbdkid4). The PCB carries only the switch matrix. The nice!nano, power switch, reset button and battery connector are wired by hand and mounted in the 3D-printed tray, which makes the half smaller than kbdkid4's. A slanted inner edge lets the two halves join with magnets and steel dowel pins into one Alice-like board.

The design, with every dimension, is in [DESIGN.md](DESIGN.md). The part choices and their sources are in [doc/components.md](doc/components.md), and the plan is in [PLAN.md](PLAN.md). The PCB itself is not designed yet. For now a printed mock stands in for it.

## 3D printed PCB mock

`scripts/export_pcb.py` exports a printable stand-in for the PCB until the real one is designed: the outline from `scripts/layout.py` (the geometry of DESIGN.md as data) extruded to 1.6 mm, with every key's Choc hotswap footprint holes and the mounting drills, and no sockets. It test-fits the printed tray and plate. To mount switches, print the fused mock below. Printed parts come out slightly larger than modelled, so the mock is pulled in by `pull_in` (default 0.2 mm) per side: the outline moves inward and every hole grows outward by that much.

    docker build -t freecad-headless -f scripts/freecad.Dockerfile scripts
    docker run --rm -v "$PWD":/work -w /work freecad-headless \
        freecadcmd scripts/export_pcb.py --pass pcb.stl [right] [pull_in=0.2]

CI first checks the layout with `python3 scripts/check_layout.py` (outline, keys, drills, the parts in the tray, the sockets against the tray, the joint), then uploads both halves as the `pcb-stl` artifact: `kbdkid5_Pcb_Left.stl` and `kbdkid5_Pcb_Right.stl` (the word `right`). The right one has the outline and the drills mirrored across the outline's center line, but not the switch footprints, since a switch cannot be mirrored: each sits as on the left half, at the mirrored key center.

## 3D printed switch plate

`scripts/export_plate.py` exports the switch plate: kbdkid3's plate (one Choc cell per key) aligned onto the layout's keys, trimmed 0.4 mm at its outer edges to fit the tray, the switch-free corner by the slant covered up to 0.35 mm past the outline's slant, and 4.17 mm holes over the screw heads at the mounting drills. kbdkid4's print corrections apply: the hole pattern moves `pattern_shift` (default 0.25 mm) along x while the outline stays put, and `side_shave` (default 0.1 mm) comes off the west and east edges and the slanted edge. The word `covered` makes the plate for a half without the hard-to-reach key S123: its cutout is filled in and a pit in the underside clears its diode. The plate is written upside down, its top face on the bed.

    docker run --rm -v "$PWD":/work -w /work freecad-headless \
        freecadcmd scripts/export_plate.py --pass plate.stl [right] [covered] \
        [pattern_shift=0.25] [side_shave=0.1] [hole_diameter=4.17]

CI uploads both halves, plain and covered, as the `plate-stl` artifact: `kbdkid5_Plate_Left.stl`, `kbdkid5_Plate_Right.stl`, `kbdkid5_Plate_Left_Covered.stl` and `kbdkid5_Plate_Right_Covered.stl`. The right ones are mirrored across the outline's center line.

## 3D printed fused mock

`scripts/export_mock.py` exports the PCB mock and the switch plate fused into one part, to mount switches in and get a feel of the layout. Each key's two pin holes become narrow slits in the PCB layer that grip the switch's flat pin blades (0.2 x 0.8 mm, as measured on kbdkid4's switch model): `slit_width` across the blade, default 0.6 mm (the blade plus `pull_in` per side), and `slit_length` along it, default 1.6 mm (the blade plus `pull_in` per side plus 0.4 mm, so only the width grips). `pull_in` sets those defaults but does not grow a given `slit_width` or `slit_length`. The plate has no `pattern_shift`, since the plate and the PCB layer are one print. The part is written PCB side down. Check in the slicer preview that every slit is still open in the first layers, since elephant foot and XY or hole compensation change slits this small. The pins, the center post and the pegs reach 1.4 mm below the part, so a mounted switch needs it raised off the table.

    docker run --rm -v "$PWD":/work -w /work freecad-headless \
        freecadcmd scripts/export_mock.py --pass mock.stl [right] \
        [pull_in=0.2] [slit_width=0.6] [slit_length=1.6]

`scripts/export_slit_test.py` exports a strip of six single-key cells to find the slit width that grips best: slits 0.5, 0.6 (the default), 0.7, 0.8, 0.9 and 1.0 mm wide, all 1.6 mm long, and cell k has k notches in its south edge. Pass the winning width to the fused mock as `slit_width`.

    docker run --rm -v "$PWD":/work -w /work freecad-headless \
        freecadcmd scripts/export_slit_test.py --pass strip.stl [pull_in=0.2]

CI uploads both halves of the fused mock and the strip as the `mock-stl` artifact: `kbdkid5_Mock_Left.stl`, `kbdkid5_Mock_Right.stl` and `kbdkid5_Slit_Test.stl`. The right half's outline and plate are mirrored like the other right parts, but not its switch footprints, since a switch cannot be mirrored: each sits as on the left half, at the mirrored key center.
