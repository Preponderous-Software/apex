"""The 3D window's keys.

Strata reports SDL scancodes. Each is folded to the pygame key the 2D window
answers to, and handed to the 2D screen's own key handler
(SimulationScreen.handleKeyDownEvent), so a key does exactly the same thing in
both windows. The names are pygame's (K_d, K_SPACE, ...) so this module needs
no pygame import; tests/view3d checks that every key the 2D simulation screen
handles has a scancode here.
"""

# SDL scancode -> pygame key name
STRATA_SCANCODE_KEYS = {
    7: "K_d",  # D: statistics
    20: "K_q",  # Q: quit
    21: "K_r",  # R: back to setup
    6: "K_c",  # C: spawn a chicken
    19: "K_p",  # P: spawn a pig
    14: "K_k",  # K: spawn a cow
    26: "K_w",  # W: spawn a wolf
    9: "K_f",  # F: spawn a fox
    5: "K_b",  # B: spawn a rabbit
    48: "K_RIGHTBRACKET",  # ]: faster
    47: "K_LEFTBRACKET",  # [: slower
    15: "K_l",  # L: tick speed limit
    44: "K_SPACE",  # Space: pause
    41: "K_ESCAPE",  # Escape: pause
    25: "K_v",  # V: local view
    11: "K_h",  # H: highlight the oldest entity
    82: "K_UP",  # Up: widen the local view
    81: "K_DOWN",  # Down: narrow the local view
    68: "K_F11",  # F11: fullscreen
    16: "K_m",  # M: mute
    8: "K_e",  # E: eyes
}

# Shown in the simulation's HUD while it is paused and for its first seconds,
# in lines short enough to fit a 1280-pixel window.
STRATA_CONTROLS_HINT = (
    "Space/Esc pause | [ ] tick speed | L speed limit | D statistics | R setup | Q quit",
    "Spawn: C chicken | P pig | K cow | W wolf | F fox | B rabbit",
    "Click a location for its contents | V local view (Up/Down size) | H oldest | E eyes | M mute | F11 fullscreen",
)


def pygameKeyFor(scancode, pygameModule):
    """The pygame key constant for a Strata scancode, or None."""
    name = STRATA_SCANCODE_KEYS.get(scancode)
    if name is None:
        return None
    return getattr(pygameModule, name)

# The browser's 3D view (web.py) gets its keys from pygame itself, as the 2D
# canvas does, so it needs no key table; its hint names what a browser has:
# Q ends the simulation (a tab has nothing to quit to) and F11 is left to the
# browser.
WEB_CONTROLS_HINT = (
    "Space/Esc pause | [ ] tick speed | L speed limit | D statistics | R setup | Q results",
    "Spawn: C chicken | P pig | K cow | W wolf | F fox | B rabbit",
    "Tap or click a location for its contents | V local view (Up/Down size) | H oldest | E eyes | M mute",
)
