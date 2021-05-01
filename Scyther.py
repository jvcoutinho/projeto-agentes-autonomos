import sc2
from sc2 import Difficulty, Race, maps, run_game
from sc2.player import Bot, Computer
from sc2.unit import Unit

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
            try:
                await manager.start()
            except AttributeError:
                pass


    async def on_step(self, iteration: int):
        for manager in self.managers:
            try:
                await manager.update(iteration)
            except AttributeError:
                pass


    async def on_building_construction_complete(self, unit: Unit):
        for manager in self.managers:
            try:
                await manager.on_structure_built(unit)
            except AttributeError:
                pass


    async def on_unit_destroyed(self, unit_tag: int):
        for manager in self.managers:
            try:
                await manager.on_structure_destroyed(unit_tag)
            except AttributeError:
                pass


run_game(maps.get("AcropolisLE"), [
    Bot(Race.Protoss, Scyther()),
    Computer(Race.Terran, Difficulty.Hard)
], realtime=False)
