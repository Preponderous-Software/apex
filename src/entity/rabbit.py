import random
from entity.berries import Berries
from entity.grass import Grass
from entity.livingEntity import LivingEntity


# @author Daniel McCoy Stephenson
# @since August 2nd, 2022
class Rabbit(LivingEntity):
    def __init__(self, name):
        # Textbook r-strategist: the highest reproduction rate in the ecosystem (RESEARCH.md, "r/K selection theory").
        LivingEntity.__init__(self, name, (250,220,200), False, random.randrange(20, 30), [Grass, Berries], reproductiveRate=2.5)