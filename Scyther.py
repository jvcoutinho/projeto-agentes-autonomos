import sc2
from sc2 import Difficulty, Race, maps, run_game
from sc2.player import Bot, Computer

from managers.MilitaryManager import MilitaryManager
from managers.ResourcesManager import ResourcesManager
from managers.ScoutingManager import ScoutingManager
from managers.StructureManager import StructureManager


class Scyther(sc2.BotAI):

    def __init__(self):
        super().__init__()
        self.managers = [
            ResourcesManager(self),
            StructureManager(self),
            ScoutingManager(self),
            MilitaryManager(self)
        ]

    async def on_start(self):
        for manager in self.managers:
            await manager.start()

    async def on_step(self, iteration: int):
        for manager in self.managers:
            await manager.update(iteration)


run_game(maps.get("AcropolisLE"), [
    Bot(Race.Protoss, Scyther()),
    Computer(Race.Zerg, Difficulty.Medium)
], realtime=False)
