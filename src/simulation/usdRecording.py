from entity.livingEntity import LivingEntity

REQUIREMENTS_HINT = "pip install -r requirements-record.txt"


# Records a simulation's history as a time-sampled OpenUSD stage (.usda), one time code per
# tick, with usd-recorder (https://github.com/Preponderous-Software/usd-recorder). Only used
# when the game is started with `--record <path>`; usd-recorder (and usd-core, which it
# depends on) is an optional dependency, imported only then.
#
# Every entity in the environment is recorded at (x, y, layer), where layer is its position in
# its location's stack (the top one is what the game draws), in the game's colour, with its
# kind (class name) and, for living entities, its energy. The stage carries per-tick counts.
#
# @author Daniel McCoy Stephenson
class UsdRecording:
    TIME_CODES_PER_SECOND = 30

    @staticmethod
    def isAvailable():
        try:
            import usd_recorder  # noqa: F401
        except ImportError:
            return False
        return True

    def __init__(self, path, gridSize=None):
        try:
            from usd_recorder import Recorder
        except ImportError as error:
            raise RuntimeError("recording needs the optional usd-recorder package: " + REQUIREMENTS_HINT) from error
        metadata = {"apex:gridSize": gridSize} if gridSize is not None else None
        self.path = path
        self.__recorder = Recorder(path, time_codes_per_second=self.TIME_CODES_PER_SECOND, metadata=metadata)
        # pyenvlib ids are UUIDs; the stage numbers entities in the order they first appear
        self.__recordedIds = {}
        self.__ticksRecorded = 0

    def getTicksRecorded(self):
        return self.__ticksRecorded

    # Records the state of the simulation at its current tick.
    def recordTick(self, simulation):
        entities = {}
        counts = {"livingEntities": 0, "grass": 0, "excrement": 0}
        for location in simulation.environment.getGrid().getLocations().values():
            for layer, entity in enumerate(location.getEntities().values()):
                values = {
                    "position": (location.getX(), location.getY(), layer),
                    "color": tuple(channel / 255 for channel in entity.getColor()),
                    "kind": type(entity).__name__,
                }
                if isinstance(entity, LivingEntity):
                    values["energy"] = int(entity.getEnergy())
                    counts["livingEntities"] += 1
                elif type(entity).__name__ == "Grass":
                    counts["grass"] += 1
                elif type(entity).__name__ == "Excrement":
                    counts["excrement"] += 1
                entities[self.__recordedId(entity)] = values
        self.__recorder.record(simulation.getNumTicks(), entities=entities, extras=counts)
        self.__ticksRecorded += 1

    # Writes the stage and returns its path.
    def close(self):
        self.__recorder.close()
        return self.path

    def __recordedId(self, entity):
        entityId = entity.getID()
        if entityId not in self.__recordedIds:
            self.__recordedIds[entityId] = len(self.__recordedIds)
        return self.__recordedIds[entityId]
