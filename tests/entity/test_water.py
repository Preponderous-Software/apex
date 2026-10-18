from entity.water import Water


def test_name_isWater():
    assert Water().getName() == "Water"

def test_water_isSolid():
    # ActionHandler.isLocationImpassible treats a location holding a solid entity as blocked
    assert Water().isSolid() == True

def test_color_isFixed():
    assert Water().getColor() == (66, 194, 229)
