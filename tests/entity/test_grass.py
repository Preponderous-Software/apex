from entity.grass import Grass


def test_name_isGrass():
    assert Grass().getName() == "Grass"

def test_grass_isNotSolid():
    assert Grass().isSolid() == False

def test_energy_isWithinRange():
    # randrange's upper bound is exclusive
    for _ in range(20):
        energy = Grass().getEnergy()
        assert 10 <= energy < 20, energy

def test_color_isAShadeOfGreen():
    for _ in range(20):
        red, green, blue = Grass().getColor()
        assert red == 0
        assert 130 <= green < 170, green
        assert blue == 0
