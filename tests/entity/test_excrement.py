from entity.excrement import Excrement


def test_name_isExcrement():
    assert Excrement(0).getName() == "Excrement"

def test_excrement_isNotSolid():
    assert Excrement(0).isSolid() == False

def test_getTick_returnsTheCreationTick():
    # Simulation subtracts this from the current tick to decide when excrement becomes grass
    assert Excrement(42).getTick() == 42

def test_excrement_hasNoEnergy():
    # unlike Grass and Berries, Excrement isn't food
    assert hasattr(Excrement(0), "getEnergy") == False

def test_color_isAShadeOfBrown():
    for _ in range(20):
        red, green, blue = Excrement(0).getColor()
        assert 135 <= red < 145, red
        assert 65 <= green < 75, green
        assert 15 <= blue < 25, blue
