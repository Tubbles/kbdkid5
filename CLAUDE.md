# CLAUDE.md

Guidance for Claude Code working in this repository.

## What this is

kbdkid5, the successor of kbdkid4 (`~/dev/kbdkid4`, https://github.com/Tubbles/kbdkid4): a wireless split keyboard whose 3D-printed parts (tray, switch plate, PCB mock) are built by FreeCAD scripts in `scripts/`, running headless in a container. [DESIGN.md](DESIGN.md) holds the design and every dimension, [doc/components.md](doc/components.md) the part research with sources, [PLAN.md](PLAN.md) the phases, `doc/work/` the work items with their status, `doc/log/` dated decision logs.

There is no PCB design yet (the user does it later in LibrePCB). Until then `scripts/layout.py` is the ground truth for the geometry: keys, outline, mounting drills, the parts in the tray and the joint. It is plain Python with no FreeCAD import, so `scripts/check_layout.py` can check it anywhere. The export scripts read it. When DESIGN.md and `layout.py` disagree, that is a bug in one of them: fix it, don't pick one silently.

## Layout, check, PCB mock and plate

`scripts/layout.py` holds DESIGN.md's numbers, each commented with its source (DESIGN.md, a kbdkid4 file, doc/components.md): the keys, the Choc footprint's holes (kbdkid4's `KHA-PG1350` package) and hotswap socket polygons (kbdkid4's `HOTSWAP_SOCKET_POLYGONS_MM`), both mapped onto the board as kbdkid4's `Placement.map_point` maps them, the outline with its slant, the mounting drills, the heights, the tray's dimensions (`scripts/tray_shape.py` re-exports them under kbdkid4's names), the diodes' place (kbdkid4's, for the covered plate's pit), the parts' envelopes with the ledge cut-aways, the sockets' cuts in the tray (kbdkid4's tab notch, ledge relief and standoff flat rules from its `export_tray.py`, applied by functions here to the sockets named here), the joint and the pin parking hole. DESIGN.md's figures that follow from those values are not in `layout.py` but in `check_layout.py`, as `DESIGN_*` constants transcribed independently. The right half is the left one mirrored across `RIGHT_HALF_MIRROR_X_MM`, the outline's center line (x 66.199), with `mirror_for_right_half()` for points: every export mirrors across that one line, so right parts line up with each other as the left ones do (the module docstring says why not x = 0 or each part's own center).

`scripts/check_layout.py` checks the layout and DESIGN.md's derived figures against it: the outline (also against the key cells and DESIGN.md's insets) and slant, keys and holes, drills, heights, the parts against the cavity wall, the ledge, the standoffs, each other and the sockets, the battery, the sockets against the tray as cut (the ledge and joint block with the notches and reliefs, the wall with the tab pockets, the standoffs with their flats, each at its rule's clearance, and the named sockets against DESIGN.md's), the joint and the parking hole. Bodies are checked against each other in plan wherever their z ranges overlap, on sharp-cornered polygons. It stops at the first failing check and lists every offender in it. A failure is a design conflict: fix DESIGN.md and `layout.py` together, never the check. Run all checks without stopping by importing it and calling each of `CHECKS`.

`scripts/export_pcb.py` builds the PCB mock from the layout: the sharp outline moved in by `pull_in` and rounded concentric with the layout's corner radius, every hole grown by `pull_in`, 1.6 thick, flat on z = 0. It checks for one valid solid, the volume against an area computed from the layout alone (no FreeCAD offsets or fillets), the hole count, the outline's rounded corner count and a closed mesh.

`scripts/plate_shape.py` builds the switch plate with kbdkid4's plate pipeline on the layout: the kbdkid3 plate model (`resources/kbdkid3-plate-left.FCStd`, one 19.05 cell per key, the right plate in it unused) aligned onto the keys by a pure translation (every cutout within 0.05 of the mean offset, one cutout per key) and put on the PCB, its outer edges trimmed 0.4, the switch-free corner between column 5, the thumb cell and the slant covered by a slab out to the slant plus 0.35 (north to column 5's top edge, east to the thumb cell's east edge), 4.17 head holes at the mounting drills, with `covered` S123's cell filled and a pit at its diode's place, then kbdkid4's `pattern_shift` (along +x) and `side_shave` (here also off the slanted edge, along its normal, leaving it 0.25 past the slant and 0.15 from the cavity wall), and the solids fused into one valid solid of unchanged volume. Every clip of the cell compound goes solid by solid, since a `common()` of the whole compound silently drops a cell on FreeCAD 1.0. `build_plate()` returns the left half's plate in the layout's frame, on the PCB (z 9.6 to 11.8), unshifted with `pattern_shift=0`. The module has no entry point, so other scripts import it. `scripts/export_plate.py` mirrors the plate for `right`, checks it against the layout and prints what it measured (inside the tray's cavity wall, taken as the outline moved out 0.4 with round corners, the slanted edge 0.25 out of the slant and the plate at least 0.15 from the cavity wall, both against DESIGN.md figures the script transcribes, not against the constants the plate is built from, every cutout on its key and every head hole on its drill, moved by the pattern shift), then writes it upside down (top face on z = 0, so the pit opens upward) as one closed mesh.

## CI

`.github/workflows/ci.yml` has one job: it runs `check_layout.py`, builds the FreeCAD image, exports `kbdkid5_Pcb_Left.stl` and `kbdkid5_Pcb_Right.stl` (the word `right`) into `pcb/` and uploads them as the `pcb-stl` artifact, then exports the plate for both halves, plain and `covered`, into `plate/` (`kbdkid5_Plate_Left.stl`, `kbdkid5_Plate_Right.stl`, `kbdkid5_Plate_Left_Covered.stl`, `kbdkid5_Plate_Right_Covered.stl`) and uploads them as the `plate-stl` artifact. The job is still called `pcb-mock`. A failing layout check fails the job before any export.

## Running the exports

Locally this machine has podman, not docker:

    podman build -t freecad-headless -f scripts/freecad.Dockerfile scripts
    podman run --rm -v "$PWD":/work -w /work freecad-headless freecadcmd scripts/<script>.py --pass <out.stl> [words]
    python3 scripts/check_layout.py

The freecadcmd quirks (exit codes swallowed, `__name__` set to the file stem, scripts run twice, dash arguments intercepted even after `--pass`, hence `key=value` words and `os._exit` through `run_and_exit`) are documented in the module docstring of `scripts/freecad_common.py`. Read it before writing a FreeCAD script here. The machine has 8 GB RAM: run at most two FreeCAD containers at once.

## Conventions

- Commit and push completed changes without asking. Keep commits small and focused.
- `tmp/` is scratch space, `work/` holds untracked notes and downloads (the research's datasheets are in `work/research/downloads/`). Neither is committed.
- Test any change to an export script by running it in the container and checking the exit code; freecadcmd hides Python failures unless the script exits through `run_and_exit`.
- To inspect geometry beyond the exit code: `freecad_common.py`, `tray_shape.py`, `plate_shape.py` and `layout.py` import normally (put `scripts/` on `sys.path`), but the export scripts must be exec'd with their trailing `run_and_exit(main)` line stripped and `__file__` predefined (a plain import would run main and `os._exit` the interpreter). Then drive their functions directly.
- Keep DESIGN.md, README.md, this file, the work items' status and the comments in the scripts current in the same commit as the change. Decisions go in a new dated file in `doc/log/` (write once, tagged with `#topic`).
- Markdown: one paragraph per line, never reflowed.
