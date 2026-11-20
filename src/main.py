"""Entry point of the browser build (pygbag), which packages src/ and runs its main.py.
The desktop game still starts from src/apex.py (run.sh); both run the same async loop,
Apex.run.

In a browser the game is WebApex: the same 2D game, which also draws itself in the page's
3D view when the player turns that on (strata_view/web.py). Its files are downloaded only
then.
"""

import asyncio
import sys

import pygame  # noqa: F401  (pygbag installs the packages main.py imports)

from apex import Apex


def chooseGame(platform=None):
    """The game class to run: WebApex in a browser, so the page's 3D toggle works; Apex
    anywhere else, or when graphik's 3D view isn't in the build (then the toggle is marked
    unavailable, with the reason)."""
    platform = sys.platform if platform is None else platform
    if platform != "emscripten":
        return Apex
    try:
        from strata_view.web import WebApex
    except ImportError as error:
        print("No 3D view in this build:", error)
        try:
            from preponderous.graphik.grid3d.web import set3D

            set3D(False, "this build has no 3D view")
        except ImportError:
            pass
        return Apex
    return WebApex


async def main():
    await chooseGame()().run()


asyncio.run(main())
