import sc2
from sc2 import Difficulty, Race, maps, run_game
from sc2.ids.unit_typeid import UnitTypeId
from sc2.player import Bot, Computer

MAXIMUM_NUMBER_NEXUSES = 3
MAXIMUM_NUMBER_GATEWAYS = 3

class ProtossBot(sc2.BotAI):
    async def on_step(self, iteration: int):
        await self.distribute_workers()
        await self.build_workers()
        await self.build_pylons()
        await self.build_assimilator()
        await self.build_gateways()
        await self.build_cybernetics_core()
        await self.build_offensive_force()
        await self.attack()
        await self.expand()


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
                    await self.build(UnitTypeId.PYLON, near=nexuses.first)


    async def expand(self):
        if self.structures(UnitTypeId.NEXUS).amount < MAXIMUM_NUMBER_NEXUSES and self.can_afford(UnitTypeId.NEXUS):
            await self.expand_now()


    async def build_assimilator(self):
        for nexus in self.structures(UnitTypeId.NEXUS).ready:
            vespenes = self.vespene_geyser.closer_than(15.0, nexus)
            for vespene in vespenes:
                if self.can_afford(UnitTypeId.ASSIMILATOR):
                    if not self.units(UnitTypeId.ASSIMILATOR).closer_than(1.0, vespene).exists:
                        await self.build(UnitTypeId.ASSIMILATOR, near=vespene, build_worker=self.select_build_worker(vespene.position)) 


    async def build_gateways(self):
        if self.structures(UnitTypeId.PYLON).ready.exists:
            pylon = self.structures(UnitTypeId.PYLON).ready.random

        gateways = self.structures(UnitTypeId.GATEWAY).ready
        if len(gateways) < MAXIMUM_NUMBER_GATEWAYS:
            if self.can_afford(UnitTypeId.GATEWAY) and not self.already_pending(UnitTypeId.GATEWAY):
                    await self.build(UnitTypeId.GATEWAY, near=pylon)

    
    async def build_cybernetics_core(self):
        if self.structures(UnitTypeId.PYLON).ready.exists:
            pylon = self.structures(UnitTypeId.PYLON).ready.random

        if self.structures(UnitTypeId.GATEWAY).ready.exists:
            if not self.structures(UnitTypeId.CYBERNETICSCORE).exists:
                if self.can_afford(UnitTypeId.CYBERNETICSCORE) and not self.already_pending(UnitTypeId.CYBERNETICSCORE):
                    await self.build(UnitTypeId.CYBERNETICSCORE, near=pylon)

    
    async def build_offensive_force(self):
        for gateway in self.structures(UnitTypeId.GATEWAY).ready.idle:
            if self.can_afford(UnitTypeId.STALKER):
                gateway.train(UnitTypeId.STALKER)

    
    async def attack(self):
        if self.units(UnitTypeId.STALKER).amount > 15:
            for s in self.units(UnitTypeId.STALKER).idle:
                s.attack(self.find_target(self.state))

        elif self.units(UnitTypeId.STALKER).amount > 3:
            if len(self.enemy_units) > 0:
                for s in self.units(UnitTypeId.STALKER).idle:
                    s.attack(self.enemy_units.random)

    
    def find_target(self, state):
        if len(self.enemy_units) > 0:
            return self.enemy_units.random
        elif len(self.enemy_structures) > 0:
            return self.enemy_structures.random
        else:
            return self.enemy_start_locations[0]

    
    def count_harvesters(self):
        ideal = 0
        assigned = 0
        for structure in self.structures:
            ideal += structure.ideal_harvesters
            assigned += structure.assigned_harvesters
        return (assigned, ideal)


run_game(maps.get("AcropolisLE"), [
    Bot(Race.Protoss, ProtossBot()),
    Computer(Race.Zerg, Difficulty.Medium)
], realtime=False)
