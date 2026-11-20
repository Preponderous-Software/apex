"""Renders each Apex screen with the 3D Strata window, headless, to PNGs.

Runs the real screens and a real simulation from a fixed seed: the main
menu, setup, the simulation (fresh, after some ticks, with statistics, with a
location's alert, paused, in local view, with the oldest entity highlighted)
and the results screen.

    python3 tools/strata_snapshot.py --out shots/

Usage reporting is off and sound is silent while it runs.
"""

import argparse
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
os.environ.setdefault("DO_NOT_TRACK", "1")
os.environ.setdefault("TRACE_USAGE_REPORTING", "off")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
if sys.platform.startswith("linux"):
    # Linux renders headless through EGL with no window. On Windows, Strata's
    # headless engine is a hidden SDL window, which the dummy driver can't make.
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


class _Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default="strata-shots")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--ticks", type=int, default=120)
    parser.add_argument("--grid-size", type=int, default=0, help="0 keeps the random size")
    args = parser.parse_args(argv)

    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    random.seed(args.seed)
    os.chdir(ROOT)  # the screens read version.txt from the working directory

    import pygame
    from screen.screenType import ScreenType
    from strata_view.app import StrataApex
    from strata_view.renderer import StrataRenderer

    renderer = StrataRenderer(args.width, args.height, window=False)
    clock = _Clock()

    def shot(name):
        app.renderFrame(present=False)
        path = os.path.join(out, "apex-3d-%s.png" % name)
        renderer.savePng(path)
        print(path)

    try:
        app = StrataApex(renderer=renderer, clock=clock)
        shot("01-main-menu")
        app.goTo(ScreenType.SETUP_SCREEN)
        if args.grid_size:
            app.config.gridSize = args.grid_size
        shot("02-setup")
        app.goTo(ScreenType.SIMULATION_SCREEN)
        screen = app.simulationScreen
        shot("03-simulation-start")
        for _ in range(args.ticks):
            clock.now += 1.0
            app.advance()
            if app.currentScreen is not screen:
                break
        clock.now += 60  # past the controls hint
        shot("04-simulation-ticks")
        screen.handleKeyDownEvent(pygame.K_d)
        shot("05-statistics")
        screen.handleKeyDownEvent(pygame.K_d)
        # click the first living entity's tile, as a player would
        from strata_view.scene import cameraFor, cellScreenPosition

        grid = screen.simulation.environment.getGrid()
        entity = screen.simulation.entities[screen.simulation.livingEntityIds[-1]]
        location = grid.getLocation(entity.getLocationID())
        camera = cameraFor(grid.getColumns(), grid.getRows(), app.width, app.height)
        at = cellScreenPosition(camera, location.getX(), location.getY(),
                                grid.getColumns(), grid.getRows(), app.width, app.height)
        app.handleClick(at)
        clock.now += 1.0
        app.advance()
        shot("06-location-alert")
        screen.handleKeyDownEvent(pygame.K_SPACE)
        shot("07-paused")
        screen.handleKeyDownEvent(pygame.K_SPACE)
        screen.handleKeyDownEvent(pygame.K_v)
        shot("08-local-view")
        screen.handleKeyDownEvent(pygame.K_v)
        screen.handleKeyDownEvent(pygame.K_h)
        screen.handleKeyDownEvent(pygame.K_e)
        shot("09-oldest-highlighted-no-eyes")
        screen.handleKeyDownEvent(pygame.K_e)
        screen.handleKeyDownEvent(pygame.K_h)
        # every living entity gone: the screen ends and shows the results
        for entityId in list(screen.simulation.livingEntityIds):
            screen.simulation.removeEntity(screen.simulation.entities[entityId])
        clock.now += 5.0
        app.advance()
        clock.now += 5.0
        app.advance()
        shot("10-results")
        times = app.frameMs
        print("render ms per frame: first %.1f, median %.1f" % (times[0], sorted(times)[len(times) // 2]))
    finally:
        renderer.close()


if __name__ == "__main__":
    main()
