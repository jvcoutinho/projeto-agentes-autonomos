import sc2
import math

from sc2 import Difficulty, Race, maps, run_game
from sc2.ids.unit_typeid import UnitTypeId
from sc2.player import Bot, Computer
from sc2.position import Point2

class ProtossBot(sc2.BotAI):
    MAXIMUM_NUMBER_CANNONS = 3

    locations = []
    advancedPylonsLocation = []
    destructablePositions = []
    deffenseLineLocation = None
    advancedBaseLocation = None
    
    async def on_start(self):
        self.destructablePositions = [x.position for x in self.destructables]
        self.locations = self.enemy_start_locations[0].sort_by_distance(self.expansion_locations_list)
        self.deffenseLineLocation = self.locations[4]
        self.advancedBaseLocation = self.locations[7]
        self.advanced_pylons_location()

    async def on_step(self, iteration: int):
        await self.distribute()
        await self.build_workers()
        await self.expand()
        await self.build_pylons()
        await self.build_forges()
        await self.build_cannons()
        await self.attack()

    async def distribute(self):
        if self.idle_worker_count > 0:
            await self.distribute_workers()

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
                        if await self.can_place_single(UnitTypeId.PYLON, self.advancedPylonsLocation[0]):
                            await self.build(UnitTypeId.PYLON, near=self.advancedPylonsLocation[0], placement_step=1)
                        else:
                            self.MAXIMUM_NUMBER_CANNONS += 3
                            await self.build(UnitTypeId.PYLON, near=self.advancedPylonsLocation[1], placement_step=1)

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

    def advanced_pylons_location(self):
        closestDestructable = self.get_closest_destructable(self.deffenseLineLocation)
        pylonPos = (self.deffenseLineLocation + closestDestructable) / 2
        
        distance = closestDestructable - self.deffenseLineLocation
        x = (self.deffenseLineLocation.x + pylonPos.x) / 2
        y = self.deffenseLineLocation.y + (distance.y * math.cos(math.pi/6))
        secondaryPylonPos = Point2((x, y))

        self.advancedPylonsLocation.append(pylonPos)
        self.advancedPylonsLocation.append(secondaryPylonPos)

    async def build_forges(self):
        if self.structures(UnitTypeId.PYLON).closer_than(1.0, self.advancedPylonsLocation[0]).ready:
            if self.structures(UnitTypeId.FORGE).amount < 1 and self.can_afford(UnitTypeId.FORGE) and not self.already_pending(UnitTypeId.FORGE):
                location = Point2(((self.deffenseLineLocation.x + self.advancedPylonsLocation[0].x) / 2, self.advancedPylonsLocation[0].y))
                
                await self.build(UnitTypeId.FORGE, near=location)

    async def build_cannons(self):
        if self.structures(UnitTypeId.FORGE).ready.exists and self.structures(UnitTypeId.PHOTONCANNON).amount < self.MAXIMUM_NUMBER_CANNONS:
            if self.can_afford(UnitTypeId.PHOTONCANNON) and not self.already_pending(UnitTypeId.PHOTONCANNON):
                if self.structures(UnitTypeId.PYLON).closer_than(1.0, self.advancedPylonsLocation[1]).ready:
                    await self.build(UnitTypeId.PHOTONCANNON, near=self.advancedPylonsLocation[1], placement_step=2)
                else:
                    await self.build(UnitTypeId.PHOTONCANNON, near=self.advancedPylonsLocation[0], placement_step=2)

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