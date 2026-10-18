from entity.rock import Rock


def test_name_isRock():
    assert Rock().getName() == "Rock"

def test_rock_isSolid():
    # ActionHandler.isLocationImpassible treats a location holding a solid entity as blocked
    assert Rock().isSolid() == True

def test_color_isAShadeOfGray():
    for _ in range(20):
        for channel in Rock().getColor():
            assert 100 <= channel < 110, channel
