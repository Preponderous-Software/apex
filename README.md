# Apex
This game allows you to manage a virtual environment containing entities that depend on each other as sources of energy. A food chain arises from the configuration of various entities and their specified diets.

<img src="pics/screenshot4.PNG" alt="screenshot" width="720"/>

## Types of Living Entities
- Chicken
- Pig
- Cow
- Wolf
- Fox
- Rabbit

Each of these attempt to gain energy and reproduce. At the bottom of the food chain is Grass, which chickens, pigs, cows and rabbits are able to eat.

Berry bushes are a second food source. A bush that has accumulated enough energy periodically grows Berries on its own location, up to a cap. Chickens, pigs and rabbits eat berries; pigs can also eat the bush itself. Cows eat grass only.

If there is no grass, everything collapses. 

## How does grass respawn?
Living entities spawn excrement when their energy needs are met and this turns into grass over time.

## Controls
Key | Action
------------ | -------------
space / escape | pause/unpause
m | mute/unmute
h | highlight oldest living entity
e | toggle entity eyes
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

At this time, the user can pause/unpause, toggle the tick speed limit, increase/decrease the tick speed, manually spawn living entities, restart the simulation, enter debug mode and quit the application.

## Usage reporting
Usage reporting is on by default: Apex sends its name (`apex`), the version from `version.txt` and the events `startup` (when the game starts) and `simulation-started` (when a simulation begins) to [trace](https://github.com/Stephenson-Software/trace) at `https://trace.danielstephenson.dev`. Nothing about you, your machine, your IP address or the simulation's contents is sent. The reporting happens on a background thread, never blocks the game, and is dropped silently if the service is unreachable.

The first run creates a `settings.json` next to `version.txt` and prints a one-line notice. To turn reporting off, any one of these is enough:

- `"usage_reporting": {"enabled": false}` in `settings.json`:

  ```json
  {
      "usage_reporting": {
          "enabled": false
      }
  }
  ```

- the environment variable `TRACE_USAGE_REPORTING=off` (also `false`, `0`, `no`), which turns off every program that reports to trace
- the environment variable `DO_NOT_TRACK=1` (see [consoledonottrack.com](https://consoledonottrack.com))

The environment variables win over `settings.json`. The `usage_reporting.endpoint` and `usage_reporting.key` entries in the same block select where reports go and the key they are sent with.

Details: https://github.com/Stephenson-Software/trace#usage-reporting

## Research
See [RESEARCH.md](RESEARCH.md) for the ecological and artificial-life research this simulator's mechanics are grounded in, and how to use it when designing new features.

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

## 📄 License

This project is licensed under the **Preponderous Non-Commercial License (Preponderous-NC)**.  
It is free to use, modify, and self-host for **non-commercial** purposes, but **commercial use requires a separate license**.

> **Disclaimer:** *Preponderous Software is not a legal entity.*  
> All rights to works published under this license are reserved by the copyright holder, **Daniel McCoy Stephenson**.

Full license text:  
[https://github.com/Preponderous-Software/preponderous-nc-license/blob/main/LICENSE.md](https://github.com/Preponderous-Software/preponderous-nc-license/blob/main/LICENSE.md)
