# 001 PCB mock and the layout module

Status: implemented

`scripts/layout.py` holds DESIGN.md's geometry as data. `scripts/check_layout.py` checks it without FreeCAD. `scripts/export_pcb.py` exports the printed PCB mock for both halves. CI runs the check and the export.
