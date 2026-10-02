import random

from entity.berries import Berries
from entity.berryBush import BerryBush
from entity.chicken import Chicken
from entity.cow import Cow
from entity.excrement import Excrement
from entity.fox import Fox
from entity.grass import Grass
from entity.livingEntity import LivingEntity
from entity.pig import Pig
from entity.rabbit import Rabbit
from entity.rock import Rock
from entity.water import Water
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

def test_needsEnergy_isFalseAtStartBecauseTargetEnergyIsTheStartingEnergy():
    entity = LivingEntity("test entity", (0, 0, 0), False, 30, [Grass])

    assert entity.getEnergy() == 30
    assert entity.needsEnergy() == False

def test_removeEnergy_belowTargetMeansTheEntityNeedsEnergy():
    entity = LivingEntity("test entity", (0, 0, 0), False, 30, [Grass])

    entity.removeEnergy(1)

    assert entity.getEnergy() == 29
    assert entity.needsEnergy() == True

def test_addEnergy_backToTargetMeansTheEntityNoLongerNeedsEnergy():
    entity = LivingEntity("test entity", (0, 0, 0), False, 30, [Grass])
    entity.removeEnergy(5)

    entity.addEnergy(5)

    assert entity.getEnergy() == 30
    assert entity.needsEnergy() == False

def test_addEnergy_isNotCappedAtTargetEnergy():
    entity = LivingEntity("test entity", (0, 0, 0), False, 30, [Grass])

    entity.addEnergy(15)

    assert entity.getEnergy() == 45
    assert entity.needsEnergy() == False

def test_removeEnergy_canGoBelowZero():
    entity = LivingEntity("test entity", (0, 0, 0), False, 1, [Grass])

    entity.removeEnergy(3)

    assert entity.getEnergy() == -2

def test_reproductiveRate_defaultsToOneWhenNotGiven():
    entity = LivingEntity("test entity", (0, 0, 0), False, 30, [Grass])

    assert entity.getReproductiveRate() == 1.0

def test_canEat_isFalseForAnEmptyDiet():
    entity = LivingEntity("test entity", (0, 0, 0), False, 30, [])

    assert entity.canEat(Grass()) == False

def test_canEat_matchesTheExactTypeOnly():
    # canEat compares type(entity) with `is`, so a subclass of an edible type isn't edible
    class TallGrass(Grass):
        pass

    entity = LivingEntity("test entity", (0, 0, 0), False, 30, [Grass])

    assert entity.canEat(Grass()) == True
    assert entity.canEat(TallGrass()) == False

def test_getSex_isMaleOrFemale():
    random.seed(0)
    sexes = set()
    for _ in range(50):
        sexes.add(LivingEntity("test entity", (0, 0, 0), False, 30, [Grass]).getSex())

    assert sexes == {LivingEntity.MALE, LivingEntity.FEMALE}

def test_livingEntities_areNotSolid():
    for species in [Chicken, Pig, Cow, Wolf, Fox, Rabbit]:
        assert species("test").isSolid() == False

def test_diets_matchTheFoodChain():
    # who eats what, as README.md's "Types of Living Entities" describes it
    edible = {
        Chicken: [Grass, Berries],
        Pig: [Grass, Berries, BerryBush],
        Cow: [Grass],
        Wolf: [Chicken, Pig, Cow, Fox, Rabbit],
        Fox: [Chicken, Pig, Rabbit],
        Rabbit: [Grass, Berries],
    }
    candidates = [
        Grass(),
        Berries(),
        BerryBush(),
        Excrement(0),
        Rock(),
        Water(),
        Chicken("prey"),
        Pig("prey"),
        Cow("prey"),
        Wolf("prey"),
        Fox("prey"),
        Rabbit("prey"),
    ]

    for species, diet in edible.items():
        eater = species("test")
        for candidate in candidates:
            expected = type(candidate) in diet
            assert eater.canEat(candidate) == expected, (species.__name__, type(candidate).__name__)

def test_noSpeciesEatsItsOwnKind():
    for species in [Chicken, Pig, Cow, Wolf, Fox, Rabbit]:
        assert species("test").canEat(species("other")) == False

def test_startingEnergy_isWithinEachSpeciesRange():
    # randrange's upper bound is exclusive
    ranges = {
        Chicken: (20, 30),
        Pig: (30, 40),
        Cow: (40, 50),
        Wolf: (100, 200),
        Fox: (50, 100),
        Rabbit: (20, 30),
    }

    for species, (low, high) in ranges.items():
        for _ in range(20):
            energy = species("test").getEnergy()
            assert low <= energy < high, (species.__name__, energy)
