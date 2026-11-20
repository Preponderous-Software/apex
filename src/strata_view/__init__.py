"""Apex's 3D window, drawn with Strata (desktop Linux and Windows).

keys.py and ui.py need neither Strata nor graphik's 3D grid view: they are the
3D window's key table and a stand-in for graphik that records what the 2D
screens draw, so the 3D window shows the 2D screens' own buttons and readouts.
scene.py maps a running simulation to 3D shapes (graphik's grid3d package,
still pure Python); renderer.py draws them with Strata; app.py runs Apex in a
Strata window. On Linux and Windows `python3 src/apex.py` opens it by default
and falls back to the 2D window, saying why, when Strata can't start (`--2d`
skips it). tools/strata_snapshot.py renders each screen headless to PNGs.
"""


class StrataUnavailable(Exception):
    """The 3D window can't start here: graphik's 3D grid view or the
    strata-engine package is missing, the Strata library couldn't be loaded,
    or no window could be opened. The message says which, in plain words."""
