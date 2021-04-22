import sc2
import math

from sc2 import Difficulty, Race, maps, run_game
from sc2.ids.unit_typeid import UnitTypeId
from sc2.player import Bot, Computer

class ProtossBot(sc2.BotAI):
    locations = []
    destructablePositions = []
    deffenseLineLocation = None
    advancedBaseLocation = None
    
    async def on_start(self):
        self.destructablePositions = [x.position for x in self.destructables]
        self.locations = self.enemy_start_locations[0].sort_by_distance(self.expansion_locations_list)
        self.deffenseLineLocation = self.locations[4]
        self.advancedBaseLocation = self.locations[7]

    async def on_step(self, iteration: int):
        await self.distribute_workers()
        await self.build_workers()
        await self.expand()
        await self.build_pylons()
        
    async def build_workers(self):
        (number_assigned_harvesters, ideal_number_harvesters) = self.count_harvesters()

        for nexus in self.structures(UnitTypeId.NEXUS).ready.idle:
            if self.can_afford(UnitTypeId.PROBE) and number_assigned_harvesters < ideal_number_harvesters:
                nexus.train(UnitTypeId.PROBE)

    async def build_pylons(self):
        if self.supply_left < 5 and not self.already_pending(UnitTypeId.PYLON):
            nexuses = self.structures(UnitTypeId.NEXUS).ready
            if nexuses.exists:
                if self.can_afford(UnitTypeId.PYLON):
                    pylonsInDeffense = self.get_amount_closest_to_nexus(UnitTypeId.PYLON, self.deffenseLineLocation)
                    if pylonsInDeffense < 2:
                        pylonPos = (self.deffenseLineLocation + self.get_closest_destructable(self.deffenseLineLocation)) / 2
                        await self.build(UnitTypeId.PYLON, near=pylonPos, placement_step=3)

    async def expand(self):
        if self.structures(UnitTypeId.NEXUS).amount < 3 and self.can_afford(UnitTypeId.NEXUS) and not self.already_pending(UnitTypeId.NEXUS):
            if not self.location_owned(self.deffenseLineLocation):
                await self.expand_now(location=self.deffenseLineLocation)
            elif not self.location_owned(self.advancedBaseLocation):
                await self.expand_now(location=self.advancedBaseLocation)

    def location_owned(self, location):
        for nexus in self.townhalls:
            if nexus.distance_to(location) < self.EXPANSION_GAP_THRESHOLD:
                return True

        return False

    def get_closest_destructable(self, location):
        positions = location.sort_by_distance(self.destructablePositions)

        return positions[0]

    def get_amount_closest_to_nexus(self, typeId, nexusLocation):
        amount = 0

        for stru in self.structures(typeId).ready:
            if stru.position.closest(self.townhalls).position == nexusLocation:
                amount += 1

        return amount

    async def build_forges(self):
        enemyBase = self.enemy_start_locations[0]

        for nexus in self.structures(UnitTypeId.NEXUS).ready:
            #if nexus.position in self.advanced_posts:
            if not self.structures(UnitTypeId.PYLON).closer_than(15.0, self.closest_spawn_location).exists and self.can_afford(UnitTypeId.PYLON) and not self.already_pending(UnitTypeId.PYLON):
                await self.build(UnitTypeId.PYLON, near=self.closest_spawn_location)
            elif self.structures(UnitTypeId.FORGE).closer_than(20.0, self.closest_spawn_location).amount < 1 and self.can_afford(UnitTypeId.FORGE) and not self.already_pending(UnitTypeId.FORGE):
                await self.build(UnitTypeId.FORGE, near=self.closest_spawn_location)

    async def build_cannons(self):
        if self.structures(UnitTypeId.FORGE).ready.exists:
            forge = self.structures(UnitTypeId.FORGE).random

            if self.can_afford(UnitTypeId.PHOTONCANNON) and not self.already_pending(UnitTypeId.PHOTONCANNON):
                await self.build(UnitTypeId.PHOTONCANNON, near=forge)

    async def attack(self):
        if self.structures(UnitTypeId.PHOTONCANNON).amount > 0 and len(self.enemy_units) > 0:
            for pc in self.structures(UnitTypeId.PHOTONCANNON).idle:
                pc.attack(self.enemy_units.random)

    def count_harvesters(self):
        ideal = 0
        assigned = 0
        for structure in self.structures:
            ideal += structure.ideal_harvesters
            assigned += structure.assigned_harvesters
        return (assigned, ideal)

run_game(maps.get("AcropolisLE"), [
    Bot(Race.Protoss, ProtossBot()),
    Computer(Race.Zerg, Difficulty.Easy)
], realtime=False)