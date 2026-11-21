"""The simulation's HUD in both 3D views: the desktop window (app.py) and the
browser's (web.py).

simulationHud() lays out everything the 2D simulation screen shows besides
the board (its statistics, its location alerts, PAUSED and the version), what
the 2D window says in its title bar (the caption), the controls and a notice,
as screen labels and panels. The two 3D views differ only in what they pass
in. fitLabels() shrinks text too wide for a narrow window (a phone) so it
stays on screen. Pure Python: no Strata, no pygame.
"""

from preponderous.graphik.grid3d import Label, Panel, fitText, measureText, wrapText

from strata_view.scene import centredLabel, overlayFrom

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
# the smallest text fitLabels() shrinks to
MIN_LABEL_SIZE = 8
EDGE_MARGIN = 8


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


def simulationHud(width, height, caption, paused, statsItems=(), alertItems=(), controls=(),
                  notice=None, versionItems=(), captionTop=12):
    """Labels and panels over the board. `statsItems`, `alertItems` and
    `versionItems` are what the 2D screen drew of its statistics (D), its
    location alerts and its version (strata_view.ui's recorder); `controls`
    the lines of the controls hint to show (none to hide it), wrapped to the
    window; `notice` a line to show for a while; `captionTop` where the
    caption's top is (the browser keeps its 2D/3D button above it)."""
    # the 2D window's title bar text, top right (the statistics take the top left)
    caption = fitText(caption, width / 2, CAPTION_SIZE)
    labels = [Label(caption, width - 16 - len(caption) * CAPTION_SIZE, captionTop, CAPTION_SIZE, DIM_TEXT)]
    panels = []
    statLabels, _ = overlayFrom(statsItems, recolorBlack=STATS_TEXT)
    statLabels = fitLabels(statLabels, width)
    if statLabels:
        panels.append(textPanel(statLabels))
    labels += statLabels
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
        size = PAUSED_SIZE
        boxWidth = len("PAUSED") * size + 48
        panels.append(Panel(width / 2 - boxWidth / 2, height / 2 - 30, boxWidth, 60, HUD_PANEL))
        labels.append(centredLabel("PAUSED", width / 2, height / 2, size))
    versionLabels, _ = overlayFrom(versionItems)
    labels += fitLabels(versionLabels, width)
    return labels, panels
