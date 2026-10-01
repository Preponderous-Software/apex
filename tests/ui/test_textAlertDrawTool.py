from unittest.mock import MagicMock, call

from ui.textAlert import TextAlert
from ui.textAlertDrawTool import TextAlertDrawTool


# helper methods -------------------------------------------------------------
def getTestGraphik(width=1280, height=720):
    graphik = MagicMock()
    graphik.gameDisplay.get_width.return_value = width
    graphik.gameDisplay.get_height.return_value = height
    return graphik

def getTestAlert(x, y, lines, size=20):
    alert = TextAlert(x, y, size, (0, 0, 0), 10)
    for line in lines:
        alert.addLine(line)
    return alert

# initialization tests -------------------------------------------------------
def test_initialization():
    # execute
    drawTool = TextAlertDrawTool()

    # assert
    assert drawTool.backgroundColor == (255, 255, 255)
    assert drawTool.backgroundWidth == 250

# prepareBackground tests ----------------------------------------------------
def test_prepareBackground_drawsAWhiteRectangleBehindTheText():
    # prepare
    drawTool = TextAlertDrawTool()
    graphik = getTestGraphik()
    alert = getTestAlert(200, 300, ["a", "b", "c"], size=20)

    # execute
    backgroundHeight = drawTool.prepareBackground(alert, graphik, 3)

    # assert
    assert backgroundHeight == 20 * 3 + 20
    graphik.drawRectangle.assert_called_once_with(200 - 20 * 6, 300 - 20, 250, 80, (255, 255, 255))

# drawTextAlert tests --------------------------------------------------------
def test_drawTextAlert_drawsEachLineTwentyPixelsApart():
    # prepare
    drawTool = TextAlertDrawTool()
    graphik = getTestGraphik()
    alert = getTestAlert(200, 300, ["first", "second"], size=20)

    # execute
    drawTool.drawTextAlert(alert, graphik)

    # assert
    assert graphik.drawText.call_args_list == [
        call("first", 200, 300, 20, (0, 0, 0)),
        call("second", 200, 320, 20, (0, 0, 0)),
    ]

def test_drawTextAlert_leavesAnOnScreenAlertInPlace():
    # prepare
    drawTool = TextAlertDrawTool()
    graphik = getTestGraphik()
    alert = getTestAlert(200, 300, ["line"])

    # execute
    drawTool.drawTextAlert(alert, graphik)

    # assert
    assert (alert.x, alert.y) == (200, 300)

def test_drawTextAlert_movesAnAlertOverflowingTheBottomEdgeUp():
    # prepare
    drawTool = TextAlertDrawTool()
    graphik = getTestGraphik(height=720)
    alert = getTestAlert(200, 700, ["a", "b"])

    # execute
    drawTool.drawTextAlert(alert, graphik)

    # assert
    assert alert.y == 720 - 20 * 2 - 20

def test_drawTextAlert_movesAnAlertOverflowingTheRightEdgeLeft():
    # prepare
    drawTool = TextAlertDrawTool()
    graphik = getTestGraphik(width=1280)
    alert = getTestAlert(1200, 300, ["a"])

    # execute
    drawTool.drawTextAlert(alert, graphik)

    # assert
    assert alert.x == 1280 - 250

def test_drawTextAlert_clampsANegativeYToZero():
    # prepare
    drawTool = TextAlertDrawTool()
    graphik = getTestGraphik()
    alert = getTestAlert(200, -50, ["a"])

    # execute
    drawTool.drawTextAlert(alert, graphik)

    # assert
    assert alert.y == 0

def test_drawTextAlert_keepsTheBackgroundOnScreenAtTheLeftEdge():
    # prepare
    drawTool = TextAlertDrawTool()
    graphik = getTestGraphik()
    alert = getTestAlert(10, 300, ["a"], size=20)

    # execute
    drawTool.drawTextAlert(alert, graphik)

    # assert
    assert alert.x == 20 * 6

def test_drawTextAlert_drawsTheBackgroundAtTheClampedPositionOnTheRightEdge():
    # prepare
    drawTool = TextAlertDrawTool()
    graphik = getTestGraphik(width=1280)
    alert = getTestAlert(1200, 300, ["a"], size=20)

    # execute
    drawTool.drawTextAlert(alert, graphik)

    # assert
    graphik.drawRectangle.assert_called_once_with(1280 - 250 - 20 * 6, 300 - 20, 250, 40, (255, 255, 255))
    graphik.drawText.assert_called_once_with("a", 1280 - 250, 300, 20, (0, 0, 0))

def test_drawTextAlert_drawsTheBackgroundAtTheClampedPositionOnTheBottomEdge():
    # prepare
    drawTool = TextAlertDrawTool()
    graphik = getTestGraphik(height=720)
    alert = getTestAlert(200, 700, ["a", "b"], size=20)

    # execute
    drawTool.drawTextAlert(alert, graphik)

    # assert
    clampedY = 720 - 20 * 2 - 20
    graphik.drawRectangle.assert_called_once_with(200 - 20 * 6, clampedY - 20, 250, 60, (255, 255, 255))
    assert graphik.drawText.call_args_list[0] == call("a", 200, clampedY, 20, (0, 0, 0))

def test_drawTextAlert_drawsTheBackgroundBeforeTheText():
    # prepare
    drawTool = TextAlertDrawTool()
    graphik = getTestGraphik()
    alert = getTestAlert(200, 300, ["a"])

    # execute
    drawTool.drawTextAlert(alert, graphik)

    # assert
    drawCalls = [name for name, _, _ in graphik.method_calls if name in ("drawRectangle", "drawText")]
    assert drawCalls == ["drawRectangle", "drawText"]
