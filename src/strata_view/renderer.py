"""Draws grid3d Scenes with Strata, through graphik's 3D grid view.

graphik's Grid3DView (preponderous.graphik.grid3d, the `graphik[strata]`
extra) owns the Strata engine: it loads libstrata (a released build pinned by
SHA-256, or STRATA_LIBRARY for a local one) and draws a Scene. Strata ships
Linux and Windows x64 builds, so this view is desktop-only (no macOS, no
browser).
"""


def _openView(width, height, window, title):
    """A graphik Grid3DView, or ImportError (the binding or graphik's grid3d
    is missing) / RuntimeError (anything else) with a plain reason."""
    try:
        from preponderous.graphik.grid3d import Grid3DView, Unavailable
    except ImportError:
        raise ImportError("graphik's 3D grid view (preponderous.graphik.grid3d) isn't installed")
    try:
        return Grid3DView.open(width, height, title, headless=not window)
    except Unavailable as reason:
        if "isn't installed" in str(reason):
            raise ImportError(str(reason))
        raise RuntimeError(str(reason))


class StrataRenderer:
    """Owns one Strata engine (a window or a headless surface)."""

    def __init__(self, width=1280, height=720, window=False, title="Apex"):
        self.view = _openView(width, height, window, title)
        self.strata, self.lib, self.engine = self.view.strata, self.view.lib, self.view.engine
        self.width, self.height = width, height
        self.isWindow = window

    def close(self):
        self.view.close()

    def resize(self, width, height):
        self.width, self.height = width, height
        self.view.resize(width, height)

    def pollEvents(self):
        return self.view.pollEvents()

    def setFullscreen(self, enabled):
        """Switches the window to desktop fullscreen or back. Returns False
        when the loaded Strata has no strata_set_fullscreen (0.7.0 hasn't)."""
        setter = getattr(self.engine, "set_fullscreen", None)
        if setter is None or not self.lib.has("strata_set_fullscreen"):
            return False
        setter(bool(enabled))
        return True

    def setTitle(self, title):
        """Sets the window title. Returns False when the loaded Strata can't
        (0.7.0 sets it only when the window opens)."""
        setter = getattr(self.engine, "set_title", None)
        if setter is None or not self.lib.has("strata_set_title"):
            return False
        setter(title)
        return True

    def draw(self, scene, present=True):
        self.view.drawScene(scene, present=present)

    def savePng(self, path):
        self.view.savePng(path)
