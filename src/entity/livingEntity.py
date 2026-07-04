import random
from entity.drawableEntity import DrawableEntity



# @author Daniel McCoy Stephenson
# @since August 5th, 2022
class LivingEntity(DrawableEntity):
    MALE = 0
    FEMALE = 1
    
    def __init__(self, name, color, solid, energy, edibleEntityTypes, reproductiveRate=1.0):
        DrawableEntity.__init__(self, name, color, solid)
        self.energy = energy
        self.edibleEntityTypes = edibleEntityTypes
        self.targetEnergy = energy
        self.sex = random.choice([LivingEntity.MALE, LivingEntity.FEMALE])
        # Multiplier on the base chance to reproduce, modeling where this species sits on the
        # r/K selection spectrum (see RESEARCH.md, "r/K selection theory"): > 1.0 for r-selected
        # species (many offspring, short investment), < 1.0 for K-selected species (few offspring,
        # high investment per offspring).
        self.reproductiveRate = reproductiveRate
    
    def getEnergy(self):
        return self.energy

    def addEnergy(self, amount):
        self.energy += amount
    
    def removeEnergy(self, amount):
        self.energy -= amount

    def needsEnergy(self):
        return self.energy < self.targetEnergy

    def canEat(self, entity):
        for entityType in self.edibleEntityTypes:
            if type(entity) is entityType:
                return True
        return False

    def getSex(self):
        return self.sex

    def getReproductiveRate(self):
        return self.reproductiveRate