# Plan

The goal: a smaller wireless split keyboard than kbdkid4 that also joins into one Alice-like board, firm enough for the lap. See [DESIGN.md](DESIGN.md).

1. **Printed mock (now).** Tray, PCB mock and plate for both halves from `scripts/layout.py`, to get a feel for size, height and the joined angle, and the fused mock (PCB mock and plate in one print) to mount switches in. Work items in [doc/work/](doc/work/).
2. **Fit check with real parts.** Measure a nice!nano with a caliper (the outline, holes and the underside are unconfirmed, see doc/components.md), fit the switch, reset button, battery connector, battery, magnets and dowel pins in a printed tray, and correct the layout.
3. **PCB design** in LibrePCB: sockets, diodes and the off-board connector on the outline, keys and mounting drills of the layout.
4. **Switch the exports to the PCB's STEP**, the way kbdkid4's scripts read its board, so the PCB design becomes the ground truth.
5. **Carrying case**, following kbdkid4's.
