# 003 Tray shell and joint

Status: todo

`scripts/export_tray.py`, ported from kbdkid4's: walls, floor, ledge and standoffs on the layout's outline, the sockets' cuts, and the slanted joint (block, magnet pockets, dowel pin bosses). Both halves, in CI.

The sockets' cuts (DESIGN.md, "Tray") come from `scripts/layout.py`, which applies kbdkid4's rules to the sockets it names: `all_socket_tray_cuts()` gives the tab notches, the wall pockets behind them and the ledge reliefs as boxes in an outline edge's frame (`tray_cut_polygon()` in plan, a z range, `cuts_wall` set on the pockets), and `all_socket_standoff_flats()` the standoff flats. kbdkid4 measured its cuts along the straight stretches between the outline's corner rounds; these use the sharp edges. As on kbdkid4, every cut but the pockets is clipped to the cavity, so it never reaches the wall, and a cut that finds nothing left to remove (a tab's relief inside its notch) is skipped. `scripts/check_layout.py` checks the sockets against the tray with these cuts, so the export should cut exactly them.
