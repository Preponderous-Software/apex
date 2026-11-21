"""The simulation's HUD in both 3D views: the desktop window (app.py) and the
browser's (web.py).

simulationHud() lays out everything the 2D simulation screen shows besides
the board (its statistics, its location alerts, PAUSED and the version), what
the 2D window says in its title bar (the caption), the controls and a notice,
as screen labels and panels. The two 3D views differ only in what they pass
in. fitLabels() shrinks text too wide for a narrow window (a phone) so it
stays on screen. Pure Python: no Strata.
"""

from dataclasses import replace

from preponderous.graphik.grid3d import Label, Panel, fitText, measureText, wrapText

from screen.simulationScreen import PAUSED_HINT
from strata_view.scene import centredLabel, overlayFrom
from strata_view.ui import UiRect

TEXT = (0.97, 0.96, 0.92, 1.0)
DIM_TEXT = (0.82, 0.80, 0.74, 1.0)
HUD_PANEL = (0.0, 0.0, 0.0, 0.62)
# the statistics are black over the 2D window's brown board; over the 3D
# scene they are drawn light on a dark panel
STATS_TEXT = (0.97, 0.96, 0.92)

CAPTION_SIZE = 14
CONTROLS_SIZE = 11
CONTROLS_LINE = 18
NOTICE_SIZE = 16
PAUSED_SIZE = 26
PAUSED_HINT_SIZE = 12
PAUSED_HINT_LINE = 26
# the smallest text fitLabels() shrinks to
MIN_LABEL_SIZE = 8
EDGE_MARGIN = 8
# Below this width (a phone held upright) the caption may take the whole width
NARROW_WIDTH = 640


def fitLabels(labels, width, margin=EDGE_MARGIN):
    """The labels, each one too wide for the window shrunk (down to
    MIN_LABEL_SIZE) and moved so it stays inside it, about the same middle."""
    room = width - 2 * margin
    fitted = []
    for label in labels:
        wide = measureText(label.text, label.pixelSize)
        if wide <= room and margin <= label.x and label.x + wide <= width - margin:
            fitted.append(label)
            continue
        size = label.pixelSize
        if wide > room:
            characters = max(1, wide / float(label.pixelSize))
            size = max(MIN_LABEL_SIZE, room / characters)
        newWide = measureText(label.text, size)
        middleX = label.x + wide / 2.0
        middleY = label.y + label.pixelSize / 2.0
        x = min(max(margin, middleX - newWide / 2.0), max(margin, width - margin - newWide))
        fitted.append(Label(label.text, x, middleY - size / 2.0, size, label.color))
    return fitted


def wrapAtSeparators(line, maxWidth, pixelSize, separator=" | "):
    """A controls line wrapped between its controls (at " | ") rather than
    between words, so a key stays on the line with what it does and no line
    starts with a stray "|". A control too long for a line of its own is
    word-wrapped."""
    lines = []
    for part in line.split(separator):
        candidate = part if not lines else lines[-1] + separator + part
        if lines and measureText(candidate, pixelSize) <= maxWidth:
            lines[-1] = candidate
        elif measureText(part, pixelSize) <= maxWidth:
            lines.append(part)
        else:
            lines += wrapText(part, maxWidth, pixelSize)
    return lines


def textPanel(labels, padX=10, padY=6):
    """The dark panel behind a block of labels."""
    left = min(label.x for label in labels) - padX
    right = max(label.x + measureText(label.text, label.pixelSize) for label in labels) + padX
    top = min(label.y for label in labels) - padY
    bottom = max(label.y + label.pixelSize for label in labels) + padY
    return Panel(left, top, right - left, bottom - top, HUD_PANEL)


def pausedBox(width):
    """The PAUSED box's width and its hint's size in a window `width` wide."""
    hintSize = min(PAUSED_HINT_SIZE, (width - 64) / float(len(PAUSED_HINT)))
    boxWidth = max(len("PAUSED") * PAUSED_SIZE, len(PAUSED_HINT) * hintSize) + 48
    return boxWidth, hintSize


def alertsClearOf(items, area, height, gap=8):
    """Location alerts as the 2D screen drew them (each a UiRect, then its
    lines) with any whose box covers `area` (x, y, width, height: the PAUSED
    box) moved below it, or above it where there is no room below."""
    groups = []
    for item in items:
        if isinstance(item, UiRect) or not groups:
            groups.append([item])
        else:
            groups[-1].append(item)
    ax, ay, aw, ah = area
    out = []
    for group in groups:
        box = group[0] if isinstance(group[0], UiRect) else None
        shift = 0
        if box is not None and (box.x < ax + aw and box.x + box.width > ax
                                and box.y < ay + ah and box.y + box.height > ay):
            below = ay + ah + gap
            above = ay - gap - box.height
            if below + box.height <= height - EDGE_MARGIN:
                shift = below - box.y
            elif above >= EDGE_MARGIN:
                shift = above - box.y
        out += [replace(item, y=item.y + shift) if shift else item for item in group]
    return out


def simulationHud(width, height, caption, paused, statsItems=(), alertItems=(), controls=(),
                  notice=None, versionItems=(), captionTop=12, captionRight=None):
    """Labels and panels over the board. `statsItems`, `alertItems` and
    `versionItems` are what the 2D screen drew of its statistics (D), its
    location alerts and its version (strata_view.ui's recorder); `controls`
    the lines of the controls hint to show (none to hide it), wrapped to the
    window; `notice` a line to show for a while; `captionTop` where the
    caption's top is (the browser keeps its 2D/3D button above it), and
    `captionRight` where its right end must stay left of (the browser's
    2D/3D button beside it), if anywhere."""
    # the 2D window's title bar text, top right (the statistics take the top left)
    # On a narrow window (a phone) half the width cut it to "Apex - S...", losing the screen and
    # the grid size; there it may use the whole width, smaller, before anything is cut.
    # Beside the browser's 2D/3D button only the room left of it counts.
    captionSize = CAPTION_SIZE
    right = width - 16 if captionRight is None else min(width - 16, captionRight)
    if width < NARROW_WIDTH:
        room = right - EDGE_MARGIN
        captionSize = max(MIN_LABEL_SIZE, min(CAPTION_SIZE, room / float(max(1, len(caption)))))
        if len(caption) * captionSize > room:
            # fitText keeps an 18-pixel margin each side of what it is given
            caption = fitText(caption, room + 36, captionSize)
    else:
        caption = fitText(caption, width / 2, CAPTION_SIZE)
    labels = [Label(caption, right - len(caption) * captionSize, captionTop, captionSize, DIM_TEXT)]
    panels = []
    statLabels, _ = overlayFrom(statsItems, recolorBlack=STATS_TEXT)
    statLabels = fitLabels(statLabels, width)
    if statLabels:
        panels.append(textPanel(statLabels))
    labels += statLabels
    if paused and alertItems:
        # a location opened while paused keeps clear of PAUSED and how to resume
        boxWidth, _ = pausedBox(width)
        alertItems = alertsClearOf(alertItems, (width / 2 - boxWidth / 2, height / 2 - 30, boxWidth,
                                                60 + PAUSED_HINT_LINE), height)
    alertLabels, alertPanels = overlayFrom(alertItems)
    labels += alertLabels
    panels += alertPanels
    lines = []
    for line in controls:
        lines += wrapAtSeparators(line, width - 32, CONTROLS_SIZE)
    if lines:
        top = height - 40 - CONTROLS_LINE * len(lines)
        panels.append(Panel(8, top - 6, width - 16, CONTROLS_LINE * len(lines) + 10, HUD_PANEL))
        for index, line in enumerate(lines):
            labels.append(Label(fitText(line, width, CONTROLS_SIZE), 16, top + CONTROLS_LINE * index,
                                CONTROLS_SIZE, DIM_TEXT))
    if notice:
        labels.append(Label(fitText(notice, width, NOTICE_SIZE), 16, 34, NOTICE_SIZE, TEXT))
    if paused:
        # PAUSED and, under it, how to resume (as the 2D screen says)
        size = PAUSED_SIZE
        boxWidth, hintSize = pausedBox(width)
        panels.append(Panel(width / 2 - boxWidth / 2, height / 2 - 30, boxWidth, 60 + PAUSED_HINT_LINE,
                            HUD_PANEL))
        labels.append(centredLabel("PAUSED", width / 2, height / 2, size))
        labels.append(centredLabel(PAUSED_HINT, width / 2, height / 2 + PAUSED_HINT_LINE + 4, hintSize))
    versionLabels, _ = overlayFrom(versionItems)
    labels += fitLabels(versionLabels, width)
    return labels, panels
