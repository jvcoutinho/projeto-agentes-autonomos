import sc2
import math

from sc2 import Difficulty, Race, maps, run_game
from sc2.ids.unit_typeid import UnitTypeId
from sc2.player import Bot, Computer
from sc2.position import Point2

class ProtossBot(sc2.BotAI):
    MAXIMUM_NUMBER_ASSIMILATORS = 2
    MAXIMUM_NUMBER_CANNONS = 3
    MAXIMUM_NUMBER_PYLONS = 4
    MAXIMUM_NUMBER_GATEWAYS = 3

    BATTLE_STATE = "deffense"

    STALKER_ENDPOINT = -1

    locations = []
    deffensePylonsLocation = []
    destructablePositions = []
    deffenseLineLocation = None
    advancedBaseLocation = None
    
    async def on_start(self):
        self.destructablePositions = [x.position for x in self.destructables]
        self.locations = self.enemy_start_locations[0].sort_by_distance(self.expansion_locations_list)
        self.deffenseLineLocation = self.locations[4]
        self.advancedBaseLocation = self.locations[7]
        self.deffense_pylons_location()

    async def on_step(self, iteration: int):
        await self.distribute()
        await self.build_workers()
        await self.expand()
        await self.build_pylons()
        await self.build_forges()
        await self.build_cannons()
        await self.build_gas_buildings()
        await self.build_army_root()
        await self.build_colossus_branch()
        await self.build_stalkers()
        await self.build_colossus()
        await self.attack()

    async def distribute(self):
        if self.idle_worker_count > 0:
            await self.distribute_workers()

    async def build_workers(self):
        (number_assigned_harvesters, ideal_number_harvesters) = self.count_harvesters()

        for nexus in self.structures(UnitTypeId.NEXUS).ready.idle:
            if self.can_afford(UnitTypeId.PROBE) and number_assigned_harvesters < ideal_number_harvesters:
                nexus.train(UnitTypeId.PROBE)

    async def build_gas_buildings(self):

        if self.structures(UnitTypeId.ASSIMILATOR).amount < self.MAXIMUM_NUMBER_ASSIMILATORS:
            baseNexus = self.townhalls.first

            baseAssimilators = self.structures(UnitTypeId.ASSIMILATOR).closer_than(15, baseNexus)
            advancedAssimilators = self.structures(UnitTypeId.ASSIMILATOR).closer_than(15, self.advancedBaseLocation)
            
            if len(baseAssimilators) < 2:
                close_vespene_geysers = self.vespene_geyser.closer_than(15, baseNexus)
                
                for vespene_geyser in close_vespene_geysers:
                    if (
                        self.can_afford(UnitTypeId.ASSIMILATOR)
                        and not self.gas_buildings.closer_than(1, vespene_geyser).exists
                    ):
                        await self.build(UnitTypeId.ASSIMILATOR, max_distance=1, near=vespene_geyser)
            elif len(advancedAssimilators) < 2:
                close_vespene_geysers = self.vespene_geyser.closer_than(15, self.advancedBaseLocation)

                for vespene_geyser in close_vespene_geysers:
                    if (
                        self.can_afford(UnitTypeId.ASSIMILATOR)
                        and not self.gas_buildings.closer_than(1, vespene_geyser).exists
                    ):
                        await self.build(UnitTypeId.ASSIMILATOR, max_distance=1, near=vespene_geyser)

    async def build_pylons(self):
        pylonsOwned = self.structures(UnitTypeId.PYLON).amount

        if (pylonsOwned < self.MAXIMUM_NUMBER_PYLONS or self.supply_left < 5) and not self.already_pending(UnitTypeId.PYLON):
            nexuses = self.structures(UnitTypeId.NEXUS).ready
            if nexuses.exists:
                if self.can_afford(UnitTypeId.PYLON):
                    pylonsInDeffense = len(self.structures(UnitTypeId.PYLON).closer_than(20, self.deffenseLineLocation))
                    pylonsInAdvanced = len(self.structures(UnitTypeId.PYLON).closer_than(20, self.advancedBaseLocation))
                    pylonsInSecondary = len(self.structures(UnitTypeId.PYLON).closer_than(20, self.locations[-2]))
                    
                    if pylonsInDeffense < 2:
                        if await self.can_place_single(UnitTypeId.PYLON, self.deffensePylonsLocation[0]):
                            await self.build(UnitTypeId.PYLON, near=self.deffensePylonsLocation[0], placement_step=1)
                        else:
                            self.MAXIMUM_NUMBER_CANNONS += 3 if self.MAXIMUM_NUMBER_CANNONS == 3 else 0
                            await self.build(UnitTypeId.PYLON, near=self.deffensePylonsLocation[1], placement_step=1)
                    elif pylonsInSecondary < 1:
                        await self.build(UnitTypeId.PYLON, near=self.locations[-2])
                    elif self.location_owned(self.advancedBaseLocation):
                        if pylonsInAdvanced < 1:
                            self.MAXIMUM_NUMBER_ASSIMILATORS += 2 if self.MAXIMUM_NUMBER_ASSIMILATORS == 2 else 0
                            await self.build(UnitTypeId.PYLON, near=self.advancedBaseLocation)
                        else:
                            await self.build(UnitTypeId.PYLON, near=self.start_location)

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

    def deffense_pylons_location(self):
        closestDestructable = self.get_closest_destructable(self.deffenseLineLocation)
        pylonPos = (self.deffenseLineLocation + closestDestructable) / 2
        
        distance = closestDestructable - self.deffenseLineLocation
        x = (self.deffenseLineLocation.x + pylonPos.x) / 2
        y = self.deffenseLineLocation.y + (distance.y * math.cos(math.pi/6))
        secondaryPylonPos = Point2((x, y))

        self.deffensePylonsLocation.append(pylonPos)
        self.deffensePylonsLocation.append(secondaryPylonPos)

    def generate_circle_edge(self, point, radius):
        circleEdge = []

        for angle in range(0, 330, 30):
            x = point.x + (radius * math.cos((angle * math.pi) / 180))
            y = point.y + (radius * math.sin((angle * math.pi) / 180))
            
            position = Point2((x, y))

            circleEdge.append(position)

        return circleEdge

    async def build_forges(self):
        if self.structures(UnitTypeId.PYLON).closer_than(1.0, self.deffensePylonsLocation[0]).ready:
            if self.structures(UnitTypeId.FORGE).amount < 1 and self.can_afford(UnitTypeId.FORGE) and not self.already_pending(UnitTypeId.FORGE):
                location = Point2(((self.deffenseLineLocation.x + self.deffensePylonsLocation[0].x) / 2, self.deffensePylonsLocation[0].y))
                
                await self.build(UnitTypeId.FORGE, near=location)

    async def build_cannons(self):
        if self.structures(UnitTypeId.FORGE).ready.exists and self.structures(UnitTypeId.PHOTONCANNON).amount < self.MAXIMUM_NUMBER_CANNONS:
            if self.can_afford(UnitTypeId.PHOTONCANNON) and not self.already_pending(UnitTypeId.PHOTONCANNON):
                if self.structures(UnitTypeId.PYLON).closer_than(1.0, self.deffensePylonsLocation[1]).exists:
                    possiblePositions = self.generate_circle_edge(self.deffensePylonsLocation[1], 6)
                    possiblePositions = self.enemy_start_locations[0].sort_by_distance(possiblePositions)

                    await self.build(UnitTypeId.PHOTONCANNON, near=self.deffensePylonsLocation[1], placement_step=1)
                else:
                    possiblePositions = self.generate_circle_edge(self.deffensePylonsLocation[0], 5)
                    possiblePositions = self.enemy_start_locations[0].sort_by_distance(possiblePositions)
                    
                    await self.build(UnitTypeId.PHOTONCANNON, near=possiblePositions[0], placement_step=1)

    async def attack(self):
        if self.BATTLE_STATE == "attack":
            for stalker in self.units(UnitTypeId.STALKER).idle:
                stalker.attack(self.enemy_start_locations[0])

                if len(self.enemy_units) > 0:
                    stalker.attack(self.enemy_units.random, queue=True)

            for colossus in self.units(UnitTypeId.COLOSSUS).idle:
                colossus.attack(self.enemy_start_locations[0])

                if len(self.enemy_units) > 0:
                    colossus.attack(self.enemy_units.random, queue=True)
        elif self.BATTLE_STATE == "deffense":
            stalkersInBase = self.units(UnitTypeId.STALKER).idle.closer_than(20, self.locations[-2])

            if len(stalkersInBase) > 5:
                for stalker in stalkersInBase:
                    if self.STALKER_ENDPOINT == -1:
                        stalker.move(self.deffenseLineLocation)
                    else: 
                        stalker.move(self.advancedBaseLocation)

                self.STALKER_ENDPOINT *= -1

            if len(self.enemy_units) > 0:
                for stalker in self.units(UnitTypeId.STALKER).idle:
                    if not stalker in stalkersInBase:
                        stalker.attack(self.enemy_units.random)
        
        if self.structures(UnitTypeId.PHOTONCANNON).amount > 0 and len(self.enemy_units) > 0:
            for pc in self.structures(UnitTypeId.PHOTONCANNON).idle:
                pc.attack(self.enemy_units.random)

    async def build_army_root(self):
        if self.structures(UnitTypeId.GATEWAY).amount < self.MAXIMUM_NUMBER_GATEWAYS and self.structures(UnitTypeId.PYLON).ready:
            gatewayLocation = None

            if len(self.structures(UnitTypeId.GATEWAY).closer_than(20, self.deffenseLineLocation)) < 1:
                location = Point2(((self.deffenseLineLocation.x + self.deffensePylonsLocation[0].x) / 2, self.deffensePylonsLocation[0].y))
                gatewayLocation = self.start_location.sort_by_distance(self.generate_circle_edge(location, 3))[0]
            else:
                gatewayLocation = self.locations[-2]

            if self.can_afford(UnitTypeId.GATEWAY) and not self.already_pending(UnitTypeId.GATEWAY):
                await self.build(UnitTypeId.GATEWAY, near=gatewayLocation)

        elif self.structures(UnitTypeId.GATEWAY).ready:
            if not self.structures(UnitTypeId.CYBERNETICSCORE).exists and self.can_afford(UnitTypeId.CYBERNETICSCORE):
                gateway = self.structures(UnitTypeId.GATEWAY).ready.first
                
                await self.build(UnitTypeId.CYBERNETICSCORE, near=gateway)

    async def build_colossus_branch(self):
        if self.structures(UnitTypeId.ROBOTICSFACILITY).amount < 1:
            advancedPylon = self.structures(UnitTypeId.PYLON).closer_than(20, self.advancedBaseLocation)

            if len(advancedPylon) > 0:
                if self.can_afford(UnitTypeId.ROBOTICSFACILITY) and not self.already_pending(UnitTypeId.ROBOTICSFACILITY):
                    await self.build(UnitTypeId.ROBOTICSFACILITY, near=advancedPylon[0])
        elif self.structures(UnitTypeId.ROBOTICSFACILITY).ready:
            if not self.structures(UnitTypeId.ROBOTICSBAY).exists and self.can_afford(UnitTypeId.ROBOTICSBAY) and not self.already_pending(UnitTypeId.ROBOTICSBAY):
                await self.build(UnitTypeId.ROBOTICSBAY, near=self.structures(UnitTypeId.ROBOTICSFACILITY).ready.first)

    async def build_stalkers(self):
        for gateway in self.structures(UnitTypeId.GATEWAY).ready.idle:
            if self.can_afford(UnitTypeId.STALKER):
                gateway.train(UnitTypeId.STALKER)

    async def build_colossus(self):
        if self.units(UnitTypeId.COLOSSUS).amount >= 5 and not self.BATTLE_STATE == "attack":
            self.BATTLE_STATE = "attack"

        for robotics in self.structures(UnitTypeId.ROBOTICSFACILITY).ready.idle:
            if self.can_afford(UnitTypeId.COLOSSUS):
                robotics.train(UnitTypeId.COLOSSUS)

    def count_harvesters(self):
        ideal = 0
        assigned = 0
        for structure in self.structures:
            ideal += structure.ideal_harvesters
            assigned += structure.assigned_harvesters
        return (assigned, ideal)

run_game(maps.get("AcropolisLE"), [
    Bot(Race.Protoss, ProtossBot()),
    Computer(Race.Zerg, Difficulty.Hard)
], realtime=False)