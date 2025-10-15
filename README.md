# Apex
This game allows you to manage a virtual environment containing entities that depend on each other as sources of energy. A food chain arises from the configuration of various entities and their specified diets.

<img src="pics/screenshot4.PNG" alt="screenshot" width="720"/>

## UI Modes
Apex can be run in two different modes:

### Pygame GUI Mode (Default)
The standard graphical interface with visual representation of the ecosystem.
```bash
python src/apex.py
```

### Text-Based Mode
A lightweight console-based interface that visualizes the ecosystem using ASCII characters and displays simulation statistics. Features include:
- Real-time environment visualization with colored ASCII characters
- Non-blocking keyboard controls (same as GUI mode)
- Interactive spawning of entities
- Pause/resume, speed control, and debug mode

```bash
python src/apex.py --text
```

**Legend for Text Mode:**
- `.` = Grass (green)
- `x` = Excrement (yellow)
- `C` = Chicken (yellow)
- `P` = Pig (magenta)
- `K` = Cow (cyan)
- `W` = Wolf (red)
- `F` = Fox (red)
- `R` = Rabbit (white)

The text mode is ideal for:
- Running simulations on headless servers
- Lower resource consumption
- Remote SSH sessions
- Automated testing and analysis

## Types of Living Entities
- Chicken
- Pig
- Cow
- Wolf
- Fox
- Rabbit

Each of these attempt to gain energy and reproduce. At the bottom of the food chain is Grass, which chickens, pigs, cows and rabbits are able to eat.

If there is no grass, everything collapses. 

## How does grass respawn?
Living entities spawn excrement when their energy needs are met and this turns into grass over time.

## Controls

### Pygame GUI Mode
The following keyboard controls are available in **Pygame GUI Mode**:

Key | Action
------------ | -------------
space | pause/unpause
m | mute/unmute
h | highlight oldest living entity
v | toggle view (global/local)
up | increase view distance (in local view)
down | decrease view distance (in local view)
d | debug mode
c | spawn a chicken
p | spawn a pig
k | spawn a cow
w | spawn a wolf
f | spawn a fox
b | spawn a rabbit
l | toggle tick speed limit
] | increase tick speed (if enabled)
[ | decrease tick speed (if enabled)
f11 | toggle fullscreen mode
r | restart
q | quit

### Text-Based Mode
The following keyboard controls are available in **Text-Based Mode**:

Key | Action
------------ | -------------
space | pause/unpause
d | debug mode
c | spawn a chicken
p | spawn a pig
k | spawn a cow
w | spawn a wolf
f | spawn a fox
b | spawn a rabbit
l | toggle tick speed limit
] | increase tick speed (if enabled)
[ | decrease tick speed (if enabled)
q | quit

At this time, the user can pause/unpause, toggle the tick speed limit, increase/decrease the tick speed, manually spawn living entities, restart the simulation, enter debug mode and quit the application.

## Support
You can find the support discord server [here](https://discord.gg/49J4RHQxhy).

## Authors and acknowledgement
### Developers
Name | Main Contributions
------------ | -------------
Daniel Stephenson | Creator

## Inspiration
This project is based on [Kreatures](https://github.com/Stephenson-Software/Kreatures) and [Interakt](https://github.com/Stephenson-Software/Interakt).

## Libraries
This project makes use of [graphik](https://github.com/Preponderous-Software/graphik) and [py_env_lib](https://github.com/Preponderous-Software/py_env_lib).


## Screenshots

<img src="pics/screenshot2.PNG" alt="screenshot2" width="400"/>
<img src="pics/screenshot3.PNG" alt="screenshot3" width="400"/>

## Sounds
- Pop sound source: https://mixkit.co/free-sound-effects/pop/
- Death sound source: https://soundbible.com/1454-Pain.html
