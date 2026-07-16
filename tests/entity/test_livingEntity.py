from entity.chicken import Chicken
from entity.cow import Cow
from entity.fox import Fox
from entity.grass import Grass
from entity.pig import Pig
from entity.rabbit import Rabbit
from entity.wolf import Wolf


def test_cow_cannotEatOtherCows():
    # a herbivore shouldn't be able to prey on its own trophic level (RESEARCH.md,
    # "Trophic energy transfer"; fixes #113)
    cow = Cow("test cow")
    otherCow = Cow("other cow")

    assert cow.canEat(otherCow) == False
    assert cow.canEat(Grass()) == True

def test_reproductiveRate_defaultsToNeutral():
    cow = Cow("test cow")
    assert cow.getReproductiveRate() == 0.5

def test_reproductiveRate_rSelectedSpeciesAreHigherThanKSelectedSpecies():
    # r/K selection theory (RESEARCH.md): small prey with short lifespans should have a
    # higher reproductive rate than large, long-lived apex predators.
    rabbit = Rabbit("test rabbit")
    chicken = Chicken("test chicken")
    pig = Pig("test pig")
    fox = Fox("test fox")
    cow = Cow("test cow")
    wolf = Wolf("test wolf")

    assert rabbit.getReproductiveRate() > chicken.getReproductiveRate() > pig.getReproductiveRate()
    assert pig.getReproductiveRate() > fox.getReproductiveRate() > cow.getReproductiveRate() > wolf.getReproductiveRate()
