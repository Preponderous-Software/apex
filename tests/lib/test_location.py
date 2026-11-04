from lib.pyenvlib.entity import Entity
from lib.pyenvlib.location import Location


# construction tests ---------------------------------------------------------
def test_newLocation_reportsItsCoordinates():
    location = Location(3, 7)

    assert location.getX() == 3
    assert location.getY() == 7

def test_newLocation_isEmpty():
    location = Location(0, 0)

    assert location.getNumEntities() == 0
    assert location.getEntities() == {}

def test_newLocations_getDistinctIDs():
    assert Location(0, 0).getID() != Location(0, 0).getID()

# addEntity tests ------------------------------------------------------------
def test_addEntity_storesTheEntityByItsID():
    location = Location(0, 0)
    entity = Entity("test entity")

    location.addEntity(entity)

    assert location.getNumEntities() == 1
    assert location.getEntities() == {entity.getID(): entity}
    assert location.isEntityPresent(entity)

def test_addEntity_recordsTheLocationOnTheEntity():
    location = Location(0, 0)
    entity = Entity("test entity")

    location.addEntity(entity)

    assert entity.getLocationID() == location.getID()

def test_addEntity_warnsInsteadOfAddingTheSameEntityTwice(capsys):
    location = Location(1, 2)
    entity = Entity("test entity")
    location.addEntity(entity)

    location.addEntity(entity)

    assert location.getNumEntities() == 1
    output = capsys.readouterr().out
    assert "Warning" in output
    assert "test entity" in output
    assert "(1, 2)" in output

def test_addEntity_doesNotClaimAnEntityThatIsAlreadyPresent(capsys):
    location = Location(0, 0)
    entity = Entity("test entity")
    location.addEntity(entity)
    entity.setLocationID("moved elsewhere")

    location.addEntity(entity)

    assert entity.getLocationID() == "moved elsewhere"

# removeEntity tests ---------------------------------------------------------
def test_removeEntity_leavesTheOtherEntitiesInPlace():
    location = Location(0, 0)
    kept = Entity("kept")
    removed = Entity("removed")
    location.addEntity(kept)
    location.addEntity(removed)

    location.removeEntity(removed)

    assert not location.isEntityPresent(removed)
    assert location.isEntityPresent(kept)
    assert location.getNumEntities() == 1

def test_removeEntity_leavesTheLocationIDOnTheEntity():
    location = Location(0, 0)
    entity = Entity("test entity")
    location.addEntity(entity)

    location.removeEntity(entity)

    assert entity.getLocationID() == location.getID()

def test_removeEntity_warnsWhenTheEntityIsNotPresent(capsys):
    location = Location(1, 2)
    location.addEntity(Entity("kept"))

    location.removeEntity(Entity("missing"))

    assert location.getNumEntities() == 1
    output = capsys.readouterr().out
    assert "Warning" in output
    assert "missing" in output
    assert "(1, 2)" in output

# getEntity tests ------------------------------------------------------------
def test_getEntity_returnsTheEntityWithTheGivenID(capsys):
    location = Location(0, 0)
    entity = Entity("test entity")
    location.addEntity(entity)

    assert location.getEntity(entity.getID()) is entity

    assert capsys.readouterr().out == ""

def test_getEntity_warnsAndReturnsNoneForAnUnknownID(capsys):
    location = Location(1, 2)

    assert location.getEntity("unknown id") is None

    output = capsys.readouterr().out
    assert "Warning" in output
    assert "unknown id" in output
    assert "(1, 2)" in output

def test_isEntityPresent_matchesByIDRatherThanName():
    location = Location(0, 0)
    location.addEntity(Entity("test entity"))

    assert not location.isEntityPresent(Entity("test entity"))
