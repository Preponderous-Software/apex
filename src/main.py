"""Entry point of the browser build (pygbag), which packages src/ and runs its main.py.
The desktop game still starts from src/apex.py (run.sh); both run the same async loop,
Apex.run.
"""

import asyncio

import pygame  # noqa: F401  (pygbag installs the packages main.py imports)

from apex import Apex


async def main():
    await Apex().run()


asyncio.run(main())
