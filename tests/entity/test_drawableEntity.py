from entity.drawableEntity import DrawableEntity


def test_getColor_returnsTheColorItWasGiven():
    entity = DrawableEntity("test entity", (1, 2, 3), False)

    assert entity.getColor() == (1, 2, 3)

def test_isSolid_returnsTheSolidityItWasGiven():
    assert DrawableEntity("test entity", (0, 0, 0), True).isSolid() == True
    assert DrawableEntity("test entity", (0, 0, 0), False).isSolid() == False

def test_getName_isPassedThroughToTheBaseEntity():
    entity = DrawableEntity("test entity", (0, 0, 0), False)

    assert entity.getName() == "test entity"

def test_newEntity_isNotPlacedAnywhere():
    # pyenvlib's Entity starts with -1 for every placement ID until a location adds it
    entity = DrawableEntity("test entity", (0, 0, 0), False)

    assert entity.getEnvironmentID() == -1
    assert entity.getGridID() == -1
    assert entity.getLocationID() == -1

def test_newEntities_getDistinctIDs():
    first = DrawableEntity("test entity", (0, 0, 0), False)
    second = DrawableEntity("test entity", (0, 0, 0), False)

    assert first.getID() != second.getID()
