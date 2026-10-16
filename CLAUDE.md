# CLAUDE.md

Guidance for Claude Code working in this repository.

## What this is

kbdkid5, the successor of kbdkid4 (`~/dev/kbdkid4`, https://github.com/Tubbles/kbdkid4): a wireless split keyboard whose 3D-printed parts (tray, switch plate, PCB mock) are built by FreeCAD scripts in `scripts/`, running headless in a container. [DESIGN.md](DESIGN.md) holds the design and every dimension, [doc/components.md](doc/components.md) the part research with sources, [PLAN.md](PLAN.md) the phases, `doc/work/` the work items with their status, `doc/log/` dated decision logs.

There is no PCB design yet (the user does it later in LibrePCB). Until then `scripts/layout.py` is the ground truth for the geometry: keys, outline, mounting drills, the parts in the tray and the joint. It is plain Python with no FreeCAD import, so `scripts/check_layout.py` can check it anywhere. The export scripts read it. When DESIGN.md and `layout.py` disagree, that is a bug in one of them: fix it, don't pick one silently.

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
- To inspect geometry beyond the exit code: `freecad_common.py`, `tray_shape.py` and `layout.py` import normally (put `scripts/` on `sys.path`), but the export scripts must be exec'd with their trailing `run_and_exit(main)` line stripped and `__file__` predefined (a plain import would run main and `os._exit` the interpreter). Then drive their functions directly.
- Keep DESIGN.md, README.md, this file, the work items' status and the comments in the scripts current in the same commit as the change. Decisions go in a new dated file in `doc/log/` (write once, tagged with `#topic`).
- Markdown: one paragraph per line, never reflowed.
