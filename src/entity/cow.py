import random
from entity.grass import Grass
from entity.livingEntity import LivingEntity


# @author Daniel McCoy Stephenson
# @since July 31st, 2022
class Cow(LivingEntity):
    def __init__(self, name):
        # Cows are herbivores and grazers, so their diet is limited to plant matter (see RESEARCH.md, "Trophic energy transfer"; fixes #113).
        LivingEntity.__init__(self, name, (random.randrange(59, 61), random.randrange(41, 45), random.randrange(29, 33)), False, random.randrange(40, 50), [Grass], reproductiveRate=0.5)