# 010 Heavy duty nice!nano bay

Status: implemented

The user printed the 006/009 bay test strip: "It needs a lot of improvements." The floor grooves under the pin rows and the shell's tabs go: "Remove all those recesses, they're completely unneccesary since _the nano is absolutely flat on its underside_. There is nothing sticking out downwards." The side ribs "are just miniscule tabs. Make them tall, thick walls that really cover the nano", and in general "make the cradle more of a heavy duty pocket in an extrusion, rather than tiny lips that's not helping at all, they're just weak when being 3d printed", "Think simple, big features". The caliper: "The nano measures, with the usb connector included: 18.30 x 34.17". doc/log/2026-10-19.md has the whole exchange.

Decided with the user: a slip-fit pocket on a flat floor, a thick east wall in place of the ribs, the bar and its posts one block across the pocket, the clamp's boss widened into a block across the pocket that takes in the standoff beside it. A lip along the west wall, which the user offered, is left out, since the board goes in nose first and its south end comes down past where such a lip would stand. Then the user asked for a foot as tall as the board: the 0.5 foot gave "no rigidity when pushing in a cable as it is right now, the foot is so low the nano simply pops up onto it, even with the clamp screwed in", and chose it fixed in the tray over one on the tab: "I prefer option A so the nano is seated really solidly". The old pry recess beside the board's east edge then had nothing left to do and went. After the foot went to 1.6, the user asked for a new way out: "Can you open up a 5 mm pry slot in the south wall with a pry recess in the floor to go along with it? So I can pry with e.g. a toothpick".

Implemented:

- The board is 18.30 wide (the caliper), its length still the render's 33.3 board (34.17 less the render's 0.87 of shell), x 0.9 to 19.2, the USB window and the shell's channel on its center line at x 10.05. The floor under it is flat. The grooves, the ribs, the bar's posts and the old pry recess with every check for them are gone.
- The pocket is the board's slip fit across (`nano_pocket_fit`, default 0.1, a `MountFits` field and a key=value override of `export_tray.py`), 18.8 from the west ledge's face at x 0.6 to the east wall's inner face at x 19.4.
- The east wall runs from x 19.4 to 21.5 (the battery's northwest rib merges into it), z 0 to 4.0, from the clamp block north to y 65.3, where it meets the PCB connector's zone as printed.
- The north block lies across the pocket from y 75.566 to 75.886, z 0 to 4.96, over the ledge cut-away's width (x 0.4 to 19.7, the board's width plus 0.5 each side), with the shell's opening through it and its bar over the shell.
- The clamp block runs x 0.6 to 21.5, y 32.616 to 38.416, z 0 to 3.6, bored for the insert, and takes in the standoff at (18.574, 37.782), which keeps its bore. The foot runs on north to y 41.766, 1.6 tall (the board's height), across the pocket.
- The tab is 10.9 long and reaches 1.5 onto the board, its nose 0.5 to 1.5 from the board's south end, 0.35 from the foot as printed. The arm is 5.115, the strain 0.69 % as printed.
- Going in, the board's south face passes the foot 0.06 clear as printed at its closest (2.75 degrees), checked in `check_layout.py`. As printed the foot's face and the block's face stand 33.4 apart, so a board longer than 33.36 cannot be tilted in. The board's length is derived, not measured, and `nano_length` resizes the bay if a board will not go in.
- The pry slot is 5.0 wide (x 1.6 to 6.6), through the clamp block and the foot from the floor up, open above. The pry recess runs under it in the floor from y 32.616 to 2.0 under the board (44.016), 0.8 deep, 0.4 of floor left. A 2.0 toothpick with a round point on its axis, tapering over 5.0, coming down the slot from over the south rim, clears the rim and the south ledge as printed at 17.4 degrees at the least and then gets its point 1.09 under the board (`check_layout.py`). On the test bay, which has no south wall, it can come in much flatter. Lifted at its south end, the board pitches up rather than rolling about its east edge: it turns about the shell's mouth while its north end's top edge rides up the north block's face, so it slides south a little, its south edge staying clear of the foot's face, or it pivots on the shell's top against the bar. Its whole south end comes up over the foot, and it slides south out of the shell's channel.
- The test bay is a single bay at the default slip fit, the press and the bar's clearance at their defaults, with the slot and recess. The strip first built for this item stepped the pocket's fit 0.1, 0.2 and 0.3 over three bays, and the user chose a single bay to shorten the print. `BAY_FITS` can step fits again.

DESIGN.md (the nice!nano's bullets) has the figures.

Open:

- Print the test bay and find whether the slip fit seats the board: whether it goes in, and whether it is loose, snug or tight across.
- Whether a USB-C cable goes in with the board held solidly by the foot and the tab.
- Whether the toothpick lifts the board out as worked out, on the test bay and in a whole tray, where it has to come in over the rim.
- The rest of the tray's mounts in the same spirit: the user said the heavy duty approach "probably goes for the rest of the details in the tray".
