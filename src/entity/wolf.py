import random

from entity.chicken import Chicken
from entity.cow import Cow
from entity.fox import Fox
from entity.livingEntity import LivingEntity
from entity.pig import Pig
from entity.rabbit import Rabbit


# @author Daniel McCoy Stephenson
# @since July 27th, 2022
class Wolf(LivingEntity):
    def __init__(self, name):
        # Apex predator: the most K-selected species, matching its larger energy pool and scarcer numbers (RESEARCH.md, "r/K selection theory" and "Trophic energy transfer").
        LivingEntity.__init__(self, name, (145, random.randrange(145, 155), random.randrange(145, 155)), False, random.randrange(100, 200), [Chicken, Pig, Cow, Fox, Rabbit], reproductiveRate=0.4)