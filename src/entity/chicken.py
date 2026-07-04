import random
from entity.berries import Berries
from entity.grass import Grass
from entity.livingEntity import LivingEntity


# @author Daniel McCoy Stephenson
# @since July 7th, 2022
class Chicken(LivingEntity):
    def __init__(self, name):
        # r-selected: small-bodied prey species, high reproduction (RESEARCH.md, "r/K selection theory").
        LivingEntity.__init__(self, name, (random.randrange(245, 249), random.randrange(245, 249), random.randrange(245, 249)), False, random.randrange(20, 30), [Grass, Berries], reproductiveRate=2.0)