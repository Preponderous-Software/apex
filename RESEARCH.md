# Research

Apex is a grid-based predator-prey simulator: entities move, eat, excrete, reproduce and die according to simple local rules, and a food chain emerges from how those rules are wired together (see `src/entity/*.py` for diets and `src/simulation/simulation.py` for the tick loop). This document connects that design to the existing body of research it resembles, so that future changes (rewrites, new species, difficulty/leveling, smarter movement, etc.) can be grounded in prior art instead of reinvented from scratch.

It is a guide, not a spec — use it to sanity-check new mechanics against how the same problem has been studied or solved elsewhere, and to find search terms when a mechanic needs more rigor than "seemed to work in testing."

## 1. How Apex's model maps to existing research

### 1.1 Predator-prey population dynamics (Lotka-Volterra)

The classic mathematical model of predator-prey populations (Lotka, 1925; Volterra, 1926) describes prey growth, predation loss, predator growth from consumption, and predator death, as a pair of coupled differential equations. Apex doesn't implement these equations directly, but its rules produce the same feedback loop discretely: `Wolf`/`Fox` populations only grow when prey (`Chicken`/`Pig`/`Rabbit`/`Cow`) are abundant enough to sustain `chanceToReproduce` (`src/simulation/config.py`), and prey populations only grow when `Grass`/`Berries` are abundant.

Why it matters for Apex: Lotka-Volterra systems are known to oscillate or collapse depending on parameter ratios (growth rate, predation rate, energy-per-meal). The current constants (energy ranges, `chanceToReproduce = 0.02`, `chanceToExcrete = 0.10`) were hand-tuned by playtesting; when retuning them (or adding new species), treat it as a parameter-stability problem, not just "does it feel right" — e.g. check whether a change pushes any species toward guaranteed extinction or unbounded growth across many simulated ticks, the same way you'd check a Lotka-Volterra parameterization for a stable limit cycle vs. a runaway.

Reference: Lotka, A.J. (1925), *Elements of Physical Biology*; Volterra, V. (1926), "Variazioni e fluttuazioni del numero d'individui in specie animali conviventi."

### 1.2 Trophic energy transfer ("the 10% rule")

Lindeman's trophic-dynamic model (1942) formalized the observation that only a fraction (commonly cited as ~10%) of energy at one trophic level is available to the next — most is lost to metabolism and heat. Apex encodes trophic levels directly in `LivingEntity.edibleEntityTypes` (`Grass`/`Berries` → `Chicken`/`Pig`/`Rabbit`/`Cow` → `Wolf`/`Fox`) and gives each level a wider energy budget than the one below it (e.g. `Grass`/`Berries` energy 10–20, `Chicken`/`Rabbit` 20–30, `Wolf` 100–200 in `src/entity/*.py`).

Why it matters: this is the real-world justification for why apex predators must be rarer and costlier to sustain than herbivores — it's not an arbitrary balance knob. When adding a new trophic level (an issue like #85's "level system" or new predators) it's worth keeping each level's energy pool and reproduction cost roughly consistent with the energy-loss pattern already established, rather than picking numbers that only look reasonable in isolation.

Reference: Lindeman, R.L. (1942), "The trophic-dynamic aspect of ecology," *Ecology* 23(4).

### 1.3 Agent-based ecosystem models: NetLogo Wolf Sheep Predation

Apex's architecture (grid world, `Grass` that regrows over time, `Wolf`/`Sheep`-equivalents that move, eat, lose energy per tick, and reproduce probabilistically) is structurally the same model as NetLogo's **Wolf Sheep Predation** model (Wilensky, 1997, based on Lotka-Volterra and instructional agent-based modeling from Uri Wilensky's group at Northwestern). That model is one of the most widely used teaching examples of emergent ecosystem dynamics from local agent rules, and its accompanying documentation is a good source of tunable-parameter intuition (e.g. what happens when grass regrowth time or predator gain-from-food is varied) that transfers almost directly to Apex's `grassGrowTime`, `berryBushGrowTime`, and per-species energy gain.

Why it matters: rather than re-deriving stability behavior from scratch, NetLogo's model (and its "Explore" exercises) is a ready-made reference for what knobs cause collapse vs. oscillation vs. steady state, since it's the same category of model with the same category of parameters.

Reference: Wilensky, U. (1997), *NetLogo Wolf Sheep Predation model*, Center for Connected Learning and Computer-Based Modeling, Northwestern University. https://ccl.northwestern.edu/netlogo/models/WolfSheepPredation

### 1.4 Sugarscape and emergent agent societies

Epstein & Axtell's *Growing Artificial Societies* (1996) introduced Sugarscape: agents on a grid that move toward and consume a regrowing resource, accumulate/spend energy ("sugar"), reproduce when conditions are met, and die when energy is depleted — the same primitive loop as Apex's `moveActionHandler` / `eatActionHandler` / `reproduceActionHandler` / energy decay in `simulation.py`. Sugarscape is the canonical reference for "simple local rules produce complex emergent population/social behavior," and its extensions (seasons, disease, trade, inheritance, sexual reproduction with genetic traits) are a natural source of ideas for Apex issues like #84 ("player-created species") and #85 ("level system").

Reference: Epstein, J.M. & Axtell, R. (1996), *Growing Artificial Societies: Social Science from the Bottom Up*, Brookings Institution Press / MIT Press.

### 1.5 Cellular automata and emergence

Conway's Game of Life (Gardner, 1970, popularizing Conway's work) is the conceptual ancestor of any grid-of-cells simulation where next-state depends only on local neighborhood rules. Apex differs in giving cells persistent, stateful agents rather than binary alive/dead cells, but the "simple local rule, complex global behavior" framing — and the general lesson that small rule changes can qualitatively change global behavior (e.g. from stable oscillators to total die-off) — applies directly and is worth keeping in mind before tweaking action-handler logic.

Reference: Gardner, M. (1970), "Mathematical Games: The fantastic combinations of John Conway's new solitaire game 'life'," *Scientific American* 223.

### 1.6 Artificial life platforms

Broader Alife research is directly relevant to where Apex's design could go next (procedurally generated or evolved species per issue #84):

- **Tierra** (Ray, 1991) and **Avida** (Ofria & Wilke, 2004): digital organisms that evolve via mutation and selection rather than being hand-authored, showing that species traits (energy needs, diet, reproduction rate) can emerge from evolutionary pressure instead of fixed per-class constants like Apex's current `Chicken`/`Wolf`/etc. classes.
- **Polyworld** (Yaeger, 1994) and **Framsticks** (Komosinski, 2000): agents with evolvable genomes controlling both morphology and behavior in a simulated ecosystem, closely resembling what a "player creates their own species" feature would need — a genome/trait schema, mutation, and fitness pressure via the existing energy/reproduction loop.

References: Ray, T.S. (1991), "An approach to the synthesis of life," in *Artificial Life II*; Ofria, C. & Wilke, C.O. (2004), "Avida: A software platform for research in computational evolutionary biology," *Artificial Life* 10(2); Yaeger, L. (1994), "Computational genetics, physiology, metabolism, neural systems, learning, vision, and behavior or Polyworld: Life in a new context," in *Artificial Life III*; Komosinski, M. (2000), "The world of Framsticks: Simulation, evolution, interaction," in *Virtual Worlds and Simulation*.

### 1.7 Optimal foraging theory

Apex's movement (`src/actionhandler/moveActionHandler.py`) is currently undirected/random rather than seeking food or mates. Optimal foraging theory (MacArthur & Pianka, 1966; Charnov's Marginal Value Theorem, 1976) models how real animals decide what to pursue and when to give up on a patch, trading off search cost against energy gain. If movement is ever made "smarter" (an obvious next step once #117's untested action handlers are covered), this is the standard framework for what "smarter" should mean, and gives testable predictions (e.g. entities should prefer denser food patches, and should leave a depleted patch sooner as its density drops) rather than an ad hoc heuristic.

References: MacArthur, R.H. & Pianka, E.R. (1966), "On optimal use of a patchy environment," *American Naturalist* 100; Charnov, E.L. (1976), "Optimal foraging, the marginal value theorem," *Theoretical Population Biology* 9(2).

### 1.8 r/K selection theory

r/K selection theory (MacArthur & Wilson, 1967; Pianka, 1970) describes a spectrum from species that produce many offspring with low individual investment and short lifespans (r-selected, e.g. rabbits) to species that produce few offspring with high investment and long lifespans (K-selected, e.g. large predators). Apex's species already sit on an implicit version of this spectrum — `Rabbit` has low energy (20–30) and presumably faster population turnover, `Wolf` has high energy (100–200) and is comparatively rare — but reproduction chance (`chanceToReproduce`) is currently a single global constant shared by every species. If per-species reproduction/lifespan tuning is added, r/K selection is the theory to model it after, rather than tuning each species' numbers independently by feel.

Reference: MacArthur, R.H. & Wilson, E.O. (1967), *The Theory of Island Biogeography*; Pianka, E.R. (1970), "On r- and K-selection," *American Naturalist* 104.

### 1.9 Detritus, decomposition, and nutrient cycling

Real ecosystems return energy to primary producers via a detritus/decomposer pathway (dead matter and waste broken down by decomposers into nutrients that plants use), not just direct photosynthesis (Swift, Heal & Anderson, 1979). Apex's `Excrement` → `Grass` mechanic (`shouldExcrementTurnIntoGrass` in `simulation.py`, gated by `grassGrowTime`) is a simplified version of exactly this nutrient cycle, and open issue #67 ("make excrement turn into grass only if near water") and #69 ("excrement not turning into grass sometimes") are both, in effect, requests to make the decomposition model closer to how real nutrient cycling depends on moisture and decomposer activity.

Reference: Swift, M.J., Heal, O.W. & Anderson, J.M. (1979), *Decomposition in Terrestrial Ecosystems*, Blackwell Scientific.

## 2. How to use this document

- When tuning existing constants in `src/simulation/config.py` or per-species energy/diet values, check §1.1–1.2 (Lotka-Volterra, trophic energy transfer) for whether a change is likely to destabilize the food chain, not just whether it "feels" right in one playtest.
- When adding a new species or trophic level, use §1.2 and §1.8 (energy transfer, r/K selection) to place it in the existing energy/reproduction spectrum rather than picking arbitrary numbers.
- When working on the database-centric rewrite (#106) or any architecture change, §1.3–1.4 (NetLogo Wolf Sheep Predation, Sugarscape) are the closest existing reference implementations of this exact class of simulation, and their published parameter-sensitivity discussions can save re-deriving stability behavior from scratch.
- When designing player-created species (#84) or a difficulty/level system (#85), §1.6 (artificial life platforms) is the relevant prior art for genome/trait schemas and evolutionary pressure, and §1.7 (optimal foraging) is the relevant prior art if entity movement becomes goal-directed instead of random.
- This document should be updated as new mechanics are added — treat it as a living index of "what research backs this feature," not a one-time write-up.
