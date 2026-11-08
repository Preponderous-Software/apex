import os
import runpy
from unittest.mock import AsyncMock, patch

import apex

MAIN_PATH = os.path.join(os.path.dirname(apex.__file__), "main.py")


# src/main.py is the browser (pygbag) entry point: importing it runs the game.
def test_mainRunsOneApexApplicationToCompletion():
    with patch("apex.Apex") as apexClass:
        apexClass.return_value.run = AsyncMock()
        runpy.run_path(MAIN_PATH)

    apexClass.assert_called_once_with()  # the browser build never records (no --record there)
    apexClass.return_value.run.assert_awaited_once()

def test_mainRunsTheApplicationInsideAsyncioRun():
    with patch("apex.Apex") as apexClass, \
            patch("asyncio.run", side_effect=lambda coroutine: coroutine.close()) as asyncioRun:
        runpy.run_path(MAIN_PATH)

    asyncioRun.assert_called_once()
    assert asyncioRun.call_args.args[0].__qualname__ == "main"
    apexClass.assert_not_called()  # the application is only built once the loop runs main()
