from ui.textAlert import TextAlert

class TextAlertFactory:

    def createTextAlertForLocationInfo(self, location, simulation, config):
        x = location.getX() * simulation.locationWidth
        y = location.getY() * simulation.locationHeight
        numEntities = location.getNumEntities()
        newAlert = TextAlert(x + 20, y + 100, 20, config.black, 10)
        newAlert.cell = (location.getX(), location.getY())
        newAlert.addLine("Location (" + str(location.getX()) + ", " + str(location.getY()) + ")")
        newAlert.addLine("Number of entities: " + str(numEntities))
        
        entityNames = []
        for entityId in location.getEntities():
            entity = location.getEntities()[entityId]
            entityNames.append(entity.getName())
        # print occurrences
        for entityName in set(entityNames):
            numOccurrences = entityNames.count(entityName)
            newAlert.addLine(entityName + ": " + str(numOccurrences))
            y += 20
        
        return newAlert