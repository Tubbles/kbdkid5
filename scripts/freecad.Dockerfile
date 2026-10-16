# Headless FreeCAD for the export scripts in scripts/, used both locally
# (podman) and in CI (docker), for example the PCB mock:
#
#     docker build -t freecad-headless -f scripts/freecad.Dockerfile scripts
#     docker run --rm -v "$PWD":/work -w /work freecad-headless \
#         freecadcmd scripts/export_pcb.py --pass <mock.stl> [right]
#
# Debian trixie ships FreeCAD 1.x; freecad-python3 is the GUI-less subset
# that provides /usr/bin/freecadcmd.
FROM debian:trixie-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends freecad-python3 \
    && rm -rf /var/lib/apt/lists/*
