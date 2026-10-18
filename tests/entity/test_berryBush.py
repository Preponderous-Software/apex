from entity.berryBush import BerryBush


def test_name_isBerryBush():
    assert BerryBush().getName() == "BerryBush"

def test_berryBush_isNotSolid():
    assert BerryBush().isSolid() == False

def test_energy_isWithinRange():
    # randrange's upper bound is exclusive
    for _ in range(20):
        energy = BerryBush().getEnergy()
        assert 10 <= energy < 20, energy

def test_color_isFixed():
    assert BerryBush().getColor() == (34, 139, 34)

def test_tick_startsAtOne():
    assert BerryBush().getTick() == 1

def test_incrementTick_addsOneEachCall():
    # Simulation compares getTick() against berryBushGrowTime to decide when to spawn berries
    berryBush = BerryBush()

    berryBush.incrementTick()
    berryBush.incrementTick()

    assert berryBush.getTick() == 3

def test_incrementTick_doesNotChangeEnergy():
    berryBush = BerryBush()
    energy = berryBush.getEnergy()

    berryBush.incrementTick()

    assert berryBush.getEnergy() == energy
