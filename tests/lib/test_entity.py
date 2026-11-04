import datetime

from lib.pyenvlib.entity import Entity


# construction tests ---------------------------------------------------------
def test_newEntity_keepsItsName():
    assert Entity("test entity").getName() == "test entity"

def test_newEntity_isNotPlacedAnywhere():
    entity = Entity("test entity")

    assert entity.getEnvironmentID() == -1
    assert entity.getGridID() == -1
    assert entity.getLocationID() == -1

def test_newEntity_recordsWhenItWasCreated():
    before = datetime.datetime.now()

    entity = Entity("test entity")

    assert before <= entity.getCreationDate() <= datetime.datetime.now()

def test_newEntities_getDistinctIDs():
    assert Entity("test entity").getID() != Entity("test entity").getID()

# setter tests ---------------------------------------------------------------
def test_setters_replaceWhatTheGettersReturn():
    entity = Entity("test entity")
    creationDate = datetime.datetime(2022, 7, 1)

    entity.setID("new id")
    entity.setName("new name")
    entity.setCreationDate(creationDate)
    entity.setEnvironmentID("environment id")
    entity.setGridID("grid id")
    entity.setLocationID("location id")

    assert entity.getID() == "new id"
    assert entity.getName() == "new name"
    assert entity.getCreationDate() == creationDate
    assert entity.getEnvironmentID() == "environment id"
    assert entity.getGridID() == "grid id"
    assert entity.getLocationID() == "location id"

# printInfo tests ------------------------------------------------------------
def test_printInfo_printsEveryField(capsys):
    entity = Entity("test entity")
    entity.setEnvironmentID("environment id")
    entity.setGridID("grid id")
    entity.setLocationID("location id")

    entity.printInfo()

    output = capsys.readouterr().out
    assert "test entity" in output
    assert str(entity.getID()) in output
    assert str(entity.getCreationDate()) in output
    assert "environment id" in output
    assert "grid id" in output
    assert "location id" in output
