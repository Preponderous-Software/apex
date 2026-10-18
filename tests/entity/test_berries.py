from entity.berries import Berries


def test_name_isBerries():
    assert Berries().getName() == "Berries"

def test_berries_areNotSolid():
    assert Berries().isSolid() == False

def test_energy_isWithinRange():
    # randrange's upper bound is exclusive
    for _ in range(20):
        energy = Berries().getEnergy()
        assert 10 <= energy < 20, energy

def test_color_isFixed():
    assert Berries().getColor() == (75, 0, 130)
