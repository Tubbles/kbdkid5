# kbdkid5 design

kbdkid5 is the successor of [kbdkid4](https://github.com/Tubbles/kbdkid4): a wireless split keyboard (Kailh Choc v1 on hotswap sockets, 19.05 mm pitch, a nice!nano v2 and a LiPo per half, ZMK), with a 3D-printed tray and switch plate. Its two changes:

1. **Nothing but the switch matrix on the PCB.** The PCB carries only the hotswap sockets, the diodes and one off-board connector. The nice!nano, the reset button, the power switch and the battery connector are wired with loose wires and mounted in the tray itself. The tray can then use the space under the PCB, and the half gets smaller.
2. **A slanted inner edge to join the halves.** The tray, PCB and plate are cut straight from the thumb key's top right corner to the rightmost top row key's top right corner. The two halves join along that slant with magnets and steel dowel pins into one Alice-like board (each half turned 17.7 degrees, rows dipping toward the middle), firm enough to type on in the lap.

The PCB itself is designed later (LibrePCB). Until then the geometry here is the ground truth, held in `scripts/layout.py`, and the PCB is a printed mock. Part choices and their sources are in [doc/components.md](doc/components.md).

## Frame and units

Millimetres. The left half in kbdkid4's board coordinates: x east, y north, the board's top side (keys) up, heights z above the tray floor's top face (the floor's underside is at z -1.2). The right half is the left half mirrored across x, apart from the joint's dowel holes (see below).

## Keys

25 per half, on kbdkid4's grid (from kbdkid4's `boards/board_1.1/board.lp`, names as there):

| Column | x | Rows (y, top to bottom) |
|---|---|---|
| 0 (S100 to S103) | 9.049 | 66.357, 47.307, 28.257, 9.207 |
| 1 (S110 to S113) | 28.099 | same as column 0 |
| 2 (S120 to S123) | 47.149 | 71.120, 52.070, 33.020, 13.970 |
| 3 (S130 to S133) | 66.199 | 73.501, 54.451, 35.401, 16.351 |
| 4 (S140 to S143) | 85.249 | same as column 2 |
| 5 (S150 to S153) | 104.299 | 68.739, 49.689, 30.639, 11.589 |
| thumb (S163) | 123.349 | 9.207 |

Each key's cell is 19.05 square around its center. Footprints sit as on kbdkid4's left half (rotation 90 degrees, top side), so each hotswap socket hangs 2.02 below the PCB over x from center - 9.28 to center + 3.87 and y from center - 8.22 to center - 1.37 (kbdkid4's measured socket polygons, `HOTSWAP_SOCKET_POLYGONS_MM`). Under every key, the north part of the cell (y above center - 1.37) and the east strip (x above center + 3.87) are free of sockets. The diodes sit on the top side under the plate, as on kbdkid4.

## Outline

kbdkid4's outline (cells inset 0.476 at the west, 0.318 at the south, 0.397 at the north, corners rounded 0.476), with the microcontroller corner replaced by the slant:

    (0, 0) (37.624, 0) (37.624, 4.763) (56.674, 4.763) (56.674, 7.144) (75.724, 7.144)
    (75.724, 4.763) (94.774, 4.763) (94.774, 2.381) (113.824, 2.381) (113.824, 0)
    (132.398, 0) (132.398, 18.335)                        east edge of the thumb, inset 0.476
    (113.348, 77.867)                                     the slant
    (94.774, 77.867) (94.774, 80.248) (75.724, 80.248) (75.724, 82.629) (56.674, 82.629)
    (56.674, 80.248) (37.624, 80.248) (37.624, 75.486) (0, 75.486)

The slant runs from (132.398, 18.335) to (113.348, 77.867): the thumb cell's top right corner (132.874, 18.732) and column 5's top cell's top right corner (113.824, 78.264), both moved in by the outline's insets, so it is parallel to the corner to corner line and 0.574 inside it. Its direction is (-19.05, 59.532): 62.51 long, 17.74 degrees from north. The half is 132.4 x 82.6, kbdkid4's was 134.6 x 82.6.

## Mounting

Five 2.4 mm drills, M2 screws into heat-set inserts in tray standoffs, as on kbdkid4: (18.574, 18.732), (18.574, 37.782), (76.041, 43.260), (94.774, 60.404), (114.141, 19.765). kbdkid4's (18.574, 56.832) moved one row down to (18.574, 37.782), the cell corner of S101, S102, S111 and S112, since the nice!nano now lies under it.

## Heights

| | z |
|---|---|
| Tray floor underside (the 1.0 rubber sole goes under it) | -1.2 |
| Battery top (4.11 thick) | 4.11 |
| Socket bottoms, 1.87 above the battery | 5.98 |
| PCB underside, standoff and ledge tops | 8.0 |
| PCB top (1.6) | 9.6 |
| Plate top (2.2, resting on the PCB) | 11.8 |
| Tray rim, 0.1 above the plate as on kbdkid4 | 11.9 |

The standoff height stays kbdkid4's 8.0 for this first iteration (the user's choice): room for padding and margin around the parts. The lowest it could go is battery 4.11 + clearance 0.5 + socket 2.02 = 6.63. The tray is 13.1 tall, like kbdkid4's. Tray walls 0.8, gap to the PCB edge 0.4, floor 1.2, ledge 1.0 wide, standoffs 5.8 across with 3.2 bores, all as kbdkid4.

## Parts in the tray

Envelopes below are bodies only. Wires need room behind every lead.

### nice!nano v2 (northwest corner)

- Board 33.3 x 18.0 x 1.6 (measured on the manufacturer's render, unconfirmed by caliper), its flat underside on the floor, the USB end north, wires soldered on its top side only.
- x 0.9 to 18.9 (0.3 from the west ledge's face), y 42.016 to 75.316. The USB-C shell (8.94 wide, 3.16 tall, z 0 to 3.16, flush with the board's underside) reaches 0.87 past the board's north end, so its mouth lies 0.5 behind the north wall's outer face, as on kbdkid4.
- USB window: kbdkid4's 10.5 x 4.5 window (corners rounded 1.95, faces chamfered 0.2), centered on the shell (x 9.9, z 1.58), so its bottom edge cuts 0.67 into the floor. The north ledge is cut away over the nano's width.
- Held down at the USB end by a bar over the shell's top (0.1 clear), just inside the north wall, no wider than the shell plus 0.5, so it stays off the B+ and B- pads at the end's corners, which carry wires.
- Held down at the far end by a snap hook over the middle of the board's south edge: the last 5.8 of the board's top side carries no parts or pads across its middle 13.7. The hook's lip reaches 0.8 onto the board. The hook stands on a blade that flexes along y: a vertical blade on the bed, free of the floor on three sides by a slot, rooted at one end, at least 10 long so the bending strain stays under 2 % for PLA. The hook's top stays 0.3 under the S101 socket above it (z 5.68).
- Located sideways by the west ledge's face and low ribs (1.0 tall) along the east edge, which touch only the board's side face.
- Shallow grooves (0.4 deep) in the floor under the two pin rows, B+ and B-, the P1.01/P1.02/P1.07 row and the shell's tab slots, so solder that runs through the plated holes cannot lift the board.

### Power switch (column 2's north wall)

- SOFNG SS-12D00-G3: body 8.8 (x, the lever's travel) x 3.9 (z) x 3.5 (y), lever 1.5 x 1.5 x 3 on the body's north face, three 3.0 pins pointing south.
- Centered at x 47.149, its north face against the cavity wall (y 80.648), z 0 to 3.9. The lever passes a 4.0 (x) x 2.0 (z) slot through the wall and stands 2.2 proud of the outer face, so a fingertip flips it.
- A cradle on the floor holds the body's ends against the 3.5 N slide force. The north ledge is cut away over the switch.

### Reset button (column 3's north wall)

- C&K PTS636 SL43 LFS: body 6.0 x 3.5, 4.3 to the stem's top, stem 3 x 1.5, two 3.9 leads, 130 gf.
- Lying on its side, centered at x 66.199: 6.0 along x, 3.5 along z (z 0 to 3.5), the stem facing north and ending 0.2 short of the cavity wall (y 83.029). A 3.0 hole through the wall over the stem (kbdkid4's plate reset hole is 3.0 too) for a SIM pin. The leads point south.
- A back wall behind the body, slotted for the leads, takes the press.

### Battery connector (column 4's north strip)

- JST PH B2B-PH-K-S (top entry) laid on its side: 5.9 along y, 4.5 along z, 6.0 along x, the plug entering from the west, the 3.4 posts pointing east for the wires. Mated, plug and header are 4.5 tall.
- Header x 85.0 to 91.0, y 72.55 to 78.45. The pocket holds the header's front shoulders, since the plug pulls out toward the west, which PH plugs resist hard.

### Battery

- 34.37 x 51.53 x 4.11 pouch, its lead (about 66 with a PH plug) leaving one corner.
- x 22.0 to 56.37, y 5.9 to 57.43, lying under the sockets of columns 1 and 2 with 1.87 of clearance, its lead's corner at the northeast (turn the pouch over to put it there), about 32 from the connector's plug.
- Located by low L-shaped ribs at its corners (1.0 tall, 0.5 clear).

### PCB connector (kept clear)

The PCB's off-board connector is the PCB design's choice, recommended a JST SH SM12B-SRSS-TB side-entry header on the underside, 2.95 deep with its plug. The tray keeps column 1's north strip clear for it: x 20.0 to 37.0, y 65.5 to 75.0, no tray feature above z 0 there. That is next to the nano's east pin row.

## The joint

The slanted tray wall is the joint face. Joined, the two halves' outer slant faces touch, each half turned 17.74 degrees.

- **Block:** below the PCB, the slanted wall is 4.0 thick (normal to the face) from the floor up to the ledge top (z 8.0), replacing the ledge there. The PCB rests on it.
- **Magnets:** five supermagnete S-08-03-N (8 x 3, N45) per half, axis normal to the face, standing on edge in slots open at the block's top (8.2 along the slant, 3.1 across, from z -0.7 up, leaving a 0.5 skin at the face and 0.5 above the bed), so each magnet drops in from above with no overhang to print and the PCB covers it. They are spread evenly along the slant, at least 5 from its ends and clear of the pins. Glue them with alternating poles along the joint, the right half opposite to the left, so the halves pull together and center themselves. Two 0.5 skins leave a 1.0 gap between opposing magnets: about 6.0 N per pair after derating (doc/components.md), about 30 N in all. That only closes the joint. It cannot carry the bending of lap use.
- **Dowel pins:** two hardened ISO 8734 4 x 24 pins, normal to the face, at z 3.4 (midway between the bed and the PCB), at the slant's y 26 and y 58 (about 33.6 apart along it), 12 embedded in each half. They carry the bending and the shear. Each sits in a boss (7 across) reaching 12.2 from the outer face into the tray, clear of the sockets above (the upper one passes between S150's and S151's sockets, the lower one 1.4 from the standoff at (114.141, 19.765)). The holes are teardrops, since they print horizontal. The left half's are sized to glue the pins in, the right half's to slide on them.

## Plate and PCB mock

- **Plate:** kbdkid4's plate pipeline. The kbdkid3 plate model's switch cells are aligned onto the keys above by a pure translation, trimmed 0.4 at the outer edges. The plate covers the switch-free triangle between column 5, the thumb key and the slant, its slanted edge at the outline's slant plus 0.35, like kbdkid4's covered corner reached 0.35 past the board edge. It gets head clearance holes at the mounting drills, and kbdkid4's print corrections (`pattern_shift` 0.25, `side_shave` 0.1) and its `covered` variant (S123 filled, a pit for D123). There are no lead recesses or reset hole, since nothing on the PCB is through-hole any more and the reset button sits in the north wall.
- **PCB mock:** kbdkid4's replica. The outline above moved in by 0.2, each key's holes from kbdkid4's Choc hotswap footprint (`KHA-PG1350` in kbdkid4's library) and the mounting drills moved out by 0.2, 1.6 thick. Switches clip into it for a feel, but there are no sockets.

## Parts to buy (both halves)

- 2 SOFNG SS-12D00-G3 slide switches (LCSC C22355741).
- 2 C&K PTS636 SL43 LFS tactile switches.
- 2 JST B2B-PH-K-S headers, plus PHR-2 housings and SPH-002T-P0.5S contacts if a battery lead needs re-terminating.
- 10 supermagnete S-08-03-N disc magnets.
- 2 hardened ISO 8734 (or DIN 6325 m6) 4 x 24 dowel pins.
- M2 heat-set inserts and screws as on kbdkid4.
