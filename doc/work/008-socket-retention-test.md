# 008 Socket retention test strips

Status: implemented

The user asked whether the keyboard could be fully hand wired, with no PCB, still with hotswap sockets "in some slot or rig where the hotswap socket lays firmly", and "paramount that the keyboard still is very rigid and that the switches doesn't jiggle around when typing". The idea: the fused mock's PCB layer becomes the switch frame, 1.6 thick so the pins reach the sockets as through a PCB, with each socket in a pocket on its underside, screwed to the tray's standoffs where the PCB would be. A switch pulled out pulls its socket up into the pocket's ceiling, which the print takes. A switch pushed in pushes the socket down and away from the frame, which a PCB's solder joints take, so something must hold the socket from below. The user's order to try: "a backing piece first, then maybe lip, and lastly glue. We might need a combination."

Decided with the user: the backing is a separate piece fastened with M2 screws into heat-set inserts in the frame, like the tray's standoffs. The cells carry no plate, like the second slit strip, so only the socket's hold is felt. The strips are stackable: they share one cell pattern and screw pattern, so the backing goes under either frame strip and any pocket can be glued, and combinations need no strip of their own. The socket is sized from the STEP figures in `layout.py` (no caliper figures yet), with the pocket's fit varied across cells.

Three strips of six cells, cell k with k notches:

- Pocket strip: the switch layer with the hotswap footprint's holes and a socket pocket under each cell, its fit stepping across the cells. Glue goes into any of them.
- Lip strip: the same, at one pocket fit, with lips at the pocket's mouth that the socket snaps past, their reach stepping across the cells.
- Backing strip: a plate screwed under either frame strip, pressing each socket up, its pressure stepping across the cells.

Done: `scripts/export_socket_test.py` exports the three strips (`pocket`, `lip`, `backing`), built by `scripts/socket_test_shape.py`. The pockets go around the socket's plastic body as kbdkid4's STEP and Kailh's drawing give it, at the body's height from the drawing rather than the STEP's reach. A wire goes on each tab before the socket is pressed in, through a slot open at the pocket's mouth. Each lip sits at the free end of a finger freed by slots and held at its root by the plate and a block under it, like the tray's snap hook, and the export fails if a finger strains over the hook's 2 %. `lip_fit` sets the lip strip's pocket fit to what the pocket strip shows. In CI as `kbdkid5_Socket_Test_Pocket.stl`, `kbdkid5_Socket_Test_Lip.stl` and `kbdkid5_Socket_Test_Backing.stl` in the `mock-stl` artifact. DESIGN.md ("Hand-wired frame test") has the figures and the order to print the strips in.

Still open: the print itself. Which fit, lip or pad holds a socket firm against typing and a switch pressed in, whether the fingers' slots print open and the lips snap in, and whether the pins still make contact deeper than through a PCB if the ceiling prints risen (if not, the plate's thickness is the figure to change). For a real frame, DESIGN.md lists what the battery and the tray's reliefs still need.
