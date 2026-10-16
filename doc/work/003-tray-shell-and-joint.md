# 003 Tray shell and joint

Status: todo

`scripts/export_tray.py`, ported from kbdkid4's: walls, floor, ledge and standoffs on the layout's outline, the sockets' cuts, and the slanted joint (block, magnet pockets, dowel pin bosses). Both halves, in CI.

The sockets' cuts (DESIGN.md, "Tray") come from `scripts/layout.py`, which applies kbdkid4's rules to the sockets it names: `all_socket_tray_cuts()` gives the tab notches, the wall pockets behind them and the ledge reliefs as boxes in an outline edge's frame (`tray_cut_polygon()` in plan, a z range, `cuts_wall` set on the pockets), and `all_socket_standoff_flats()` the standoff flats. kbdkid4 measured its cuts along the straight stretches between the outline's corner rounds; these use the sharp edges. As on kbdkid4, every cut but the pockets is clipped to the cavity, so it never reaches the wall, and a cut that finds nothing left to remove (a tab's relief inside its notch) is skipped. `scripts/check_layout.py` checks the sockets against the tray with these cuts, so the export should cut exactly them.

The right half is not the left one mirrored where the sockets are: its switch footprints sit unmirrored at the mirrored key centers (DESIGN.md, "Frame and units"), so its sockets reach toward the slant. Measured with check_layout.py's own separation functions in the right half's frame (005 and its review): S150's socket overlaps the upper dowel boss (55.5 along the slant) by 1.641 in plan, over z 5.98 to 6.9, and comes 1.034 from the magnet slot at 46.9. The thumb's (S163) socket tab reaches 0.231 past the thumb's outer edge, where on the left half column 0's tabs reach past the west edge, so the right half's ledge reliefs are the bottom row's only. No socket comes within 1.0 of a standoff (closest 1.391), so the right half needs no standoff flats. check_layout.py has no right half checks yet, so it passes. To do here:

- The right tray gets its own socket cuts: a tab notch and wall pocket at the thumb's outer edge instead of column 0's, the bottom row's ledge reliefs, no standoff flats.
- A change at the upper dowel boss and the magnet slot at 46.9 to clear the right half's S150 socket. Which change depends on the PCB design's choice of the right half's footprint orientation.
- Right half checks in check_layout.py: the sockets against the tray as cut, the joint and the parking hole, as for the left half.
